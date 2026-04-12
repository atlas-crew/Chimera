---
id: TASK-2.1
title: Migrate Tier 2 blueprints to Starlette
status: To Do
assignee: []
created_date: '2026-04-12 04:06'
labels:
  - refactor
dependencies: []
parent_task_id: TASK-2
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Run the codemod on 11 Tier 2 blueprints and wire them into app/asgi.py. These are standard blueprints with request.json + jsonify patterns, possibly with hotpatch but no session usage.

**Blueprints (Tier 2):**
- compliance (218 lines)
- loyalty (195 lines)
- ics_ot (266 lines)
- infrastructure (269 lines)
- security_ops (163 lines)
- attack_sim (577 lines)
- genai (261 lines) — manual fix for request.files in 2 routes
- energy_utilities (414 lines)
- telecom (448 lines)
- government (684 lines)
- admin (730 lines)

**Process per blueprint:**
1. Run `uv run python scripts/flask_to_starlette.py app/blueprints/<name>/`
2. Manual review of output (especially Response/abort/send_from_directory)
3. Update __init__.py to use DecoratorRouter
4. Remove blueprint from app/__init__.py Flask factory
5. Add router.routes to app/asgi.py route list
6. Run Flask test suite to verify no regressions
7. Smoke test Starlette endpoints

**Reference commit:** 990741b (Tier 1 migration)

**Companion doc:** /Users/nick/.claude/plans/idempotent-knitting-star.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 11 Tier 2 blueprints transformed by codemod
- [ ] #2 DecoratorRouter used in all Tier 2 __init__.py files
- [ ] #3 Routes mounted in app/asgi.py
- [ ] #4 Flask factory no longer imports Tier 2 blueprints
- [ ] #5 Flask test suite still passes (with Tier 1+2 tests adapted or skipped)
- [ ] #6 Starlette smoke test confirms representative endpoints work
<!-- AC:END -->
