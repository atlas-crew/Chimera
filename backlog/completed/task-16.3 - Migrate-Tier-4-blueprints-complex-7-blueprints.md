---
id: TASK-16.3
title: 'Migrate Tier 4 blueprints (complex, 7 blueprints)'
status: Done
assignee: []
created_date: '2026-04-12 04:07'
updated_date: '2026-04-28 17:28'
labels:
  - refactor
dependencies:
  - TASK-16.1
  - TASK-16.2
  - TASK-16.5
parent_task_id: TASK-16
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate the 7 most complex blueprints. These combine session state, hotpatch decorators, current_app access, and deeper Flask coupling. **Requires Tier 4 hotpatch rewrite (TASK-16.5) to be done first or in parallel.**

## Blueprints (ordered by complexity)
- banking (213 lines) — hotpatch + session
- integrations (276 lines) — apparatus service, logger
- testing (364 lines) — request.form, request.data, request.cookies, config introspection
- saas already in Tier 3 — skip
- ecommerce (588 lines) — hotpatch likely
- insurance (838 lines) — hotpatch likely
- healthcare (992 lines) — hotpatch likely
- auth (1158 lines) — heaviest session usage, JWT with current_app.secret_key (already migrated to app_config)

## Process
Same codemod workflow, but manual review is more involved:
1. Run codemod
2. Check for @hotpatch() decorated routes — verify they still work with the new hotpatch decorator (TASK-16.5)
3. testing/routes.py: manually handle request.form/data/cookies calls
4. auth/routes.py: verify render_template_string usages (JWT demo pages)
5. Wire into asgi.py, remove from Flask factory
6. Run full Flask test suite — auth has 200+ tests

## Dependencies
- Depends on TASK-16.5 (hotpatch rewrite) for hotpatch-using routes
- Depends on TASK-16.1 and TASK-16.2 being completed (stable migration pattern)

## Reference
- Tier 1 reference commit: 990741b
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 7 Tier 4 blueprints transformed
- [x] #2 Hotpatch decorator works correctly for migrated routes
- [x] #3 auth blueprint JWT flows verified end-to-end
- [x] #4 testing/leak_config endpoint continues to leak app metadata
- [x] #5 Flask factory no longer imports Tier 4 blueprints
- [x] #6 Flask test suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All 7 Tier 4 blueprints migrated to Starlette. Full suite: 739 passed, 1 skipped. OpenAPI drift checker: 479/479 routes clean.

## Migration commits (in order shipped)
- banking — `86d7343`
- insurance — `824d49f`
- ecommerce — `f97b530`
- integrations — `3c01c8d`
- healthcare — `8fb4371`
- testing — `a8f7025`
- auth — `f73f08f` (final, 1158 lines, 30+ routes)

## Hotpatch decorator
TASK-16.5 closed in `2676913` ahead of Tier 4. Banking uses the rewritten decorator end-to-end.

## AC #5 nuance worth recording
The original criterion ("Flask factory no longer imports Tier 4 blueprints") predates the WSGI-compat-bridge design. The Flask factory at `app/__init__.py:194-203` still imports the Tier 4 modules — but they are now Starlette `_router` objects (not Flask `Blueprint` `_bp` objects), and the factory wires them via `register_flask_compat_routes` rather than `app.register_blueprint`. The spirit of the AC (no Flask-native blueprints in Tier 4) is satisfied; the literal text is contradicted by the transitional bridge. The full Flask-import removal happens at TASK-16.8 cutover.

## Follow-up hygiene before TASK-16.8 cutover
Surfaced by post-migration multi-perspective review:
- F-001 (P2): convert `time.sleep` → `await asyncio.sleep` in async handlers (auth has 3 sites at routes.py:113, 225, 227; audit other migrated blueprints)
- F-002 (P2): smoke-test the 8 legacy alias paths in auth (`/api/oauth/authorize`, `/api/saml/sso`, etc. — currently zero coverage)
- F-003 (P3): bulk `ruff format` to normalize codemod whitespace (`status_code = 400` → `status_code=400`)
- F-004 (P3): one-line comment near `generate_jwt` explaining the threaded `request` parameter

## Recurring fixups the codemod doesn't handle (record for future blueprint-style ports)
1. Helpers reading bare `request.headers` need `request` threaded through callers (auth's `generate_jwt`).
2. `await request.json() or {}` has wrong precedence — `(await x) or y` raises before `or {}`. Use `await safe_json(request)` instead.
3. Legacy delegating aliases: `return foo()` → `return await foo(request)`.
<!-- SECTION:FINAL_SUMMARY:END -->
