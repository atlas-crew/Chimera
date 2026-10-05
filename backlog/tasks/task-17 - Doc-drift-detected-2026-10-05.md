---
id: TASK-17
title: 'Doc drift detected 2026-10-05'
status: To Do
assignee: []
created_date: '2026-10-05 00:00'
updated_date: '2026-10-05 00:00'
labels:
  - docs
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Automated doc-drift scan run on 2026-10-05 across 12 audited files. Findings below are grouped by file with severity P0 (user-facing factual error), P1 (dev-doc error), and P2 (minor staleness / internal inconsistency).

---

### README.md

- README.md:48 — `| \`DEMO_MODE\` | \`strict\` | \`full\` enables all vulnerabilities… |` — claims default is `strict`; `app/config.py:31` defaults to `'full'` via `os.environ.get('DEMO_MODE', 'full')` — update table default to `full` or align the code default. **[P0]**
- README.md:247 — `just api-test-unit       # Run API unit tests directly` — root `justfile`'s `api-test-unit` recipe calls `make -C apps/vuln-api test-unit`; no `Makefile` exists in `apps/vuln-api/`; command would fail — fix recipe to use `just -f apps/vuln-api/justfile test-unit`. **[P1]**

---

### docs/architecture.md

- docs/architecture.md:165 — `| \`DEMO_MODE\` | \`true\` | \`full\` enables all vulns, \`strict\` blocks dangerous endpoints |` — default value `true` is neither a valid mode string nor matches code (`app/config.py:31` defaults to `'full'`); all other doc files say `strict` — fix to `full` (or `strict` if intent is safe-by-default) and align with `app/config.py`. **[P1]**
- docs/architecture.md:89–115 — blueprint table lists 26 domains but omits the `education` blueprint; `app/asgi.py:185` imports `from app.blueprints.education import education_router` and `app/blueprints/education/` directory exists — add `education` entry to the table. **[P1]**

---

### docs/developer-guide.md

- docs/developer-guide.md:47 — `| \`DEMO_MODE\` | \`strict\` | \`full\` enables all vulnerabilities… |` — claims default is `strict`; `app/config.py:31` defaults to `'full'` — update table default or align code. **[P0]**

---

### docs/dockerhub-overview.md

- docs/dockerhub-overview.md:23 — `| \`DEMO_MODE\` | \`strict\` | \`full\` = all vulnerabilities enabled… |` — claims default is `strict`; `app/config.py:31` defaults to `'full'` — update table default or align code. **[P0]**

---

### AGENTS.md (root)

- AGENTS.md:~line for Vulnerability gating section — `**Vulnerability gating** (\`security.py\`): … \`is_full_mode()\` / \`get_demo_mode()\` helpers for conditional logic in routes` — `is_full_mode()` does not exist in the Starlette app at all (only in legacy Flask `apps/vuln-api/security.py` which is not imported by any blueprint); `get_demo_mode()` is defined locally in `app/blueprints/auth/routes.py`, not in `security.py`; actual per-vuln gating uses `security_config` from `app.utils.security_config` — update to describe the actual gating mechanism. **[P1]**
- AGENTS.md:~coverage line — `Coverage target: 80% minimum (\`make test-coverage\`)` — `make test-coverage` references a non-existent `Makefile`; correct command is `just -f apps/vuln-api/justfile test-coverage`. **[P1]**

---

### apps/vuln-api/API-DOCUMENTATION.md

- apps/vuln-api/API-DOCUMENTATION.md:17 — `a honeypot with 469 vulnerable endpoints` — contradicts 456+ stated in README.md, dockerhub-overview.md, apps/vuln-api/README.md, and AGENTS.md (root). **[P2]**
- apps/vuln-api/API-DOCUMENTATION.md:20 — `**469 Vulnerable Endpoints** across 28 router packages` — same count inconsistency; docs/architecture.md shows 26 blueprint entries (and misses `education`, making it at least 27); 28 vs 26/27 also disagrees. **[P2]**

---

### docs/endpoints-catalog.md

