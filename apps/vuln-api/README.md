# Chimera - Starlette Honeypot Application

A Python Starlette/uvicorn ASGI application with 456+ intentionally vulnerable endpoints for testing WAF capabilities.

## 📚 Documentation

- **[docs/API-DOCUMENTATION.md](docs/API-DOCUMENTATION.md)** - Complete API documentation
- **[docs/openapi.yaml](docs/openapi.yaml)** - Static OpenAPI spec (Swagger UI at `/swagger`). Generated from blueprint routes with minimal schemas; some routes are conditional (e.g., `USE_DATABASE=true`).
- **[../DOCUMENTATION.md](../DOCUMENTATION.md)** - Project-wide documentation index

## 🚀 Quick Start

### Local Development
```bash
# 1. Install uv (https://github.com/astral-sh/uv) if you don't have it yet
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install project dependencies (creates .venv/ automatically)
uv sync --extra dev

# 3. Launch the vulnerable demo API
just run-vulnerable

# Or invoke uvicorn directly:
DEMO_MODE=full uv run uvicorn app.asgi:app --host 0.0.0.0 --port 8880 --reload

# Access at http://localhost:8880
```

> **Fallback:** uv is the preferred Python toolchain (matches the Docker image). `pip install chimera-api` works for end users that don't need to develop against the source.

### Docker Deployment
```bash
# As part of WAF demo
./waf-demo --sites=demo start

# Or standalone
docker build -t demo-api .
docker run -p 8080:80 demo-api
```

### Running Tests
```bash
# All tests (runs the same uv environment used locally/Docker)
just test

# Quick tests
just test-quick

# With coverage
just test-coverage
```

### Database Mode (Opt-In)

**NEW:** Enable real SQL injection vulnerabilities with SQLite backend.

```bash
# Enable database mode locally
USE_DATABASE=true just run-vulnerable

# Enable in Docker
USE_DATABASE=true docker run -p 8080:80 demo-api

# Or via docker-compose (in apps/demo-targets/)
USE_DATABASE=true ./waf-demo --sites=demo start
```

**What Database Mode Enables:**
- 📊 **Real SQLite database** with banking, healthcare, insurance data
- 🔓 **8 intentionally vulnerable endpoints** for SQL injection testing
- 💉 **Multiple SQLi types**: Classic, Blind Boolean, Time-based, UNION, Error-based
- 📈 **Realistic demo data**: 5 users, 3 bank accounts, 3 patient records, 3 policies
- 🎯 **Traffic generator support**: `PROFILE=database` for baseline SQL queries

**New Vulnerable Endpoints** (only active with `USE_DATABASE=true`):
```
GET  /api/v1/patients/search?ssn=<ssn>              # Classic SQLi
POST /api/v1/auth/login-vulnerable                  # Auth bypass
GET  /api/v1/banking/accounts/search?account_number # UNION-based
GET  /api/v1/insurance/policies/lookup?policy_number # Blind Boolean
GET  /api/v1/transactions/history?account_id        # Time-based blind
GET  /api/v1/claims/search?policy_id&order_by       # ORDER BY injection
GET  /api/v1/users/profile?user_id                  # Error-based
POST /api/v1/healthcare/records                     # Second-order SQLi
```

**Example SQL Injection Attack:**
```bash
# Classic SQL injection to dump all patient records
curl 'http://localhost:8880/api/v1/patients/search?ssn=%27%20OR%20%271%27=%271'

# Authentication bypass
curl -X POST http://localhost:8880/api/v1/auth/login-vulnerable \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com'\'' OR '\''1'\''='\''1'\'' --","password":"anything"}'

# UNION-based data exfiltration
curl 'http://localhost:8880/api/v1/banking/accounts/search?account_number=ACC-1001'\'' UNION SELECT id,email,password,role,1,2,3,4 FROM users --'
```

**Traffic Generation with Database Mode:**
```bash
# Generate baseline database traffic (10 RPS for 60 seconds)
PROFILE=database RPS=10 DURATION=60 ./scripts/traffic-generator.sh
```

## 🎯 Key Features

- **456+ Vulnerable Endpoints** across Auth, Banking, Healthcare, and Admin domains
- **50+ Vulnerability Types** including SQL injection, XSS, command injection, and more
- **Thread-Safe Data Layer** with validation bypass for testing
- **200+ Unit Tests** with 94% code coverage
- **uvicorn / ASGI** server with multiple worker processes in production

## 📁 Project Structure

