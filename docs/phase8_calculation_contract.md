# Phase 8 application simulation and assurance methodology (V1)

This increment extends the earlier NOT_EVALUATED gate only for supported, complete calculations. Earlier calendar, progress, relationship, constraint, float, path and persistence contracts remain unchanged. These are application-defined DCMA-style methods and thresholds, not claimed official DCMA limits or P6 Longest Path equivalence.

## Immutable simulation

Deep-copy the canonical Schedule, calculate source CPM, validate an explicit incomplete ordinary positive-duration activity, and overlay only the private copied activity duration field selected by the existing effective-duration policy. Recalculate the complete network with CPMService. Never calculate completion by adding a delay to its timestamp. Source/imported fields and the caller's configuration remain untouched. Copies share no mutable calendar or activity objects with the caller. Result audit includes both CPM results, configurations, anchors, effective durations, path/float changes, and movements. General duration simulation allows finite positive/negative deltas while requiring nonnegative resulting duration; CPT only permits a positive injected delay.

Default anchor policy FIXED_ACTIVITY locks the source resolved internal activity ID for the simulation. Missing/ambiguous/date-only anchors stop evaluation. Explicit opt-in RESELECT_TERMINAL permits the existing unambiguous-terminal resolver to run again; no arbitrary latest terminal selection is introduced. Authority is not established by a simulation anchor.

## Critical Path Test

Select an incomplete ordinary positive-duration activity on a complete calculated critical controlling path, with known TF at/below CPM's configured critical threshold. Deterministically prefer greatest controlling hop distance upstream of the anchor, then lexical Activity ID/code and internal ID. An explicit test internal ID must meet the same criteria. Bounded/incomplete critical traces are not sufficient evidence for automatic selection.

Default injected delay is **8 working hours**, an application methodology default, not an eight-hour-day conversion or asserted standard. Use the activity's effective calendar through the unchanged CPM duration arithmetic. The source and simulation must both return CALCULATED under STRICT complete-network policy. Partial or unsupported schedules remain NOT_EVALUATED, with source diagnostics retained.

Response ratio = completion movement working hours / injected working hours. Use the shared activity/anchor calendar only when the selected controlling chain has one calendar; mixed-calendar chains require an explicitly configured completion calendar. Always retain elapsed movement separately. PASS when abs(ratio-required_response_ratio) <= response_tolerance (defaults 1.0 and 1e-9); WARNING when within warning_response_tolerance (default 0.05); otherwise FAIL. Configuration errors, unavailable calendars/dates/anchors/candidates or simulation failures are NOT_EVALUATED, never FAIL.

## CPLI formula and input provenance

Formula version APPLICATION-CPLI-V1:

`CPLI = (CPL_hours + selected_anchor_deadline_float_hours) / CPL_hours`

Numerator and denominator are preserved separately. Required completion is resolved from (1) explicit CPLI required finish, (2) CPMConfig.required_project_finish, (3) an unambiguous supported FINISH_ON_OR_BEFORE constraint on the selected terminal completion activity. Conflicting configured dates or multiple different milestone constraint dates are not silently reconciled. Lower-bound finish constraints are not deadlines. No imported Early/Late Finish, planned finish or calculated completion is treated as a required date. The current canonical Project has no separately semantically established project deadline field; no guessed project-field fallback is implemented.

Resolve the source anchor, then recalculate with the selected explicit required finish using existing CPM mathematics. Require a terminal anchor, reliable dates/float and no unresolved blockers. Reuse the validated selected-anchor controlling-path tracer, which follows FORWARD controlling records without changing published criticality. Positive path float does not prevent a connected controlling chain. Preserve all tied paths; reject truncated/incomplete traces. Rank meaningful path lengths by descending length then deterministic existing path rank. Do not sum parallel paths.

CPL default: existing SINGLE_CALENDAR_FS_WORKING_SPAN path.duration_hours, already proven equal at datetime resolution to activity-duration plus signed-lag contributions. Preserve the two raw contributions separately. Mixed-calendar, non-FS overlap or unexplained span is NOT_EVALUATED unless the caller explicitly chooses COMMON_CALENDAR_WORKING_SPAN and supplies a calendar ID. That method measures one connected path's start-to-finish working span on the named common calendar; it does not claim component-hour sums are commensurate. Every tied path must have an interpretable length. Zero/nonpositive CPL is NOT_EVALUATED.

Float default: the selected completion anchor's calculated Total Float (ACTIVITY_CALENDAR_START), only when its start/finish float methods agree and its calculated LF is working-time-equivalent to the required finish. This excludes an earlier independent constraint deadline or unrelated successor bound from silently replacing the requested required date. With an explicit common calendar, use the signed required-minus-calculated-finish working margin on that common calendar, labelled COMMON_CALENDAR_REQUIRED_FINISH_MARGIN, while retaining native anchor TF separately. Require that the effective anchor deadline corresponds to the required finish. Never substitute imported P6 float; never clamp negative float.

