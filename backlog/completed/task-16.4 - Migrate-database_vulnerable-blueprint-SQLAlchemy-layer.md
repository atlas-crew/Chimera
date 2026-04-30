---
id: TASK-16.4
title: Migrate database_vulnerable blueprint + SQLAlchemy layer
status: Done
assignee: []
created_date: '2026-04-12 04:07'
updated_date: '2026-04-28 21:09'
labels:
  - refactor
dependencies:
  - TASK-16.1
  - TASK-16.2
  - TASK-16.3
parent_task_id: TASK-16
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate the database_vulnerable blueprint (340 lines) and replace Flask-SQLAlchemy with plain SQLAlchemy 2.0. This is the only blueprint that depends on the database layer, and it's opt-in via USE_DATABASE=true.

## Changes
### app/models.py (ORM models, not app/models/ which is in-memory stores)
- `db = SQLAlchemy()` → `from sqlalchemy.orm import DeclarativeBase; class Base(DeclarativeBase): pass`
- `db.Column(...)` → `mapped_column(...)`
- `db.Model` → `Base`
- `db.relationship` → `relationship`

### app/database.py
- Remove `db.init_app(app)`
- Replace `app.config['SQLALCHEMY_DATABASE_URI']` with plain `create_engine(url)`
- Replace `with app.app_context(): db.create_all()` with `Base.metadata.create_all(engine)` in lifespan startup
- Provide a session factory (`sessionmaker(bind=engine)`) for route handlers

### app/blueprints/database_vulnerable/routes.py
- Run codemod
- Routes use raw SQL via db.session.execute() — verify this still works with plain SQLAlchemy 2.0 syntax
- Add the router to app/asgi.py conditionally (only when USE_DATABASE=true)

## Constraints
- Keep SQLAlchemy **synchronous** — SQLite for SQL injection testing doesn't benefit from async. Starlette supports sync route handlers via `def` (not `async def`) for this blueprint.
- SQL injection vulnerabilities must be preserved — do not add parameter binding or validation.

## Dependencies
- Blocks on: TASK-16.1, TASK-16.2, TASK-16.3 (stable Starlette pattern)
- 6 models: User, BankAccount, Patient, InsurancePolicy, Transaction, Claim
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Flask-SQLAlchemy removed from pyproject.toml
- [x] #2 Plain SQLAlchemy 2.0 used for 6 models
- [x] #3 init_database() works without Flask app context
- [x] #4 database_vulnerable routes transformed and wired into asgi.py
- [x] #5 SQL injection test endpoints confirmed vulnerable (USE_DATABASE=true pytest tests/unit/test_dal.py)
- [x] #6 Test suite passes under both USE_DATABASE=false and USE_DATABASE=true
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Migration shape

**Renamed `app/models.py` → `app/orm.py`.** Discovered the SQLAlchemy module file at `app/models.py` had been silently shadowed by the `app/models/` package (Python's regular package finder wins over a sibling module file), making `USE_DATABASE=true` already broken at boot. Moved the ORM models to `app/orm.py` and deleted the dead module.

**ORM models** (`app/orm.py`): plain `DeclarativeBase` + `Mapped[T]` annotations + `mapped_column(...)`. Six tables preserved (`User`, `BankAccount`, `Patient`, `InsurancePolicy`, `Transaction`, `Claim`) with their relationships re-expressed as `relationship(back_populates=..., foreign_keys=...)` instead of Flask-SQLAlchemy `backref`. Length-bounded `String(N)` dropped (no-op on SQLite).

**Database init** (`app/database.py`): module-level `_engine` + `_SessionLocal`, `init_database()` no longer takes a Flask app. Uses `create_engine("sqlite:///...", connect_args={"check_same_thread": False}, future=True)` so a single connection can be shared across the threadpool, then `Base.metadata.drop_all/create_all` for fresh state per boot. Seed data is committed inside a context-managed `Session`.

**Routes** (`app/blueprints/database_vulnerable/`): `Blueprint('database_vulnerable', __name__)` → `DecoratorRouter(routes=[])` and the eight handlers preserve f-string SQL interpolation, raw cursor access, error-leaking exception bodies, and 503 gating. GET handlers stayed sync (`def`) per the task constraint; the two POST handlers (`/api/v1/auth/login-vulnerable`, `/api/v1/healthcare/records`) became `async def` only because they need `await safe_json(request)` for body parsing — `DecoratorRouter` accepts both styles. Sessions are closed in `finally` to return connections to the pool.

**Wiring**: `app/asgi.py` calls `init_database()` and conditionally extends `routes` with `db_vuln_router.routes` when `USE_DATABASE=true`. The Flask factory `app/__init__.py` mirrors the same router into Flask via `register_flask_compat_routes(...)` in the same gate. `scripts/check_openapi_drift.py` updated to register the new router.

**Deps**: `Flask-SQLAlchemy==3.1.1` removed from `pyproject.toml`; replaced with a direct `SQLAlchemy>=2.0` pin (was already pulled in transitively).

## Verification

- `uv sync --all-extras` uninstalls `flask-sqlalchemy==3.1.1` cleanly.
- `pytest tests/ --ignore=tests/integration` → **717 passed, 1 skipped** under both `USE_DATABASE=false` and `USE_DATABASE=true`.
- Live SQLi smoke through the Starlette TestClient (with `USE_DATABASE=true`):
  - SSN bypass `' OR '1'='1` returns all 3 patients with plaintext SSNs.
  - Auth bypass `admin@example.com' OR '1'='1' --` returns `success=True`.
  - UNION attack against bank accounts returns 6 rows (3 real + 3 leaked from `users`).
  - ORDER BY injection works.
  - Error-based info leak still echoes the offending `query` in the 500 body.
- `scripts/check_openapi_drift.py` reports zero drift.

## Notes / out-of-scope

- `datetime.utcnow()` deprecation warnings in seed data are pre-existing (the original Flask code used the same idiom in models + monitoring); not addressed here.
- The Flask compat layer keeps the routes reachable via the WSGI app for existing tests + Docker healthchecks until the uvicorn cutover (task-16.8).
<!-- SECTION:NOTES:END -->
