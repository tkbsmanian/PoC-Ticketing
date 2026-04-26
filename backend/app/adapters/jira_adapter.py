"""
JIRA Cloud adapter.
All JIRA REST API calls are made exclusively from this module.
Implements the SyncAdapter interface from domain/interfaces.py.
"""

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx

from app.adapters.jira_mappings import (
    PORTAL_PRIORITY_TO_JIRA,
    PORTAL_STATUS_TO_JIRA,
)
from app.adapters.jira_utils import build_labels, to_adf, truncate_summary
from app.core.config import Settings
from app.domain.exceptions import SyncAdapterError, SyncTransientError
from app.domain.interfaces import ExternalTaskRef, SyncAdapter

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [10, 30, 90]  # seconds — used by SyncWorker, not this adapter directly
_CACHE_TTL_SECONDS = 3600


class JiraAdapter(SyncAdapter):
    """
    JIRA Cloud REST API v3 adapter.
    Credentials are read from Settings — never hardcoded.
    """

    def __init__(self, settings: Settings):
        self._base_url = settings.JIRA_BASE_URL.rstrip("/")
        self._project_key = settings.JIRA_PROJECT_KEY
        self._issue_type = settings.JIRA_ISSUE_TYPE
        self._auth = (settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN)
        self._client = httpx.Client(
            auth=self._auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15.0,
        )
        self._create_meta_cache: dict = {}
        self._cache_fetched_at: datetime | None = None
        self._reporter_cache: dict[str, str] = {}  # email → accountId

    # ── SyncAdapter interface ─────────────────────────────────────────────────

    def create_task(
        self,
        ticket_id: str,
        title: str,
        description: str,
        department: str,
        urgency: str,
        cost: float | None,
        submitter_name: str,
        submitter_email: str,
        category: str | None,
        priority: str | None,
    ) -> ExternalTaskRef:
        # Idempotency: check if issue already exists by portal-id label
        existing_id = self._find_existing_issue(ticket_id)
        if existing_id:
            logger.info(
                "JIRA issue already exists — skipping creation",
                extra={"ticket_id": ticket_id, "jira_id": existing_id},
            )
            return ExternalTaskRef(
                external_id=existing_id,
                external_url=self.get_task_url(existing_id),
            )

        meta = self._get_create_meta()
        labels = build_labels(
            ticket_id=ticket_id,
            department=department,
            urgency=urgency,
            category=category,
            cost=cost,
            director_required=cost is not None and cost > 0,
        )
        payload: dict = {
            "fields": {
                "project": {"key": self._project_key},
                "issuetype": {"name": self._issue_type},
                "summary": truncate_summary(ticket_id, title),
                "description": to_adf(description),
                "labels": labels,
            }
        }
        if priority and "priority" in meta:
            payload["fields"]["priority"] = {"name": PORTAL_PRIORITY_TO_JIRA.get(priority, priority)}
        if "reporter" in meta:
            account_id = self._lookup_reporter(submitter_email)
            if account_id:
                payload["fields"]["reporter"] = {"id": account_id}

        resp = self._post(f"{self._base_url}/rest/api/3/issue", json=payload)
        jira_id = resp["id"]
        jira_key = resp["key"]
        jira_url = f"{self._base_url}/browse/{jira_key}"
        logger.info(
            "JIRA issue created",
            extra={"ticket_id": ticket_id, "jira_task_id": jira_id},
        )
        return ExternalTaskRef(external_id=jira_id, external_url=jira_url)

    def update_status(self, external_id: str, portal_status: str) -> None:
        jira_status = PORTAL_STATUS_TO_JIRA.get(portal_status, portal_status)
        transition_id = self._get_transition_id(external_id, jira_status)
        if not transition_id:
            raise SyncAdapterError(
                f"Transition to '{jira_status}' not available for issue {external_id}."
            )
        self._post(
            f"{self._base_url}/rest/api/3/issue/{external_id}/transitions",
            json={"transition": {"id": transition_id}},
        )

    def add_comment(
        self, external_id: str, author_name: str, body: str, is_internal: bool
    ) -> None:
        # Internal comments must never be synced — caller is responsible for filtering,
        # but we guard here as a safety net.
        if is_internal:
            return
        formatted_body = f"[Portal] {author_name}: {body}"
        self._post(
            f"{self._base_url}/rest/api/3/issue/{external_id}/comment",
            json={"body": to_adf(formatted_body)},
        )

    def attach_file(
        self, external_id: str, filename: str, file_path: str, mime_type: str
    ) -> None:
        with open(file_path, "rb") as f:
            resp = self._client.post(
                f"{self._base_url}/rest/api/3/issue/{external_id}/attachments",
                headers={
                    "X-Atlassian-Token": "no-check",
                    "Accept": "application/json",
                },
                files={"file": (filename, f, mime_type)},
            )
        self._raise_for_status(resp)

    def get_task_url(self, external_id: str) -> str:
        resp = self._get(f"{self._base_url}/rest/api/3/issue/{external_id}?fields=key")
        key = resp["key"]
        return f"{self._base_url}/browse/{key}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_create_meta(self) -> dict:
        now = datetime.now(timezone.utc)
        if (
            not self._cache_fetched_at
            or (now - self._cache_fetched_at).seconds > _CACHE_TTL_SECONDS
        ):
            url = (
                f"{self._base_url}/rest/api/3/issue/createmeta"
                f"?projectKeys={self._project_key}"
                f"&issuetypeNames={quote(self._issue_type)}"
                f"&expand=projects.issuetypes.fields"
            )
            data = self._get(url)
            fields: dict = {}
            try:
                fields = (
                    data["projects"][0]["issuetypes"][0]["fields"]
                )
            except (KeyError, IndexError):
                logger.warning("Could not parse create metadata — using empty field set.")
            self._create_meta_cache = fields
            self._cache_fetched_at = now
        return self._create_meta_cache

    def _get_transition_id(self, jira_id: str, target_status: str) -> str | None:
        data = self._get(f"{self._base_url}/rest/api/3/issue/{jira_id}/transitions")
        for t in data.get("transitions", []):
            if t["to"]["name"].lower() == target_status.lower():
                return t["id"]
        return None

    def _find_existing_issue(self, ticket_id: str) -> str | None:
        jql = f'project = {self._project_key} AND labels = "portal-id:{ticket_id}"'
        data = self._get(
            f"{self._base_url}/rest/api/3/search?jql={quote(jql)}&maxResults=1&fields=id,key"
        )
        issues = data.get("issues", [])
        return issues[0]["id"] if issues else None

    def _lookup_reporter(self, email: str) -> str | None:
        if email in self._reporter_cache:
            return self._reporter_cache[email]
        try:
            data = self._get(
                f"{self._base_url}/rest/api/3/user/search?query={quote(email)}&maxResults=1"
            )
            if data:
                account_id = data[0]["accountId"]
                self._reporter_cache[email] = account_id
                return account_id
        except Exception:
            pass
        return None

    def _get(self, url: str) -> dict:
        resp = self._client.get(url)
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, url: str, json: dict) -> dict:
        resp = self._client.post(url, json=json)
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code in (200, 201, 204):
            return
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            raise SyncTransientError(f"Rate limited. Retry after {retry_after}s.")
        if resp.status_code >= 500:
            raise SyncTransientError(f"JIRA server error {resp.status_code}.")
        # 400, 401, 403, 404 — permanent
        error_body = resp.text[:500]
        raise SyncAdapterError(
            f"JIRA permanent error {resp.status_code}: {error_body}"
        )