Required finish is a deadline, not a mandatory forced Early Finish. Constraint releases may terminate a controlling trace; CPL begins at that controlling release, and constraint causes stay in the path record. This is remaining-work CPL, not an elapsed Data-Date-to-finish duration or universal official CPL definition.

Default CPLI application thresholds: PASS >= 1.0; WARNING >= 0.95 and < 1.0; FAIL < 0.95. Invalid configuration or missing required inputs remains NOT_EVALUATED. These thresholds are visible and configurable.

## DCMA boundary

Dedicated CPM services own simulation and CPLI. DCMA adapts their audit results and classifications; it contains no scheduling arithmetic. No analysis run, result or selection is persisted. Existing stored-version DCMA operations reload canonical Schedule and use the same services. A caller can supply Phase 8 and CPM configuration to the existing domain DCMA service. No specialized simulation endpoint is introduced.


## Usage and audit results

```python
from datetime import datetime
from app.cpm.config import CPMConfig
from app.cpm.simulation import simulate_duration_change, CriticalPathTestService, CriticalPathTestConfig
from app.cpm.cpli import CPLIService, CPLIConfig
from app.dcma.config import DCMAConfig
from app.dcma.service import DCMAAssessmentService
from app.graph.schedule_graph import ScheduleGraph

cp = CPMConfig(completion_activity_code="CALLER_SELECTED_FINISH")
experiment = simulate_duration_change(schedule, "internal_task_id", 8.0, cp)
test_config = CriticalPathTestConfig(delay_hours=8.0)
cpt = CriticalPathTestService().evaluate(schedule, cp, test_config)
index_config = CPLIConfig(required_finish=datetime(2026, 12, 31, 17))
cpli = CPLIService().calculate(schedule, cp, index_config)
assessment = DCMAAssessmentService().analyze(
    schedule, ScheduleGraph(schedule),
    DCMAConfig(cpm_config=cp, critical_path_test_config=test_config, cpli_config=index_config),
)
```

This selection is an analysis boundary, not a determination of contractual completion authority. An explicit deadline is an input to this analysis; its provenance is retained rather than inferred from imported LF or calculated completion. Optional `completion_calendar_id` belongs to CriticalPathTestConfig. For a mixed-calendar CPLI experiment, explicitly provide `CPLIConfig(common_calendar_id=..., path_length_method="COMMON_CALENDAR_WORKING_SPAN", required_finish=...)`.

DurationSimulationResult preserves both complete CPM domain results, selected internal ID/code, original/new effective hours, delta, source configuration, anchor policy, both anchors/timestamps, elapsed/working movement, measurement calendar, critical path/activity changes, and per-activity TF before/after/variance. CriticalPathTestResult preserves configuration, source CPM evidence even when evaluation is blocked, selection/reason, injected delay, simulation and raw ratio. CPLIResult preserves source and deadline-bound CPM evidence, all tied controlling paths, chosen path, separate duration/lag contributions, calendar/method, required-finish provenance, native anchor TF, participating float/provenance, numerator, denominator, unrounded value, formula/version and diagnostics.

The thin DCMA adapter projects these records into DCMAMetricResult.details, preserving calculation configuration, per-activity CPM results, controlling paths, anchors and diagnostics. It omits duplicated full canonical Schedule objects/indexes from JSON, while the dedicated simulation/CPLI domain result retains them. No scheduling mathematics occurs in the adapter. NOT_EVALUATED has no finding percentage or invented value and contributes no evaluated scoring weight. Assessment configuration version is DCMA-STYLE-PHASE8-V1.

## Validation results and file scope

Initial baseline:

```text
pytest -q -m "not external_xer and not postgres"
582 passed, 38 deselected, 1 warning in 35.43s

# Explicitly selected test_cpm*.py and test_dcma*.py files (PowerShell selection)
306 passed, 1 warning in 6.01s
```

Final results:

```text
pytest -q -m "not external_xer and not postgres"
649 passed, 39 deselected, 1 warning in 34.24s

# Explicitly selected CPM, DCMA, calendars and calendar-boundary files,
# excluding external_xer and postgres
452 passed, 1 deselected, 1 warning in 8.81s

pytest -q -m postgres
37 passed, 651 deselected, 1 warning in 32.65s
```

The warning is the existing FastAPI/Starlette TestClient deprecation. The two external NRG00800 tests remain deselected and no unavailable real data was fabricated. Phase 8 domain development does not require PostgreSQL.

