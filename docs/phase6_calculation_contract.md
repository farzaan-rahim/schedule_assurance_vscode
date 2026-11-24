# Phase 6 calculation contract and validation report

The original date/float contract and its checkpoint results are preserved below.
The current extension is [Completion-anchor, path and comparison increment](#completion-anchor-path-and-comparison-increment).
It supersedes the earlier statements that path outputs are empty and tracing has
not yet been implemented; the validated date/float methodology remains intact.

## Test results and external data

Initial complete `pytest -q`: **157 passed, 2 failed, 1 warning**.
Both failures are unchanged external dependencies:

- `tests/test_calendars.py::test_real_xer_calendars_and_activity_coverage`
- `tests/test_phase5_optional.py::test_nrg00800_optional_mapping_counts`

Both require `sample_data/NRG00800.xer`, which remains unavailable and was not
fabricated. They now carry the registered `external_xer` marker. Default tests
still fail when that fixture is absent; no missing-data test becomes a synthetic
success. The marker excludes exactly these two tests.

Final validation:

| Command | Result |
| --- | --- |
| `pytest -q -m "not external_xer"` | 275 passed, 2 deselected, 1 warning |
| `pytest -q tests/test_calendars.py tests/test_calendar_boundaries.py -m "not external_xer"` | 79 passed, 1 deselected |
| `pytest -q tests/test_cpm.py tests/test_cpm_states.py tests/test_cpm_float.py tests/test_cpm_invariants.py` | 149 passed |
| `pytest -q` | 275 passed, 2 failed, 1 warning; only the external tests fail |

The warning is the existing FastAPI/Starlette TestClient deprecation.
The two synthetic comparison fixtures reconstructed in the previous increment
are retained. No fixture assertions were weakened or unrelated tests skipped.

## Boundary arithmetic and normalization

Work intervals are half-open `[start, finish)`. `is_working_time` excludes a
closing instant, while a finish date may validly equal that instant. Positive
addition starts at `next_working_time`, consumes only work, and may return an
exact close. Positive subtraction skips gaps backward and may return an exact
opening. Both positive and negative zero preserve the input timestamp. Negative
hours delegate to the opposite operation. Adjacent intervals are continuous.

`working_boundaries_equivalent` means exactly zero working hours between two
instants on the specified calendar; there is no elapsed-time tolerance. It is
used to compare inverse boundary representations, not to excuse a violated CPM
relationship. All relationship endpoint checks still use raw timestamp order.

Overnight periods (finish at/before start) extend into the following civil day.
Calendar arithmetic clips and merges intervals from the current and preceding
origin day. Exceptions apply to the date on which the shift starts; an overnight
working exception can therefore continue into the next civil day. Parsing now
preserves these overnight periods instead of rejecting an end such as 04:00.
All duration arithmetic uses Python datetime/timedelta microsecond resolution.

### The two previously unsupported conversions

1. **Forward FF, zero lag.** A uses C1, weekdays 08:00-17:00, and finishes
   Monday 2026-01-05 14:00. B uses C2, weekdays 10:00-12:00, and requires 1h.
   Ordinary `subtract_working_hours(C2, Monday 14:00, 1)` returns Monday 11:00;
   adding 1h returns Monday 12:00, earlier than the required finish. The bound
   lies in C2's non-working afternoon gap, not an overnight/exception boundary.
   The earliest *working start* meeting the raw bound is Monday
   **11:00:00.000001**, finishing Tuesday **10:00:00.000001**. One tick earlier
   finishes Monday 12:00 and fails the bound. The shared
   `start_for_finish_not_before` helper proves this minimality in tests.

2. **Backward FS, -2h lag.** A uses C1, weekdays 08:00-17:00; B uses C2,
   weekdays 07:00-11:00. Required finish is Wednesday 2026-01-07 11:00, making
   B late start Wednesday 07:00. Ordinary `add_working_hours(C1, 07:00, 2)`
   gives 10:00, but subtracting 2h gives 08:00, later than B's start. The bound
   is at C2's opening but in C1's overnight non-working gap. The latest source
   finish is Wednesday **09:59:59.999999**; its negative lag lands Tuesday
   **16:59:59.999999**, before B's start. One tick later violates the bound.
   `inverse_lag_deadline` uses the shared `finish_for_start_not_after` helper.

These are discrete, exact generalized inverses of functions with non-working
plateaus, not arbitrary timestamp tolerances. The protective per-pass endpoint
audits remain. Tests deliberately corrupt both passes and prove that the audit
still rejects infeasible dates before float.

37 new calendar cases cover both inverse directions, starts/closes, lunch,
adjacent shifts, midnight and overnight shifts, weekend and holiday boundaries,
working exceptions, fractional hours, signed zero, parser preservation, and
exact minimal/maximal inverse bounds.

## Central activity-state policies

`activity_decision` in `app/cpm/activity_state.py` owns state decisions. Passes
receive validated effective states; they do not guess unknown statuses/types.
The configuration is retained in each result, with an activity-level effective
finish anchor and date basis.

| Condition | Default disposition | Configurable alternative |
| --- | --- | --- |
| Negative or non-finite original/remaining duration | ERROR | No silent fallback |
| Unknown/missing status or type | ERROR | `invalid_activity_policy=EXCLUDE` |
| Missing usable duration | ERROR after fallback is exhausted | `missing_duration_policy=EXCLUDE` |
| Remaining missing, original present | WARNING + original-duration fallback | `duration_fallback_policy=ERROR` |
| Remaining populated | Use remaining when preferred | Explicit original-duration preference |
| Ordinary zero duration / in-progress zero remaining | INCLUDE as a zero-work event | `zero_duration_task_policy=ERROR` |
| Missing calendar | ERROR | `missing_calendar_policy=EXCLUDE`; no implicit calendar fallback |
| Unusable calendar | ERROR | No silent arithmetic fallback |
| LOE | EXCLUDE with diagnostic | `loe_policy=ERROR` |
| Not-started with actual dates | ERROR | Invalid-activity exclusion |
| Planned/forecast start before Data Date | INFORMATIONAL; preserve imported date and bound remaining work by Data Date | No imported-date overwrite |
| In-progress missing Actual Start or with Actual Finish | ERROR | Invalid-activity exclusion |
| Actual Start/Finish after Data Date or finish before start | ERROR | Invalid-activity exclusion |
| Complete missing Actual Start or Actual Finish | ERROR | Invalid-activity exclusion |
| Complete with non-zero remaining | WARNING + effective remaining zero | `completed_remaining_duration_policy=ERROR` |
| Milestone with non-zero imported duration | WARNING + effective zero | `milestone_duration_policy=ERROR` |
| Start/finish/generic milestone with zero/missing duration | INCLUDE as a zero-work event | Actual/status validation still applies |

Exclusions are permitted for isolated activities. An incident relationship to an
excluded activity causes an explicit fatal diagnostic: the engine never silently
reconnects or deletes logic to bypass LOE or invalid work. If nothing remains,
calculation fails explicitly.

In-progress work represents remaining work from Data Date; its imported Actual
Start is retained separately. This is not a claim to implement P6 retained logic
or Progress Override. Start overrides cannot pull remaining work before Data
Date or authorize actual dates after Data Date.

Completed records have `date_basis=PRESERVED_ACTUALS`: both passes retain their
Actual Start/Finish, effective *remaining* duration is zero, and remaining-work
float is None with a diagnostic. Their historical span is deliberately not
collapsed into a zero-length activity or rescheduled using unfinished-work
arithmetic. Historical actual dates are not normalized to calendar shifts.
Unfinished records have `date_basis=REMAINING_WORK`.

Constraints currently supported are Start On or After and Finish On or Before,
in either constraint slot. Missing dates and other constraint types are explicit
errors. Unsupported scheduling/configuration choices are diagnosed, not guessed.

## Date invariants and reproducibility

Before any float is produced, runtime validation checks unfinished work:

- EF equals calendar addition of effective duration to ES.
- LS equals calendar subtraction of effective duration from LF.
- Positive-duration starts are working instants; finishes are working instants
  or exact valid closing boundaries.
- Zero-work events retain their valid event timestamps, including non-working
  instants; no duration arithmetic is fabricated.
- Completed history instead exactly matches preserved actual dates in both
  passes, under the explicit historical date basis above.

Failure returns no activity/float results. Tests inject a broken invariant and
prove float is not called. Canonical Schedule values remain unchanged, including
imported dates, durations and float. A 1,000-activity chain runs repeatedly with
identical results and no recursion-depth adjustment; cycle validation uses the
existing iterative topological sort. A 200-source / 200-successor fan around a
join verifies 25 tied incoming and 200 tied outgoing controlling requirements.

## Total Float

The activity's own calendar is used:

- `start_float = working_hours_between(calendar, ES, LS)`
- `finish_float = working_hours_between(calendar, EF, LF)`
- Primary Total Float is explicitly **start_float**, basis
  `ACTIVITY_CALENDAR_START`.

Both values are retained in separate result fields. Any difference emits
`float_methods_disagree`; values are never averaged or selected to match P6.
Positive, zero, negative and fractional hours remain signed. None is preserved
when unavailable/not applicable, including completed historical records.

Tests verify the critical FS chain, a shorter parallel path (+4h), required
finish causing -1h and -0.5h, signed lags, SS/FF/SF, split shifts, different
calendars and milestones. Disconnected components use separate calculated finish
anchors by default (`INDEPENDENT_ANCHOR`). `PROJECT_FINISH` gives all components
the common finish; an explicit required finish always applies globally. Both
policies are tested. This changes no imported float.

## Free Float

Current lag policy is explicitly **PREDECESSOR working hours**; other policies
remain rejected. For every outgoing relationship, invert signed lag against the
successor's selected early endpoint to obtain the latest permitted predecessor
endpoint. Measure the displacement from its current endpoint in the activity
calendar:

| Relationship | Current predecessor endpoint | Successor bound |
| --- | --- | --- |
| FS | EF | successor ES |
| SS | ES | successor ES |
| FF | EF | successor EF |
| SF | ES | successor EF |

In notation, `limit = inverse_lag_deadline(predecessor_calendar, bound, lag)` and
`relationship_FF = working_hours_between(activity_calendar, endpoint, limit)`.
The minimum across successors is returned, with each relationship's hours
retained. No successor, unsupported methodology or missing dates yields None
and a diagnostic. Signed negative slack is not clamped; a helper test verifies
-1h while the service still refuses to publish an infeasible schedule.
Tests cover every relationship with positive and negative lag, multiple
successors and differing calendars. This is an explicit application methodology,
not a proprietary P6 or Deltek formula.

## Classification and control provenance

Critical means TF <= configured critical threshold. Near critical means TF is
above that threshold and <= the configured near threshold. Tests cover negative,
exact critical, between thresholds, exact near, above near, and missing TF.
Invalid/non-finite/reversed threshold configurations fail validation.

Imported-critical state is explicitly a proxy derived from imported Total Float
using the same threshold, labelled `IMPORTED_TOTAL_FLOAT_THRESHOLD`; the canonical
model does not contain a separate P6 critical flag. This proxy, application
critical/near-critical flags and optional disagreement are stored separately.
Missing imported TF or calculated TF yields None for disagreement.

Each controlling relationship retains its ID, predecessor/successor IDs and
visible codes, type, lag, lag calendar ID/policy, direction, resolved ES/LF
requirement timestamp, and whether it tied with another relationship. Constraints
have separate structured cause records, imported constraint dates, resolved
requirements and a relationship-tie flag. Both constraint slots are honored.
Legacy ID/string fields remain for compatibility; they are no longer the only
explanation. Critical activities are not labelled a critical path; path outputs
remain empty.

## Files and stopping point

Created this increment:

- `docs/phase6_calculation_contract.md`
- `tests/test_calendar_boundaries.py`
- `tests/test_cpm_states.py`
- `tests/test_cpm_float.py`
- `tests/test_cpm_invariants.py`

Modified this increment:

- `README.md`, `pyproject.toml`
- `app/calendars/parser.py`, `app/calendars/working_time.py`
- `app/cpm/activity_state.py`, `config.py`, `models.py`, `validation.py`
- `app/cpm/forward_pass.py`, `backward_pass.py`, `relationship_math.py`
- `app/cpm/service.py`, `float_calculation.py`
- `tests/test_calendars.py`, `tests/test_phase5_optional.py`, `tests/test_cpm.py`

Earlier uncommitted fixture and ignore-rule changes were preserved. Neither
`original_files` nor `legacy_reference` was changed or activated. No new package
or Ruff was installed or invoked.

The requested synthetic calculation gates pass. Remaining restrictions before
path work are explicit scope decisions: selected completion-anchor/path semantics,
bounded tied-path enumeration, and handling or rejecting incident excluded LOE
without inventing logic. Wider P6 scheduling options and additional constraint or
lag policies remain unsupported and diagnosed. The external real NRG fixture is
still needed for its two existing import regressions and any later real-project
work. No critical/near-critical path tracing, CPM API, real-project calibration,
DCMA Critical Path Test, CPLI, persistence or other phase was implemented.


## Completion-anchor, path and comparison increment

### Regression and file manifest

Initial local baseline: **275 passed, 2 deselected, 1 existing warning**.
Final `pytest -q -m "not external_xer"`: **335 passed, 2 deselected, 1 warning**.
The external marker still selects exactly the two unavailable NRG00800 import
integration tests. No real-project CPM calibration was attempted or fabricated.

Focused calendar command remains the one above: **79 passed, 1 deselected**.
Focused CPM command now includes `tests/test_cpm_paths.py` and
`tests/test_cpm_comparison.py` in addition to the five earlier CPM test files:
**209 passed**. The new files contribute 37 path/anchor cases and 23 comparison
cases. `git diff --check` passes. The existing warning remains the
FastAPI/Starlette TestClient deprecation.

Created this increment:

- `app/cpm/anchors.py`
- `app/cpm/paths.py`
- `app/cpm/comparison.py`
- `app/cpm/post_calculation.py`
- `tests/test_cpm_paths.py`
- `tests/test_cpm_comparison.py`

Modified this increment:

- `app/cpm/config.py`, `models.py`, `validation.py`, `service.py`
- `app/models/schedule.py`, `app/importers/schedule_mapper.py`
- `tests/test_cpm_float.py`, `tests/test_cpm_invariants.py`
- `README.md`, `docs/phase6_calculation_contract.md`

The two earlier assertions that paths were always empty were replaced with
stronger expectations for the implemented chain and explicit default-depth
truncation. Existing date/float/invariant assertions remain. Previously
uncommitted work and synthetic fixtures were preserved. This increment did not
modify forward/backward passes, relationship arithmetic, float arithmetic,
calendars, original_files or legacy_reference.

### Explicit completion selection

Post-calculation selection uses this priority:

1. `completion_activity_id` and/or `completion_activity_code`.
2. `required_finish_activity_id` and/or `required_finish_activity_code`.
3. `project_completion_timestamp`.
4. A sole eligible graph-terminal activity, with source UNAMBIGUOUS_TERMINAL.

An ID/code pair must identify the same calculated activity. Missing, conflicting,
excluded or ambiguous selectors never fall through to a lower-priority choice.
A duplicate visible code requires an internal ID. Candidate ordering is lexical
code then internal ID; all terminal candidates are retained for an unconfigured
multi-terminal/disconnected network. Selection is AMBIGUOUS and paths are not
evaluated until an activity is selected. Date/float calculation remains valid;
`anchor_selection_status` and `path_status` communicate selection problems
separately from the CALCULATED core status.

A configured timestamp binds an activity only when exactly one terminal has that
exact calculated EF. Otherwise it is retained as a project event with no invented
activity ID or relationship, and path status is NO_ACTIVITY_ANCHOR. An explicit
activity is then needed to trace. Comparison tolerances do not affect selection.

The snapshot contains internal ID, visible code, name, source, calculated EF/LF,
imported finish, configured required finish and configured completion timestamp.
The generic imported-finish field prefers imported early finish, then planned
finish; it is not a substitute for imported Early Finish in comparisons.

Selection does not reschedule work or change previously validated backward/float
semantics. `required_project_finish` remains the existing scheduling deadline;
`project_completion_timestamp` is a distinct selection/reporting event. Per-
activity constraints remain structured causes. The existing project maximum
completion and the selected activity's EF may legitimately differ (for example
with SS logic or an explicitly selected internal anchor); they are not conflated.