```
apps/vuln-api/
├── app/                    # Application code
│   ├── asgi.py            # Starlette factory + module-level `app` for uvicorn
│   ├── __init__.py        # Re-exports `create_app` and `app` from `app.asgi`
│   ├── blueprints/        # Domain-specific routers (one package per domain)
│   ├── models/            # In-memory data stores + DataStore / TransactionalDataStore
│   ├── orm.py             # SQLAlchemy 2.0 ORM (used when USE_DATABASE=true)
│   ├── routing.py         # DecoratorRouter shim + safe_json / get_json_or_default
│   └── utils/             # Hotpatch decorator, monitoring, demo data, templates
├── tests/                  # Test suite (Starlette TestClient)
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Fixtures (client, app, set_session, read_session)
├── docs/                   # Additional documentation
├── static/                 # Static assets served via StaticFiles mount
├── pyproject.toml          # Dependencies (Starlette + uvicorn + SQLAlchemy)
├── Dockerfile              # Dev container (uvicorn --reload)
├── Dockerfile.prod         # Production container (uvicorn --workers 4)
├── Dockerfile.fargate      # ECS/Fargate container
└── justfile                # Build automation (run-vulnerable, run-secure, test-*)
```

## 🔒 Security Warning

⚠️ **This application contains intentional security vulnerabilities for testing purposes.**

**DO NOT**:
- Deploy to production
- Expose to the internet
- Use with real data

**DO**:
- Use only in isolated test environments
- Run behind WAF protection
- Reset regularly

## 🧪 Example Vulnerability Tests

```bash
# SQL Injection
curl -X POST http://localhost:8880/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"any"}'

# Command Injection
curl -X POST http://localhost:8880/api/v1/admin/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"ls; cat /etc/passwd"}'

# Path Traversal
curl "http://localhost:8880/api/v1/admin/logs?file=../../../../etc/passwd"
```

## 📚 Feature Reference

The application simulates a wide range of industries and technical domains to provide a comprehensive attack surface.

| Domain / Industry | Endpoints | Description |
|-------------------|-----------|-------------|
| **Admin** | ~19 | User management, system configuration, data export, and administrative overrides. |
| **Attack Sim** | ~24 | Simulation of kill-chain phases: reconnaissance, lateral movement, persistence, and exfiltration. |
| **Auth** | ~28 | Authentication flows including OAuth, MFA, SAML, API keys, and session management. |
| **Banking** | ~29 | Core banking operations, wire transfers, loans, KYC, open banking, and remote check deposit. |
| **Checkout** | ~12 | E-commerce checkout flows: shipping, taxes, promotions, and payment processing. |
| **Compliance** | ~16 | Regulatory compliance features: AML monitoring, SAR reporting, and audit trails. |
| **Database Vuln** | ~8 | dedicated endpoints for demonstrating various SQL injection techniques (Classic, Blind, Time-based). |
| **Ecommerce** | ~40 | Online marketplace features: product catalog, vendor management, inventory, orders, and webhooks. |
| **Energy** | ~22 | Utility operations: grid dispatch, smart metering, outage management, and SCADA config. |
| **GenAI** | ~4 | LLM-based chat interfaces, RAG uploads, AI agent browsing (SSRF), and prompt injection targets. |
| **Government** | ~30 | Public sector services: benefits, permits, licensing, FOIA requests, and citizen records. |
| **Healthcare** | ~27 | Medical systems: patient records (EMR), prescriptions, appointments, and HIPAA data. |
| **ICS / OT** | ~10 | Industrial control systems: PLC commands, setpoints, HMI interfaces, and sensor readings. |
| **Infrastructure** | ~19 | Cloud & DevOps targets: Kubernetes pods, service mesh, gateway routes, and secrets. |
| **Insurance** | ~42 | InsurTech operations: claims processing, underwriting, policy management, and premiums. |
| **Integrations** | ~13 | Third-party connectivity: webhooks, CRM sync, email gateways, and analytics. |
| **Loyalty** | ~14 | Rewards programs: points transfer, tier management, referrals, and cashback. |
| **Mobile** | ~13 | Mobile app backend: device fingerprinting, biometric auth, and app configuration. |
| **Payments** | ~19 | Payment gateway features: card processing, fraud rules, settlements, and disputes. |
| **SaaS** | ~30 | B2B SaaS features: multi-tenancy, billing/invoices, SSO/SCIM, and API key management. |
| **Security Ops** | ~8 | SOC workflows: incident creation, threat intelligence, and automated remediation. |
| **Telecom** | ~21 | Telco operations: subscriber profiles, SIM swap, network provisioning, and CDRs. |

**Total Surface Area:** 456+ Endpoints across 25+ domains.

## 🛠️ Development

See [docs/API-DOCUMENTATION.md](docs/API-DOCUMENTATION.md) for:
- Adding new endpoints
- Creating vulnerabilities
- Writing tests
- Configuration options
- Troubleshooting guide

## 📈 Test Coverage

- **Overall**: 94%
- **Auth Module**: 97%
- **Banking Module**: 95%
- **Healthcare Module**: 93%
- **Admin Module**: 92%

## 🤝 Contributing

1. Add endpoints to appropriate blueprint
2. Include intentional vulnerabilities
3. Write comprehensive tests
4. Update documentation
5. Run test suite before committing

## 📄 License

For testing and demonstration purposes only.

---

For detailed information, see **[docs/API-DOCUMENTATION.md](docs/API-DOCUMENTATION.md)**
