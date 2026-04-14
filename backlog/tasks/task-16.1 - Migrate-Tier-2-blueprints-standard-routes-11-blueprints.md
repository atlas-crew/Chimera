---
id: TASK-16.1
title: 'Migrate Tier 2 blueprints (standard routes, 11 blueprints)'
status: In Progress
assignee:
  - codex
created_date: '2026-04-12 04:07'
updated_date: '2026-04-14 15:35'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Audit Tier 2 blueprints and their existing test coverage to choose a safe first migration chunk that can move off Flask without losing verification.
2. Improve the migration pattern where needed (router shim, codemod, and/or test fixtures) so migrated routes can be exercised through the ASGI app while unmigrated routes continue using Flask.
3. Convert the first Tier 2 blueprint subset, mount those routers in app/asgi.py, remove them from app/__init__.py, and migrate their tests to the appropriate client path.
4. Verify targeted pytest coverage after each migrated blueprint group before expanding to the remaining Tier 2 set.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Migrated first Tier 2 wave into Starlette: government, telecom, and energy_utilities now mount in app/asgi.py while Flask create_app() deregisters those blueprints.

Added parallel ASGI pytest fixtures in tests/conftest.py and converted the three migrated route suites to TestClient/json() semantics so Starlette routes can be exercised without breaking remaining Flask tests.

Extended app/routing.py so the decorator shim forwards path params, preserves Flask-like static-over-dynamic route precedence, and exposes get_json_or_default() for lenient JSON parsing during migration.

Verification: cd apps/vuln-api && uv run pytest tests/unit/test_government_routes.py tests/unit/test_telecom_routes.py tests/unit/test_energy_utilities_routes.py tests/unit/test_banking_routes.py tests/unit/test_hotpatch.py tests/unit/test_routing.py -q -> 36 passed in 0.54s.

Source review receipts: .agents/reviews/review-20260414-111916.md (blocked on JSON parsing), .agents/reviews/review-20260414-112325.md (pass with issues), .agents/reviews/review-20260414-112739.md (source-only pass with issues, no P0/P1).

Test audit receipt: .agents/reviews/test-audit-20260414-113044.md. Main findings are broader missing endpoint coverage across these blueprints and helper edge cases; no regression was found in the migrated route/test slice.
<!-- SECTION:NOTES:END -->