### Connected critical traces and constraints

A critical trace is an ordered connected chain ending at the selected activity,
using only calculated FORWARD controlling predecessor relationships. Every
included activity has a known TF <= the configured critical threshold. A set of
critical activities is never presented as a path. All equally controlling
relationship branches are explored, within explicit limits; chains are reversed
for start-to-anchor presentation.

Each path retains stable ID/rank, anchor, ordered internal IDs and visible codes,
ordered full relationship records, counts, min/max signed TF, start/finish,
activity-hour sum, signed lag-hour sum, ties, constraint causes, qualification
reason, end reason, diagnostics and truncation/completeness flags.

A dominating Start On or After constraint ends the predecessor trace cleanly
with end reason CONSTRAINT and the activity-labelled constraint record. A tied
constraint is retained alongside relationship branches; it does not manufacture
an edge or a duplicate fictitious constraint path. A float/Data Date boundary
is explicitly labelled, has a partial-trace diagnostic and `trace_complete=False`.
Budget-cut prefixes are connected suffixes leading to the selected anchor and
also have `truncated=True`; they never pretend to start at a network root.
Negative TF remains signed, including the tested required-finish path at -1h.

### Near-critical qualification

Near traces are connected chains to the same anchor. All activities have known
TF <= `near_critical_float_threshold_hours`, and at least one has TF strictly
above the critical threshold. This excludes all-critical primary/tied traces
from the near collection.

