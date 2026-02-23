# AGENTS.md

This file provides guidance to AI Agents (claude, codex, gemini, etc) when working with code in this repository.

## What This Is

Chimera is an **intentionally vulnerable** monorepo for WAF (Web Application Firewall) testing and security education. It contains a Flask API with 456+ vulnerable endpoints across 25+ industry domains and a React portal frontend. **All vulnerabilities are deliberate** — do not "fix" security issues unless explicitly asked.

## Monorepo Layout

```
Chimera/                    # pnpm + Nx workspace
├── apps/
│   ├── vuln-api/           # Flask/Python backend (Gunicorn + gevent)
│   └── vuln-web/           # React/Vite/TypeScript frontend
├── nx.json                 # Nx workspace config
├── pnpm-workspace.yaml     # pnpm workspace definition
├── justfile                # Task runner (preferred entry point)
└── package.json            # Root devDependencies (nx, @nx/js)
```

## Commands

### Task runner (justfile)
```bash
just                    # List all recipes
just dev                # Start both API and web dev server
just build              # Build all projects
just test               # Test all projects
just lint               # Lint all projects
just run <proj> <tgt>   # Generic: just run vuln-api test
```

### Nx (underlying orchestrator)
```bash
pnpm nx show projects               # List projects: vuln-api, vuln-web
pnpm nx run vuln-web:build           # Build web app
pnpm nx run vuln-api:test            # Run API tests
pnpm nx run-many -t test --parallel  # All tests in parallel
pnpm nx affected -t test             # Test only changed projects
```

### vuln-api (Python/Flask)
```bash
# Dependencies (uses uv, not pip)
cd apps/vuln-api && uv sync --extra dev --frozen

# Run locally
uv run python app.py                           # Default (port 5000)
DEMO_MODE=full uv run python app.py            # Vulnerable mode
USE_DATABASE=true uv run python app.py         # SQLite for real SQLi

# Tests via Makefile
make -C apps/vuln-api test-ci          # CI: unit + coverage, fail-fast
make -C apps/vuln-api test-unit        # Unit tests with coverage report
make -C apps/vuln-api test-quick       # Fast feedback (-x --maxfail=5)
make -C apps/vuln-api test-vulnerability  # Security-specific tests
make -C apps/vuln-api test-smoke       # Smoke tests

# Single test file
cd apps/vuln-api && uv run pytest tests/unit/test_auth_routes.py -v

# Formatting / linting
make -C apps/vuln-api format           # black (120-char lines)
make -C apps/vuln-api lint             # flake8 + pylint
```

### vuln-web (React/Vite/TypeScript)
```bash
just web-dev            # Dev server (port 5175, proxies /api → localhost:5000)
just web-build          # Production build (tsc -b && vite build)
just web-lint           # ESLint
```

## Architecture

### vuln-api

**Flask app factory** (`app/__init__.py` → `create_app()`) that registers 25+ blueprints, security headers, error handlers, traffic recorder middleware, and demo data seeding.

**Blueprint pattern** — each domain lives in `app/blueprints/{domain}/`:
- `__init__.py` exports `{domain}_bp = Blueprint(...)`
- `routes.py` contains all endpoints for that domain
- Registered in `create_app()` via `app.register_blueprint()`

**Data layer** (`app/models/`):
- `dal.py`: `DataStore` / `TransactionalDataStore` — thread-safe in-memory CRUD with gevent locks
- `data_stores.py`: 100+ named stores (`users_db`, `accounts_db`, `medical_records_db`, etc.)
- Optional SQLite via `USE_DATABASE=true` for real SQL injection endpoints (`app/database.py`)

**Vulnerability gating** (`security.py`):
- `DEMO_MODE` env var: `full` (vulns active) vs `strict` (safe mode, default)
- `@require_full_demo` decorator blocks dangerous endpoints in strict mode
- `is_full_mode()` / `get_demo_mode()` helpers for conditional logic in routes

**Key env vars**: `DEMO_MODE`, `USE_DATABASE`, `DATABASE_PATH`, `DEMO_THROUGHPUT_MODE`

### vuln-web

**React 18 SPA** with React Router v6. Each industry vertical is a page component in `src/pages/` that fetches from `/api/v1/{domain}/...` endpoints.

**Vite dev server** proxies `/api` → `http://localhost:5000` (configured in `vite.config.ts`).

**Notable components**:
- `ThemeProvider` — dark/light mode via React context + localStorage
- `RedTeamConsole` — mock attack traffic overlay (Ctrl+\`)
- `TourGuide` — react-joyride exploit walkthrough
- `AiAssistant` — floating chat widget hitting `/api/v1/genai/chat`
- `VulnerabilityModal` — per-dashboard exploit documentation

### Frontend ↔ Backend

The web app makes `fetch()` calls to `/api/v1/...` endpoints. In development, Vite proxies these to the Flask backend on port 5000. In production (Docker), nginx handles the proxy.

## Testing Conventions

### API tests (pytest)
- `tests/conftest.py` has an **autouse fixture** that clears all in-memory stores before/after each test
- Fixtures: `client` (Flask test client), `mock_users`, `mock_medical_records`, `sample_user`, `mfa_user`
- Attack payload fixtures: `sql_injection_payloads`, `command_injection_payloads`, `path_traversal_payloads`, etc.
- Markers: `@pytest.mark.vulnerability`, `@pytest.mark.integration`, `@pytest.mark.smoke`
- `demo_mode_full` / `demo_mode_strict` fixtures for testing both modes
- Coverage target: 80% minimum (`make test-coverage`)

### Web tests
No test framework configured yet. Build script (`tsc -b && vite build`) serves as the type-check gate.

## Conventions

- **Commits**: Conventional Commits with scope — `feat(api):`, `fix(web):`, `docs(readme):`
- **Python style**: black (120-char), flake8 + pylint
- **TypeScript**: strict mode, no unused locals/params (enforced by `tsc`)
- **New API endpoints**: add to the appropriate blueprint in `app/blueprints/{domain}/routes.py`, update docs and tests in the same change
- **New stores**: declare in `app/models/data_stores.py`, import/clear in `tests/conftest.py`



## Task Tracking and Project Management

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools) or use the CLI `backlog --help`

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and finalization
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

