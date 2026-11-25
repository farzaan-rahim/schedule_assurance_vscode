# Phase 6E: forensic change reporting foundation

## Scope and protected boundaries

This increment is the user's reporting Phase 6E; the earlier Phase 6E completion-anchor
investigation remains separately documented and unchanged. Initial local regression:
`pytest -q -m "not external_xer"`: **463 passed, 2 deselected, 1 existing warning**.

No validated CPM, calendar, comparison, milestone, health, DCMA, progress or importer
calculation was modified. No genuine XER or controlled sample fixture was modified.
Completion authority stays NOT_ESTABLISHED, selected analysis anchor stays None, and
real-project late/float availability is not changed. DCMA Critical Path Test and
CPLI remain NOT_EVALUATED. This increment does not run CPM, select an anchor, schedule
resources, persist reports or start UI/simulation work.

## Domain architecture

Import -> existing ScheduleComparisonEngine -> ComparisonResult ->
ForensicReportBuilder -> ForensicChangeReport -> JSON or Excel.

The builder consumes existing matching, activity and relationship results. It uses
existing elapsed/numeric variance helpers for projection of imported fields not
represented individually by the comparison result, and computes only presentation
percentages/counts. It never performs scheduling, calendar arithmetic, float, path,
health or DCMA calculations. Constraints are reported as imported fields, not applied.
Imported criticality uses the existing schedule TF-threshold query, with its basis
and threshold exposed; this is not a claim about P6's configured critical flag or
Longest Path. Optional health/DCMA/milestone score blocks were not implemented and
no combined score is invented.

The report metadata contains ID/title, UTC generation timestamp, optional author,
project identity, source/current schedule references and Data Dates, configuration,
completion authority and selected anchor. Schedules and ComparisonResult are not
embedded in serialized output. Fixed ID/time inputs produce deterministic output.

ActivityRowContext retains sequence, internal task ID, visible Activity ID, description,
type/status, remaining hours, WBS code/name/path, both internal identities, both WBS
contexts and both calendar assignments. Context objects are shared among category
views rather than copying full schedules. Ambiguous matches remain NOT_COMPARABLE
with no asserted paired variance. Activities includes matched, added, removed and
ambiguous records; changes are identified in explicit category labels, including WBS_MOVED.

ChangeValue retains baseline/current values, signed absolute variance, percentage,
unit, classification, availability, provenance and diagnostics. "Absolute variance"
means the signed difference in original units, not absolute magnitude. Percentage
is `(current - baseline) / baseline` only for a strictly positive numeric denominator.
Zero/negative/missing denominators retain None plus a diagnostic. Signed, negative
and fractional variances remain exact; number formats affect display only.
Missing values are never replaced by zero. Date differences use elapsed hours and
hours/24 elapsed calendar days, never working days. Mixed aware/naive reporting
variances are blocked explicitly. Aware Excel timestamps are shown in UTC because
Excel cannot retain tzinfo; exact offsets remain in JSON. Naive P6 dates retain their
source clock time. Application values are never populated from imported values.

Availability: AVAILABLE, NOT_EVALUATED, BLOCKED, EXCLUDED, NOT_APPLICABLE.
Provenance: IMPORTED_P6, APPLICATION_CALCULATED, BASELINE_COMPARISON,
CURRENT_SCHEDULE, DCMA_ANALYSIS, HEALTH_ANALYSIS, MILESTONE_ANALYSIS.
The supported vocabulary includes ADDED, REMOVED, CHANGED, UNCHANGED, DELAYED,
IMPROVED, DETERIORATED, RECOVERED, BECAME_NEGATIVE, WBS_MOVED, TYPE_CHANGED,
LAG_CHANGED, STATUS_CHANGED and NOT_COMPARABLE. Rendering does not interpret changes.

## Sections and population policy