Edges are either calculated controlling edges, or supported predecessor edges
whose relationship Free Float is in `[0, max(0, near threshold)]`. Noncontrolling
edges retain the resolved early-start requirement, signed lag/calendar policy,
qualification reason, `controlling=False`, direction NEAR_QUALIFYING, and their
relationship slack. This is an explicit deterministic qualification rule, not a
risk probability or a P6 multiple-float-path implementation. A dominating forward
constraint still ends tracing rather than allowing unrelated upstream near work
to masquerade as its controlling chain.

A linear topological reachability pass prunes all-critical branches from near
tracing without enumerating them. The tested shorter diamond branch has +2h TF,
is returned at a 2h near threshold and excluded at 1h.

### Bounds, counts and ranking

`maximum_critical_paths` and `maximum_near_critical_paths` independently inherit
legacy `maximum_path_count` (20 by default) when None. `maximum_path_depth`
remains 500; `maximum_path_nodes_inspected` defaults to 10000. Bounds are validated
integers, with depth >= 1 and other limits >= 0.

Enumeration uses explicit DFS frames, never recursion. Adjacency/provenance and
near reachability preparation are O(V+E); the inspection budget counts trace
visit events (including repeated visits), shared across critical then near
tracing. Limits cap enumeration rather than claiming to avoid reading the
already calculated input graph.

