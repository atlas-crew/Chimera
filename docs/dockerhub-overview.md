# Chimera

Intentionally vulnerable application with 456+ endpoints across 25+ industry verticals for WAF testing, security research, and education. Bundles a Starlette/uvicorn API and React web portal in a single image.

Part of the [Inferno Lab](https://github.com/inferno-lab) security testing suite.

## Quick Start

```bash
docker run -p 8880:8880 -e DEMO_MODE=full nickcrew/chimera
```

- Web portal: [localhost:8880](http://localhost:8880)
- Swagger UI: [localhost:8880/swagger](http://localhost:8880/swagger)
- Health check: [localhost:8880/healthz](http://localhost:8880/healthz)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8880` | Server port |
| `DEMO_MODE` | `strict` | `full` = all vulnerabilities enabled; `strict` = dangerous endpoints return 403 |
| `USE_DATABASE` | `false` | Enable SQLite for real SQL injection testing |
| `DATABASE_PATH` | `demo.db` | SQLite location (when `USE_DATABASE=true`) |
| `DEMO_THROUGHPUT_MODE` | `false` | Enable high-throughput testing endpoints |
| `LOG_LEVEL` | `info` | Logging level |

### Enable real SQL injection

```bash
docker run -p 8880:8880 \
  -e DEMO_MODE=full \
  -e USE_DATABASE=true \
  nickcrew/chimera
```

## Industry Domains

456+ endpoints spanning: E-commerce, Banking, Healthcare, Insurance, SaaS, Government, Telecom, Energy/SCADA, Payments, Mobile, Loyalty, ICS/OT, GenAI, and more. Full OWASP Top 10 coverage with 200+ intentional vulnerabilities.

## Using with Apparatus

[Apparatus](https://hub.docker.com/r/nickcrew/apparatus) is a security simulation platform. Chimera has a built-in integration that enables ghost traffic generation and coordinated attack simulations when both are running:

```bash
docker run -d --name apparatus -p 8090:8090 -e DEMO_MODE=true nickcrew/apparatus
docker run -d --name chimera -p 8880:8880 \
  -e DEMO_MODE=full \
  -e APPARATUS_ENABLED=true \
  -e APPARATUS_BASE_URL=http://host.docker.internal:8090 \
  nickcrew/chimera
```

### Apparatus integration variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APPARATUS_ENABLED` | `false` | Enable Apparatus integration |
| `APPARATUS_BASE_URL` | `http://127.0.0.1:8090` | Apparatus service URL |
| `APPARATUS_TIMEOUT_MS` | `5000` | Timeout for Apparatus requests |

## Using with Crucible

[Crucible](https://hub.docker.com/r/nickcrew/crucible) is an attack simulation and assessment engine. Its scenario catalog includes attacks designed for Chimera's endpoints — SQL injection, IDOR, JWT manipulation, SSRF, and more.

```bash
docker run -d --name chimera -p 8880:8880 -e DEMO_MODE=full nickcrew/chimera
docker run -d --name crucible -p 3000:3000 \
  -e CRUCIBLE_TARGET_URL=http://host.docker.internal:8880 \
  nickcrew/crucible
```

## Full Security Lab (Compose)

Run all three Inferno Lab products — Chimera as the target, Apparatus for simulation, and Crucible for assessments:

```yaml
services:
  chimera:
    image: nickcrew/chimera
    ports:
      - "8880:8880"
    environment:
      DEMO_MODE: "full"
      APPARATUS_ENABLED: "true"
      APPARATUS_BASE_URL: http://apparatus:8090
    networks:
      - lab

  apparatus:
    image: nickcrew/apparatus
    ports:
      - "8090:8090"
      - "8443:8443"
    environment:
      DEMO_MODE: "true"
    networks:
      - lab

  crucible:
    image: nickcrew/crucible
    ports:
      - "3000:3000"
    environment:
      CRUCIBLE_TARGET_URL: http://chimera:8880
    volumes:
      - crucible-data:/app/data
    networks:
      - lab

networks:
  lab:

volumes:
  crucible-data:
```

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Chimera Portal | [localhost:8880](http://localhost:8880) |
| Chimera Swagger | [localhost:8880/swagger](http://localhost:8880/swagger) |
| Apparatus Dashboard | [localhost:8090/dashboard](http://localhost:8090/dashboard) |
| Crucible UI | [localhost:3000](http://localhost:3000) |

## Also available on PyPI

```bash
pip install chimera-api
chimera-api --port 8880 --demo-mode full
```

## Links

- [Documentation](https://chimera.atlascrew.dev)
- [GitHub](https://github.com/inferno-lab/Chimera)
- [PyPI](https://pypi.org/project/chimera-api/)
