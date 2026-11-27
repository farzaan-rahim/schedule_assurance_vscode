# Phase 9: Schedule Assurance planner workspace

## Scope, framework and launch

The first planner UI is implemented with NiceGUI 3.19.0, mounted at `/ui/` on the existing FastAPI application. `/` redirects to `/ui/`; existing analytical and persistence API URLs remain intact. There is no React/Node build, separate frontend server, authentication, tenancy, result persistence, reporting redesign or new analytical methodology.

Configure PostgreSQL and source storage as documented in [Phase 7](phase7_persistence_contract.md), then run from the repository root:

```powershell
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/ui/`. Persistence settings use the existing SA_DATABASE_URL and SA_STORAGE_ROOT configuration. Keep existing local credentials; do not overwrite a configured .env with an example. The UI needs a configured database for project/version workflows; analytical/domain tests still run without PostgreSQL. Missing configuration produces an explicit application error rather than invented projects or zero scores.

NiceGUI integration and APIs were checked against the installed framework and official documentation: [configuration](https://nicegui.io/documentation/run), [tables](https://nicegui.io/documentation/table), [uploads](https://nicegui.io/documentation/upload), [storage](https://nicegui.io/documentation/storage).

## Architecture and protected boundaries

```text
NiceGUI page/session
  -> PlannerService orchestration
     -> existing persistence catalogue/import/analysis services
     -> canonical Schedule + existing graph/analysis/comparison services
     -> ForensicChangeReport -> presentation pages / existing Excel renderer
```

The UI contains no forward/backward, calendar, retained-logic, float, path, DCMA, CPLI, health or comparison formulas. UI projections associate identities, preserve existing values, format text/percentages, and filter/sort/page records. ES/EF variances come from the existing compare_activities service; selected-analysis late/float variances come from its existing per-metric comparison records. Preferred milestone dates use the existing milestone policy. WBS paths use the existing domain helper.

A new read-only NavigationRepository supplies bounded metadata queries. It uses ordinary SQLAlchemy/PostgreSQL COUNT, whitelisted ordering, OFFSET and LIMIT; it does not change Project/Version policies, schemas, migrations or import transactions. Literal wildcard searches are escaped. Existing persistence APIs/services remain unchanged.

A file-hash audit across 127 existing implementation/methodology files found only `app/main.py` changed (the UI mount). All validated analytical, reporting and persistence implementations/contracts remained unchanged. Requirements add `nicegui>=3.19,<4`.

## Navigation and session

The original navy/slate navigation, light panels and restrained blue accent provide these destinations:

1. Overview
2. Projects
3. Schedule Versions
4. Schedule Health
5. DCMA
6. Change Analysis
7. Milestones
8. CPM / Paths
9. Diagnostics
10. Reports

Project and active version context stay visible in the header. UUID selection is independent of visible Activity IDs. A volatile NiceGUI tab-session object preserves project/version selections, source/target versions, requested Analysis Anchor, mode, required finish and filters across navigation and refresh. This is server-memory tab state, not database-backed user preferences. Separate new sessions do not inherit a default project completion milestone. Process restart loses session state.

Service results are kept in an eight-entry per-client LRU cache. Work runs in worker threads; UI creation/updates stay on the event loop. Operations are serialized and show a spinner plus actual task state. Context selectors are disabled while work is active. There is no background job queue or fabricated percentage progress.

## Projects and schedule versions

Projects can be created with code/name/description and selected from a bounded directory. Use a code matching the P6 export; the existing importer enforces that policy. Version history supports all four existing types (BASELINE, UPDATE, CURRENT, SNAPSHOT), native UUID identity, Data Date/import time/original filename and imported activity, relationship, WBS, calendar and resource counts. Selecting a row activates it; existing analyses, comparison, reporting and import diagnostics are reachable from that context.

Metadata lists are ordered and paginated in PostgreSQL. Recent version choices are bounded at 200; older versions can be activated through paginated history and are retained among choices. Several baselines remain possible. Source/baseline selection is explicit; the UI does not manufacture a singular authoritative baseline. Overview distinguishes the latest imported version and its Data Date from selected analysis versions. Latest activity/relationship metadata is available immediately; milestone count, generic health score and DCMA score are populated by existing services after Analyze latest schedule runs.

Import lifecycle:

```text
Ready -> upload -> Validating -> Importing (parsing/mapping/persistence)
      -> Complete / Failed
```

The upload widget reports actual transfer progress. The current backend parses/maps/persists synchronously, so those internal stages are not presented as separate completed asynchronous events. The upload is bounded by both the widget limit and the existing configured backend limit. Duplicate hashes and project mismatch remain controlled errors. ImportRejected diagnostics remain visible after failure, including background loading of the diagnostic table. Success refreshes version history only after the import service returns its committed result.

## Schedule Health and DCMA

Generic health shows its own score/rating, total/critical/warning findings, and every existing rule. A rule displays issue count, severity and a presentation status derived from whether the service reported findings. Eligible population is explicitly unavailable when the domain rule does not provide one. Selecting a rule opens its returned findings. Service detail limits are displayed rather than hidden.

DCMA is a separate assessment. Every existing metric has its own expansion, textual status badge, eligible/excluded populations, findings, percentage, threshold/interpretation, notes, limitations and exclusion reasons. PASS, WARNING, FAIL, NOT_EVALUATED and NOT_APPLICABLE remain distinct. Missing percentages remain unavailable. Findings include activity identity/status/WBS, structural predecessor/successor counts where available, relationship endpoint codes/names, type/lag and configured threshold context.

CPT evidence includes internal/visible test activity identity, selection reason, injected hours, source/simulated anchors/completion, elapsed and working movement, response ratio, calendar/anchor policy, configuration and diagnostics. It explicitly says a FAIL is measured response, not proof of defective scheduling logic.

CPLI evidence includes path length, raw activity/lag contributions, deadline and provenance, calculated finish, native/participating float and its source, calendar, numerator, denominator, raw value, separately formatted display value, formula/version and configuration. Unsupported states retain exact reasons. Per-metric source-calculation diagnostics are server-paged rather than dumping the source CPM network into the browser.

These screens use existing default stored-version DCMA configuration. They show methodology but do not add a threshold editor or automatically treat a selected-anchor subset as a valid complete-network CPT/CPLI input.

## Change Analysis and investigation

Comparison uses the existing ForensicChangeReport domain/serialization contract. It does not implement a second comparison engine. All 29 report sections are selectable, including the summary, activities, relationships, descriptions/types/durations, float, calendars, imported planned/early/late dates, status, criticality, constraints, resources, costs, paths and diagnostics. WBS Movement is a filtered view of the existing activity change categories, not a new change calculation.

Source and target selections are independent of the active version. Global Activity ID/name search applies across change sections. WBS uses substring matching; status, type, classification, severity and category filters are exact and case-insensitive. This prevents CHANGED from also matching UNCHANGED. Column sorting and pagination run on the server. Percentage formatting preserves the original numeric value in the report. Empty supported sections retain No changes identified; unsupported sections retain Not evaluated and their existing reason.

Selecting an activity lazily opens Imported P6 and Application Calculated panels, with identity, WBS, calendar, imported dates/durations/float/status/constraints, directional availability, predecessor/successor relationships, health/DCMA findings, resources and milestone status. The application panel excludes imported-prefixed fields; imported values are never substituted for missing calculated values. Comparison context retains source/current WBS/calendar and selected change values. Removed activities are investigated in the source version; current activities use the actual report target, even when it differs from the header's active version.

Internal IDs resolve activity identity. Code-only health evidence is labelled potentially ambiguous when codes repeat; code-based detail lookup requires exactly one match and never chooses an arbitrary duplicate. Existing finding detail limits remain explicit.

## Milestones and CPM / Paths

Milestones use the existing inventory/comparison/driver services. The table shows ID/name/type/status/WBS, preferred imported planned date, baseline date, existing elapsed movement, imported float/critical proxy and overdue state. Filters expose delayed, improved, negative float, critical, overdue and completed records. Health findings and candidate drivers remain separate existing outputs.

CPM requires an explicit Analysis Anchor selection by candidate row, internal ID, or visible Activity ID/code. Candidate rows show identity, WBS, imported dates, evidence class, suitability and diagnostics. No Ontario Line milestone or other candidate is automatically selected. The page prominently states:

`Analysis Anchor does not establish contractual completion authority.`

CALIBRATION uses the existing explicitly labelled imported-LF timestamp rule. INDEPENDENT requires the existing caller-required-finish semantics. Invalid/missing/ambiguous identity, unsuitable activity/calendar or missing finish returns an application error; there is no fallback candidate.

Selected analysis shows anchor identity, mode/timestamp/source, independent authority status, population summaries, diagnostics and all upstream dispositions. Reliable ES/EF stay distinct from blocked late/float outputs. Blocked/excluded rows retain their available imported values and exact availability reasons. The table shows imported/calculated ES/EF/LS/LF/TF/FF and existing service variances. Directional activity/relationship tables retain excluded and blocked boundaries.

Application Calculated Controlling Paths are ordered tables with sequence, identity/name/WBS, effective duration, relationship type, signed lag, ES/EF/LS/LF/TF. Rank, raw duration/lag contributions, floats, end reason and truncation come from the existing path model. They are not labelled P6 Longest Path. Selected-anchor summary NOT_EVALUATED fields do not replace the separately evaluated complete-network DCMA assessment.

## Diagnostics and Excel export

Diagnostics consolidate import findings with the existing directional forward or selected-anchor diagnostics and availability reasons. Missing/unusable calendars, malformed values, Expected Finish, excluded LOE and progress-support limitations remain explicit. Severity/category filters and server paging keep large diagnostic populations usable. This is a presentation join, not a new validation policy.

Reports accepts a source/target pair and optional explicitly selected Analysis Anchor. Metadata preview shows actual report identity, source/current versions, dates, authority/anchor fields and section availability/counts/reasons. Export invokes the existing ExcelReportRenderer through the reporting service and downloads `Schedule Assurance Forensic Change Report.xlsx`. No Excel layout, calculation, rendering logic or report schema was redesigned.

## Performance and UI states

- Browser table pages are 50, 100 or 200 rows; no show-all option is exposed.
- Metadata filtering/count/order/page queries are bounded in PostgreSQL. Only detached DTOs reach UI code.
- Report/domain filtering retains references to matching source rows and serializes only the selected page, avoiding a second complete flattened dataset.
- Existing analyses still operate on canonical schedules on the server. No complete Schedule, comparison population or source/simulated CPM network is shipped to the browser for calculation.
- Full schedule reconstruction/analysis is still in-process and may be required on first investigation. It is cached, not replaced with browser arithmetic.
- Session caches are bounded by entry count, not a production memory quota. No shared distributed cache, job cancellation or streaming analytical cursor is added.
- Loading, no data, unavailable, blocked/excluded and application error states have text. Null does not become zero. Classification/status colors supplement labels.
- Labels, keyboard-focus styling, named controls, responsive drawer and readable palette are implemented. Actual rendered accessibility/contrast and monitor-size QA remain outstanding.

## Tests and observed results

Initial:

```text
pytest -q -m "not external_xer and not postgres"
649 passed, 39 deselected, 1 warning in 58.99s

pytest -q -m postgres
37 passed, 651 deselected, 1 warning in 36.69s
```

Final:

```text
pytest -q -m "not external_xer and not postgres"
671 passed, 41 deselected, 2 warnings in 43.34s

pytest -q -m postgres
39 passed, 673 deselected, 2 warnings in 33.85s
```

The warnings are the existing FastAPI/Starlette TestClient deprecation and an upstream AnyIO BlockingPortal-alias deprecation exposed by NiceGUI's updated dependency requirements. They are reported, not suppressed. No Ruff was used. External NRG00800 tests remain deselected; no source fixture was fabricated or changed.

22 new non-database UI checks cover state/navigation, selection, exact categorical filtering, 25,000-row server paging/filter/sort behavior, missing/zero values, all report sections/unavailable sections, code ambiguity, internal/source/target identity, directional and early-comparison projections, milestone preferred dates, CPT/CPLI evidence, import success/failure, errors, download and mounting with existing APIs. The isolated NiceGUI User scenario exercises server-rendered controls/events, actual existing importer/analytical services with an in-memory catalogue double, tab refresh restoration and the existing workbook download. It fails on unexpected tracebacks. It is not a real browser or pixel-level visual test.

Two new actual PostgreSQL tests validate literal-wildcard project search, bounded version ordering/sorting/page queries, persisted imports, duplicate handling, canonical reconstruction, overview, anchors/directional rows, investigation, diagnostics and report/Excel orchestration. All 37 prior PostgreSQL tests also pass.

The existing controlled report acceptance continues passing: A1500 removed, A1700 added, A1200 renamed/delayed/duration increase/float deterioration, A1300 WBS movement and relationship type/lag changes. An additional UI report-page check verifies removed/added identities and delayed values survive projection.

Real-browser visual verification was attempted, but the browser access host was unavailable and the native Edge tool stopped because it could not confidently determine the current URL. That restriction was not bypassed. No screenshot/real-browser responsive or visual acceptance claim is made. The real ASGI UI mount and API smoke checks pass, and a loopback UI test server started successfully with controlled PostgreSQL fixtures.

The native PostgreSQL 18.4 test cluster was task-owned and isolated on port 55437. Per-test schemas were removed. A separate generated UI QA schema and its source files were removed, and the temporary UI server/cluster were stopped after validation. Existing system PostgreSQL services/data were untouched.

## File manifest

Created:

- app/ui/__init__.py
- app/ui/state.py
- app/ui/presentation.py
- app/ui/service.py
- app/ui/pages.py
- app/ui/setup.py
- app/ui/styles.css
- app/persistence/repositories/navigation.py
- tests/ui_helpers.py
- tests/ui_scenario.py
- tests/test_ui.py
- tests/test_ui_postgres.py
- docs/phase9_ui_contract.md

Modified:

- app/main.py: separate UI mount and home redirect
- requirements.txt: NiceGUI dependency

Pre-existing repository changes from earlier phases were preserved. original_files and legacy_reference were untouched. No new analytical result tables or persistence architecture were introduced.

## Remaining gaps and recommended productionization phase

Before production acceptance, perform real-browser UAT at desktop/responsive sizes, keyboard/screen-reader checks, actual Quasar table/socket interactions and upload/download checks. These are specifically outstanding because the computer-use bridge could not perform its URL policy check, not because server event tests establish visual correctness.

Additional gaps: no deep-link/browser-history navigation for individual workspace views; no complete finding cursor beyond existing domain detail limits; default DCMA configuration is viewable rather than editable; no graph visualization; no 23,263-activity end-to-end browser latency benchmark; no job queue/cancellation, deployment observability or production memory quotas. Cache and UI selections are volatile. Unsupported analytical populations remain blocked/NOT_EVALUATED according to the unchanged contracts.

Recommended next phase: production-readiness hardening and planner UAT, including dependency reconciliation, real-browser coverage, workload/performance limits, operational diagnostics and deployment configuration. Authentication/Entra ID, organizations/tenancy and access policies require a separately scoped later phase. None is started here. Monte Carlo, AI, resource leveling and earned value remain out of scope.