At a count limit, one additional qualifying endpoint is inspected when the
budget allows, so exactly N paths at an N-path limit do not falsely report
truncation. At depth/node limits, known connected prefixes may be returned as
explicitly truncated traces. Collection statistics include returned count,
finished enumeration endpoints found, a lower bound, inspection count and all
limit reasons. The endpoint count includes declared control-boundary endpoints;
`trace_complete` separately states whether a path reached a network start or
constraint. Exact `known_total_paths` is provided only when enumeration exhausts;
otherwise it is None, not an invented combinatorial total. Partial prefixes do
not inflate the completed lower bound.

Each hit emits `path_trace_truncated`. Full returned paths can individually be
complete while their collection is truncated because other branches remain.
Ranking is always scoped to RETURNED_PATHS. Candidate traversal is lexical by
predecessor code, internal ID, relationship ID. Returned paths sort by:

1. The selected anchor (all returned paths share it).
2. Lower minimum TF.
3. Longer effective-activity duration sum at exact datetime resolution.
4. Lexical code sequence, internal-ID sequence, relationship-ID sequence.

IDs CP-001 / NCP-001 etc. follow that ranking. Bounded results do not claim to be
global top-N paths among unexplored branches. No probabilistic score is used.

### Duration methodology

`sum_effective_activity_duration_hours` and
`relationship_lag_contribution_hours` are separate, accurately named sums. The
latter preserves negative lag and its clock policy; sums are not claimed to be
universal critical-path length.

