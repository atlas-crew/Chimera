# Architecture

## System Overview

Chimera is a pnpm + Nx monorepo containing two applications that can run independently in development or be bundled into a single Python package for distribution.

```
                    ┌─────────────────────────────────────┐
                    │           Chimera Monorepo           │
                    │                                     │
                    │  ┌──────────────┐ ┌──────────────┐  │
                    │  │   vuln-api   │ │   vuln-web   │  │
                    │  │ Starlette/   │ │ React/Vite/TS│  │
                    │  │  uvicorn     │ │              │  │
                    │  │  Port 8880   │ │  Port 5175   │  │
                    │  └──────┬───────┘ └──────┬───────┘  │
                    │         │                │          │
                    │         │    Vite Proxy   │          │
                    │         │◄── /api/* ──────┘          │
                    │         │                            │
                    └─────────┴────────────────────────────┘
```

## Request Routing

### Development Mode (two servers)

```mermaid
flowchart LR
    Browser -->|:5175| Vite[Vite Dev Server]
    Vite -->|/api/*| API[uvicorn :8880]
    Vite -->|other| SPA[React SPA]
    API -->|JSON| Browser
```

In development, the Vite dev server on port 5175 proxies `/api/*` requests to the uvicorn ASGI server on port 8880. All other routes serve the React SPA with hot module replacement.

### Production Mode (single server)

```mermaid
flowchart LR
    Browser -->|:8880| API[uvicorn / Starlette]
    API -->|/api/*| Routers[Domain Routers]
    API -->|/swagger| SwaggerUI[Static Swagger UI]
    API -->|/openapi.yaml| Spec[Static OpenAPI spec]
    API -->|/assets/*| Assets[web_dist/assets/]
    API -->|other paths| Index[web_dist/index.html]
    Routers -->|JSON| Browser
    Assets -->|JS/CSS| Browser
    Index -->|HTML| Browser
```

When `web_dist/index.html` exists, the Starlette factory serves both the API and the SPA from a single uvicorn process. The path-converter catch-all handles three cases:

1. **API prefixes** (`api/`, `apidocs`, `flasgger_static`, `apispec`) — returns JSON 404 for missing API routes
2. **Static files** — serves JS, CSS, and images from `web_dist/`
3. **Everything else** — returns `index.html` for React Router client-side routing

### API-Only Mode (no web_dist)

When `web_dist/index.html` is absent, the `main_router` `/` handler returns the built-in demo template and the API operates standalone. This is the default for development and API-only installs.

## ASGI Application Factory

```mermaid
flowchart TD
    A[create_app] --> B[init_config — populate app_config from env + overrides]
    B --> C{USE_DATABASE?}
    C -->|true| D[init_database — SQLAlchemy engine + drop_all/create_all + seed]
    C -->|false| E[Skip DB init]
    D --> F[Import 25+ domain routers]
    E --> F
    F --> G[Compose middleware stack: TrafficRecorder, BodyBuffer, CORS, Session, CSP]
    G --> H[Construct Starlette app with routes + middleware + exception_handlers]
    H --> I[Seed in-memory demo data]
    I --> J{web_dist/index.html?}
    J -->|exists| K[Mount /assets + add /\{path:path\} catch-all]
    J -->|absent| L[main_router serves demo template at /]
    K --> M[return app]
    L --> M
```

## Router Architecture

Each industry domain is a self-contained Starlette router in `app/blueprints/{domain}/`. The directory name "blueprints" is preserved from the pre-migration layout; the underlying object is a `DecoratorRouter` (a thin `starlette.routing.Router` subclass that supports `@router.route(...)` decorators):

