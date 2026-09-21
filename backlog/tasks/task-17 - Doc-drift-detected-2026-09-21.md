---
id: TASK-17
title: 'Doc drift detected 2026-09-21'
status: To Do
assignee: []
created_date: '2026-09-21 00:00'
updated_date: '2026-09-21 00:00'
labels:
  - docs
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Automated drift audit run on 2026-09-21 against the 12-file doc set. 26 verifiable claims are inconsistent with the current codebase. Findings grouped by file below. Each entry follows the shape: `path:line — \`exact quote\` — claim — proposed fix`. Severity: **P0** = user-facing factual error, **P1** = dev-doc error, **P2** = minor staleness.

---

### docs/architecture.md

- `docs/architecture.md:165` — `DEMO_MODE | true | full enables all vulns, strict blocks dangerous endpoints` — Default value shown as `true`; `app/config.py:32` reads `os.environ.get('DEMO_MODE', 'full')`, so the real default is `full`. (P1)
- `docs/architecture.md:88–116` — blueprint tree listing — `education/` directory exists on disk (`apps/vuln-api/app/blueprints/education/`), is imported and mounted in `app/asgi.py:185,231`, and has tests (`test_education_routes.py`), but is absent from the blueprint tree. (P1)

---

### docs/developer-guide.md

- `docs/developer-guide.md:46` — `DEMO_MODE | strict | full enables all vulnerabilities; strict blocks dangerous endpoints` — Default shown as `strict`; actual default from `app/config.py:32` is `full`. (P1)
- `docs/developer-guide.md:204–213` — project structure tree for `app/blueprints/` — does not include `education/` even though the directory exists and the router is mounted in `asgi.py`. (P1)

---

### docs/endpoints-catalog.md

- `docs/endpoints-catalog.md:15` — `verified against the live route table via \`just docs-drift\`` — recipe `docs-drift` does not exist in `apps/vuln-api/justfile`; the correct recipe is `docs-check` (line 105 of justfile). (P1)
- `docs/endpoints-catalog.md:4,15` — `469 unique endpoints` — internally inconsistent with `README.md`, `AGENTS.md`, and `apps/vuln-api/README.md` which all state `456+`. Same doc set, two different counts. (P2)

---

### README.md

- `README.md:47` — `DEMO_MODE | strict | full enables all vulnerabilities; strict blocks dangerous endpoints` — Default shown as `strict`; actual default from `app/config.py:32` is `full`. This is user-facing and security-relevant: a user who omits `DEMO_MODE` gets a fully vulnerable instance, not a safe one. (P0)
- `README.md:243–246` — `make -C apps/vuln-api test-unit`, `make -C apps/vuln-api test-quick`, `make -C apps/vuln-api test-vulnerability`, `make -C apps/vuln-api test-smoke` — `apps/vuln-api/Makefile` does not exist; all four commands would fail at runtime. Equivalent recipes exist in `apps/vuln-api/justfile`. (P1)

---

### AGENTS.md

- `AGENTS.md:95` — `DEMO_MODE env var: full (vulns active) vs strict (safe mode, default)` — Default is described as `strict`; actual default from `app/config.py:32` is `full`. (P1)
- `AGENTS.md:116–117` — `In production (Docker), nginx handles the proxy.` — No nginx is present in any of the three Dockerfiles. `Dockerfile.prod` and `Dockerfile.fargate` run `uvicorn app.asgi:app` directly; the Starlette factory itself serves the bundled SPA. (P1)

---

### docs/dockerhub-overview.md

- `docs/dockerhub-overview.md:21` — `DEMO_MODE | strict | full = all vulnerabilities enabled; strict = dangerous endpoints return 403` — Default shown as `strict`; actual default from `app/config.py:32` is `full`. User-facing DockerHub README; security-relevant. (P0)

---

### apps/vuln-api/README.md

- `apps/vuln-api/README.md:123` — `200+ Unit Tests with 94% code coverage` — task-16.8 verification recorded **492 passed, 1 skipped**; "200+" is significantly stale. Coverage % is a runtime stat not verified here but the test count claim is wrong. (P2)
- `apps/vuln-api/README.md:186–211` — feature reference table — does not include an `Education` row, though the blueprint exists (`apps/vuln-api/app/blueprints/education/`). (P2)

---

### apps/vuln-api/AGENTS.md

- `apps/vuln-api/AGENTS.md:8` — `static/: Demo assets served as Starlette StaticFiles mounts` — `app/asgi.py` only mounts `/assets` → `web_dist/assets/` (line 258); there is no `Mount("/static", StaticFiles(...))` or equivalent. The `static/` directory exists on disk but is not served via a StaticFiles mount. (P1)

