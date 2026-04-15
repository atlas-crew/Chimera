---
id: TASK-16
title: Flask → Starlette migration (epic)
status: In Progress
assignee:
  - codex
created_date: '2026-04-12 04:06'
updated_date: '2026-04-15 00:16'
labels:
  - refactor
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate the vuln-api from Flask 3.0 to Starlette for 10-20x throughput gains in WAF testing scenarios. The Rust echo server at apps/vuln-api-hp handles pure throughput benchmarks; this epic is about getting the real vulnerable endpoints running faster while preserving all intentional vulnerabilities.

## Why Starlette (not FastAPI)
FastAPI's automatic Pydantic validation would silently block SQL injection payloads, malformed JSON, and type-coercion attacks — defeating the purpose of a vulnerable API. Starlette gives raw ASGI with no implicit validation.

## Progress
- ✅ Phase 0: Foundation (app/config.py, app/asgi.py skeleton, gevent→threading locks)
- ✅ Phase 1A: libcst codemod (scripts/flask_to_starlette.py)
- ✅ Phase 1B Tier 1: main, recorder, diagnostics, throughput migrated
- ⬜ Phase 1B Tiers 2-5: remaining 24 blueprints
- ⬜ Phase 2: middleware, hotpatch decorator, error handlers
- ⬜ Phase 3: database layer (SQLAlchemy without Flask-SQLAlchemy)
- ⬜ Phase 4: infrastructure cutover (Dockerfiles, uvicorn, pyproject cleanup)
- ⬜ Phase 5: SPA / static files
- ⬜ Test suite migration to Starlette TestClient

## Reference
- Plan: /Users/nick/.claude/plans/idempotent-knitting-star.md
- Tier 1 reference commit: 990741b
- Codemod: apps/vuln-api/scripts/flask_to_starlette.py
- Router shim: apps/vuln-api/app/routing.py
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 28 blueprints running on Starlette
- [ ] #2 Flask dependencies removed from pyproject.toml
- [ ] #3 uvicorn replaces gunicorn in all Dockerfiles
- [ ] #4 Full test suite passes on Starlette TestClient
- [ ] #5 No regressions in intentional vulnerabilities (verified via representative vuln tests)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rewrite app/utils/hotpatch.py for Starlette request/response objects while preserving X-Chimera educational headers and body injection behavior.
2. Migrate remaining Flask blueprints in ordered tiers using the existing libcst codemod plus targeted manual fixes for sessions, file uploads, current_app usage, and hook-heavy routes.
3. Expand app/asgi.py to mount every migrated router and remove migrated blueprints from app/__init__.py so Flask only remains as a shrinking compatibility path during the cutover.
4. Replace Flask-specific middleware/error plumbing (traffic recorder, request-id monitoring, auth helpers, exception handlers) with Starlette-compatible request.state and exception handler flows.
5. Replace Flask-SQLAlchemy usage with plain SQLAlchemy for the optional database_vulnerable endpoints and wire startup/teardown from the ASGI app.
6. Migrate the pytest fixtures and callers to Starlette TestClient, then update Makefile/Dockerfiles/pyproject to remove Flask/Gunicorn dependencies and run on uvicorn.
7. Verify in short loops with focused pytest runs during each slice, then broader vuln-api coverage once the routing cutover is complete.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Work started by Codex on 2026-04-14 after live inspection of the current ASGI skeleton, remaining Flask blueprints, and migration support tooling.

Completed the first migration loop around app/utils/hotpatch.py and supporting routing/codemod infrastructure. Remaining work is still concentrated in bulk blueprint conversion, middleware/error plumbing, test-client migration, and infra cutover.

Completed first Tier 2 Starlette migration slice: government, telecom, and energy_utilities now run under app/asgi.py with ASGI test fixtures and focused passing validation (36 targeted tests). Routing shim now forwards path params, preserves static-over-dynamic precedence, and provides lenient JSON parsing for migrated handlers.

Completed the second Tier 2 Starlette migration wave for security_ops, loyalty, and compliance with Flask compatibility bridging preserved for migrated domains. Verification: targeted mixed ASGI/Flask suite passed at 60 tests. Final review: .agents/reviews/review-20260414-131942.md. Test audit: .agents/reviews/test-audit-20260414-131637.md.

2026-04-14: Completed the third Tier 2 Starlette migration wave by moving ics_ot and infrastructure onto the ASGI app while keeping Flask mixed-mode compatibility via register_flask_compat_routes.

Wave receipt: targeted regression batch passed with 78 tests; source reviews in .agents/reviews/review-20260414-141735.md, review-20260414-142249.md, review-20260414-143018.md, and review-20260414-143446.md; test audit in .agents/reviews/test-audit-20260414-143935.md.

2026-04-14: Completed another Tier 2 Starlette migration wave by moving genai onto the ASGI app and preserving create_app() reachability through the Flask compatibility bridge.

Wave receipt: targeted regression batch passed with 88 tests in 6.72s; source review artifacts .agents/reviews/review-20260414-192436.md and review-20260414-192831.md; test audit artifact .agents/reviews/test-audit-20260414-193416.md.

2026-04-14: Completed another Tier 2 Starlette migration wave by moving attack_sim onto the ASGI app and preserving create_app() reachability through the Flask compatibility bridge.

Wave receipt: targeted regression batch passed with 97 tests in 6.46s; source review artifact .agents/reviews/review-20260414-194453.md; test audit artifact .agents/reviews/test-audit-20260414-194733.md. This wave also repaired eight previously dead attack_sim endpoints that were returning empty 200 responses in Flask.

2026-04-14: Closed TASK-16.1 after migrating the final Tier 2 blueprint (admin) into the Starlette mixed-mode path. Tier 2 now has all 11 blueprints mounted in app/asgi.py with Flask compatibility preserved via register_flask_compat_routes while the broader epic continues.

Admin/Tier 2 closure receipts: focused admin migration tests passed at 114 tests; full vuln-api unit suite passed at 715 passed / 1 skipped / 133 warnings; uvicorn smoke checks on http://127.0.0.1:8899 returned expected 200/201 responses across all 11 Tier 2 blueprints.

Latest source review artifact: .agents/reviews/review-20260414-200618.md (PASS WITH ISSUES, no P0/P1). Latest test audit artifact: .agents/reviews/test-audit-20260414-200859.md; follow-on findings are broader coverage debt and ASGI middleware checks, not blockers for Tier 2 completion.
<!-- SECTION:NOTES:END -->