Legacy `duration_hours` is supplied only for a single-calendar, all-FS,
remaining-work trace whose non-negative calendar working span equals the sum of
activity durations and signed lags at exact datetime resolution. The method is
SINGLE_CALENDAR_FS_WORKING_SPAN. Raw component sums remain unchanged; the
fractional 0.1h + 0.2h case correctly yields a 0.3h calendar span without a binary
float-equality failure. Mixed calendars, non-FS overlap or unexplained idle/slack
do not get an invented combined duration: None with method
SEPARATE_ACTIVITY_AND_LAG_HOURS. Raw elapsed timestamp spans are never summed.

### Imported P6 versus calculated values

Activity now independently retains imported `early_start`, `early_finish`,
`late_start`, `late_finish` and `expected_finish`. The mapper makes only focused
assignments from TASK early/late/expected-end fields. Existing planned-date
mapping is preserved. Missing early/late values remain None even when planned
dates exist; neither planned nor actual dates masquerade as imported early dates.
No imported date or float is overwritten by CPM.

Per-activity comparison records contain both imported and calculated ES/EF/LS/LF,
TF/FF, imported-critical proxy, calculated critical and optional disagreement.
Each metric also retains status, tolerance/unit and exact raw variance. Date
variance is **calculated minus imported in elapsed hours**, with raw seconds
retained too, rather than calendar working hours. Float variance is calculated
minus imported hours. No rounding or tolerance changes values.