- docs/endpoints-catalog.md:4 — frontmatter `description: Complete reference of 469 API endpoints` — contradicts 456+ stated in README.md and other docs. **[P2]**
- docs/endpoints-catalog.md:16 — `**Total Endpoints**: 469 unique endpoints (verified against the live route table via \`just docs-drift\`)` — same count inconsistency; `just docs-drift` is not a recipe in the root `justfile` (closest is `just -f apps/vuln-api/justfile docs-check`). **[P2]**

---

### apps/vuln-api/tests/README.md

This file contains extensive stale content from a pre-migration era. Key drift findings:

- apps/vuln-api/tests/README.md:73-74 — claims `tests/pytest.ini` and `tests/run_tests.sh` exist in the `tests/` directory — neither file exists at that path (script is at `apps/vuln-api/scripts/run_tests.sh`, pytest config is in `pyproject.toml` or absent). **[P1]**
- apps/vuln-api/tests/README.md:75 — claims `tests/justfile` exists — does not exist. **[P1]**
- apps/vuln-api/tests/README.md:68–72 — claims `tests/vulnerability/` directory exists with `test_sql_injection.py`, `test_xss.py`, `test_command_injection.py`, `test_auth_bypass.py` — `tests/vulnerability/` directory does not exist; these files are absent. **[P1]**
- apps/vuln-api/tests/README.md:63–66 — claims `tests/integration/test_auth_flow.py`, `test_transaction_flow.py`, `test_admin_operations.py` exist — `tests/integration/` directory contains only `__init__.py`. **[P1]**
- apps/vuln-api/tests/README.md:56–58 — claims `tests/unit/test_validators.py` and `tests/unit/test_responses.py` exist — neither file exists in `tests/unit/`. **[P1]**
- apps/vuln-api/tests/README.md:234–237 — claims fixtures `auth_headers`, `sample_data`, `mock_services` exist in `conftest.py` — none of these fixtures are defined in `tests/conftest.py`. **[P1]**
- apps/vuln-api/tests/README.md:220–230 — `pytest.ini` block shows markers `slow`, `security`, `critical` — actual project markers used are `vulnerability`, `integration`, `smoke` per AGENTS.md, justfile, and conftest.py. **[P1]**
- apps/vuln-api/tests/README.md:213–215 — `Coverage Requirements: Minimum overall: 90%` — contradicts `--cov-fail-under=80` in `apps/vuln-api/justfile:48`. **[P2]**
- apps/vuln-api/tests/README.md:301–315 — `Test Template` uses `self.app = create_app('testing')` and `self.app.test_client()` — these are Flask patterns; Starlette `create_app()` does not accept a positional string arg and uses `TestClient(app)`, not `.test_client()`. **[P1]**

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

- [ ] README.md:48 — DEMO_MODE default column updated to match `app/config.py` actual default
- [ ] README.md:247 — `just api-test-unit` recipe fixed (no `Makefile` in `apps/vuln-api/`)
- [ ] docs/architecture.md:165 — DEMO_MODE default value corrected from `true`
- [ ] docs/architecture.md — `education` blueprint added to the blueprint table
- [ ] docs/developer-guide.md:47 — DEMO_MODE default column updated
- [ ] docs/dockerhub-overview.md:23 — DEMO_MODE default column updated
- [ ] AGENTS.md — Vulnerability gating section updated to describe actual Starlette gating (`security_config`, `app.utils.security_config`)
- [ ] AGENTS.md — `make test-coverage` reference replaced with `just -f apps/vuln-api/justfile test-coverage`
- [ ] apps/vuln-api/API-DOCUMENTATION.md — endpoint count reconciled with README.md or a definitive recount performed
- [ ] docs/endpoints-catalog.md — endpoint count reconciled; `just docs-drift` recipe reference corrected
- [ ] apps/vuln-api/tests/README.md — stale file paths, fixture names, markers, coverage threshold, test template updated to reflect current Starlette test infrastructure
- [ ] All linked claims verified against current code after fixes are applied
