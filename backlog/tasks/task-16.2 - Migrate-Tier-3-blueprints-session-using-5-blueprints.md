---
id: TASK-16.2
title: 'Migrate Tier 3 blueprints (session-using, 5 blueprints)'
status: To Do
assignee: []
created_date: '2026-04-12 04:07'
labels:
  - refactor
dependencies: []
parent_task_id: TASK-16
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Run the codemod on 5 Tier 3 blueprints that use Flask session state, and verify the session migration path to Starlette's SessionMiddleware works correctly.

## Blueprints
- education (73 lines) — `session.get('user_id')`
- checkout (124 lines) — `session.get('session_id')`
- mobile (146 lines) — `session.get('user_id')`
- saas (567 lines) — `session['tenant_id']`
- payments (683 lines) — `session.get('customer_id')`

## Session handling
The codemod already rewrites `session['key']` → `request.session['key']` and `session.get(...)` → `request.session.get(...)`. Starlette's SessionMiddleware (already configured in app/asgi.py with cfg.secret_key) stores session data in a signed cookie — same mechanism Flask uses by default.

## Process
Same as Tier 2, but verify session behavior:
1. Run codemod
2. Manual review for session keys and any session.pop() / session.clear() calls
3. Update __init__.py and wire into asgi.py
4. Smoke test a session-requiring flow (e.g., login → authenticated endpoint)

## Gotchas
- Session cookies from Flask won't be readable by Starlette unless the secret_key matches — they use different signing algorithms. Fresh login required on cutover.
- Any blueprint-level `@bp.before_request` hooks (e.g., education/routes.py:12 `check_access()`) need manual conversion to Starlette middleware or moved into the handler body.

## Reference
- Tier 1 reference commit: 990741b
- Tier 2 subtask: TASK-16.1
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 5 Tier 3 blueprints transformed by codemod
- [ ] #2 Session state correctly flows through request.session
- [ ] #3 education check_access hook converted (to middleware or inline)
- [ ] #4 Flask factory no longer imports Tier 3 blueprints
- [ ] #5 Session-requiring endpoint smoke tests pass on uvicorn
- [ ] #6 Flask test suite still passes
<!-- AC:END -->