There are 29 sections in a fixed public order. Activities is the complete matching
population. Field-specific views contain changed or missing-side records, preserving
source/current context; unchanged records remain in Activities. Added/removed fields
retain values but have no paired percentage/variance. A section's count is its own
record count, not necessarily the number of matched field changes. Summary counts
reuse existing matched comparison counters. Date-change-record totals exclude
non-comparable rows; constraint counts are changed slots, not unique activities.
A relationship changing both type and lag retains two existing domain variance
records rather than silently discarding one change.

Supported empty sections say "No changes identified". Unavailable sections say
"Not evaluated" with reasons. Missing imported early/late populations are identified
separately from supported no-change evaluations. Empty/unavailable sheets have
schemas, metadata and explanatory text, never an ambiguous blank tab.

Resources and all four cost sections are NOT_EVALUATED because a cross-version
resource/assignment/cost comparison and validated currency basis do not exist.
No assignment aggregation is invented. Calendars and Calendar Exceptions are
NOT_EVALUATED because a definition/exception comparison does not exist. Calendar
Assignment reuses the existing name-based comparison policy: different internal
IDs alone do not establish a definition change. App Controlling Paths is NOT_EVALUATED
because no authoritative selected analysis anchor is supplied. A generic Primary
Critical Path UDF is not promoted to a calculated path.

Total Float contains separate imported baseline/current TF and FF, signed variances,
and optional application TF/FF with independent availability and diagnostic columns.
Free-float-only changes are retained even if TF does not change. Dates similarly
separate imported changes and supplied calculated early/late values. Planned-date
sheets label any supplied application endpoint explicitly as Early Start/Finish.
Optional CPM results must belong to the exact current schedule. Only availability-
certified result values are displayed: blocked/excluded fields stay None even if
an incidental numeric/date payload exists. No CPM result is generated by reporting.
The current real-project LS/LF/TF/FF gates remain in force.

The summary includes metadata, source/current versions and Data Dates, match counts,
activity/relationship/duration/date/float/WBS/status/calendar changes, constraint
counts, and up to ten finish delays, float deteriorations and duration increases.
Top lists use existing comparison variances with stable Activity ID tie breaks.
Unavailable metrics are explicit and no health/DCMA/milestone scores are merged.

## Excel output

`outputs/forensic-change/Schedule Assurance Forensic Change Report.xlsx` is built
from the unchanged `sample_baseline.xer` and `sample_current.xer`. Python's openpyxl
is declared as an application runtime dependency; rendering is a reusable Python
service, not a dependency on a Codex-local artifact runtime. Spreadsheet Artifact
Tool is used separately for visual QA of the generated workbook, not its production
calculation or export path.

The workbook uses original navy/teal styling. It has a title, source/current file
and Data Date bands, section count/availability, report generation/authority metadata,
row-6 headers, filters and frozen header rows. Activity sheets freeze identity
columns through Activity ID (D7); other sheets freeze A7. Descriptions wrap; column
widths and readable row heights are explicit. Dates are real Excel date cells
(`yyyy-mm-dd hh:mm`), hours `0.00`, percentages `0.00%`, counts `0`. No currency
symbol is invented. Text classifications remain visible alongside green additions/
improvements, red removals/deteriorations, amber changes/delays and gray unavailable
states. No formulas, external links, images, branding or source hidden formulas
are inserted. Formula-like imported strings are forced to literal Excel text.

Streaming write-only sheets avoid retaining a full cell graph and avoid Excel
calculations. Export consumes completed report rows; the preview serializer slices
before recursive serialization. A 25,000-row synthetic export is verified through
the final record. The report itself retains its row collections; this is not an
unbounded streaming import/analysis API. Uploads are capped at 100 MiB per file and
sections at 200,000 rows by default; explicit configurable guards raise errors,
never silently truncate. Excel cell text exceeding 32,767 characters is rejected
instead of silently clipped. No persistence is introduced; import temporary files
are cleaned up and the export response is generated in memory.

