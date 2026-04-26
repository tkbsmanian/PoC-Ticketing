---
inclusion: always
---

# Testing Standards

All generated code must include tests. Untested code is not considered complete.

## Test Structure

```
backend/
  tests/
    unit/           ← Pure logic tests, no DB or HTTP
    integration/    ← Tests against real SQLite test DB
    property/       ← Hypothesis property-based tests
    smoke/          ← Startup and connectivity checks
frontend/
  src/
    __tests__/      ← Component and hook tests (Jest + React Testing Library)
```

## Coverage Requirements

- Domain logic (`domain/`) MUST have unit test coverage for every public function
- Status transition guard MUST be tested for every valid and every invalid transition pair
- `director_approval_required` computation MUST be tested for all 8 combinations of urgency × cost
- Every Pydantic schema MUST have at least one test for a valid payload and one for each required field missing
- Every API endpoint MUST have at least one integration test covering the happy path and one covering a 403 unauthorized case
- JIRA adapter MUST be tested using a mock HTTP client — never call real JIRA in tests

## Property-Based Tests (Hypothesis)

Use `hypothesis` for all 10 correctness properties defined in the design document. Each test file must include the property reference comment:

```python
# Feature: internal-ticketing-system, Property N: <property name>
```

Minimum 100 examples per property. Run with `pytest --hypothesis-seed=0` for reproducibility.

## Test Isolation Rules

- Integration tests MUST use a separate in-memory or temp-file SQLite database — never the development database
- Each integration test MUST set up and tear down its own data — no shared mutable state between tests
- Tests MUST NOT make real HTTP calls to JIRA, SMTP, or any external service — use `pytest-httpx` or `unittest.mock`
- Tests MUST NOT read from `.env` files — use `pytest` fixtures to inject test configuration

## Test Naming Convention

```python
# Unit: test_<module>_<function>_<scenario>
def test_ticket_lifecycle_transition_pending_to_approved_valid(): ...
def test_ticket_lifecycle_transition_closed_to_any_raises(): ...

# Integration: test_<endpoint>_<scenario>
def test_post_tickets_valid_payload_returns_201(): ...
def test_post_tickets_missing_title_returns_422(): ...
def test_get_tickets_business_user_sees_only_own(): ...
```

## Running Tests

```bash
# All tests
pytest

# Unit only (fast)
pytest tests/unit/

# With coverage report
pytest --cov=app --cov-report=term-missing

# Property tests with verbose output
pytest tests/property/ -v --hypothesis-show-statistics
```
