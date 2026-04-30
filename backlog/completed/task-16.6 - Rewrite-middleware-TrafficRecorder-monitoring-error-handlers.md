---
id: TASK-16.6
title: 'Rewrite middleware (TrafficRecorder, monitoring, error handlers)'
status: Done
assignee: []
created_date: '2026-04-12 04:08'
updated_date: '2026-04-28 18:09'
labels:
  - refactor
dependencies: []
parent_task_id: TASK-16
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port Flask-coupled middleware and error handlers to Starlette equivalents.

## 1. TrafficRecorder — app/middleware/traffic_recorder.py (68 lines)
- `g.start_time = time.time()` → `request.state.start_time = time.time()`
- `app.before_request` / `app.after_request` hooks → Starlette `BaseHTTPMiddleware.dispatch()` method
- Reads from RECORD_TRAFFIC env var — no Flask coupling beyond g and hooks

## 2. Request ID / Monitoring — app/utils/monitoring.py (~500 lines)
- All 12 `flask.g` usages across 3 files become `request.state.*`
- `@app.before_request` (line 473) injects X-Request-ID → Starlette middleware
- `@app.after_request` (line 482) copies request_id to response header → same middleware's dispatch method
- `has_request_context()` checks (lines 48, 56, 296, 346) can be removed (always true in middleware)

## 3. Error handlers — app/error_handlers.py (308 lines)
- `DemoErrorHandler` class with `app.register_error_handler(code, fn)` → Starlette `app.add_exception_handler(code, fn)`
- Intentional info leakage (by design for WAF testing) must be preserved:
  - request.headers, args, form, cookies, body
  - Exception stack traces when debug=true
  - Stack frame locals
- `request.environ`, `request.blueprint`, `request.endpoint` → Starlette scope equivalents
- `app.url_map.iter_rules()` → `app.routes` introspection
- `request.authorization` → parse Authorization header manually

## 4. auth_helpers — app/utils/auth_helpers.py
- `g.user_id`, `g.auth_method`, `g.token_payload`, `g.api_key` (lines 317-334) → `request.state.*`
- This file is imported by many routes; may need a request parameter threading pass

## Dependencies
- Can run in parallel with blueprint migrations
- Blocks: final infrastructure cutover (TASK-16.7)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 TrafficRecorder works as Starlette middleware
- [ ] #2 Request ID middleware injects X-Request-ID
- [x] #3 Error handlers preserve intentional info leakage patterns
- [ ] #4 auth_helpers uses request.state instead of flask.g
- [ ] #5 All error scenarios tested (400, 401, 403, 404, 500, generic Exception)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Three atomic commits delivered the load-bearing scope. ACs #2 and #4 were scoped out per a deliberate "delete dead code" decision; AC #5 was smoke-verified but no new automated tests were added.

## Commits
- `af09f87` feat(api): add Starlette TrafficRecorder middleware (sub-task A)
- `fed70d0` feat(api): port DemoErrorHandler to Starlette exception handlers (sub-task B)
- `464dc0e` refactor(api): delete unused Flask-coupled helpers in app/utils (sub-task C)

## AC reconciliation
- AC #1 ✅ TrafficRecorderMiddleware mirrors Flask's RECORD_TRAFFIC behavior with the same JSON entry schema. Smoke-tested: GET + POST both logged with method/path/status/duration/body.
- AC #2 ⚠ Scoped out. The original `request_id_middleware` in `app/utils/monitoring.py` was exported but had zero callers (verified by grep across `app/`, `tests/`, `scripts/`); it was never wired into the Flask factory. Per the user-approved sub-task C scope, dead code was deleted rather than ported. If X-Request-ID propagation is wanted later, it's a small follow-up (~20 lines of ASGI middleware) — but no current consumer needs it.
- AC #3 ✅ DemoErrorHandler ported to `app/error_handlers_asgi.py`. Every documented info leak preserved: headers, args, cookies, body (via BodyBufferMiddleware), content_type/length, JSON body, raw body, environment block, exception details with stack trace AND frame locals. Per-status extras: auth_debug (401, with Basic-auth username extraction), permission_debug (403), routing_debug (404, leaks all 484 routes), system_debug (500). Top-level field shape matches `build_http_exception_body` for parity with the Flask compat shim — verbose leak fields ship alongside, not in place of, the baseline shape.
- AC #4 ⚠ Scoped out. `g.user_id`, `g.auth_method`, `g.token_payload`, `g.api_key` lived in `require_auth` / `require_role`, both of which had zero callers and were deleted in sub-task C. `auth_helpers.py` now has zero Flask imports — the spirit of the AC (decouple from Flask) is satisfied; the literal text (use `request.state` instead) is moot because the affected code is gone.
- AC #5 ⚠ Partially met. Each error scenario (400, 401, 403, 404, 500, generic Exception) was smoke-tested manually via `TestClient` and the verbose leak surface verified — but no new automated tests were added. The existing `test_migrated_flask_compat_routes.py` parity tests (35 passing) exercise the baseline error contract through both Flask and ASGI clients, so the field shape (`error`, `status`, `path`, `method`, `debug.headers`, `debug.query_params`) is regression-protected. The verbose extras (`leaked_data`, `stack_frames`, etc.) are not. **Recommended follow-up**: add `tests/unit/test_error_handlers_asgi.py` covering each per-status handler — could land alongside or in task-16.7 (test suite TestClient port).

## Suite delta
- Before: 739 passed, 1 skipped
- After: 717 passed, 1 skipped (22-test drop is exactly the deleted-symbol test coverage)
- All parity tests pass: `test_migrated_flask_compat_routes.py` 35/35

## What this unblocks for task-16.8 cutover
- TrafficRecorder no longer requires Flask hooks.
- Error handling no longer requires Flask `register_error_handler` or Werkzeug `HTTPException`.
- `app/utils/monitoring.py` and `app/utils/auth_helpers.py` have zero Flask imports.
- Remaining Flask coupling in `app/utils/`: `validators.py` (uses `flask.request`, `jsonify`) and `responses.py` (uses `flask.jsonify`, `Response`). Both are out of scope here; they'll need a separate decoupling pass before 16.8.

## Remaining task-16.8 prerequisites
1. task-16.4 (database_vulnerable + SQLAlchemy port) — only Flask-native blueprint left
2. task-16.7 (test suite → Starlette TestClient) — drops the dual `client`/`asgi_client` fixtures
3. Hygiene from f73f08f review: F-001 (time.sleep → asyncio.sleep), F-002 (legacy alias smoke tests), F-003 (ruff format), F-004 (generate_jwt comment)
4. NEW from this task: decouple `app/utils/validators.py` and `app/utils/responses.py` from Flask
5. NEW from this task: AC #5 follow-up — formal tests for `app/error_handlers_asgi.py`
<!-- SECTION:FINAL_SUMMARY:END -->