## JSON/UI contract and API

Schema version 1.0 exposes report metadata and ordered sections with key/title/sheet,
full count, availability/reasons, typed columns, rows, typed filter definitions,
sort metadata, pagination and truncation. Each row preserves context, display cells,
structured ChangeValues, classification, availability, provenance and diagnostics.
Dates are ISO strings, enums are strings and None is JSON null. Counts remain full
section counts when preview pages are sliced. `has_more` means pagination; it does
not falsely indicate truncation. Filters/sort metadata describe future UI capabilities;
this increment does not implement interactive filtering or a frontend.

- POST /api/reports/forensic-change/preview: multipart baseline/current .xer uploads,
  optional generated_by, query offset >= 0 and limit 1..5000 (default 500), JSON report.
- POST /api/reports/forensic-change/excel: the same source uploads/optional author,
  XLSX attachment with the requested filename and MIME type.

Routes validate uploads and orchestrate the reporting service on a worker thread.
No schedule calculations occur in handlers. Invalid extensions return 415; missing/
invalid inputs or cross-project pairs return 422; resource limits return 413.
No server-side filesystem path or persisted report identifier is exposed as a lookup.
The two routes were added only after reporting-domain and Excel tests passed.

## Controlled fixture validation

- Matching: 6 matched, 1 source-only, 1 current-only, 0 ambiguous; Activities has 8 rows.
- A1500: REMOVED; A1700: ADDED.
- A1200 description: A1200 -> Revised build.
- A1300: ROOT > AREA1 -> ROOT > AREA2, WBS_MOVED category retained.
- A1200 planned finish: 2026-03-02 17:00 -> 2026-03-09 17:00,
  +168 elapsed hours / +7 elapsed calendar days, DELAYED.
- A1200 original/remaining duration: 40 -> 80 hours, +40 hours / +100%.
- A1200 imported TF: 40 -> -16 hours, -56 hours / -140%, BECAME_NEGATIVE.
- M1400 imported TF: 10 -> -12 hours, -22 hours, BECAME_NEGATIVE.
- A1100 -> A1200: FS -> SS and lag 0 -> 40 hours, both change records preserved.
- A1200 -> A1300: FS lag 0 -> 16 hours.
- One added and one removed relationship; relationship change-record count is 5.
- Imported early/late dates are absent in these fixtures; those sections explicitly
  identify the missing source population. No planned-date substitute or CPM is invented.
- Application TF/FF and controlling paths remain NOT_EVALUATED, not imported values.

## Verification and files

Initial suite: 463 passed, 2 deselected, 1 existing warning.
Reporting/Excel/API: 43 new tests all passed in the complete suite (37 domain/Excel,
6 API). The earlier focused run passed 41 before two additional unit/FF regressions
were added and corrected. Focused failures were confined to new reporting projections;
no pre-existing analytical defect or analytical formula correction was required.

Final `pytest -q -m "not external_xer"`:
**506 passed, 2 deselected, 1 warning in 14.30s**.
The warning is the existing FastAPI/TestClient deprecation. Existing external fixture
policy remains unchanged. `git diff --check` and protected-contract/source-fixture
integrity checks are performed before delivery.

Workbook tests cover all sheet names/order, actual headers, counts, empty/unavailable
messages, date/percentage formats, pane/filter metadata, missing/negative/fractional
values, provenance, ambiguous matches, source immutability, deterministic projection,
granular calculation availability, explicit UI filters/pagination, literal formula-
like strings, 25,000 rows, resource guards, Excel download and API error handling.
All 29 worksheet previews plus representative numeric/date detail ranges were
rendered and reviewed. Spreadsheet-tool teardown returned nonzero after emitting
all previews without a rendering diagnostic; saved PNGs were inspected and production
XLSX creation/reopen checks passed. Native desktop Excel was not required or tested.

