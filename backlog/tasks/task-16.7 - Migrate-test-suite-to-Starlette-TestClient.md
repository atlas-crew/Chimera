---
id: TASK-16.7
title: Migrate test suite to Starlette TestClient
status: To Do
assignee: []
created_date: '2026-04-12 04:08'
updated_date: '2026-04-12 04:09'
labels:
  - refactor
dependencies:
  - TASK-16.1
  - TASK-16.2
  - TASK-16.3
  - TASK-16.4
  - TASK-16.6
parent_task_id: TASK-16
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the 577 unit tests (632 including new additions) from Flask test_client() to Starlette's TestClient. The Starlette TestClient is nearly API-compatible with Flask's — the biggest change is in conftest.py fixtures and a few session-transaction helpers.

## Changes required

### tests/conftest.py (600+ lines)
- `from app import create_app` → `from app.asgi import create_app`
- `app = create_app()` → same (factory signature compatible)
- `app.config.update({'TESTING': True})` → handled via init_config({'TESTING': True})
- `app.test_client()` → `TestClient(app)` (from starlette.testclient)
- `app.test_cli_runner()` → remove (no equivalent, unused)
- The `reset_databases` autouse fixture and all in-memory db dicts stay as-is (framework-agnostic)

### session_transaction usages (4 total)
Currently uses Flask's `client.session_transaction()` context manager to pre-populate session cookies:
- tests/conftest.py:601 (authenticated_session fixture)
- tests/unit/test_auth_routes.py:520, 541, 858

Replacement: set session cookie directly via httpx.
```python
# Before (Flask)
with client.session_transaction() as sess:
    sess['user_id'] = '123'

# After (Starlette)
from itsdangerous import TimestampSigner
signer = TimestampSigner(secret_key)
cookie = signer.sign(json.dumps({'user_id': '123'}).encode()).decode()
client.cookies.set('session', cookie)
```
Or use a helper fixture that calls a login endpoint.

### response API changes
- `response.get_json()` → `response.json()` (codemod handles in-file tests)
- `response.status_code` → same
- `response.data` → `response.content` (for bytes) or `response.text` (for str)
- `response.headers` → same

## Process
1. Update conftest.py fixtures
2. Run tests — many will pass immediately
3. Fix response.get_json() → response.json() via codemod or sed
4. Fix response.data → response.content/text
5. Fix 4 session_transaction usages
6. Iterate on failures

## Dependencies
- Depends on: all blueprint migrations (Tier 1-5)
- Depends on: TASK-16.6 (middleware) for error handler tests
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 conftest.py uses Starlette TestClient
- [ ] #2 All response.get_json() calls replaced with response.json()
- [ ] #3 4 session_transaction usages replaced with direct cookie setting or login helpers
- [ ] #4 Full test suite passes (632 tests or close, with any Flask-only tests removed or ported)
- [ ] #5 Coverage maintained (spot-check via pytest --cov)
<!-- AC:END -->