`comparison_date_tolerance_seconds` and `comparison_float_tolerance_hours`
default to zero and must be finite/non-negative. Absolute variance <= tolerance
classifies MATCH; otherwise DIFFERENCE. Missing statuses are MISSING_IMPORTED,
MISSING_CALCULATED and BOTH_MISSING. Critical-state agreement is Boolean and not
altered by float/date tolerances. The imported critical proxy remains explicitly
based on imported TF and the configured threshold, not a guessed P6 critical flag.

The aggregate summary retains eligible activities compared, all activity records,
missing imported date fields, activities with a missing imported date, matches
and differences for each of the six date/float metrics, critical agreements and
disagreements, and per-metric counts of all missing statuses. Excluded activities
still have detailed records with unavailable calculated values; they do not
become zeros or false matches. Failed calculations do not fabricate comparisons.

### Capability diagnostics and observed options

Comparison-level hints carry support status, observed/evidence metadata and
`cause_established=False`. Progress hints require in-progress activities. Lag
hints require non-zero lag. Expected Finish, inheritance, external endpoints,
unsupported constraints/types are included only when observed. Resource
assignments alone are not evidence of resource-dependent scheduling.

Observed progress-order diagnostics check the correct FS/SS/FF/SF actual endpoints
and the application's signed predecessor-calendar lag. Valid SS overlap and valid
negative-FS-lag overlap are explicitly tested not to be labelled out-of-sequence.
An observed violation does not establish a P6 scheduling-option choice or the
cause of a comparison difference.

SCHEDOPTIONS is still outside the canonical model. No scheduling-option values
were observed or interpreted in this increment, so no option-derived hidden
policy or fabricated observation was introduced. Its absence from this model is
INFORMATIONAL_ONLY. The P6 critical-definition flag/options are UNSUPPORTED for
comparison; current progress/lag/inheritance support is labelled partial when
relevant. Retained Logic, Progress Override, longest-path and multiple-float-path
settings are explicitly unobserved possible capability differences, not asserted
causes. A separate SCHEDOPTIONS parser or importer redesign was unnecessary for
the controlled synthetic scope.

### Controlled evidence and remaining scope

The synthetic cases verify: A-B-C-Finish gives exactly one connected path; a
longer diamond branch is critical and the shorter branch can be near; an exact
diamond tie gives both paths; multiple/disconnected terminals select no arbitrary
path; missing/conflicting selectors do not fall back; constraints terminate a
trace without fabricated logic; required finish preserves -1h TF. A complete
1,101-activity trace runs repeatedly without recursion. A layered 256-path graph
hits count/depth/node limits deterministically; near branching has a separate
count limit and shares the inspection budget. Exact-count and zero-count cases
are explicit. Comparison tests independently vary every date/float field, missing
values, critical state, tolerance boundaries and elapsed time across a weekend.

API remains a future thin-wrapper task after model review. Before real-P6
calibration, the genuine `sample_data/NRG00800.xer` is still required, along with
option/capability review; real calibration remains NOT_EVALUATED. Timestamp-only
anchors need an activity binding for tracing. Unsupported constraint/lag/resource
conditions remain diagnosed under the existing conservative contract.

DCMA Critical Path Test remains NOT_EVALUATED: path tracing is not immutable
schedule-delay simulation/recalculation. CPLI remains NOT_EVALUATED: this duration
representation is not a validated universal critical-path-length methodology.
No API, simulation, CPLI, persistence, UI, report export, real-project calibration
or another phase was implemented.