Created:
- app/reporting/__init__.py
- app/reporting/models.py
- app/reporting/builder.py
- app/reporting/sections.py
- app/reporting/change_values.py
- app/reporting/serialization.py
- app/reporting/excel_renderer.py
- app/reporting/formatting.py
- app/reporting/limits.py
- app/reporting/service.py
- app/api/reports.py
- tests/test_reporting.py
- tests/test_reporting_api.py
- docs/phase6e_reporting_foundation.md
- docs/phase6e_reference_workbook_structure.md
- outputs/forensic-change/Schedule Assurance Forensic Change Report.xlsx

Modified in this increment: app/main.py (router import/registration only),
requirements.txt (openpyxl dependency). Earlier dirty repository changes and all
protected Phase 6 contracts are preserved. The reference workbook was supplied by
the user and is not an implementation-created file.

## Remaining gaps and next phase

Cross-version ResourceAssignmentComparison and calendar-definition/exception comparison
are the next reporting-domain services needed to activate the unavailable categories.
Health/DCMA/milestone adapters could then expose existing results as separate optional
blocks without recomputing or merging scores. A real baseline/current XER pair is
needed for production-scale report acceptance beyond the synthetic row-volume test.
UI filtering, authentication/deployment concerns and persistence are outside this
foundation. The recommended next increment is a separately scoped resource-assignment
comparison with cost/currency semantics and synthetic tests; no next phase is started.
Selected-anchor CPM, Expected Finish, LOE and completion authority policies are unchanged.

## Exported section inventory for the controlled fixtures

| Order | Section | Worksheet | Records | Availability |
| --- | --- | --- | --- | --- |
| 1 | Report Summary | Report Summary | 45 | AVAILABLE |
| 2 | Projects | Projects | 2 | AVAILABLE |
| 3 | Activities | Activities | 8 | AVAILABLE |
| 4 | Relationships | Relationships | 5 | AVAILABLE |
| 5 | Resources | Resources | 0 | NOT_EVALUATED |
| 6 | Calendars | Calendars | 0 | NOT_EVALUATED |
| 7 | Calendar Exceptions | Calendar Exceptions | 0 | NOT_EVALUATED |
| 8 | Description | Description | 3 | AVAILABLE |
| 9 | Activity Type | Activity Type | 2 | AVAILABLE |
| 10 | Original Duration | Original Duration | 3 | AVAILABLE |
| 11 | Remaining Duration | Remaining Duration | 3 | AVAILABLE |
| 12 | Total Float | Total Float | 4 | AVAILABLE |
| 13 | Calendar Assignment | Calendar Assignment | 2 | AVAILABLE |
| 14 | Planned Start | Planned Start | 2 | AVAILABLE |
| 15 | Planned Finish | Planned Finish | 3 | AVAILABLE |
| 16 | Early Start | Early Start | 2 | NOT_EVALUATED |
| 17 | Early Finish | Early Finish | 2 | NOT_EVALUATED |
| 18 | Late Start | Late Start | 2 | NOT_EVALUATED |
| 19 | Late Finish | Late Finish | 2 | NOT_EVALUATED |
| 20 | Activity Status | Activity Status | 2 | AVAILABLE |
| 21 | Criticality | Criticality | 4 | AVAILABLE |
| 22 | Application Calculated Controlling Paths | App Controlling Paths | 0 | NOT_EVALUATED |
| 23 | Primary Constraint | Primary Constraint | 0 | AVAILABLE |
| 24 | Secondary Constraint | Secondary Constraint | 0 | AVAILABLE |
| 25 | Budget Cost | Budget Cost | 0 | NOT_EVALUATED |
| 26 | Actual Cost | Actual Cost | 0 | NOT_EVALUATED |
| 27 | Remaining Cost | Remaining Cost | 0 | NOT_EVALUATED |
| 28 | Total Cost | Total Cost | 0 | NOT_EVALUATED |
| 29 | Diagnostics | Diagnostics | 8 | AVAILABLE |
