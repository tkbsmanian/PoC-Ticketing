"""
Unit tests for JIRA adapter utilities and adapter logic using mock HTTP client.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.adapters.jira_mappings import PORTAL_PRIORITY_TO_JIRA, PORTAL_STATUS_TO_JIRA
from app.adapters.jira_utils import build_labels, to_adf, truncate_summary
from app.domain.exceptions import SyncAdapterError, SyncTransientError


# ── ADF conversion ────────────────────────────────────────────────────────────

def test_to_adf_single_paragraph():
    result = to_adf("Hello world")
    assert result["version"] == 1
    assert result["type"] == "doc"
    assert result["content"][0]["type"] == "paragraph"
    assert result["content"][0]["content"][0]["text"] == "Hello world"


def test_to_adf_multiline_creates_multiple_paragraphs():
    result = to_adf("Line one\nLine two\nLine three")
    assert len(result["content"]) == 3


def test_to_adf_empty_string():
    result = to_adf("")
    assert len(result["content"]) == 1
    assert result["content"][0]["content"][0]["text"] == ""


# ── Summary truncation ────────────────────────────────────────────────────────

def test_truncate_summary_short():
    assert truncate_summary("TKT-001", "Short title") == "[TKT-001] Short title"


def test_truncate_summary_long_title():
    long_title = "A" * 300
    result = truncate_summary("TKT-001", long_title)
    assert len(result) <= 255
    assert result.startswith("[TKT-001]")


# ── Label building ────────────────────────────────────────────────────────────

def test_build_labels_basic():
    labels = build_labels("TKT-001", "Finance", "Medium")
    assert "portal-id:TKT-001" in labels
    assert "dept:Finance" in labels
    assert "urgency:Medium" in labels


def test_build_labels_with_cost():
    labels = build_labels("TKT-002", "IT", "Low", cost=500.0)
    assert "cost:yes" in labels


def test_build_labels_no_cost():
    labels = build_labels("TKT-003", "IT", "Low", cost=0)
    assert "cost:yes" not in labels


def test_build_labels_director_required():
    labels = build_labels("TKT-004", "IT", "High", director_required=True)
    assert "director-approval:required" in labels


# ── Priority mapping ──────────────────────────────────────────────────────────

def test_critical_maps_to_highest():
    assert PORTAL_PRIORITY_TO_JIRA["Critical"] == "Highest"


def test_all_priorities_mapped():
    for p in ["Low", "Medium", "High", "Critical"]:
        assert p in PORTAL_PRIORITY_TO_JIRA


# ── Status mapping ────────────────────────────────────────────────────────────

def test_all_statuses_mapped():
    expected = ["Pending", "Approved", "In Review", "In Progress",
                "Resolved", "Closed", "Rejected", "Removed"]
    for s in expected:
        assert s in PORTAL_STATUS_TO_JIRA


# ── Internal comment not synced ───────────────────────────────────────────────

def test_internal_comment_not_synced():
    """Internal comments must never be sent to JIRA."""
    import os
    os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
    os.environ.setdefault("JIRA_BASE_URL", "https://mock.atlassian.net")
    os.environ.setdefault("JIRA_USER_EMAIL", "test@example.com")
    os.environ.setdefault("JIRA_API_TOKEN", "mock-token")

    from app.core.config import Settings
    settings = Settings(
        SECRET_KEY="test-secret-key-32-bytes-minimum!!",
        JIRA_BASE_URL="https://mock.atlassian.net",
        JIRA_USER_EMAIL="test@example.com",
        JIRA_API_TOKEN="mock-token",
    )
    from app.adapters.jira_adapter import JiraAdapter
    adapter = JiraAdapter(settings)

    with patch.object(adapter, "_post") as mock_post:
        adapter.add_comment("JIRA-1", "Jane", "Internal note", is_internal=True)
        mock_post.assert_not_called()


# ── create_task returns ExternalTaskRef ───────────────────────────────────────

def test_create_task_returns_external_task_ref():
    import os
    os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")

    from app.core.config import Settings
    settings = Settings(
        SECRET_KEY="test-secret-key-32-bytes-minimum!!",
        JIRA_BASE_URL="https://mock.atlassian.net",
        JIRA_USER_EMAIL="test@example.com",
        JIRA_API_TOKEN="mock-token",
    )
    from app.adapters.jira_adapter import JiraAdapter
    adapter = JiraAdapter(settings)

    with patch.object(adapter, "_find_existing_issue", return_value=None), \
         patch.object(adapter, "_get_create_meta", return_value={}), \
         patch.object(adapter, "_lookup_reporter", return_value=None), \
         patch.object(adapter, "_post", return_value={"id": "10001", "key": "BB-1", "url": ""}):

        ref = adapter.create_task(
            ticket_id="TKT-001",
            title="Test",
            description="Desc",
            department="IT",
            urgency="Low",
            cost=None,
            submitter_name="Jane",
            submitter_email="jane@example.com",
            category=None,
            priority=None,
        )
        assert ref.external_id == "10001"
        assert "BB-1" in ref.external_url


# ── Duplicate prevention ──────────────────────────────────────────────────────

def test_create_task_skips_if_existing_issue_found():
    import os
    os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")

    from app.core.config import Settings
    settings = Settings(
        SECRET_KEY="test-secret-key-32-bytes-minimum!!",
        JIRA_BASE_URL="https://mock.atlassian.net",
        JIRA_USER_EMAIL="test@example.com",
        JIRA_API_TOKEN="mock-token",
    )
    from app.adapters.jira_adapter import JiraAdapter
    adapter = JiraAdapter(settings)

    with patch.object(adapter, "_find_existing_issue", return_value="10042"), \
         patch.object(adapter, "_post") as mock_post, \
         patch.object(adapter, "get_task_url", return_value="https://mock/BB-42"):

        ref = adapter.create_task(
            ticket_id="TKT-001", title="T", description="D",
            department="IT", urgency="Low", cost=None,
            submitter_name="Jane", submitter_email="j@e.com",
            category=None, priority=None,
        )
        mock_post.assert_not_called()
        assert ref.external_id == "10042"
