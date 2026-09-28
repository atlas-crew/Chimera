---
id: TASK-17
title: 'Docs: Fix doc-claim drift detected on 2026-09-28'
status: To Do
assignee: []
created_date: '2026-09-28 00:00'
updated_date: '2026-09-28 00:00'
labels:
  - docs
priority: low
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Automated drift scan on 2026-09-28 found 17 concrete, verifiable claims in the active doc set that disagree with the current codebase. Findings are grouped by file and labelled P0 (user-facing factual error), P1 (dev-doc error), or P2 (minor staleness).

---

### docs/architecture.md

- `docs/architecture.md:165` — `| \`DEMO_MODE\` | \`true\` | …` — default listed as `true`; actual default in `app/config.py` line 31 is `'full'` (`os.environ.get('DEMO_MODE', 'full')`). Propose: change default cell to `full`. **P0**

---

### docs/developer-guide.md

- `docs/developer-guide.md:47` — `| \`DEMO_MODE\` | \`strict\` | …` — default listed as `strict`; actual default is `'full'`. Propose: change default cell to `full`. **P0**

---

### docs/dockerhub-overview.md

- `docs/dockerhub-overview.md:23` — `| \`DEMO_MODE\` | \`strict\` | …` — default listed as `strict`; actual default is `'full'`. Propose: change default cell to `full`. **P0**

---

### README.md

- `README.md:48` — `| \`DEMO_MODE\` | \`strict\` | …` — default listed as `strict`; actual default is `'full'`. Propose: change default cell to `full`. **P0**

- `README.md:243-246` — four `make -C apps/vuln-api test-unit/test-quick/test-vulnerability/test-smoke` commands — no `Makefile` exists in `apps/vuln-api/`. Propose: replace with `just -f apps/vuln-api/justfile test-unit` (etc.) or the `just api-test-unit` root alias. **P1**

---

### AGENTS.md

- `AGENTS.md:94` — `` **Vulnerability gating** (`security.py`) `` — `app/security.py` does not exist. The gating configuration lives in `app/utils/security_config.py`. Propose: update reference to `app/utils/security_config.py`. **P1**

- `AGENTS.md:96-97` — `@require_full_demo` decorator and `is_full_mode()` helper are named as existing symbols — neither appears anywhere in the codebase (`grep -rn require_full_demo` and `grep -rn is_full_mode` return no results). `get_demo_mode()` does exist but is defined in `app/blueprints/auth/routes.py`. Propose: remove non-existent symbols and update location of `get_demo_mode()`. **P1**

---

### apps/vuln-api/AGENTS.md

- `apps/vuln-api/AGENTS.md:29` — "feature toggles in `security.py`" — `security.py` does not exist. Propose: update to `app/utils/security_config.py`. **P1**

---

### docs/endpoints-catalog.md

- `docs/endpoints-catalog.md:15` — "verified against the live route table via `just docs-drift`" — no `docs-drift` recipe exists in the root justfile or `apps/vuln-api/justfile`. Closest existing recipe is `docs-check` in `apps/vuln-api/justfile`. Propose: replace `just docs-drift` with `just -f apps/vuln-api/justfile docs-check`. **P1**

- `docs/endpoints-catalog.md:4` vs `docs/endpoints-catalog.md:601` — front-matter description and intro claim "469 unique endpoints"; conclusion claims "243 Total Routes". Internally inconsistent. Propose: reconcile to a single accurate count. **P1**

---

### apps/vuln-api/README.md

- `apps/vuln-api/README.md:7` — link to `docs/API-DOCUMENTATION.md` (relative to `apps/vuln-api/`) — file does not exist at `apps/vuln-api/docs/API-DOCUMENTATION.md`; the documentation file is at `apps/vuln-api/API-DOCUMENTATION.md`. Propose: fix relative path to `./API-DOCUMENTATION.md`. **P1**

---

### apps/vuln-api/tests/README.md

- `apps/vuln-api/tests/README.md:71-74` — test directory structure tree shows `tests/pytest.ini`, `tests/run_tests.sh`, `tests/justfile`, and `tests/vulnerability/` — none exist: pytest config lives in `apps/vuln-api/pyproject.toml`, `run_tests.sh` is at `apps/vuln-api/scripts/run_tests.sh`, there is no `tests/justfile`, and there is no `tests/vulnerability/` directory. Propose: remove missing entries from the tree and add correct paths. **P1**

- `apps/vuln-api/tests/README.md:295-308` — test template uses `create_app('testing')` (config-string factory) and `self.app.test_client()` — Flask API patterns that do not apply to Starlette. Current correct pattern is `from app import create_app; app = create_app(); client = TestClient(app)`. Propose: replace template with Starlette `TestClient` pattern. **P1**

- `apps/vuln-api/tests/README.md:253` — CI YAML step `run: pip install -r requirements.txt` — no `requirements.txt` exists; project uses `uv sync --extra dev --frozen`. Propose: update to `uv sync --extra dev --frozen`. **P1**

- `apps/vuln-api/tests/README.md:56-57` — tree lists `tests/unit/test_validators.py` and `tests/unit/test_responses.py` — neither file exists in `tests/unit/`. Propose: remove stale entries. **P2**

- `apps/vuln-api/tests/README.md:220-225` — `pytest.ini` snippet registers markers `slow`, `security`, `critical`; actual codebase markers (per AGENTS.md, developer-guide.md, conftest.py) are `vulnerability`, `integration`, `smoke`. Propose: update marker definitions to match real codebase. **P2**

- `apps/vuln-api/tests/README.md:212` — "Minimum overall: 90%" — AGENTS.md and developer-guide.md state "80% minimum". Propose: align to 80% or update the authoritative source. **P2**

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `docs/architecture.md` DEMO_MODE default corrected from `true` to `full`
- [ ] #2 `docs/developer-guide.md` DEMO_MODE default corrected from `strict` to `full`
- [ ] #3 `docs/dockerhub-overview.md` DEMO_MODE default corrected from `strict` to `full`
- [ ] #4 `README.md` DEMO_MODE default corrected from `strict` to `full`
- [ ] #5 `README.md` `make -C apps/vuln-api …` commands replaced with `just` equivalents
- [ ] #6 `AGENTS.md` `security.py` reference updated to `app/utils/security_config.py` and non-existent `@require_full_demo` / `is_full_mode()` symbols removed
- [ ] #7 `apps/vuln-api/AGENTS.md` `security.py` reference updated to `app/utils/security_config.py`
- [ ] #8 `docs/endpoints-catalog.md` `just docs-drift` reference replaced with correct recipe name
- [ ] #9 `docs/endpoints-catalog.md` endpoint count inconsistency (469 vs 243) reconciled
- [ ] #10 `apps/vuln-api/README.md` broken `docs/API-DOCUMENTATION.md` link fixed
- [ ] #11 `apps/vuln-api/tests/README.md` directory tree corrected (missing dirs/files removed, correct paths added)
- [ ] #12 `apps/vuln-api/tests/README.md` Flask test template replaced with Starlette `TestClient` pattern
- [ ] #13 `apps/vuln-api/tests/README.md` CI YAML step updated from `pip install -r requirements.txt` to `uv sync`
- [ ] #14 `apps/vuln-api/tests/README.md` stale test filenames removed from tree
- [ ] #15 `apps/vuln-api/tests/README.md` pytest markers aligned to actual codebase markers
- [ ] #16 `apps/vuln-api/tests/README.md` coverage minimum percentage reconciled across docs
- [ ] #17 All linked claims verified against current code
<!-- AC:END -->
