---
id: TASK-16.6
title: 'Rewrite middleware (TrafficRecorder, monitoring, error handlers)'
status: To Do
assignee: []
created_date: '2026-04-12 04:08'
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
- [ ] #1 TrafficRecorder works as Starlette middleware
- [ ] #2 Request ID middleware injects X-Request-ID
- [ ] #3 Error handlers preserve intentional info leakage patterns
- [ ] #4 auth_helpers uses request.state instead of flask.g
- [ ] #5 All error scenarios tested (400, 401, 403, 404, 500, generic Exception)
<!-- AC:END -->
