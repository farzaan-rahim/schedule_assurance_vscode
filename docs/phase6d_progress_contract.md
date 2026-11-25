# Phase 6D: forward progress and directional availability extension

The four Phase 6/6B/6C contracts remain unchanged. Baseline: 393 passed,
2 deselected, 1 existing warning. This opt-in extension does not alter the
validated default forward/backward/float/constraint/path/calendar methodology.

## Source options and authority

Observed SCHEDOPTIONS: sched_retained_logic=Y, sched_progress_override=N,
sched_lag_early_start_flag=Y, sched_calendar_on_relationship_lag=rcal_Predecessor,
sched_use_expect_end_flag=Y, sched_outer_depend_type=SD_Both,
sched_setplantoforecast=N. No separate actual-date or remaining-duration
recalculation switch is present in this table. Do not invent those settings.

[Oracle scheduling options](https://docs.oracle.com/cd/G48897_01/p6help/en/90519.htm)
describes retained remaining-work logic and SS expired-lag behavior.
[Oracle status fields](https://docs.oracle.com/cd/G48897_01/p6help/en/90151.htm)
describes Expected Finish as a resource-entered forecast and remaining duration
as working time between remaining start/finish. Neither a forecast date nor
coincidence with imported EF proves its conflict-resolution scheduling semantics.

Six synthetic parser/mapper tests fail before the typed options/date mapping.
Map only identified relevant fields; preserve every raw option as immutable
key/value pairs for audit. Unknown flags stay unknown and diagnostic; duplicate
project option rows are not arbitrarily selected. Scheduling policy reads typed
fields, never arbitrary raw dictionaries. No SCHEDOPTIONS option is automatically
applied by the existing STRICT or VALID_COMPONENTS calculations.

## Precise opt-in forward methodology (before implementation)

DIRECTIONAL_FORWARD plus explicit P6_RETAINED_LOGIC policy requires matching
canonical retained=Y/progress_override=N. No Progress Override or Actual Dates
mode is implemented. Actual Start/Finish remain source history; an internal
progress snapshot retains history, Data Date, imported remaining dates/duration
and calculated remaining dates without splitting canonical activities.

FS remaining work obeys predecessor actual finish if complete, otherwise its
calculated remaining finish, plus signed predecessor-calendar lag. Data Date
is a lower bound. A completed-predecessor lag partly consumed before Data Date
is naturally handled by its absolute lagged date, not replaying full lag at
Data Date. Multiple predecessor bounds remain max-combined.

For a positive SS lag from an in-progress predecessor with known Actual Start,
only the observed Early Start option is implemented: expired work is calendar
work from Actual Start to Data Date, clipped to [0, lag]; residual lag is
lag-expired, applied to calculated predecessor remaining ES. This accounts for
predecessor eligibility from its own logic. Complete predecessors retain their
historical actual-start endpoint; not-started predecessors use calculated ES.
Progressed negative SS lag and progressed SF conditions remain unsupported rather
than guessed. FF remaining finish bounds use existing calendar inverse math.
These are a narrow retained/expired-lag subset, not a full P6 reproduction claim.

A completed successor has no remaining requirement. Its actual dates are
preserved even if historical incoming logic was out of sequence. Such source
relationships remain recorded as HISTORICAL_ONLY, with diagnostics; they are
not declared feasible remaining-work relationships. This is a documented
historical/remaining segment distinction, not dropped source logic.

Expected Finish remains blocked for unfinished work when enabled or unknown.
The observed data include forecasts both equal to and different from imported
EF and cannot establish how P6 resolves conflicts/recalculates remaining hours.
Explicitly disabled use allows the preserved informational field without applying
it. No imported duration or date is overwritten or tuned.

LOE/WBS remain excluded. A normal predecessor of an excluded downstream LOE
can retain early dates; late/float bounds across that endpoint are unavailable.
A normal successor of an excluded LOE has an unresolved early predecessor;
that block propagates downstream only. Valid completed actuals remain available,
while their prospective retained release may be unavailable as described below.
Missing endpoints, invalid calendars/states, unknown constraints and active
cycles similarly block affected early work. Global datetime/config/Data Date
failures retain their global gate. No fake LOE boundary or bypass relationship.

Forward calculation does not require a finish anchor. Every published unfinished
ES/EF must satisfy duration/calendar, forward constraint and active relationship
invariants. Blocked ancestors never supply imported ES/EF as substitutes.
Only valid remaining-work ES/EF enter comparison; history is separately preserved.
Late dates, TF, FF, critical classification and paths are NOT_EVALUATED in this
mode. Per-activity and per-relationship directional availability is explicit.
DCMA Critical Path Test and CPLI remain NOT_EVALUATED.


## Remaining-duration reliability gate

Two additional synthetic tests show that original-duration preference/fallback
must not be labeled retained remaining work. In DIRECTIONAL_FORWARD, ordinary
unfinished work requires populated remaining hours and remaining-duration
preference. Missing remaining duration or explicit original preference blocks
that activity, with a diagnostic. Existing STRICT fallback configuration remains
unchanged. Milestones and completed actuals retain their separate zero-work
policies. No original duration is silently substituted for a P6 remaining segment.


## Completed-history versus retained-release gap: real evidence before correction

Initial forward calibration returned 955 remaining records (745 exact ES/EF).
A trace of its largest difference exposed an availability defect in the new mode,
not an established date-arithmetic defect. Source chain:
1604233 (unfinished, Expected Finish 2026-09-30) -> 1604230 (complete,
Actual Finish 2024-06-28, imported early endpoint 2026-09-30) -> 1604231
(complete, Actual Finish 2026-01-30, imported early endpoint 2026-09-30) ->
1604234 (unfinished zero work, P6 remaining start 2026-10-01).
TASKPRED 3508811 records aref=2026-09-30. The initial application incorrectly
certified the final remaining release using the actual-date boundary alone,
although an unimplemented retained bridge carried unresolved upstream work.

Two generic synthetic cases fail before the correction: unfinished predecessor
(with known remaining calculation or blocked Expected Finish) -> completed
history -> future task. History must remain preserved, but the future release
cannot be certified without documented completed-bridge semantics. A source
Expected Finish/LOE uncertainty also cannot disappear through a completed chain.
This refines the earlier statement that uncertainty stops at history: it stops
for historical actual availability, not automatically for prospective release.

Correction is availability-only, not a compatibility formula fitted to P6 dates.
No imported early date or TASKPRED aref is used as a replacement. A completed
node reached from blocked/excluded work, or from an unfinished FS/FF finish
endpoint, retains its actual ES/EF but its forward release is marked BLOCKED.
That release uncertainty propagates through completed chains and blocks affected
unfinished descendants. The rule depends on graph/state, never match percentage
or variance magnitude. Completed predecessors with established releases retain
the documented actual-endpoint behavior. Fully deriving P6 completed proxies is
still unsupported; project-specific future dates are never copied into results.
