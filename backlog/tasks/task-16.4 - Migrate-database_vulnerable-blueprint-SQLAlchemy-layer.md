---
id: TASK-16.4
title: Migrate database_vulnerable blueprint + SQLAlchemy layer
status: To Do
assignee: []
created_date: '2026-04-12 04:07'
updated_date: '2026-04-12 04:09'
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
- [ ] #1 Flask-SQLAlchemy removed from pyproject.toml
- [ ] #2 Plain SQLAlchemy 2.0 used for 6 models
- [ ] #3 init_database() works without Flask app context
- [ ] #4 database_vulnerable routes transformed and wired into asgi.py
- [ ] #5 SQL injection test endpoints confirmed vulnerable (USE_DATABASE=true pytest tests/unit/test_dal.py)
- [ ] #6 Test suite passes under both USE_DATABASE=false and USE_DATABASE=true
<!-- AC:END -->
