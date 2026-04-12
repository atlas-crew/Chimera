---
id: TASK-16.1
title: 'Migrate Tier 2 blueprints (standard routes, 11 blueprints)'
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
Run the flask_to_starlette.py codemod on 11 Tier 2 blueprints and wire them into app/asgi.py. These are standard blueprints with request.json + jsonify patterns, possibly hotpatch-decorated, but no session usage.

## Blueprints (ordered roughly by complexity)
- security_ops (163 lines)
- loyalty (195 lines)
- compliance (218 lines)
- ics_ot (266 lines)
- infrastructure (269 lines)
- genai (261 lines) — **manual fix**: request.files in 2 routes
- energy_utilities (414 lines)
- telecom (448 lines)
- attack_sim (577 lines)
- government (684 lines)
- admin (730 lines)

## Process per blueprint
1. `uv run python scripts/flask_to_starlette.py app/blueprints/<name>/`
2. Manual review of output — watch for: Response() calls, abort(), send_from_directory(), make_response()
3. Edit __init__.py: `from starlette.routing import Router` → `from app.routing import DecoratorRouter as Router`
4. Remove blueprint from Flask factory (app/__init__.py imports + register_blueprint calls)
5. Add `*<name>_router.routes` to app/asgi.py routes list
6. Run `make test-ci` — Flask tests should still pass
7. Smoke test a representative endpoint via `curl` against uvicorn

## Known manual fixes
- **genai/routes.py**: `request.files` has no 1:1 Starlette equivalent. Use `await request.form()` and `.getlist()`.
- **Response() objects**: codemod imports Response but doesn't rewrite `Response(body, mimetype=...)` — use `Response(content=body, media_type=...)`.

## Reference
- Tier 1 reference commit: 990741b (shows exact pattern for main/recorder/diagnostics/throughput)
- Plan: /Users/nick/.claude/plans/idempotent-knitting-star.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 11 Tier 2 blueprints transformed by codemod
- [ ] #2 DecoratorRouter used in all Tier 2 __init__.py files
- [ ] #3 Routes mounted in app/asgi.py
- [ ] #4 Flask factory no longer imports Tier 2 blueprints
- [ ] #5 genai request.files manually migrated to Starlette form API
- [ ] #6 Flask test suite passes (632 tests, allowing for Tier 1+2 shims)
- [ ] #7 Smoke test confirms representative endpoint from each blueprint works on uvicorn
<!-- AC:END -->
