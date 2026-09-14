---
id: TASK-17
title: 'Docs: Fix documentation drift detected 2026-09-14'
status: To Do
assignee: []
created_date: '2026-09-14 00:00'
updated_date: '2026-09-14 00:00'
labels:
  - docs
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Automated drift audit on 2026-09-14 found **23 drift findings** across 8 of the 12 audited doc files. Findings are grouped below by file. Severity key: **P0** = user-facing factual error, **P1** = developer-doc error (broken feature, wrong symbol, non-existent file), **P2** = minor staleness or internal inconsistency.

---

### docs/endpoints-catalog.md

- Line 15 — `` `just docs-drift` `` — claims endpoint count "verified against the live route table via `just docs-drift`" but that recipe does not exist; the correct recipe is `docs-check` in `apps/vuln-api/justfile`. — **Proposed fix**: Replace `` `just docs-drift` `` with `` `just docs-check` ``. **(P1)**

- Line 15 vs line 601 — `"469 unique endpoints"` (line 15) vs `"243 Total Routes"` (line 601 in the Implementation Status summary) — internally inconsistent endpoint count within the same file. — **Proposed fix**: Reconcile to one authoritative number or remove the bottom count. **(P2)**

---

### docs/architecture.md

- Env var table row `DEMO_MODE` (line ~165) — `"Default: true"` — listed default is `true`; `app/config.py:31` shows `os.environ.get('DEMO_MODE', 'full')`, so the code default is `full`. — **Proposed fix**: Change default cell to `full`. **(P1)**

- Env var table row `DEMO_THROUGHPUT_PATHS` (line ~169) — claims this is a valid env var ("Comma-separated paths to short-circuit") but `app/config.py` contains no `DEMO_THROUGHPUT_PATHS` attribute or mapping; only `DEMO_THROUGHPUT_MODE`, `DEMO_THROUGHPUT_PAYLOAD_BYTES`, and `DEMO_THROUGHPUT_MAX_BYTES` exist. — **Proposed fix**: Remove the row or add the env var to config.py if intentional. **(P2)**

---

### docs/developer-guide.md / README.md / docs/dockerhub-overview.md

- `DEMO_MODE` default listed as `"strict"` in all three files — `app/config.py:31` defaults to `"full"` (not `"strict"`). The discrepancy means running the server with no env var set silently enables all vulnerabilities contrary to what the docs promise. — **Proposed fix**: Correct all three doc tables to show `full` as the default, or change the code default to `strict` with a deliberate decision. **(P1)**

---

### AGENTS.md (root)

- Line 94 — `` `security.py` `` — "Vulnerability gating (`security.py`)" — the file `apps/vuln-api/app/security.py` does not exist; gate logic lives in `app/utils/security_config.py` and inline in blueprint routes. — **Proposed fix**: Replace `security.py` with `app/utils/security_config.py`. **(P1)**

- Line 95 — `` `@require_full_demo` `` — decorator referenced as blocking dangerous endpoints in strict mode; does not exist anywhere in the codebase (`grep -rn require_full_demo app/` returns no results). — **Proposed fix**: Remove the mention or add the decorator to `security_config.py`. **(P1)**

- Line 95 — `` `is_full_mode()` `` — helper function referenced; does not exist anywhere in the codebase (`grep -rn is_full_mode app/` returns no results). — **Proposed fix**: Remove or replace with `get_demo_mode()` (which does exist in `app/blueprints/auth/routes.py`). **(P1)**

- Line 116 — `"In production (Docker), nginx handles the proxy."` — The production Dockerfile (`apps/vuln-api/Dockerfile.prod`) uses `CMD ["uv", "run", "uvicorn", "app.asgi:app", "--workers", "4"]` with no nginx layer; Starlette itself serves the SPA catch-all. nginx was never added in the Flask → Starlette migration. — **Proposed fix**: Replace with "In production (Docker), uvicorn serves the API and SPA from a single process." **(P1)**

---

### apps/vuln-api/AGENTS.md