67 new non-database cases cover manually derived dates, ratios and CPLI numerator/denominator/value; positive/negative lag; FS/SS/FF/SF recalculation; parallel/tied chains; a general negative-duration-delta experiment that changes the controlling path and removes activity criticality; negative float; constraint-controlled completion/release; milestone anchors; explicit activity immediately before finish; mixed-calendar rejection and explicit-clock opt-in; split shifts, holidays and working exceptions; unsupported/invalid inputs; in-progress/complete historical dates; failure before and during recalculation; duration preference/fallback; ambiguous anchors; fixed anchor identity versus explicitly reselected timestamp binding; trace bounds; and a 1,001-activity immutable experiment. Exact warning-bound inclusion has a regression: compare the ratio to interval endpoints directly, preserving the raw ratio without rounding or an arithmetic tolerance workaround.

The immutable source snapshot test populates imported ES/EF/LS/LF, planned dates, signed imported TF/FF and both constraint slots. It checks canonical equality and repeats source CPM after simulation, proving deterministic equality. Nested calendars and activity objects are separate copies. Completed actuals remain historical and cannot be selected for injected remaining work.

One new real-PostgreSQL test uses a new proprietary-free XER fixture with a single terminal milestone and a supported Finish On or Before deadline. It checks canonical in-memory vs persisted/reloaded assessment equality, both metrics evaluated PASS, and the existing stored-version DCMA endpoint's response ratio (1.0), CPL (6h), and CPLI (1.0). The existing 36 PostgreSQL tests also pass. The initial new parity fixture accidentally used CS_MFOB, which existing normalization correctly treated as unsupported MUST_FINISH_ON; the fixture was corrected to supported CS_FNLT, with an explicit normalization assertion. No importer/constraint behavior or existing fixtures changed to satisfy it.

Actual PostgreSQL validation used only the previously created task-owned isolated native PostgreSQL 18.4 cluster on loopback port 55437. Existing production/system PostgreSQL services were untouched. All per-test schemas were removed and the task-owned cluster was stopped after validation. No Phase 7 schema, migration, repository, mapper, storage, service or API code changed. Source-version immutability remains enforced by the original database guards.

Created:

- app/cpm/simulation.py
- app/cpm/cpli.py
- app/dcma/cpm_metrics.py
- tests/test_cpm_simulation.py
- tests/test_dcma_cpm_assurance.py
- tests/test_persistence_phase8.py
- docs/phase8_calculation_contract.md

Modified:

- app/dcma/config.py: explicit CPM/CPT/CPLI configuration and assessment version
- app/dcma/service.py: delegate the two metrics to the dedicated adapters

A file-hash audit verifies that these are the only pre-existing Python/methodology files changed. Validated CPM, calendar, retained-logic, constraint, comparison, health, reporting and persistence implementation files are unchanged. `git diff --check` passes. No new database dependencies, specialized simulation endpoint, result persistence, UI or reporting redesign was added.

## Remaining methodological limitations

- Only STRICT complete-network CALCULATED results are eligible. Directional/partial real-P6 populations, unsupported Expected Finish, incident excluded LOE, unresolved constraints/endpoints and missing calendars continue to block these assessments. Phase 8 does not establish full real-P6 calibration or contractual authority.
- CPT needs a complete critical controlling trace under the visible CPM float threshold. A schedule with all positive float and no threshold-critical path can legitimately have CPLI but no CPT candidate. Truncated/partial or historical-boundary traces are not silently accepted.
- A CPT FAIL reports measured duration-response behavior, not proof that schedule logic is defective. In particular an SS controlling relationship can transmit start control without a duration increase moving the selected successor completion. Constraint slack and calendar waiting can also absorb injected work.
- Default CPL is deliberately restricted to the existing proven single-calendar FS path span. The explicitly chosen common-calendar span is a separate application methodology, not a claim that mixed-calendar component duration/lag sums form a universal CPL.
- Required completion is explicit or an unambiguous supported selected terminal activity deadline. Raw planned/project dates, imported P6 Late Finish and reverse-engineered float never establish required completion. Unsupported hard/mandatory constraints remain unsupported.
- Source/native anchor float and required deadline must be consistent. Conflicting effective deadlines, differing start/finish anchor float, missing meaningful length or zero denominator remain NOT_EVALUATED. Negative float and a negative CPLI numerator are not clamped.
- Thresholds and the default 8h injection are application settings, not assertions of official DCMA requirements. Date arithmetic retains the existing datetime-resolution calendar convention.
- The selected-anchor path helper is reused internally for bounded controlling traces; no P6 Longest Path equivalence is claimed. RESELECT_TERMINAL is deliberate opt-in to the existing resolver, not automatic selection of whichever terminal happens to finish latest.

No later phase is started automatically.
