# Subagent Recommendations by Workstream

- **Workstream A — Package foundations (TS lib + CLI, schemas)**
  - Primary: `typescript-pro`
  - Support: `security-auditor`
  - Gate: `code-reviewer`

- **Workstream B — Demo-dashboard integration (UI + WebSocket plumbing)**
  - Primary: `typescript-pro`
  - Support: `debugger`
  - Gate: `code-reviewer`

- **Workstream C — Load-testing integration (k6 helpers, CLI flags)**
  - Primary: `typescript-pro`
  - Support: `debugger`
  - Gate: `code-reviewer`

- **Workstream D — Demo-targets traffic generator (bash adapter, CLI env mapping)**
  - Primary: `debugger`
  - Gate: `code-reviewer`

- **Workstream E — Docs & gh-pages updates**
  - Primary: `deployment-engineer`
  - Gate: `code-reviewer`

- **Workstream F — Quality gates, testing, coverage**
  - Primary: `code-reviewer`
  - Support: `security-auditor`, `debugger`, `test-automator` (tests), `technical-writer` (docs)

Use `code-reviewer` as the default final gate across streams.
