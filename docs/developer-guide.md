# Developer Guide

Setup, development workflow, testing, and contributing conventions for the Chimera project.

## Prerequisites

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

## Initial Setup

```bash
# Clone the repo
git clone <repo-url> && cd chimera

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

## Development Workflow

### Start Everything

```bash
just dev
```

This starts both servers in parallel via Nx:
- **Flask API** on `http://localhost:5000`
- **Vite dev server** on `http://localhost:5175` (proxies `/api/*` to Flask)

### Start Individually

```bash
# API only
just api-start

# Web only
just web-dev
```

### Demo Modes

Control vulnerability behavior with `DEMO_MODE`:

```bash
# All vulnerabilities active
DEMO_MODE=full uv run python app.py

# Dangerous endpoints blocked
DEMO_MODE=strict uv run python app.py

# Real SQL injection via SQLite
USE_DATABASE=true DEMO_MODE=full uv run python app.py
```

### Using the CLI

After installing the package (`pip install -e .` or from a wheel):

```bash
chimera-api --port 8880 --demo-mode full --debug
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8880` | Server port |
| `--debug` | off | Enable Flask debug mode |
| `--demo-mode` | none | `full` or `strict` |

## Project Structure

### vuln-api (Flask/Python)

```
apps/vuln-api/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── cli.py               # CLI entry point
│   ├── blueprints/          # 25+ domain modules (auth, banking, etc.)
│   │   └── {domain}/
│   │       ├── __init__.py  # Blueprint definition
│   │       └── routes.py    # Endpoint handlers
│   ├── models/
│   │   ├── dal.py           # DataStore (thread-safe CRUD)
│   │   └── data_stores.py   # 100+ named stores
│   ├── utils/               # Helpers, validators, monitoring
│   ├── web_dist/            # Bundled SPA (populated by build)
│   └── error_handlers.py    # JSON error responses
├── tests/
│   ├── conftest.py          # Shared fixtures, store reset
│   └── unit/                # Unit tests per domain
├── pyproject.toml           # Package config (hatchling)
├── Makefile                 # Test/lint recipes
└── app.py                   # Development entry point
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
├── vite.config.ts           # Dev config (proxy to Flask)
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
make -C apps/vuln-api test-quick

# Full CI suite with coverage
make -C apps/vuln-api test-ci

# Single test file
cd apps/vuln-api && uv run pytest tests/unit/test_auth_routes.py -v

# Vulnerability-specific tests
make -C apps/vuln-api test-vulnerability
```

### Test Conventions

**Fixtures** (defined in `tests/conftest.py`):

| Fixture | Description |
|---------|-------------|
| `client` | Flask test client |
| `app` | Flask application instance |
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
from flask import Blueprint
mydomain_bp = Blueprint('mydomain', __name__)
from . import routes
```

```python
# app/blueprints/mydomain/routes.py
from flask import request, jsonify
from . import mydomain_bp

@mydomain_bp.route('/api/v1/mydomain/items', methods=['GET'])
def list_items():
    return jsonify({"items": []})
```

2. **Register in `create_app()`** (`app/__init__.py`):

```python
from app.blueprints.mydomain import mydomain_bp
app.register_blueprint(mydomain_bp)
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
- **Run**: `make -C apps/vuln-api format` and `make -C apps/vuln-api lint`

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
| `just web-build` | Build web app |
| `just graph` | Show Nx dependency graph |
| `just affected test` | Test only changed projects |
| `just reset` | Clear Nx cache |
