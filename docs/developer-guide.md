# Getting Started

This guide covers installing, running, and developing the Chimera project. Choose the method that fits your needs -- PyPI and Docker are the fastest paths; source installs give you the full development environment.

## Option A: Install from PyPI (recommended)

Requires **Python 3.12+**.

```bash
pip install chimera-api
chimera-api --port 8880 --demo-mode full
```

Open [http://localhost:8880](http://localhost:8880) for the web portal, or [http://localhost:8880/swagger](http://localhost:8880/swagger) for the interactive API docs.

### CLI Options

```bash
chimera-api --help

chimera-api \
  --host 0.0.0.0 \
  --port 8880 \
  --demo-mode full \
  --debug
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8880` | Server port |
| `--debug` | off | Enable debug mode (Starlette debug=True + verbose error responses) |
| `--demo-mode` | none | `full` or `strict` |

### Configuration

Customize the runtime with environment variables:

```bash
DEMO_MODE=full \
USE_DATABASE=true \
chimera-api --port 8880
```

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `strict` | `full` enables all vulnerabilities; `strict` blocks dangerous endpoints |
| `USE_DATABASE` | `false` | Enable SQLite backend for real SQL injection testing |
| `DATABASE_PATH` | `demo.db` | SQLite file location (when `USE_DATABASE=true`) |
| `PORT` | `80` (container) / `8880` (dev) | Server listening port |
| `DEMO_THROUGHPUT_MODE` | `false` | Enable high-throughput testing endpoints |
| `APPARATUS_ENABLED` | `false` | Enable the Apparatus service-to-service integration |
| `APPARATUS_BASE_URL` | `http://127.0.0.1:8090` | Base URL for the external Apparatus service |
| `APPARATUS_TIMEOUT_MS` | `5000` | Timeout for Chimera-to-Apparatus HTTP requests (ms) |

---

## Option B: Run with Docker

```bash
docker run -p 8880:8880 -e DEMO_MODE=full nickcrew/chimera
```

Open [http://localhost:8880](http://localhost:8880). Same bundled server as the PyPI package.

Pass environment variables with `-e`:

```bash
docker run -p 8880:8880 \
  -e DEMO_MODE=full \
  -e USE_DATABASE=true \
  nickcrew/chimera
```

---

## Option C: Run from Source

Use this option when you want to develop Chimera itself or need fine-grained control over individual components.

### Prerequisites

Before you begin, install:

- **Node.js** 18+ and **pnpm** 8+ ([install pnpm](https://pnpm.io/installation))
- **Python** 3.12+ ([install](https://www.python.org/downloads/))
- **uv** ([install](https://github.com/astral-sh/uv)) — fast Python package manager
- **just** ([install](https://github.com/casey/just)) — task runner (optional but recommended)

Verify your setup:

```bash
node --version    # v18+
pnpm --version    # 8+
python3 --version # 3.12+
uv --version      # 0.4+
just --version    # 1.0+ (optional)
```

### 1. Clone and install

```bash
git clone https://github.com/NickCrew/Chimera.git
cd Chimera

# Install Node.js dependencies (pnpm workspace)
pnpm install

# Install Python dependencies
cd apps/vuln-api && uv sync --extra dev
cd ../..
```

Verify it worked:

```bash
just projects
# Should output: chimera-api, vuln-web
```

### 2. Start the dev servers

```bash
just dev
```

This starts both servers in parallel via Nx:
- **Starlette API** (uvicorn) on `http://localhost:8880`
- **Vite dev server** on `http://localhost:5175` (proxies `/api/*` to uvicorn)

Start individually:

```bash
# API only
just api-start

# Web only
just web-dev
```

### 3. Demo modes

Control vulnerability behavior with `DEMO_MODE`:

```bash
# All vulnerabilities active
DEMO_MODE=full just -f apps/vuln-api/justfile run-vulnerable

# Dangerous endpoints blocked
DEMO_MODE=strict just -f apps/vuln-api/justfile run-secure

# Real SQL injection via SQLite
USE_DATABASE=true DEMO_MODE=full just -f apps/vuln-api/justfile run-vulnerable

# Or invoke uvicorn directly:
DEMO_MODE=full uv run uvicorn app.asgi:app --host 0.0.0.0 --port 8880 --reload
```

### Apparatus Integration (optional)

The Apparatus integration is service-to-service: Chimera backend proxies to an external Apparatus instance, and the React app talks only to Chimera. Keep Apparatus in its own repo or deployment and point Chimera at it with environment variables.

```bash
# Chimera terminal
APPARATUS_ENABLED=true \
APPARATUS_BASE_URL=http://127.0.0.1:8090 \
APPARATUS_TIMEOUT_MS=5000 \
just dev

# Apparatus terminal
cd ../Apparatus
tx run apparatus
```

Smoke-check the integration with:

```bash
curl http://localhost:8880/api/v1/integrations/apparatus/status
curl http://localhost:8880/api/v1/integrations/apparatus/history?limit=5
curl -X POST http://localhost:8880/api/v1/integrations/apparatus/ghosts/start \
  -H 'Content-Type: application/json' \
  -d '{"rps":5,"duration":30000,"endpoints":["/api/v1/auth/login"]}'
curl -X POST http://localhost:8880/api/v1/integrations/apparatus/ghosts/stop
```

The Chimera web Admin Dashboard also exposes these controls through the Apparatus panel once both services are running.

## Project Structure

### vuln-api (Starlette/Python)

```
apps/vuln-api/
├── app/
│   ├── asgi.py              # Starlette ASGI factory + module-level `app`
│   ├── __init__.py          # Re-exports `create_app` and `app` from app.asgi
│   ├── cli.py               # CLI entry point
│   ├── routing.py           # DecoratorRouter + safe_json / get_json_or_default
│   ├── orm.py               # SQLAlchemy 2.0 ORM (used when USE_DATABASE=true)
│   ├── database.py          # Engine + sessionmaker + seed_data
│   ├── error_handlers_asgi.py  # Starlette exception handlers + body buffer
│   ├── middleware/
│   │   └── traffic_recorder_asgi.py  # ASGI traffic recorder middleware
│   ├── blueprints/          # 25+ domain packages (filesystem name preserved)
│   │   └── {domain}/
│   │       ├── __init__.py  # `{domain}_router = DecoratorRouter(routes=[])`
│   │       └── routes.py    # Endpoint handlers, decorated with @router.route
│   ├── models/
│   │   ├── dal.py           # DataStore (thread-safe CRUD with threading.Lock)
│   │   └── data_stores.py   # 100+ named stores
│   ├── utils/               # Hotpatch decorator, monitoring, demo data
│   └── web_dist/            # Bundled SPA (populated by build)
├── tests/
│   ├── conftest.py          # Shared fixtures (Starlette TestClient, store reset)
│   └── unit/                # Unit tests per domain
├── pyproject.toml           # Package config (hatchling)
├── justfile                 # Run/test/lint recipes
├── Dockerfile               # Dev container (uvicorn --reload)
├── Dockerfile.prod          # Production container (uvicorn --workers 4)
└── Dockerfile.fargate       # ECS/Fargate container
```

### vuln-web (React/TypeScript)

```
apps/vuln-web/
├── src/
│   ├── App.tsx              # Router setup
│   ├── main.tsx             # Entry point
│   ├── pages/               # Industry dashboards
│   │   ├── BankingDashboard.tsx
│   │   ├── HealthcareDashboard.tsx
│   │   └── ...
│   └── components/
│       ├── Layout.tsx       # Shell with nav
│       ├── ThemeProvider.tsx # Dark/light mode
│       ├── RedTeamConsole.tsx # Attack overlay (Ctrl+`)
│       ├── AiAssistant.tsx  # Chat widget
│       └── TourGuide.tsx    # Exploit walkthrough
├── vite.config.ts           # Dev config (proxy to uvicorn :8880)
├── vite.config.bundle.ts    # Bundle config (output to web_dist)
└── package.json
```

## Testing

### Running Tests

```bash
# All tests via Nx
just test

# API tests only
just api-test

# Quick feedback (stops on first failure)
just -f apps/vuln-api/justfile test-quick

# Full CI suite with coverage
just -f apps/vuln-api/justfile test-ci

# Single test file
cd apps/vuln-api && uv run pytest tests/unit/test_auth_routes.py -v

# Vulnerability-specific tests
just -f apps/vuln-api/justfile test-vulnerability
```

### Test Conventions

**Fixtures** (defined in `tests/conftest.py`):

| Fixture | Description |
|---------|-------------|
| `client` | Starlette `TestClient` (raise_server_exceptions=False) |
| `app` | Starlette application instance |
| `remote_client` | TestClient with non-local source address (auth-gate coverage) |
| `set_session(client, dict)` | Seed an itsdangerous-signed session cookie |
| `read_session(client) -> dict` | Decode the session cookie set by the server |
| `mock_users` | Pre-populated user database |
| `mock_medical_records` | Pre-populated PHI records |
| `sample_user` | Single user with known credentials |
| `mfa_user` | User with MFA enabled |
| `demo_mode_full` | Sets `DEMO_MODE=full` |
| `demo_mode_strict` | Sets `DEMO_MODE=strict` |
| `sql_injection_payloads` | Common SQLi attack strings |
| `command_injection_payloads` | Command injection strings |

**Markers**:

```python
@pytest.mark.vulnerability   # Security-specific tests
@pytest.mark.integration     # Integration tests
@pytest.mark.smoke           # Smoke tests
```

**Autouse store reset**: Every test gets a clean slate. The `reset_databases` fixture clears all 100+ in-memory stores before and after each test.

### Writing Tests

Place tests in `tests/unit/test_{domain}_routes.py`. Follow the existing pattern:

```python
class TestBankingTransfers:
    def test_wire_transfer_success(self, client, mock_users):
        resp = client.post('/api/v1/transfers/wire', json={
            'from_account': 'ACC-001',
            'to_account': 'ACC-002',
            'amount': 100.00
        })
        assert resp.status_code == 200

    def test_wire_transfer_negative_amount(self, client):
        """Business logic flaw: negative amounts accepted."""
        resp = client.post('/api/v1/transfers/wire', json={
            'amount': -500.00
        })
        assert resp.status_code == 200  # Intentionally vulnerable
```

## Building & Packaging

### Bundle the Web Frontend

```bash
just bundle-web
# Builds React SPA into apps/vuln-api/app/web_dist/
```

### Build the Python Wheel

```bash
just build-api
# Runs bundle-web first (via Nx dependency), then uv build
# Output: apps/vuln-api/dist/chimera_api-0.1.0-py3-none-any.whl
```

### Verify the Wheel

```bash
unzip -l apps/vuln-api/dist/chimera_api-*.whl | grep web_dist
# Should show bundled assets (index.html, JS, CSS)
```

### Publish

```bash
just publish-api
# Runs uv publish (requires PyPI credentials)
```

## Adding a New Domain

1. **Create the blueprint**:

```bash
mkdir apps/vuln-api/app/blueprints/mydomain
```

```python
# app/blueprints/mydomain/__init__.py
from app.routing import DecoratorRouter as Router

mydomain_router = Router(routes=[])

from . import routes  # noqa: E402,F401  (decorator side-effects)
```

```python
# app/blueprints/mydomain/routes.py
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.routing import safe_json
from . import mydomain_router


@mydomain_router.route('/api/v1/mydomain/items', methods=['GET'])
async def list_items(request: Request):
    return JSONResponse({"items": []})
```

2. **Mount in `create_app()`** (`app/asgi.py`):

```python
from app.blueprints.mydomain import mydomain_router

routes = [
    # ... existing routers ...
    *mydomain_router.routes,
]
```

3. **Add data stores** (if needed) in `app/models/data_stores.py`:

```python
mydomain_items_db = DataStore("mydomain_items")
```

4. **Add store reset** in `tests/conftest.py`:

```python
from app.models import mydomain_items_db
# In reset_databases fixture:
mydomain_items_db.clear()
```

5. **Write tests** in `tests/unit/test_mydomain_routes.py`

6. **Add a web page** (optional) in `apps/vuln-web/src/pages/MydomainDashboard.tsx`

## Code Style

### Python

- **Formatter**: black with 120-character line length
- **Linters**: flake8 + pylint
- **Run**: `just -f apps/vuln-api/justfile format` and `just -f apps/vuln-api/justfile lint`

### TypeScript

- **Strict mode** enabled (`tsconfig.json`)
- **No unused locals/params** enforced by `tsc`
- **Linter**: ESLint — `just web-lint`

### Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/) with scope:

```
feat(api): add telecom SIM swap endpoint
fix(web): correct dark mode toggle in sidebar
test(api): add healthcare PHI exposure tests
docs(readme): update quick start instructions
```

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `just` | List all recipes |
| `just dev` | Start API + web dev servers |
| `just test` | Run all tests |
| `just lint` | Lint all projects |
| `just bundle` | Build wheel with bundled web |
| `just api-test-unit` | Run API unit tests directly |
| `APPARATUS_ENABLED=true APPARATUS_BASE_URL=http://127.0.0.1:8090 APPARATUS_TIMEOUT_MS=5000 just dev` | Start Chimera with the external Apparatus integration enabled |
| `just web-build` | Build web app |
| `just graph` | Show Nx dependency graph |
| `just affected test` | Test only changed projects |
| `just reset` | Clear Nx cache |