---

### apps/vuln-api/API-DOCUMENTATION.md

No drift found. Route count (469) and router package count (28, including `education`) are consistent with `asgi.py`. Recipe name `docs-check` is correct.

---

### apps/vuln-api/tests/README.md

- `apps/vuln-api/tests/README.md:56` — `test_validators.py` — file listed in directory tree does not exist on disk; it was deleted in TASK-16.8 (Flask validator helpers removed). (P1)
- `apps/vuln-api/tests/README.md:57` — `test_responses.py` — same as above; deleted in TASK-16.8. (P1)
- `apps/vuln-api/tests/README.md:73` — `pytest.ini` listed in directory structure — `apps/vuln-api/tests/pytest.ini` and `apps/vuln-api/pytest.ini` do not exist. (P1)
- `apps/vuln-api/tests/README.md:7` — `Total Tests: 267` — task-16.8 verification recorded 492 passed; 267 is significantly stale. (P1)
- `apps/vuln-api/tests/README.md:213–215` — `Minimum overall: 90% / New code: 95% / Critical paths: 100%` — `apps/vuln-api/justfile:47` specifies `--cov-fail-under=80`; developer-guide.md and AGENTS.md both state "Coverage target: 80% minimum". The 90%/95%/100% thresholds are wrong. (P1)
- `apps/vuln-api/tests/README.md:303` — `self.app = create_app('testing')` — `create_app` signature in `app/asgi.py:161` is `def create_app(config: dict | None = None) -> Starlette`. Passing a string `'testing'` is incorrect; the pattern is pre-migration Flask syntax. (P1)

---

### Summary by severity

| Severity | Count | Files |
|----------|-------|-------|
| P0 user-facing | 2 | README.md, docs/dockerhub-overview.md |
| P1 dev-doc | 19 | architecture, developer-guide, endpoints-catalog, README, AGENTS, dockerhub-overview, vuln-api/AGENTS, tests/README |
| P2 minor | 5 | endpoints-catalog, README, vuln-api/README |

**Total findings: 26**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 `docs/architecture.md:165` — DEMO_MODE default corrected from `true` to `full`
- [ ] #2 `docs/architecture.md:88–116` — `education/` added to blueprint tree
- [ ] #3 `docs/developer-guide.md:46` — DEMO_MODE default corrected from `strict` to `full`
- [ ] #4 `docs/developer-guide.md:204–213` — `education/` added to project structure
- [ ] #5 `docs/endpoints-catalog.md:15` — `just docs-drift` corrected to `just docs-check`
- [ ] #6 `docs/endpoints-catalog.md:4,15` — 469 vs 456+ reconciled to a single count
- [ ] #7 `README.md:47` — DEMO_MODE default corrected from `strict` to `full` (P0)
- [ ] #8 `README.md:243–246` — `make -C apps/vuln-api test-*` commands replaced with `just -f apps/vuln-api/justfile test-*` equivalents
- [ ] #9 `AGENTS.md:95` — DEMO_MODE default corrected from `strict` to `full`
- [ ] #10 `AGENTS.md:116–117` — nginx proxy claim removed; replaced with accurate Starlette/uvicorn SPA serving description
- [ ] #11 `docs/dockerhub-overview.md:21` — DEMO_MODE default corrected from `strict` to `full` (P0)
- [ ] #12 `apps/vuln-api/README.md:123` — test count updated from "200+" to reflect actual count (492+)
- [ ] #13 `apps/vuln-api/README.md:186–211` — `Education` domain added to feature table
- [ ] #14 `apps/vuln-api/AGENTS.md:8` — `static/` StaticFiles claim corrected or removed
- [ ] #15 `apps/vuln-api/tests/README.md:56` — `test_validators.py` entry removed from directory listing
- [ ] #16 `apps/vuln-api/tests/README.md:57` — `test_responses.py` entry removed from directory listing
- [ ] #17 `apps/vuln-api/tests/README.md:73` — `pytest.ini` entry removed from directory listing
- [ ] #18 `apps/vuln-api/tests/README.md:7` — total test count updated from 267 to reflect actual count (492+)
- [ ] #19 `apps/vuln-api/tests/README.md:213–215` — coverage thresholds corrected from 90%/95%/100% to 80%
- [ ] #20 `apps/vuln-api/tests/README.md:303` — `create_app('testing')` pattern updated to `create_app({'TESTING': True})` or equivalent dict form
- [ ] #21 All linked claims verified against current code after fixes
<!-- AC:END -->
