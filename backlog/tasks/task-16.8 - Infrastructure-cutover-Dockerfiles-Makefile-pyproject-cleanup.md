---
id: TASK-16.8
title: 'Infrastructure cutover: Dockerfiles, Makefile, pyproject cleanup'
status: To Do
assignee: []
created_date: '2026-04-12 04:09'
updated_date: '2026-04-12 04:09'
labels:
  - refactor
dependencies:
  - TASK-16.1
  - TASK-16.2
  - TASK-16.3
  - TASK-16.4
  - TASK-16.5
  - TASK-16.6
  - TASK-16.7
parent_task_id: TASK-16
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Final cutover from Flask/gunicorn to Starlette/uvicorn across all infrastructure files. Only runnable after all blueprints are migrated and the test suite is on Starlette.

## Dockerfiles (3 files)

### apps/vuln-api/Dockerfile (dev)
- `CMD ["uv", "run", "python", "app.py"]` → `CMD ["uv", "run", "uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "80", "--reload"]`

### apps/vuln-api/Dockerfile.prod (production)
- `CMD ["uv", "run", "gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]` → `CMD ["uv", "run", "uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8880", "--workers", "4"]`
- Update HEALTHCHECK command — already uses `curl /healthz` which still works
- Remove `COPY gunicorn.conf.py` line
- Remove `COPY wsgi.py` line (if present)

### apps/vuln-api/Dockerfile.fargate
- `CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "4", "app:app"]` → `CMD ["uv", "run", "uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]`

## pyproject.toml cleanup
Remove:
- `Flask==3.0.0`
- `Flask-SQLAlchemy==3.1.1`
- `Werkzeug==3.0.1`
- `gunicorn==21.2.0`
- `gevent>=24.2.1`
- `flasgger>=0.9.7.1`

Update description and keywords — remove "Flask" references.

## Delete obsolete files
- `apps/vuln-api/gunicorn.conf.py` (replaced by uvicorn CLI args)
- `apps/vuln-api/wsgi.py` (replaced by app.asgi:app reference)
- `apps/vuln-api/app/__init__.py` Flask factory → becomes re-export from app.asgi
- `apps/vuln-api/app.py` dev entry point → update or delete

## Makefile updates
- `run-vulnerable` / `run-secure` targets: swap gunicorn command for `uv run uvicorn app.asgi:app --host 0.0.0.0 --port $(PORT)`
- Remove references to gunicorn.conf.py

## project.json (Nx)
- No changes needed — `start` target calls `make run` which we'll update

## Dependencies
- Blocks on: ALL blueprint migrations complete (16.1-16.4)
- Blocks on: TASK-16.6 (middleware) and TASK-16.7 (tests)
- This is the LAST task in the migration
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 3 Dockerfiles use uvicorn
- [ ] #2 Flask deps removed from pyproject.toml
- [ ] #3 gunicorn.conf.py and wsgi.py deleted
- [ ] #4 app/__init__.py becomes re-export from app.asgi (or deleted if possible)
- [ ] #5 make run starts uvicorn
- [ ] #6 Docker image builds and health check passes
- [ ] #7 Fargate deployment smoke test (or plan documented if no Fargate access)
- [ ] #8 uv.lock regenerated and committed
<!-- AC:END -->
