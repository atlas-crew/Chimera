---
id: TASK-16.3
title: 'Migrate Tier 4 blueprints (complex, 7 blueprints)'
status: To Do
assignee: []
created_date: '2026-04-12 04:07'
updated_date: '2026-04-12 04:09'
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
- [ ] #1 All 7 Tier 4 blueprints transformed
- [ ] #2 Hotpatch decorator works correctly for migrated routes
- [ ] #3 auth blueprint JWT flows verified end-to-end
- [ ] #4 testing/leak_config endpoint continues to leak app metadata
- [ ] #5 Flask factory no longer imports Tier 4 blueprints
- [ ] #6 Flask test suite passes
<!-- AC:END -->
