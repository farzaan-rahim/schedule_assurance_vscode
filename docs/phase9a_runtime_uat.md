# Phase 9A runtime and UAT hardening

This increment changes configuration discovery, runtime diagnostics and UI presentation only. It does not change analytical formulas, persistence schemas or transaction semantics.

## Regression evidence (2026-11-26)

Initial non-database command: `python -m pytest -q -m "not external_xer and not postgres"`

- 671 passed, 41 deselected, 2 warnings in 66.69s.
- Initial PostgreSQL command: `python -m pytest -q -m postgres`: 39 passed, 673 deselected, 2 warnings in 45.87s.
- Final non-database command: 684 passed, 45 deselected, 2 warnings in 59.21s.
- Final PostgreSQL command: 43 passed, 686 deselected, 2 warnings in 42.72s.
- Focused runtime/UI command: `python -m pytest -q tests/test_runtime.py tests/test_ui.py`: 35 passed, 2 warnings in 16.76s.

PostgreSQL tests used actual PostgreSQL 18.4, an isolated cluster on loopback port 55437, and per-test schemas. They did not use SQLite. The warnings are the existing Starlette/httpx TestClient and AnyIO BlockingPortal deprecations. External XER tests were deselected. No Ruff was used.

A start-of-phase SHA-256 inventory of existing app, contract and migration files confirmed only app/main.py, app/persistence/settings.py, app/ui/pages.py and app/ui/styles.css changed. Existing analytical modules, old contracts and migrations remain unchanged. `git diff --check` passes.

## Configuration and readiness

At initial inspection the repository had no .env and the process had no SA_DATABASE_URL. The persistence warning therefore represented missing configuration, not a scheduling failure. Settings previously used a working-directory-relative .env; it now resolves the repository .env explicitly. Environment variables retain precedence and explicit test env-file overrides still work. The storage-root policy is unchanged; start from the repository root or set an absolute SA_STORAGE_ROOT.

.env.example contains placeholders only, with coherent Compose port 5433 settings and a native PostgreSQL port 5432 example. No actual .env or production credentials were written. README documents virtual-environment setup, PostgreSQL, configuration, Alembic, uvicorn, UI and API URLs.

Read-only startup diagnostics distinguish UNCONFIGURED, INVALID_CONFIGURATION, DATABASE_UNAVAILABLE, MIGRATIONS_REQUIRED, MIGRATIONS_UNKNOWN and READY. They expose separate configured/reachable/migrations-current flags, with None when unknown. UI availability is separate. Diagnostics never run migrations or return exception text, credentials or complete connection strings. Connection and statement timeouts bound normal diagnostic work. Bare postgresql URLs are normalized to the existing psycopg 3 driver for probing.

GET /api/runtime exposes the snapshot; ?refresh=true rechecks. GET /setup gives local instructions. The workspace provides Recheck setup, a database-status banner and a setup link. Persistence-dependent controls are disabled until ready. No-project, no-version, no-analysis, setup-required and application-error states are distinct. The UI shell and all navigation destinations remain usable without a database.

## Documentation routing

FastAPI docs remain /docs, /redoc and /openapi.json. NiceGUI's link component prepended its /ui prefix to the ostensibly root-relative /docs link, producing /ui/docs. Root links now use native anchors; a stale /ui/docs bookmark receives a 307 redirect to /docs. There is no duplicate Swagger application.

Actual HTTP checks against the temporary migrated UAT server verified /ui/, /docs, /redoc, /openapi.json, /setup and /api/runtime return 200, and /ui/docs redirects to /docs. The runtime endpoint reported configured=True, reachable=True, migrations_current=True, state=READY.

## Presentation and accessibility hardening

Changes bound the drawer navigation scroll region, keep menu items from shrinking, preserve an active-item indicator, wrap header selectors, contain long table content, make table headers sticky, bound dialog height, and add visible focus outlines. Navigation and main regions, the sidebar toggle, spinner, runtime updates, root links and tables have accessible labels/roles where applicable. State badges retain text; additional change classes receive consistent styling. No classification or analytical value changed.

Source-level contrast checks found subtitle text on the page background at approximately 4.39:1 and white text on the warning color at approximately 4.46:1. Both were darkened and all five authored text-palette tests now satisfy 4.5:1. This is a focused source check, not a claim of rendered accessibility conformance. The reference threshold is [WCAG 2.2 contrast minimum](https://www.w3.org/TR/2023/REC-WCAG22-20231005/#contrast-minimum).

NiceGUI server-event tests click every destination: Overview, Projects, Schedule Versions, Schedule Health, DCMA, Change Analysis, Milestones, CPM / Paths, Diagnostics and Reports. They verify no-database shell behavior, setup recovery, no-project/no-version states, sidebar collapse/expand state, actual in-flight operation indicators and disabled selectors. Synthetic long-ID/description/WBS rows verify 50/100/200 page sizes, negative float and NOT_EVALUATED preservation. Existing UI tests cover import, analysis, comparison, details, anchor, export and error orchestration. These are server-side tests, not real-browser visual results.

## Real-browser UAT status

The browser access host remains unavailable despite reconnection attempts. The native inventory shows an Edge window titled Schedule Assurance; native inspection was attempted but reported that window minimized and returned no usable control handle. Restoring/focusing the window is pending with the user. Actual viewport inspection at 1366x768, 1440x900 and 1920x1080 is not yet verified. Browser tab order, rendered focus, clipping, nested scrollbars, dialogs and real download interaction remain pending. Do not infer a visual pass from HTTP or NiceGUI event tests.

A temporary loopback UAT server at http://127.0.0.1:8765/ui/ uses a dedicated schema in the isolated test database, not a production configuration. It contains the existing baseline/current fixtures and a separate explicitly synthetic 250-row long-content pair. Original fixtures were not modified. No genuine P6 or NRG file was fabricated. The persistent operator configuration remains the user's responsibility; README provides the setup and repeatable planner workflow.

## Files

Created: app/runtime.py; tests/test_runtime.py; tests/test_runtime_postgres.py; tests/ui_runtime_scenario.py; docs/phase9a_runtime_uat.md.

Modified in this increment: .env.example; README.md; app/main.py; app/persistence/settings.py; app/ui/pages.py; app/ui/styles.css; tests/ui_scenario.py.

There are 13 new non-database test cases and four PostgreSQL readiness cases. No new analytical functionality or subsequent phase was started.
