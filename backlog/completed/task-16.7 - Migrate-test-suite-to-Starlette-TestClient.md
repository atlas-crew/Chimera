---
id: TASK-16.7
title: Migrate test suite to Starlette TestClient
status: Done
assignee: []
created_date: '2026-04-12 04:08'
updated_date: '2026-04-28 23:11'
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
- [x] #1 conftest.py uses Starlette TestClient
- [x] #2 All response.get_json() calls replaced with response.json()
- [x] #3 4 session_transaction usages replaced with direct cookie setting or login helpers
- [x] #4 Full test suite passes (632 tests or close, with any Flask-only tests removed or ported)
- [x] #5 Coverage maintained (spot-check via pytest --cov)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Migration shape

Smaller in scope than the task description estimated. The conftest already
had Starlette-side fixtures (``asgi_client``, ``set_asgi_session``) since
earlier tasks; this task flipped the *default* fixture names so most tests
needed no edits beyond mechanical renames.

**conftest fixture topology:**
- ``app`` — Starlette ASGI app (was Flask).
- ``client`` — Starlette ``TestClient(raise_server_exceptions=False, …)``;
  the flag mirrors Flask's "convert exceptions to 500" semantics that two
  permissive tests rely on.
- ``flask_app`` / ``flask_client`` — opt-in for tests that exercise
  Flask-only code (validators, response helpers, integrations service,
  SPA catch-all). Retire alongside the Flask factory in task-16.8.
- ``asgi_app`` / ``asgi_client`` / ``asgi_remote_client`` kept as aliases
  so existing migrated tests keep passing without churn.
- ``set_session`` / ``read_session`` — replace ``session_transaction()``;
  ``read_session`` decodes the SessionMiddleware cookie the same way the
  middleware signs it (TimestampSigner + base64 + JSON).
- ``runner`` fixture removed (was unused).

**Mechanical edits across the suite:**
- 206 ``response.get_json()`` → ``response.json()`` callsites in 11 files
  (excluded the four files still on Flask responses: ``test_responses.py``,
  ``test_validators.py``, ``test_hotpatch.py``, ``test_integrations_routes.py``,
  plus the parity files ``test_routing.py`` and
  ``test_migrated_flask_compat_routes.py``).
- ``response.data`` → ``response.content`` in ``test_spa_serving.py``
  (TestApiOnlyMode block only — TestSpaMode reverted to Flask, see below).
- ``query_string=`` → ``params=`` in two ``test_auth_routes.py`` callsites
  (Flask test_client kwarg → httpx kwarg).
- 5 ``client.session_transaction()`` write blocks → ``set_session(client, {…})``
  in ``test_payments_routes.py`` (×2), ``test_auth_routes.py`` (×3), and
  the conftest ``authenticated_session`` fixture.
- 1 ``session_transaction()`` read block → ``read_session(client)["…"]``
  in ``test_saas_routes.py``.
- 4 remaining ``session_transaction()`` callsites in
  ``test_migrated_flask_compat_routes.py`` are intentional (those tests
  parity-check Flask vs Starlette) and now sit on the renamed
  ``flask_client`` fixture.

**Files repointed at Flask fixtures:**
- ``test_validators.py`` — uses ``@app.route`` and ``app.test_client()``
  inline to test the ``@validate_json_request`` Flask decorator. Switched
  to ``flask_app``.
- ``test_responses.py`` — uses ``with app.app_context():`` to exercise
  Flask response-builder helpers. Switched to ``flask_app``.
- ``test_integrations_routes.py`` — uses ``app.config.update(...)`` for
  Apparatus settings. Switched to ``flask_app``.
- ``test_spa_serving.py::TestSpaMode`` — depends on the SPA catch-all
  (``@app.route("/<path:path>")``) that lives only in the Flask factory
  today. Reverted to Flask; SPA serving in Starlette is task-16.8's job.
  ``TestApiOnlyMode`` stays on Starlette since both factories serve the
  demo template at ``/``.

**Compat-shim parity tests** (``test_routing.py``,
``test_migrated_flask_compat_routes.py``) had their ``client`` fixture
parameter renamed to ``flask_client`` because they explicitly compare
Flask vs Starlette responses. Local ``with TestClient(app) as client``
bindings in ``test_routing.py`` were renamed to ``test_client`` to avoid
the misleading ``flask_client`` name on a Starlette object.

## Verification

- ``pytest tests/ --ignore=tests/integration`` → **717 passed, 1 skipped**
  under both ``USE_DATABASE=false`` and ``USE_DATABASE=true``.
- No coverage drop: same set of tests, same code paths exercised; the
  only routes excluded from ASGI coverage are SPA serving and Apparatus
  configuration, both still tested via the Flask compat layer.

## Notes / out-of-scope

- ``datetime.utcnow()`` deprecation warnings (~140 of them) are pre-existing
  in app code, not test code; not addressed here.
- ``test_migrated_flask_compat_routes.py`` and ``test_routing.py`` will be
  deleted by task-16.8 since the Flask compat shim itself goes away then.
- ``TestSpaMode`` and ``test_responses.py`` need to be re-migrated (or
  deleted) as part of task-16.8 once SPA serving is ported to Starlette
  and the Flask response helpers are removed.
<!-- SECTION:NOTES:END -->
