---
id: TASK-16
title: Flask → Starlette migration (epic)
status: To Do
assignee: []
created_date: '2026-04-12 04:06'
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
