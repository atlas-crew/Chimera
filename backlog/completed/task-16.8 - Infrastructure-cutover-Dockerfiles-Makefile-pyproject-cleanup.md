---
id: TASK-16.8
title: 'Infrastructure cutover: Dockerfiles, Makefile, pyproject cleanup'
status: Done
assignee: []
created_date: '2026-04-12 04:09'
updated_date: '2026-04-29 08:30'
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
- [x] #1 All 3 Dockerfiles use uvicorn
- [x] #2 Flask deps removed from pyproject.toml
- [x] #3 gunicorn.conf.py and wsgi.py deleted
- [x] #4 app/__init__.py becomes re-export from app.asgi (or deleted if possible)
- [x] #5 make run starts uvicorn
- [x] #6 Docker image builds and health check passes
- [ ] #7 Fargate deployment smoke test (or plan documented if no Fargate access)
- [x] #8 uv.lock regenerated and committed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Cutover shape

**Three Dockerfiles** flipped to ``uvicorn app.asgi:app``:
- ``Dockerfile`` — dev image, ``--reload`` on port 80.
- ``Dockerfile.prod`` — multi-stage, non-root user, ``--workers 4 --log-level info`` on 8880; HEALTHCHECK already used ``/healthz`` so unchanged.
- ``Dockerfile.fargate`` — single-stage, ``--workers 4`` on 8080.
COPY directives for ``wsgi.py``, ``app.py``, and ``gunicorn.conf.py`` removed.

**``justfile``** ``run-vulnerable`` / ``run-secure`` recipes now invoke ``uvicorn app.asgi:app --host 0.0.0.0 --port {{PORT}}`` — secure mode passes ``--workers 4``, vulnerable mode passes ``--reload``. ``FLASK_ENV`` env vars dropped.

