---
id: TASK-16
title: Flask → Starlette migration (epic)
status: In Progress
assignee:
  - codex
created_date: '2026-04-12 04:06'
updated_date: '2026-04-14 15:35'
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
<!-- SECTION:NOTES:END -->
