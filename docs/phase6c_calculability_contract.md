# Phase 6C: explicit calculability and constraint extension

The Phase 6 calculation contract and Phase 6B evidence remain unchanged.
This document records a deliberate extension, not a silent replacement.

## Evidence and proposed behavior before implementation

Baseline: 346 passed, 2 deselected, 1 existing warning. All 72 unsupported
constraints have dates: CS_MEOA / FINISH_ON_OR_AFTER 71 (55 complete, 16
not started), CS_MSOB / START_ON_OR_BEFORE 1 (complete); all primary.
All ten WBS summaries are isolated. LOE remains unsupported; 18 have outgoing
logic. All 492 historical-planned-start findings are in-progress and informational.

Oracle operational authority:
- [Finish On or After](https://docs.oracle.com/cd/G48902_01/client_help/en_US/finish_on_or_after_constraint.htm)
- [Start On or Before](https://docs.oracle.com/cd/G48902_01/client_help/en_US/start_on_or_before_constraint.htm)
- [Constraint types](https://docs.oracle.com/cd/F88968_01/client_help/en_US/types_of_constraints.htm)
- [Raw identities](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/26/p6-cpp/constraintselectiondescriptions-101902a.html)

Raw-code identity comes from the supplied mapping; scheduling semantics come
from P6 Professional help. The CPP mapping labels some deadline constraints
hard for its own justification categories, whereas Professional distinguishes
only Mandatory Start/Finish as hard date overrides. No deadline is implemented
as a Mandatory override. Network bounds remain; late deadlines may yield negative
float. Mandatory constraints remain unsupported and fatal.

FINISH_ON_OR_AFTER is IMPLEMENTABLE as a forward finish lower bound, using the
existing exact start_for_finish_not_before calendar inverse; it does not override
logic or constrain late dates. START_ON_OR_BEFORE is IMPLEMENTABLE as a backward
start upper bound, using finish_for_start_not_after; it does not pull early work
before Data Date. START_ON_OR_AFTER / FINISH_ON_OR_BEFORE remain SUPPORTED.
Other known constraints remain UNSUPPORTED, not guessed from source dates.
Completed supported constraints are VALIDATION_ONLY historical information:
require well-formed dates, retain actuals, do not reschedule history.

Both slots produce independent max/min bounds and structured control causes.
An empty soft-constraint window emits conflicting_constraint_window and retains
signed negative float rather than overwriting either constraint. Runtime invariants
must verify early lower bounds and late upper bounds before float calculation.

Existing contract gaps: selected constraint subset omitted these two documented
bounds; WBS identity lacked a safe isolated exclusion; all-or-nothing failure
prevented calculations on unrelated components. Proposed extensions preserve
the strict default incident-exclusion behavior and all existing calendar/float math.

Before implementation tests/test_cpm_constraints.py produced 11 failed, 4 passed.
New cases manually verify both slots, weekend exact inverses, zero-work events,
compatible/conflicting dual constraints, isolated/linked WBS, unchanged historical
fields and continued refusal to soften mandatory constraints.

## Component policy (documented before implementation)

18 synthetic component tests fail before implementation (missing explicit policy).
The opt-in component_calculation_policy=VALID_COMPONENTS retains STRICT as default.
Uncertainty propagates through whole weak components because both early bounds
and late/float bounds depend on opposite directions. No partial component dates
are emitted: PARTIALLY_CALCULATED is an overall result containing fully calculated
components plus blocked/excluded records. Activity states are CALCULATED, BLOCKED,
EXCLUDED; partially_calculated_activity_count is zero by deliberate policy.

All exclusions preserve canonical activities and relationships. Incident excluded
LOE/WBS cannot become invented network boundaries; their components are blocked.
Isolated exclusions do not poison other components. Unsupported constraints/types,
invalid states/calendars, missing endpoints and cycles block affected components.
Global invalid configuration, missing Data Date or datetime-domain failures remain
global blockers. Local runtime invariant/relationship failures also quarantine the
component before any float/result escapes. Traversals/retries are iterative.

For conservative real-P6 comparison, this mode also blocks unfinished Expected
Finish and observed out-of-sequence FS / progressed positive-SS-lag conditions
whose P6 progress/expired-lag compatibility is unconfirmed. Ordinary valid
in-progress work remains calculable under the existing application policy with
capability diagnostics; in-progress status alone is not a blocking condition. It does not infer options or implement Retained Logic/Progress
Override. STRICT retains the existing explicit application remaining-work policy;
these extra compatibility gates apply only to the opted-in conservative mode.

No dates/results/comparisons are emitted for blocked/excluded activities. Source
records and root reasons remain available via per-activity, relationship and
component disposition records. Comparison denominator contains only returned
calculated rows; remaining-work calibration additionally excludes PRESERVED_ACTUALS
history because imported early placeholders are not actual-span equivalents.
A partial result has no project completion anchor/path/completion timestamp.
Independent component finish bounds are mathematical bounds, not contractual
project anchors. An implicit PROJECT_FINISH shared bound cannot be established
with blocked components; an explicit required finish remains a valid bound.


## Excluded-record calendar validation refinement

Two further synthetic cases fail before correction: isolated excluded WBS/LOE
records without calendars prevent unrelated calculation. These records do not
receive dates or duration arithmetic, so a calendar is not a missing scheduling
input for them. Calendar validation is waived only for the known informational
exclusion dispositions (WBS/LOE); incident logic is still rejected/quarantined.
Included activities and unknown/invalid states keep the existing calendar errors.
This is an exclusion-policy correction, not an implicit fallback calendar.


## Final progress-gate refinement

Two synthetic cases exposed an unnecessarily broad initial progress gate. A valid
in-progress task with no unsupported logic (isolated or followed by ordinary FS
not-started work) must remain calculable. The final gate is relationship-evidenced:
FS with nonnegative lag, unfinished predecessor and an actually started successor;
or positive SS lag with an in-progress predecessor and Actual Start. Negative FS
lag overlap is not assumed invalid. Excluded LOE/WBS already have their own gate.
The affected component is withheld; this does not implement a P6 option. Other
progress retains the existing REMAINING_FROM_DATA_DATE policy and capability
warning. The original synthetic blocker case now explicitly describes positive
SS lag, rather than assuming that all progress is unsupported.

Stale unused constraint stubs that treated Mandatory dates as soft bounds were
removed; validated passes use only the calendar-aware requirement helpers.