```
app/blueprints/
├── auth/              # JWT, MFA, sessions, API keys (30 routes)
├── banking/           # Accounts, transfers, KYC (29 routes)
├── healthcare/        # HIPAA, PHI, claims (31 routes)
├── ecommerce/         # Cart, checkout, gift cards (48 routes)
├── insurance/         # Policies, claims, underwriting (42 routes)
├── saas/              # Multi-tenant, SAML, billing (30 routes)
├── government/        # Citizen services, benefits (28 routes)
├── telecom/           # SIM swaps, CDR, porting (23 routes)
├── energy_utilities/  # SCADA, meters, grid control (23 routes)
├── admin/             # System admin, config (20 routes)
├── payments/          # Card processing, refunds (18 routes)
├── mobile/            # Biometric, device trust (15 routes)
├── compliance/        # AML, sanctions, audit (16 routes)
├── loyalty/           # Points, rewards (14 routes)
├── integrations/      # Webhooks, SSRF targets (13 routes)
├── checkout/          # Payment flow (12 routes)
├── ics_ot/            # Industrial control (10 routes)
├── infrastructure/    # Cloud, secrets (18 routes)
├── security_ops/      # Blue team tools (8 routes)
├── attack_sim/        # Red team simulation (25 routes)
├── testing/           # Test utilities (7 routes)
├── genai/             # AI/ML exploitation (4 routes)
├── diagnostics/       # System diagnostics (2 routes)
├── recorder/          # Traffic recording (3 routes)
├── throughput/        # Performance testing (2 routes)
├── main/              # Health check, home (2 routes)
└── database_vulnerable/ # Real SQLi endpoints (8 routes)
```

## Data Layer

```mermaid
flowchart TD
    Routes[Blueprint Routes] --> DS{Data Source}
    DS -->|Default| Mem[In-Memory DataStore]
    DS -->|USE_DATABASE=true| SQLite[SQLite via SQLAlchemy]
    Mem --> DAL[dal.py: thread-safe CRUD with threading.Lock]
    DAL --> Stores[data_stores.py: 100+ named stores]
    SQLite --> ORM[orm.py: SQLAlchemy 2.0 DeclarativeBase models]
    SQLite --> DB[database.py: engine + sessionmaker + seed_data]
```

- **In-memory mode** (default): `DataStore` and `TransactionalDataStore` classes provide thread-safe CRUD with `threading.Lock`. 100+ named stores defined in `data_stores.py`.
- **Database mode** (`USE_DATABASE=true`): plain SQLAlchemy 2.0 (no Flask-SQLAlchemy) backs the `database_vulnerable` router with f-string SQL paths used by the SQLi WAF tests. ORM models live in `app/orm.py`; engine/session lifecycle in `app/database.py`.

## Build Pipeline

```mermaid
flowchart LR
    A[just bundle] --> B[Nx resolves deps]
    B --> C[vuln-web:build:bundle]
    C --> D[tsc -b + vite build]
    D --> E[Output to app/web_dist/]
    E --> F[chimera-api:build]
    F --> G[uv build]
    G --> H[chimera_api-0.1.0.whl]
```

The `chimera-api:build` Nx target declares a dependency on `vuln-web:build:bundle`. Running `just bundle` (or `pnpm nx run chimera-api:build`) triggers the full pipeline:

1. **TypeScript check** — `tsc -b` validates the React code
2. **Vite bundle** — builds the SPA into `apps/vuln-api/app/web_dist/`
3. **Python wheel** — `uv build` packages everything via hatchling, with `force-include` ensuring `web_dist/` makes it into the wheel despite being gitignored

## CSP Header Strategy

| Route Type | `style-src` | Reason |
|------------|-------------|--------|
| `/swagger`, `/openapi.yaml` | `'self' unpkg.com 'unsafe-inline'` | Swagger UI needs external CDN + inline styles |
| `/api/*` | `'self'` | Strict CSP for API responses |
| All other paths (SPA) | `'self' 'unsafe-inline'` | Tailwind/Vite require inline styles |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `true` | `full` enables all vulns, `strict` blocks dangerous endpoints |
| `USE_DATABASE` | `false` | Enable SQLite for real SQL injection |
| `DATABASE_PATH` | `demo.db` | SQLite file location |
| `PORT` | `80` | Server port (container), CLI defaults to `8880` |
| `DEMO_THROUGHPUT_MODE` | `false` | Enable throughput testing short-circuit |
| `DEMO_THROUGHPUT_PATHS` | `` | Comma-separated paths to short-circuit |