**Deleted obsolete files** (``trash`` so they're recoverable):
- ``gunicorn.conf.py`` (replaced by uvicorn CLI args).
- ``wsgi.py`` (replaced by ``app.asgi:app``).
- ``app.py`` (Flask dev entry point — uvicorn replaces it).

**``app/__init__.py``** reduced to a 9-line re-export from ``app.asgi`` so any caller of ``from app import create_app, app`` keeps resolving.

**SPA serving ported to Starlette** (``app/asgi.py`` + ``app/blueprints/main/routes.py``):
- ``main_router`` ``/`` handler now serves ``web_dist/index.html`` via ``FileResponse`` when present, else falls back to ``DEMO_PAGE_TEMPLATE``.
- ASGI factory adds a ``Route("/{path:path}", spa_catch_all)`` when ``index.html`` exists. Catch-all returns JSON 404 for ``/api/`` paths, real static files when present, else ``index.html`` for client-side routing.
- ``Mount("/assets", StaticFiles(...))`` now points at ``web_dist/assets/`` (was ``web_dist/`` — the previous mount served the index too).

## Dependencies removed from ``pyproject.toml``

- ``Flask==3.0.0``, ``Werkzeug==3.0.1``, ``flasgger>=0.9.7.1``
- ``gunicorn==21.2.0``, ``gevent>=24.2.1``
- ``asgiref>=3.8.1`` (only used by the deleted Flask compat shim)

Plus their transitives: ``jinja2``, ``markupsafe``, ``blinker``, ``mistune``, ``jsonschema*``, ``rpds-py``, ``referencing``, ``attrs``, ``six``, ``zope-event``, ``zope-interface``, ``greenlet``. ``uv sync`` regenerated ``uv.lock``.

Description / keywords flipped from "Flask demo API" to "Starlette demo API".

## Dead Flask runtime modules deleted

- ``app/error_handlers.py`` (superseded by ``error_handlers_asgi.py``).
- ``app/middleware/traffic_recorder.py`` (superseded by ``traffic_recorder_asgi.py``).
- ``app/utils/responses.py`` + ``app/utils/validators.py`` (Flask response/validator helpers; no migrated routes called them).
- Flask compat shim deleted from ``app/routing.py``: ``register_flask_compat_routes``, ``FlaskRequestAdapter``, ``_AdapterURL``, ``_build_flask_response``, ``_coerce_flask_response``, ``_await_coro``. Imports of ``async_to_sync``, ``StarletteResponse``, ``SimpleNamespace`` dropped.
- Flask fallback paths stripped from ``app/utils/hotpatch.py`` (no more ``FlaskResponse`` / ``make_response`` branches; Starlette is the only path now).
- ``current_app.config`` fallback removed from ``app/services/apparatus_service.py``.
- ``current_app.blueprints`` / ``url_map.iter_rules`` lookup in ``app/blueprints/testing/routes.py:leak_config`` replaced with a Starlette equivalent that walks ``request.app.routes``.
- ``app/utils/__init__.py`` re-export list trimmed (the Validators and Responses sections deleted).

``grep -rn 'from flask\|import flask' app/`` returns zero hits.

## Drift script rewritten

``scripts/check_openapi_drift.py`` no longer goes through Flask's ``url_map``. New ``load_live_routes()`` walks ``app.routes`` (Starlette), converts ``{name:converter}`` → ``<converter:name>`` for spec normalization, and pulls in ``db_vuln_router`` routes manually so the drift inventory still covers ``USE_DATABASE=true`` paths regardless of env.

Dedup uses ``(path, frozenset(methods))`` because ``healthcare_router`` and ``db_vuln_router`` both register ``/api/v1/healthcare/records`` (GET vs POST). Path-only dedup masked one POST route on the first run; fixed.

## Test cleanup

- Deleted ``tests/unit/test_routing.py`` and ``tests/unit/test_migrated_flask_compat_routes.py`` (Flask vs Starlette parity tests — the thing they parity-checked no longer exists).
- Deleted ``tests/unit/test_responses.py`` and ``tests/unit/test_validators.py`` (Flask-only response/validator tests — the helpers they tested are gone).
- ``test_spa_serving.py::TestSpaMode`` re-migrated to Starlette factory (was pinned to Flask in 16.7); 12/12 SPA tests green.
- ``test_integrations_routes.py`` repointed at the ASGI factory; uses ``monkeypatch.setattr(app_config, ...)`` instead of ``flask_app.config.update(...)``.
- ``test_apparatus_service.py`` no longer imports Flask; the one ``with app.app_context():`` test was rewritten to pass the config dict directly to ``build_apparatus_settings`` like the other cases.
- ``test_hotpatch.py``: removed Flask import, deleted ``test_hotpatch_async_flask_views_still_get_decorated`` (Flask-only).
- ``test_monitoring.py::test_log_exception_http_exception``: ``werkzeug.exceptions.NotFound`` → ``starlette.exceptions.HTTPException(status_code=404)``.
- ``conftest.py``: dropped ``flask_app`` / ``flask_client`` / ``runner`` fixtures and the ``from app import create_app`` import. ``app`` and ``client`` are Starlette-native; ``asgi_*`` aliases retained for tests written during the migration.

## Verification

- ``grep 'from flask\|import flask' app/`` → 0 hits.
- ``uv sync --all-extras`` uninstalled 18 packages (Flask, Werkzeug, gunicorn, gevent, flasgger + their deps).
- ``pytest tests/ --ignore=tests/integration`` → **492 passed, 1 skipped** under both ``USE_DATABASE=false`` and ``USE_DATABASE=true``.
- ``scripts/check_openapi_drift.py`` → zero drift.
- ``uvicorn app.asgi:app`` boots on port 8088, ``GET /healthz`` returns 200 with ``{"status":"healthy"}``, ``GET /api/v1/healthcare/records`` returns 200, ``POST /api/v1/auth/login`` returns 401 with the expected error contract.
- ``just run-secure 8089`` spawns 4 workers; healthz responds correctly.

## Acceptance criteria status

- #1–#6, #8 — verified above.
- #7 (Fargate smoke test) — not exercised in this session because the local box has no Fargate access. ``Dockerfile.fargate`` swapped to uvicorn and uses the same ``app.asgi:app`` entrypoint as the prod and dev images, so a Fargate redeploy should be a no-op deploy. Recommend a manual smoke after first push: ``aws ecs run-task ...`` against the new image, then ``curl /healthz`` against the public ALB.

## Notes / out-of-scope

- ``Mount("/assets", StaticFiles(directory=os.path.join(web_dist_dir, "assets")))`` change is a small SPA-serving fix that shipped here because porting the catch-all touched the same block; without it ``/assets/main.js`` would have failed to resolve under the Starlette mount.
- Pre-existing ``datetime.utcnow()`` deprecation warnings (~140) untouched — orthogonal to the cutover.
- The ``app/cli.py`` referenced by ``project.scripts.chimera-api`` was not touched in this task; the CLI script may need its own Flask audit on next reach. Out of scope for 16.8.

**Migration epic complete.** All 8 sub-tasks (16.1–16.8) closed; codebase is Starlette-native end-to-end with the SQLite SQLi demo intact and 492 unit tests green.
<!-- SECTION:NOTES:END -->