- Line 21 — `` `./run_tests.sh all` `` — "Default: `just test` (delegates to `./run_tests.sh all`)" — `run_tests.sh` does not exist at `apps/vuln-api/run_tests.sh`. — **Proposed fix**: Remove the parenthetical; `just test` delegates to `just test-all` which runs pytest directly via `uv run pytest`. **(P1)**

- Line 29 — `` `security.py` `` — "feature toggles in `security.py`" — same as AGENTS.md root finding above; `app/security.py` does not exist. — **Proposed fix**: Replace with `app/utils/security_config.py`. **(P1)**

---

### apps/vuln-api/README.md

- Line 7 — `` `docs/API-DOCUMENTATION.md` `` — broken relative link: the file is at `apps/vuln-api/API-DOCUMENTATION.md`, not `apps/vuln-api/docs/API-DOCUMENTATION.md`. The `docs/` subdirectory has `openapi.yaml` but not `API-DOCUMENTATION.md`. — **Proposed fix**: Change link to `API-DOCUMENTATION.md`. **(P2)**

---

### apps/vuln-api/tests/README.md

This file is heavily stale post-migration; it describes the pre-migration test suite. All findings below are P1 unless noted.

- Lines 29, 35 — `` `./run_tests.sh` `` — two references to `./run_tests.sh` (variants `all` and `--quick`); file does not exist. — **Proposed fix**: Replace with `just test` and `just test-quick`. **(P1)**

- Lines 221–230 — `` `pytest.ini` `` — shows contents of `tests/pytest.ini`; file does not exist (`ls apps/vuln-api/tests/pytest.ini` fails). — **Proposed fix**: Remove the section or move settings to `pyproject.toml [tool.pytest.ini_options]`. **(P1)**

- Lines 52–76 (test structure tree) — `` `tests/vulnerability/` `` — directory listed in tree does not exist. — **Proposed fix**: Remove from tree. **(P1)**

- Lines 52–76 (test structure tree) — `` `tests/smoke/` `` — directory listed in tree does not exist. — **Proposed fix**: Remove from tree; smoke tests run via `-m smoke` marker, not a separate directory. **(P1)**

- Line 56 — `` `test_validators.py` `` — listed in unit test tree; does not exist at `apps/vuln-api/tests/unit/test_validators.py`. — **Proposed fix**: Remove from tree. **(P1)**

- Line 57 — `` `test_responses.py` `` — listed in unit test tree; does not exist at `apps/vuln-api/tests/unit/test_responses.py`. — **Proposed fix**: Remove from tree. **(P1)**

- Lines 60–65 (integration test tree) — `` `test_auth_flow.py` ``, `` `test_transaction_flow.py` ``, `` `test_admin_operations.py` `` — all three files listed under `tests/integration/` do not exist; only `__init__.py` is in that directory. — **Proposed fix**: Remove the three file lines. **(P1)**

- Line 9 — `"Total Tests: 267"` — current test suite has ~492 tests (per TASK-16.7 migration receipt). — **Proposed fix**: Update to reflect current count or remove. **(P2)**

- Lines 217–220 — `"Coverage minimum: 90%"` — other docs and the justfile `test-coverage` recipe enforce 80% (`--cov-fail-under=80`), not 90%. — **Proposed fix**: Correct to 80%. **(P2)**

- Lines 163–166 — `` `response.json['success']` `` — test example uses Flask-style dict attribute access on the response; Starlette `TestClient` returns an `httpx.Response` where JSON is accessed via `response.json()` (a method call). The test would raise `TypeError` as-is. — **Proposed fix**: Update example to `response.json()['success']`. **(P1)**

- Lines 297–304 (test template) — `` `create_app('testing')` `` / `` `.test_client()` `` — uses Flask factory-and-test-client API pattern; Starlette fixtures use `TestClient(app)`. — **Proposed fix**: Rewrite template to use Starlette `TestClient`. **(P1)**

- Lines 251–253 — `` `pip install -r requirements.txt` `` — GitHub Actions snippet installs `requirements.txt`; no such file exists in the repo; deps are managed via `uv sync --extra dev`. — **Proposed fix**: Replace with `uv sync --extra dev --frozen`. **(P1)**

