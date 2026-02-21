# Catalog Artifacts Migration Plan

## Goal
Move catalog-api assets into a versioned package and make it the single source of presets, scenarios, and plugins for demo-dashboard, load-testing, and demo-targets, with ≥85% coverage (unit, integration, e2e, UI) and gh-pages documentation updates.

## Workstreams
- **A — Package Foundations (platform)**
  - Create `packages/catalog-artifacts` (TS ESM) with schemas, loaders, CLI.
  - Move canonical data (presets, scenarios, plugins, packs) into package.
  - Build/publish pipeline with lint, type-check, unit tests (≥90% for package).
  - Optional compatibility symlinks until consumers flip.

- **B — Demo-Dashboard Integration (dashboard)**
  - Adapter in `TrafficPresetManager`/`ScenarioEngine`; flag `USE_CATALOG_PKG`.
  - UI preset dropdown using package data; pass presetId via WS start command.
  - E2E/UI tests (Playwright/Vitest) for list/render/start/fallback; ≥85% coverage.

- **C — Load-Testing Integration (load-test)**
  - Loader/CLI flag `--preset <id>` to seed target/RPS/users/host defaults; packs/workflows remain authoritative.
  - Docs + scripts updated; unit + integration (k6 config dry-run) tests; ≥85% coverage.

- **D — Demo-Targets Traffic Generator (demo-targets)**
  - Use `catalog-artifacts --preset <id> --target demo-targets --format env` when available; flags still override.
  - Fallback to current behavior if CLI missing.
  - Bash/pytest harness to assert env mapping; included in CI.

- **E — Documentation & gh-pages (docs)**
  - Update architecture docs showing package as source of truth.
  - gh-pages updates for dashboard + demo-targets usage.
  - Changelogs + migration guide with rollback steps.

- **F — Quality & Release Management (QA/release)**
  - Gates: lint/type-check; unit ≥90% (package), overall ≥85% per app area; integration/e2e must pass.
  - Contract tests: bundle snapshot + schema validation in CI; adapters must conform.
  - Automated gate: `test-automator` generates/updates tests to meet coverage and runs suites; `technical-writer` produces/updates user-facing and internal docs before merge.
  - Release phases: shadow (flag off), staging on, default on, cleanup. Rollback: flip flags off.

## Parallelization
- A starts first; freeze schemas early so B/C/D can proceed in parallel.
- E follows API stability; F runs continuously and blocks default-on.

## Milestones
- **M1**: Package scaffold, schema freeze, unit tests (A1–A3).
- **M2**: Consumer adapters behind flags (B1, C1, D1) + docs draft (E1).
- **M3**: E2E/UI/integration green, coverage ≥85% (B3, C3, D3).
- **M4**: Flags on in staging; gh-pages updated (E2).
- **M5**: Default-on; remove legacy artifacts (F3).