---

### README.md (root)

- Lines ~242–248 — `` `make -C apps/vuln-api test-unit` `` (and `test-quick`, `test-vulnerability`, `test-smoke`) — four `make` commands in the testing section reference a `Makefile` that does not exist in `apps/vuln-api/`; the equivalent recipes are in `apps/vuln-api/justfile`. — **Proposed fix**: Replace with `just -f apps/vuln-api/justfile test-unit` etc. **(P1)**

---

### Cross-file endpoint count inconsistency

- README.md, AGENTS.md, docs/dockerhub-overview.md, apps/vuln-api/README.md all state `"456+"` endpoints; apps/vuln-api/API-DOCUMENTATION.md and docs/endpoints-catalog.md state `"469"`. The two numbers cannot both be accurate. — **Proposed fix**: Run `just docs-check` to get the authoritative count and update all six files to one consistent figure. **(P2)**

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 `docs/endpoints-catalog.md` line 15: `` `just docs-drift` `` replaced with `` `just docs-check` ``
- [ ] #2 `docs/endpoints-catalog.md` lines 15/601: endpoint count reconciled to one number
- [ ] #3 `docs/architecture.md` env var table: `DEMO_MODE` default corrected from `true` to `full`
- [ ] #4 `docs/architecture.md` env var table: `DEMO_THROUGHPUT_PATHS` row removed or added to config.py
- [ ] #5 `docs/developer-guide.md`, `README.md`, `docs/dockerhub-overview.md`: `DEMO_MODE` default corrected from `strict` to `full` (or code default changed to `strict` with intentional decision)
- [ ] #6 `AGENTS.md` (root) line 94: `security.py` replaced with `app/utils/security_config.py`
- [ ] #7 `AGENTS.md` (root) line 95: `@require_full_demo` mention removed or symbol added to codebase
- [ ] #8 `AGENTS.md` (root) line 95: `is_full_mode()` mention removed or symbol added to codebase
- [ ] #9 `AGENTS.md` (root) line 116: nginx production proxy claim corrected to uvicorn/Starlette
- [ ] #10 `apps/vuln-api/AGENTS.md` line 21: `./run_tests.sh all` reference removed
- [ ] #11 `apps/vuln-api/AGENTS.md` line 29: `security.py` reference corrected
- [ ] #12 `apps/vuln-api/README.md` line 7: broken `docs/API-DOCUMENTATION.md` link corrected
- [ ] #13 `apps/vuln-api/tests/README.md`: `./run_tests.sh` references replaced with `just` equivalents
- [ ] #14 `apps/vuln-api/tests/README.md`: `pytest.ini` section removed or corrected
- [ ] #15 `apps/vuln-api/tests/README.md`: `tests/vulnerability/` dir reference removed from tree
- [ ] #16 `apps/vuln-api/tests/README.md`: `tests/smoke/` dir reference removed from tree
- [ ] #17 `apps/vuln-api/tests/README.md`: non-existent test files (`test_validators.py`, `test_responses.py`) removed from tree
- [ ] #18 `apps/vuln-api/tests/README.md`: non-existent integration test files removed from tree
- [ ] #19 `apps/vuln-api/tests/README.md`: test count updated from 267 to current value
- [ ] #20 `apps/vuln-api/tests/README.md`: coverage minimum corrected from 90% to 80%
- [ ] #21 `apps/vuln-api/tests/README.md`: test example updated from Flask `response.json['key']` to Starlette `response.json()['key']`
- [ ] #22 `apps/vuln-api/tests/README.md`: test template updated from Flask `test_client()` to Starlette `TestClient`
- [ ] #23 `apps/vuln-api/tests/README.md`: GitHub Actions snippet updated from `pip install -r requirements.txt` to `uv sync --extra dev --frozen`
- [ ] #24 `README.md` (root) testing section: `make -C apps/vuln-api` commands replaced with `just -f apps/vuln-api/justfile` equivalents
- [ ] #25 Cross-file endpoint count: all 6 affected docs updated to one consistent authoritative number
- [ ] All linked claims verified against current code
<!-- AC:END -->
