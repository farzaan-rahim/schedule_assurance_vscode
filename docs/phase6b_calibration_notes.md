# Phase 6B calibration evidence

Protected methodology: docs/phase6_calculation_contract.md. The existing contract
is not changed by this investigation.

## Initial evidence before any application change

Source: sample_data/1414_RSM-RSM-CW-PWD-RPT-PRM0-00063_C01 Appendix.10 - OL-RSSOM-PWS_June 2026.xer
SHA-256: 77ad15c128638db79792ab915301ba236785fd134768ecd98a6992072de23999.
Size: 65,498,834 bytes. Export header: P6 26.5, 2026-07-05, Project Management Cloud.
The file contains a substantial genuine project/export schema, distinct from the
small synthetic fixtures. Source authenticity relies on the supplied provenance;
the unsigned XER structure itself is not cryptographic proof of origin.

Baseline: 335 passed, 2 external tests deselected, 1 existing warning.
Existing importer succeeded: 23,263 activities, 36,521 relationships, 5,139 WBS,
27 calendars; no import diagnostics. Default CPM was invoked unchanged.
It did not return activity calculations: all 27 weekly calendars parsed as empty,
leading to repeated 3,660-day reachability searches. The run was interrupted
during calendar validation rather than misreported as a successful calculation.

Initial ES/EF/LS/LF imported-present counts: 23,252 each (11 missing).
Initial TF/FF imported-present counts: 9,011 each (14,252 missing).
All six metrics had 0 calculated/comparable records, 23,263 calculated values
unavailable, and no computable median/maximum variance. These are unavailable
comparisons, not observed zero agreement or observed zero differences.
No initial controlling path, anchor or critical agreement was fabricated.

## Defect reduction and proposed correction

Observed source evidence: calendar 11683 contains Monday 08:00-12:00 and
13:00-17:00, serialized as s|08:00|f|12:00 and s|13:00|f|17:00.
The current parser searches only f|...|s|..., silently returns zero weekly work,
and next_working_time raises ValueError. This contradicts the explicit source
periods before any relationship/progress/float methodology is considered.

Contract gap: the calendar arithmetic contract assumes correctly decoded work
intervals but does not state that serialized s/f key ordering is immaterial.
Required clarification: period start/finish are identified by their keys in both
weekly patterns and exceptions, not by their text position.

Proposed correction: accept both orders through key-based period decoding,
retaining the same WorkPeriod model, exceptions, overnight and working arithmetic.
This is an application calendar-import defect correction, not a P6-specific
scoring/scheduling policy or an attempt to maximize agreement.

Synthetic proof: tests/test_phase6b_reproductions.py uses a new generic calendar,
January 2026 dates and no project data. It asserts equivalent weekly/split-shift
and working-exception arithmetic for both key orders. Existing f-first behavior
must continue to pass. No CPM formulas, progress policy, constraint policy, lag
policy, completion-anchor policy, DCMA test or CPLI will be changed by this fix.


## Observed normalization identity defects (before correction)

After the calendar-only correction, the full real import again succeeded and
CPM returned FAILED, with 684 unsupported_constraint errors, 67
unsupported_activity_type errors and 492 historical-planned-start information
messages. No activity/float results were emitted. Canonical core values and the
source file hash were unchanged by calculation.

Observed raw codes include CS_MSOA (371), CS_MEOB (241 including three secondary),
CS_MEOA (71), CS_MSOB (1), and TT_LOE (57). The current normalizer leaves the
first three constraint codes raw, mislabels CS_MSOB as MUST_START_ON, and leaves
TT_LOE as tt_loe. Oracle's primary mapping confirms their identities:

- CS_MSOA: Start On or After.
- CS_MEOB: Finish On or Before.
- CS_MEOA: Finish On or After.
- CS_MSOB: Start On or Before.
- TT_LOE: Level of Effort.

Sources:
[Oracle constraint mapping](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/26/p6-cpp/constraintselectiondescriptions-101902a.html)
and [Oracle P6/Prime data mapping](https://docs.oracle.com/cd/E75426_01/English/Mapping_and_Schema/p6_pro_prime_import_export_data_map_prime_sync/p6_pro_prime_import_export_data_map_prime_sync.pdf).

Contract gap: normalized identities were assumed correct but these observed
source aliases were absent/incorrect. The proposed correction changes only
these five observed identities, not any scheduling formula. Existing Start On or
After / Finish On or Before arithmetic is reused. Finish On or After and Start
On or Before remain explicitly unsupported. LOE remains excluded under the
existing conservative policy and must not be scheduled as an ordinary task.
Unrelated, unobserved legacy mappings are not silently rewritten in this scope.

The proprietary-free reproduction adds direct identity assertions, an LOE
exclusion assertion and two tiny single-activity calculations exercising the
already validated constraint math with these source aliases. An improvement in
agreement percentage is not the justification for this normalization correction.

## Final calibration outcome

The original full project is rejected by the existing conservative CPM validation gate. No constraints, summary activities, LOE relationships, or historical activities were deleted to obtain a numerical result. Final status is FAILED; calculated activity population is zero. No CPM formula or protected contract was modified. Imported canonical core values and the source SHA-256 were verified unchanged across calculation.
Two ingestion defects were corrected only after real-source evidence, documented contract gaps and failing proprietary-free tests: start-first calendar tokens (2 failed / 2 passed before correction), and observed constraint/LOE identities (7 failed / 4 passed before correction). All 11 reproductions pass afterward. These correct decoding/normalization, not scheduling policy.
The initial unchanged run was interrupted during calendar validation; the post-calendar-fix run returned FAILED (684 unsupported constraints, 67 unknown types). After normalization, the remaining explicit findings are:
| Severity | Code | Count | Meaning |
|---|---|---:|---|
| ERROR | unsupported_constraint | 72 | Finish On or After 71; Start On or Before 1 |
| ERROR | unsupported_activity_type | 10 | WBS Summary (TT_WBS) |
| WARNING | loe_not_supported | 57 | LOE excluded by existing policy; no incident-logic bypass |
| INFORMATIONAL | planned_start_before_data_date | 492 | Historical forecast retained; remaining work bounded by Data Date |
## Schedule suitability and characteristics

```json
{
  "project": {
    "project_id": "782",
    "project_code": "OL-RSSOM-PWS-Live",
    "project_name": "OL-RSSOM-PWS-Live",
    "data_date": "2026-07-01 00:01:00",
    "planned_start": "2022-09-06 00:00:00",
    "planned_finished": "2031-05-27 17:00:00"
  },
  "project_root_name": "Ontario Line Subway RSSOM Project - Progress Works Schedule - Live",
  "activities": 23263,
  "relationships": 36521,
  "wbs": 5139,
  "calendars": 27,
  "statuses": {
    "complete": 14252,
    "not_started": 8367,
    "in_progress": 644
  },
  "types": {
    "task": 20067,
    "milestone": 357,
    "finish_milestone": 2772,
    "level_of_effort": 57,
    "tt_wbs": 10
  },
  "constraints": {
    "START_ON_OR_AFTER": 371,
    "FINISH_ON_OR_BEFORE": 241,
    "FINISH_ON_OR_AFTER": 71,
    "START_ON_OR_BEFORE": 1
  },
  "milestones": 3129,
  "relationship_types": {
    "FS": 31228,
    "SS": 2111,
    "FF": 3182
  },
  "positive_lag": 806,
  "negative_lag": 0,
  "open_starts": 7168,
  "open_finishes": 7200,
  "open_both": 7161,
  "open_either": 7207,
  "open_starts_by_status": {
    "complete": 7164,
    "in_progress": 3,
    "not_started": 1
  },
  "open_finishes_by_status": {
    "complete": 7160,
    "not_started": 3,
    "in_progress": 37
  },
  "float": {
    "missing": 14252,
    "positive": 8900,
    "zero": 77,
    "negative": 34
  },
  "activity_calendars": {
    "11683": {
      "name": "RSSOM 5d/w+H",
      "count": 18834
    },
    "3479": {
      "name": "RSSOM_7d/w (no holidays)",
      "count": 2467
    },
    "3489": {
      "name": "RSSOM_5d/w+H+Winter productivity (CJV)",
      "count": 752
    },
    "3490": {
      "name": "RSSOM_5d/w+H+Planting period",
      "count": 37
    },
    "15907": {
      "name": "RSSOM_5d/W+H+winter productivity 4/5 (CJV)",
      "count": 9
    },
    "10485": {
      "name": "RSSOM_5d/w+H",
      "count": 74
    },
    "3483": {
      "name": "RSSOM_5d/w+H+Winter block period",
      "count": 12
    },
    "3482": {
      "name": "RSSOM_7d/w+H",
      "count": 1
    },
    "3484": {
      "name": "RSSOM_5d/w+H+Winter productivity",
      "count": 20
    },
    "3487": {
      "name": "RSSOM_Quality",
      "count": 98
    },
    "3480": {
      "name": "RSSOM_5d/w+H-1",
      "count": 897
    },
    "13779": {
      "name": "RSSOM 5d/w+H+Italian August Shutdown",
      "count": 61
    },
    "3481": {
      "name": "RSSOM_6d/w+H",
      "count": 1
    }
  }
}
```
All 36,521 relationships have both internal endpoints; missing endpoint population is zero. All activities reference an available calendar. All 27 calendars now decode work periods. There are no imported external early/late boundary dates. The project contains one project record; its canonical project name is the short code, while the root WBS supplies the descriptive name above. Source TT_Mile denotes start milestones; the existing canonical label remains generic milestone. Constraint counts include primary and secondary entries (three secondary Finish On or Before).
This is useful genuine calibration evidence but exceeds current full-project scheduling capabilities. Unsupported conditions prevent end-to-end validation; a large source file alone does not certify P6 equivalence.
## SCHEDOPTIONS: observed values, not applied configuration

Read-only inspection of the raw table was used. SCHEDOPTIONS remains outside the canonical schedule model. No hidden option was enabled. The application diagnostic p6_scheduling_options_unobserved remains correct for what the engine itself receives; this investigation independently observes the raw options below.
| P6 field | Actual value | Application support | Expected impact / evidence |
|---|---|---|---|
| schedoptions_id | `1` | NOT_RELEVANT_TO_CURRENT_FILE | Record identity only. |
| proj_id | `782` | NOT_RELEVANT_TO_CURRENT_FILE | Record identity only. |
| sched_outer_depend_type | `SD_Both` | NOT_RELEVANT_TO_CURRENT_FILE | External dependency mode; no missing endpoints or imported external date boundaries observed. |
| sched_open_critical_flag | `N` | PARTIALLY_SUPPORTED | Open-end critical handling differs from per-component float classification; many open historical activities exist. |
| sched_lag_early_start_flag | `Y` | PARTIALLY_SUPPORTED | Simple SS early-start lag supported; P6 expired-lag treatment for progressed work is not reproduced. |
| sched_retained_logic | `Y` | UNSUPPORTED | Observed retained logic enabled; application remaining-from-Data-Date is a different progress policy. |
| sched_setplantoforecast | `N` | NOT_RELEVANT_TO_CURRENT_FILE | Disabled; application preserves imported planned dates. |
| sched_float_type | `FT_FF` | PARTIALLY_SUPPORTED | FT_FF indicates finish-float selection (raw-code interpretation); application primary TF is start-based and separately retains finish-based float. |
| sched_calendar_on_relationship_lag | `rcal_Predecessor` | SUPPORTED | Predecessor calendar matches current explicit lag policy. |
| sched_use_expect_end_flag | `Y` | UNSUPPORTED | Enabled with 720 populated Expected Finish dates; preserved but not used as a scheduling bound. |
| sched_progress_override | `N` | NOT_RELEVANT_TO_CURRENT_FILE | Disabled; do not activate progress override. |
| level_float_thrs_cnt | `0` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_outer_assign_flag | `N` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_outer_assign_priority | `5` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_over_alloc_pct | `25` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_within_float_flag | `N` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_keep_sched_date_flag | `Y` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| level_all_rsrc_flag | `Y` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
| sched_use_project_end_date_for_float | `Y` | PARTIALLY_SUPPORTED | Project-finish basis differs from default application independent-component anchors; no anchor selected after validation failure. |
| enable_multiple_longest_path_calc | `Y` | UNSUPPORTED | Enabled P6 multiple-float-path calculation is not the application controlling-chain definition. |
| limit_multiple_longest_path_calc | `Y` | UNSUPPORTED | P6 path limit does not configure application tracing. |
| max_multiple_longest_path | `10` | UNSUPPORTED | Source path limit 10; not applied. |
| use_total_float_multiple_longest_paths | `N` | UNSUPPORTED | N selects non-total-float path methodology; do not claim equivalence to application paths. |
| key_activity_for_multiple_longest_paths | `(blank)` | UNSUPPORTED | Blank ending key does not authorize an arbitrary application anchor. |
| LevelPriorityList | `priority_type,ASC_BY_FIELD/ASC` | NOT_RELEVANT_TO_CURRENT_FILE | Resource-leveling setting; no leveling implementation or evidence of a leveling run. |
PROJECT critical_path_type=CT_TotFloat; critical_drtn_hr_cnt=0. The imported critical proxy can therefore use TF <= 0 for this file (111 activities: 34 negative and 77 zero); 14,252 lack imported float. This is distinct from driving_path_flag. last_level_date is blank, and no TT_Rsrc activities are present. Leveling settings alone do not prove leveling occurred. Out-of-sequence behavior is a possible capability difference, not an established cause of an unavailable comparison.
Primary field/semantic references: [Oracle XER SCHEDOPTIONS](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/26/p6-xer-proj/schedoptions-scheduleoptions-97903a.html), [Oracle ScheduleOptions definitions](https://docs.oracle.com/cd/F74773_01/English/Integration_Documentation/p6_eppm_web_services_reference/42402.htm), and [Oracle scheduling options](https://docs.oracle.com/cd/G48897_01/p6help/en/90519.htm). Raw FT_FF expansion is an interpretation; the actual source token is preserved.
## Global imported-versus-calculated agreement

Variance convention is calculated minus imported, dates in elapsed hours and float in working hours. Existing tolerances remain 0 seconds and 0 hours. No tolerance or rounding altered any value. Because calculation fails validation, zero observations must not be reported as 0% agreement or 100% agreement.
| Metric | Imported present | Imported missing | Calculated missing | Comparable | Exact / within tolerance / different | Median / maximum absolute variance |
|---|---:|---:|---:|---:|---|---|
| ES | 23252 | 11 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
| EF | 23252 | 11 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
| LS | 23252 | 11 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
| LF | 23252 | 11 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
| TF | 9011 | 14252 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
| FF | 9011 | 14252 | 23263 | 0 | NOT_EVALUATED | NOT_EVALUATED |
Critical-state comparable population=0; agreements, application-only critical, P6-only critical and disagreement percentage are NOT_EVALUATED. Missing application classifications are not false/noncritical. There is no defensible global top-20 discrepancy ranking, calculated anchor, or application controlling path. The independent checks below must not be substituted for full CPM outputs.
## Independent calendar-only validation

Eligibility: not-started ordinary tasks with remaining duration and imported ES/EF; no primary/secondary constraints, Expected Finish, external date boundary or suspend/resume fields. Calculation: add_working_hours(activity_calendar, imported_ES, remaining_duration), compared to imported_EF. This is a local duration check using imported starts, not a recalculated network.
7,042 eligible activities; 7,019 exactly equal finishes; median absolute elapsed variance=0 hours. The other 23 comprise nine strictly working-time-equivalent boundaries (exactly zero work between finishes), and fourteen +/-0.0012-second residuals (raw +/-3.333333333333333e-07 hours) consistent with six-decimal duration-hour serialization and minute-resolution dates. All 14 residuals are retained; no rounding or tolerance was used to erase them. Maximum elapsed variance=87 hours across a holiday/weekend gap, with zero working variance. Thus calendar arithmetic appears aligned in this controlled population; this does not confirm all calendars, constraints or progress behavior.
Largest 20 calendar-only residuals, ordered by absolute elapsed variance, are below. These are not the unavailable full-project CPM mismatch ranking.
| Task ID / code | Calendar | Imported start | Duration h | P6 finish | Calendar finish | Exact elapsed variance h | Exact working variance h |
|---|---|---|---:|---|---|---:|---:|
| 1613568 / OL_RSSOM_530100 | 11683 | 2027-04-26 08:00:00 | 160.0 | 2027-05-25 08:00:00 | 2027-05-21 17:00:00 | -87.0 | -0.0 |
| 1614295 / OL_RSSOM_530630 | 11683 | 2027-02-26 08:00:00 | 160.0 | 2027-03-29 08:00:00 | 2027-03-25 17:00:00 | -87.0 | -0.0 |
| 1613913 / OL_RSSOM_530290 | 11683 | 2027-02-05 08:00:00 | 160.0 | 2027-03-08 08:00:00 | 2027-03-05 16:00:00 | -64.0 | -0.0 |
| 1613916 / OL_RSSOM_530320 | 11683 | 2027-03-05 08:00:00 | 160.0 | 2027-04-05 08:00:00 | 2027-04-02 16:00:00 | -64.0 | -0.0 |
| 1604867 / OL_RSSOM_DE_101330 | 11683 | 2030-11-29 08:00:00 | 152.0 | 2030-12-30 08:00:00 | 2030-12-27 16:00:00 | -64.0 | -0.0 |
| 1595892 / OL_RSSOM_13240 | 11683 | 2028-09-08 08:00:00 | 360.0 | 2028-11-13 08:00:00 | 2028-11-10 17:00:00 | -63.0 | -0.0 |
| 8804406 / OL_RSSOM_535210 | 11683 | 2028-09-08 08:00:00 | 360.0 | 2028-11-13 08:00:00 | 2028-11-10 17:00:00 | -63.0 | -0.0 |
| 8804412 / OL_RSSOM_535270 | 11683 | 2028-09-08 08:00:00 | 360.0 | 2028-11-13 08:00:00 | 2028-11-10 17:00:00 | -63.0 | -0.0 |
| 1596861 / OL_RSSOM_CN_510890 | 3489 | 2026-12-30 08:00:00 | 120.0 | 2027-02-03 08:00:00 | 2027-02-01 17:00:00 | -39.0 | -0.0 |
| 1612465 / OL_RSSOM_DE_539980 | 11683 | 2026-09-02 08:00:00 | 160.016667 | 2026-10-01 08:01:00 | 2026-10-01 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 4618606 / OL_RSSOM_DE_563542 | 11683 | 2026-09-01 08:00:00 | 640.033333 | 2026-12-24 08:02:00 | 2026-12-24 08:01:59.998800 | -3.333333333333333e-07 | -3.333333333333333e-07 |
| 4639473 / OL_RSSOM_DE_563730 | 11683 | 2026-09-01 08:00:00 | 640.016667 | 2026-12-24 08:01:00 | 2026-12-24 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 4639488 / OL_RSSOM_DE_563880 | 11683 | 2026-09-01 08:00:00 | 640.016667 | 2026-12-24 08:01:00 | 2026-12-24 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 4639503 / OL_RSSOM_DE_564030 | 11683 | 2026-09-01 08:00:00 | 640.016667 | 2026-12-24 08:01:00 | 2026-12-24 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 4639518 / OL_RSSOM_DE_564180 | 11683 | 2026-09-01 08:00:00 | 640.016667 | 2026-12-24 08:01:00 | 2026-12-24 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 4639533 / OL_RSSOM_DE_564330 | 11683 | 2026-09-01 08:00:00 | 640.016667 | 2026-12-24 08:01:00 | 2026-12-24 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 1612449 / OL_RSSOM_PR_509550 | 11683 | 2026-11-03 08:00:00 | 1120.016667 | 2027-05-26 08:01:00 | 2027-05-26 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 1613469 / OL_RSSOM_PR_512750 | 11683 | 2026-12-31 08:00:00 | 720.033333 | 2027-05-11 08:02:00 | 2027-05-11 08:01:59.998800 | -3.333333333333333e-07 | -3.333333333333333e-07 |
| 1613483 / OL_RSSOM_PR_512780 | 11683 | 2027-04-27 08:00:00 | 480.016667 | 2027-07-22 08:01:00 | 2027-07-22 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
| 5083194 / OL_RSSOM_PR_518950 | 11683 | 2027-01-14 08:00:00 | 320.016667 | 2027-03-12 08:01:00 | 2027-03-12 08:01:00.001200 | 3.333333333333333e-07 | 3.333333333333333e-07 |
Existing contract normalization remains unchanged: work periods are half-open; activity finishes may equal a closing instant. Do not shift application finishes to next work openings merely to match P6. The nine equivalent boundaries have next_working_time(calendar_finish)==P6_finish. The 14 duration serialization residuals are evidence of source precision, not a demonstrated calculation defect.
## Local relationship requirement validation

Only not-started ordinary task-to-task relationships with complete imported dates and no endpoint constraints/Expected Finish were eligible. Imported predecessor dates and successor remaining duration were passed through the current relationship function, using predecessor-calendar lag, then successor-calendar start normalization. Satisfied means imported successor start is at or after that local application requirement. Other predecessors can legitimately make successor starts later. This is not a full network calculation or proof of driving control.
| Type / lag | Population | Satisfied raw bound | Exact lower bound | Earlier than raw bound |
|---|---:|---:|---:|---:|
| FS_zero | 11673 | 11673 | 5695 | 0 |
| SS_zero | 417 | 417 | 352 | 0 |
| FF_zero | 482 | 479 | 213 | 3 |
| FS_positive | 15 | 15 | 12 | 0 |
| SS_positive | 177 | 177 | 74 | 0 |
| FF_positive | 35 | 34 | 30 | 1 |
Representative imported endpoints, calendars, lag and application requirement:
```json
{
  "FS_zero": {
    "id": "10022545",
    "pre_id": "1598051",
    "pre_code": "OL_RSSOM_CN_113770",
    "suc_id": "1598052",
    "suc_code": "OL_RSSOM_CN_113780",
    "type": "FS",
    "lag": 0.0,
    "lag_calendar": "11683",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "pre_es": "2028-07-24 08:00:00",
    "pre_ef": "2028-11-01 17:00:00",
    "suc_es": "2028-11-02 08:00:00",
    "suc_ef": "2028-11-15 17:00:00",
    "application_requirement": "2028-11-02 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  },
  "SS_zero": {
    "id": "13966377",
    "pre_id": "1596882",
    "pre_code": "OL_RSSOM_CN_503810",
    "suc_id": "1596883",
    "suc_code": "OL_RSSOM_CN_503940",
    "type": "SS",
    "lag": 0.0,
    "lag_calendar": "11683",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "pre_es": "2028-03-13 08:00:00",
    "pre_ef": "2028-03-29 17:00:00",
    "suc_es": "2028-03-13 08:00:00",
    "suc_ef": "2028-03-29 17:00:00",
    "application_requirement": "2028-03-13 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  },
  "FF_zero": {
    "id": "15127978",
    "pre_id": "1600031",
    "pre_code": "OL_RSSOM_CN_515240",
    "suc_id": "1595844",
    "suc_code": "OL_RSSOM_12760",
    "type": "FF",
    "lag": 0.0,
    "lag_calendar": "11683",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "pre_es": "2029-01-04 08:00:00",
    "pre_ef": "2029-01-12 16:00:00",
    "suc_es": "2028-11-08 08:00:00",
    "suc_ef": "2029-01-12 16:00:00",
    "application_requirement": "2028-11-08 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  },
  "FS_positive": {
    "id": "29057294",
    "pre_id": "1607058",
    "pre_code": "OL_RSSOM_PR_503670",
    "suc_id": "1607054",
    "suc_code": "OL_RSSOM_CN_500070",
    "type": "FS",
    "lag": 480.0,
    "lag_calendar": "3479",
    "pre_calendar": "3479",
    "suc_calendar": "3479",
    "pre_es": "2027-04-12 08:00:00",
    "pre_ef": "2027-05-11 17:00:00",
    "suc_es": "2027-07-11 08:00:00",
    "suc_ef": "2027-11-07 17:00:00",
    "application_requirement": "2027-07-11 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  },
  "SS_positive": {
    "id": "22912140",
    "pre_id": "1614161",
    "pre_code": "OL_RSSOM_530440",
    "suc_id": "1606995",
    "suc_code": "OL_RSSOM_PR_504310",
    "type": "SS",
    "lag": 264.0,
    "lag_calendar": "3479",
    "pre_calendar": "3479",
    "suc_calendar": "3479",
    "pre_es": "2026-07-01 08:00:00",
    "pre_ef": "2026-09-30 17:00:00",
    "suc_es": "2026-08-03 08:00:00",
    "suc_ef": "2026-09-16 17:00:00",
    "application_requirement": "2026-08-03 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  },
  "FF_positive": {
    "id": "15681536",
    "pre_id": "1595849",
    "pre_code": "OL_RSSOM_12810",
    "suc_id": "1595850",
    "suc_code": "OL_RSSOM_12880",
    "type": "FF",
    "lag": 200.0,
    "lag_calendar": "11683",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "pre_es": "2029-06-11 08:00:00",
    "pre_ef": "2029-06-12 17:00:00",
    "suc_es": "2029-05-15 08:00:00",
    "suc_ef": "2029-07-18 17:00:00",
    "application_requirement": "2029-05-15 08:00:00",
    "elapsed_slack_hours": 0.0,
    "satisfied": true
  }
}
```
All four earlier-than-bound observations are exactly one microsecond at non-working discontinuities. The protected contract explicitly chooses the earliest discrete working start whose computed finish meets the raw FF bound. P6 instead stores a later work-opening finish for an otherwise equivalent duration boundary. This is a documented methodology/representation difference, not evidence justifying a formula change. Exact records follow; no tolerance hides the difference.
```json
[
  {
    "relationship_id": "3540853",
    "predecessor_id": "1613516",
    "predecessor_code": "OL_RSSOM_529950",
    "successor_id": "1613568",
    "successor_code": "OL_RSSOM_530100",
    "lag": 0.0,
    "pre_finish": "2027-05-23 17:00:00",
    "successor_start": "2027-04-26 08:00:00",
    "successor_finish": "2027-05-25 08:00:00",
    "application_start_requirement": "2027-04-26 08:00:00.000001",
    "elapsed_slack_hours": -2.7777777777777777e-10,
    "working_slack_hours": -2.7777777777777777e-10,
    "calendars": [
      "3479",
      "11683"
    ],
    "remaining": 160.0
  },
  {
    "relationship_id": "3543397",
    "predecessor_id": "1614292",
    "predecessor_code": "OL_RSSOM_530600",
    "successor_id": "1614295",
    "successor_code": "OL_RSSOM_530630",
    "lag": 0.0,
    "pre_finish": "2027-03-26 17:00:00",
    "successor_start": "2027-02-26 08:00:00",
    "successor_finish": "2027-03-29 08:00:00",
    "application_start_requirement": "2027-02-26 08:00:00.000001",
    "elapsed_slack_hours": -2.7777777777777777e-10,
    "working_slack_hours": -2.7777777777777777e-10,
    "calendars": [
      "3479",
      "11683"
    ],
    "remaining": 160.0
  },
  {
    "relationship_id": "29057259",
    "predecessor_id": "1596855",
    "predecessor_code": "OL_RSSOM_CN_512240",
    "successor_id": "1596861",
    "successor_code": "OL_RSSOM_CN_510890",
    "lag": 40.0,
    "pre_finish": "2027-01-26 17:00:00",
    "successor_start": "2026-12-30 08:00:00",
    "successor_finish": "2027-02-03 08:00:00",
    "application_start_requirement": "2026-12-30 08:00:00.000001",
    "elapsed_slack_hours": -2.7777777777777777e-10,
    "working_slack_hours": -2.7777777777777777e-10,
    "calendars": [
      "11683",
      "3489"
    ],
    "remaining": 120.0
  },
  {
    "relationship_id": "37691053",
    "predecessor_id": "1613912",
    "predecessor_code": "OL_RSSOM_530270",
    "successor_id": "1613916",
    "successor_code": "OL_RSSOM_530320",
    "lag": 0.0,
    "pre_finish": "2027-04-04 17:00:00",
    "successor_start": "2027-03-05 08:00:00",
    "successor_finish": "2027-04-05 08:00:00",
    "application_start_requirement": "2027-03-05 08:00:00.000001",
    "elapsed_slack_hours": -2.7777777777777777e-10,
    "working_slack_hours": -2.7777777777777777e-10,
    "calendars": [
      "3479",
      "11683"
    ],
    "remaining": 160.0
  }
]
```
No SF or negative-lag relationships occur in this source; those capabilities remain supported by synthetic tests but are NOT_CONFIRMED by this project.
## Progress and constraints

```json
{
  "in_progress": 644,
  "early_start_equals_actual_start": 0,
  "early_start_before_data_date": 0,
  "restart_present": 644,
  "restart_at_or_after_data_date": 644,
  "expected_finish_by_status": {
    "in_progress": 519,
    "not_started": 201
  },
  "not_started_early_before_data_date": 0,
  "samples": [
    {
      "id": "1596231",
      "code": "OL_RSSOM_10110",
      "status": "complete",
      "actual_start": "2024-05-23 00:00:00",
      "actual_finish": "2024-05-28 00:00:00",
      "data_date": "2026-07-01 00:01:00",
      "remaining": 0.0,
      "early_start": "2026-07-01 00:01:00",
      "early_finish": "2026-07-01 00:01:00",
      "restart": "",
      "reend": ""
    },
    {
      "id": "1596232",
      "code": "OL_RSSOM_10120",
      "status": "complete",
      "actual_start": "2024-05-28 00:00:00",
      "actual_finish": "2024-06-26 00:00:00",
      "data_date": "2026-07-01 00:01:00",
      "remaining": 0.0,
      "early_start": "2026-07-01 00:01:00",
      "early_finish": "2026-07-01 00:01:00",
      "restart": "",
      "reend": ""
    },
    {
      "id": "1596233",
      "code": "OL_RSSOM_10130",
      "status": "complete",
      "actual_start": "2024-09-16 00:00:00",
      "actual_finish": "2024-09-20 00:00:00",
      "data_date": "2026-07-01 00:01:00",
      "remaining": 0.0,
      "early_start": "2026-07-01 00:01:00",
      "early_finish": "2026-07-01 00:01:00",
      "restart": "",
      "reend": ""
    },
    {
      "id": "1606794",
      "code": "1OL_RSSOM_PR_500000",
      "status": "in_progress",
      "actual_start": "2026-05-26 08:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 696.0,
      "early_start": "2026-07-01 08:00:00",
      "early_finish": "2026-09-25 17:00:00",
      "restart": "2026-07-01 08:00",
      "reend": "2026-09-25 17:00"
    },
    {
      "id": "1595673",
      "code": "OL_RSSOM_10400",
      "status": "in_progress",
      "actual_start": "2024-12-13 16:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 776.0,
      "early_start": "2026-09-29 08:00:00",
      "early_finish": "2027-02-17 17:00:00",
      "restart": "2026-09-29 08:00",
      "reend": "2027-02-17 17:00"
    },
    {
      "id": "1595818",
      "code": "OL_RSSOM_12560",
      "status": "in_progress",
      "actual_start": "2024-12-09 00:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 776.0,
      "early_start": "2026-09-29 08:00:00",
      "early_finish": "2027-02-17 17:00:00",
      "restart": "2026-09-29 08:00",
      "reend": "2027-02-17 17:00"
    },
    {
      "id": "1595674",
      "code": "OL_RSSOM_10410",
      "status": "not_started",
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 16.0,
      "early_start": "2027-02-18 08:00:00",
      "early_finish": "2027-02-19 16:00:00",
      "restart": "2027-02-18 08:00",
      "reend": "2027-02-19 16:00"
    },
    {
      "id": "1595712",
      "code": "OL_RSSOM_11080",
      "status": "not_started",
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 360.0,
      "early_start": "2028-06-15 08:00:00",
      "early_finish": "2028-08-18 17:00:00",
      "restart": "2028-06-15 08:00",
      "reend": "2028-08-18 17:00"
    },
    {
      "id": "1595713",
      "code": "OL_RSSOM_11090",
      "status": "not_started",
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "remaining": 40.0,
      "early_start": "2028-08-21 08:00:00",
      "early_finish": "2028-08-25 17:00:00",
      "restart": "2028-08-21 08:00",
      "reend": "2028-08-25 17:00"
    }
  ]
}
```
All 644 in-progress imported early starts are on/after Data Date, differ from Actual Start, and have Remaining Start/restart dates on/after Data Date. This is consistent with remaining-work dates but does not establish equivalence to the application progress policy: retained logic and enabled Expected Finish are known capability differences. Expected Finish occurs on 519 in-progress and 201 not-started activities. Complete-task samples have historical actual spans but imported early dates at Data Date; comparing those imported early dates directly with preserved actual spans would mix different semantics. Application policy preserves actuals; no completed work was rescheduled or overwritten. No comprehensive out-of-sequence progress cause was proven.
```json
{
  "START_ON_OR_AFTER": {
    "count": 371,
    "by_status": {
      "complete": 116,
      "not_started": 255
    },
    "raw_type": "CS_MSOA",
    "example": {
      "id": "1596011",
      "code": "OL_RSSOM_CN_100260",
      "status": "not_started",
      "primary_type": "START_ON_OR_AFTER",
      "primary_date": "2025-01-01 00:00:00",
      "secondary_type": null,
      "secondary_date": null,
      "es": "2026-07-01 08:00:00",
      "ef": "2026-07-01 08:00:00",
      "ls": "2030-09-10 08:00:00",
      "lf": "2030-09-10 08:00:00",
      "restart": "2026-07-01 08:00"
    },
    "application_support": "SUPPORTED",
    "real_full_calculation_confirmation": "NOT_CONFIRMED"
  },
  "FINISH_ON_OR_BEFORE": {
    "count": 241,
    "by_status": {
      "complete": 172,
      "not_started": 49,
      "in_progress": 20
    },
    "raw_type": "CS_MEOB",
    "example": {
      "id": "1596816",
      "code": "OL_RSSOM_CN_528740",
      "status": "not_started",
      "primary_type": "FINISH_ON_OR_BEFORE",
      "primary_date": "2029-01-26 08:01:00",
      "secondary_type": null,
      "secondary_date": null,
      "es": "2028-05-12 08:00:00",
      "ef": "2028-05-18 17:00:00",
      "ls": "2028-06-19 08:00:00",
      "lf": "2028-06-23 17:00:00",
      "restart": "2028-05-12 08:00"
    },
    "application_support": "SUPPORTED",
    "real_full_calculation_confirmation": "NOT_CONFIRMED"
  },
  "FINISH_ON_OR_AFTER": {
    "count": 71,
    "by_status": {
      "complete": 55,
      "not_started": 16
    },
    "raw_type": "CS_MEOA",
    "example": {
      "id": "1599062",
      "code": "OL_RSSOM_CN_113740",
      "status": "not_started",
      "primary_type": "FINISH_ON_OR_AFTER",
      "primary_date": "2030-06-01 17:00:00",
      "secondary_type": null,
      "secondary_date": null,
      "es": "2030-06-01 17:00:00",
      "ef": "2030-06-01 17:00:00",
      "ls": "2030-06-17 17:00:00",
      "lf": "2030-06-17 17:00:00",
      "restart": "2030-06-01 17:00"
    },
    "application_support": "UNSUPPORTED",
    "real_full_calculation_confirmation": "NOT_CONFIRMED"
  },
  "START_ON_OR_BEFORE": {
    "count": 1,
    "by_status": {
      "complete": 1
    },
    "raw_type": "CS_MSOB",
    "example": {
      "id": "1598944",
      "code": "OL_RSSOM_CN_100030",
      "status": "complete",
      "primary_type": "START_ON_OR_BEFORE",
      "primary_date": "2023-10-01 00:00:00",
      "secondary_type": null,
      "secondary_date": null,
      "es": "2026-07-01 00:01:00",
      "ef": "2026-07-01 00:01:00",
      "ls": "2026-10-12 08:00:00",
      "lf": "2026-10-12 08:00:00",
      "restart": ""
    },
    "application_support": "UNSUPPORTED",
    "real_full_calculation_confirmation": "NOT_CONFIRMED"
  }
}
```
Start On or After and Finish On or Before identities/math remain synthetically supported, but full-project real confirmation is NOT_CONFIRMED because validation rejects the network first. Finish On or After and Start On or Before remain unsupported, including historical completed constraints under current conservative validation. No behavior is classified INCORRECT merely because the capability is absent. Supporting them or deciding to ignore historical constraints requires an explicit future contract decision and focused tests, rather than removal to improve agreement.
## Completion anchor and path findings

```json
{
  "application_selected_anchor": null,
  "reason": "Calculation rejected before anchor selection",
  "terminal_candidates": 7200,
  "p6_project_plan_end_date": "",
  "p6_project_scheduled_end": "2031-05-27 17:00",
  "latest_imported_activity_finish": "2031-05-27 17:00:00",
  "latest_terminal_samples": [
    {
      "id": "1600284",
      "code": "OL_RSSOM_WM_100160",
      "name": "(vii) Completion of the Ontario Line Subway",
      "type": "finish_milestone",
      "finish": "2031-05-27 17:00:00",
      "tf": 0.0
    },
    {
      "id": "1611815",
      "code": "OL_RSSOM_DE_500160",
      "name": "S-172_p - ENV_SUBM - Environmental Conditions Summary - Development & Submission - CONTINUOUS",
      "type": "level_of_effort",
      "finish": "2031-04-02 17:00:00",
      "tf": 440.0
    },
    {
      "id": "1611856",
      "code": "OL_RSSOM_DE_500080",
      "name": "S-172_h - ENV_SUBM - Doc. demonstrating qualification of Independent Env. Cons. - Development & Submission - CONTINUOUS",
      "type": "level_of_effort",
      "finish": "2031-04-02 17:00:00",
      "tf": 440.0
    },
    {
      "id": "1611846",
      "code": "OL_RSSOM_DE_500030",
      "name": "S-172_c - ENV_SUBM - Demonstration of qualification of Environmental Position - Development & Submission - CONTINUOUS",
      "type": "level_of_effort",
      "finish": "2031-04-02 17:00:00",
      "tf": 440.0
    },
    {
      "id": "1611795",
      "code": "OL_RSSOM_DE_100320",
      "name": "S-172 - Environmental Management System - Development & Submission - CONTINUOUS",
      "type": "level_of_effort",
      "finish": "2031-04-02 17:00:00",
      "tf": 440.0
    }
  ],
  "p6_driving_flag": {
    "N": 23191,
    "Y": 72
  },
  "p6_float_paths": {
    "": 23196,
    "1": 37,
    "6": 22,
    "7": 1,
    "8": 1,
    "10": 1,
    "9": 1,
    "3": 1,
    "4": 1,
    "5": 1,
    "2": 1
  }
}
```
The imported latest terminal completion milestone is an evidence-based candidate, not an automatically selected new anchor. PROJECT.plan_end_date is blank; scd_end_date is a scheduled finish, not an explicit required finish. 7,200 terminals (many historical/disconnected) preclude arbitrary anchor selection. The application never reached anchor selection. No APPLICATION_CALCULATED_CONTROLLING_PATH was emitted; 72 P6 driving flags and 67 nonblank float-path tags are source evidence only, not proof of P6 Longest Path equivalence.
## Discrepancy categories and evidence limits

| Category | Evidence | Conclusion |
|---|---|---|
| APPLICATION_IMPORT_DEFECT | All 27 calendars decoded empty; five observed aliases incorrect/missing; failed synthetic reproductions | Proven and corrected decoding/normalization defects |
| CONSTRAINT_HANDLING | 71 Finish On or After, one Start On or Before validation errors | Proven reason calculation is rejected, not quantified date variance |
| UNSUPPORTED_P6_OPTION | Retained logic/Expected Finish/multiple float paths enabled; ten WBS summaries, 57 LOE | Capability gaps; unsupported activity types also reject calculation |
| HARMLESS_METHODOLOGY_DIFFERENCE | Nine zero-working-hour finish boundaries; four FF one-tick inverse requirements | Documented representation difference in local checks |
| SOURCE_PRECISION | 14 residuals of +/-0.0012s with six-decimal duration hours | Precision explanation supported by values; no rounding applied |
| STATUS_PROGRESS_TREATMENT | 644 progressed tasks; completed early dates differ from actual spans | Possible future comparison cause, not measured global variance |
| LAG_CALENDAR_POLICY | Source predecessor lag agrees with config | No mismatch demonstrated for selected local checks |
| EXPECTED_FINISH | Enabled; 720 values | Possible future discrepancy cause; not applied |
| OPEN_END | 7,168 open starts, 7,200 open finishes | Proven topology; effect on unavailable float not quantified |
| COMPLETION_ANCHOR_DIFFERENCE | P6 scheduled finish vs independent components; no selected app anchor | Possible capability/configuration difference |
| MULTIPLE_FLOAT_PATH_BEHAVIOR | P6 paths enabled, limit10, non-total-float mode | Source/config difference; no path equality claim |
| EXTERNAL_RELATIONSHIP | No missing endpoints or external date bounds | No supporting current-file evidence |
| OUT_OF_SEQUENCE_PROGRESS | Retained logic enabled, progressed population present | Hypothesis only; no specific mismatch proven |
| CALENDAR_DIFFERENCE / UNKNOWN | No remaining substantial local duration mismatch | Do not invent causes for missing global outputs |
Most negative imported activities (audit priorities, NOT calculated discrepancy ranking):
```json
[
  {
    "id": "1606403",
    "code": "OL_RSSOM_DE_509370",
    "name": "South Civil - S-111A - Stations \ufffd Structural - Cherry Street EEB",
    "tf": -7984.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606568",
    "code": "OL_RSSOM_DE_511330",
    "name": "South Civil - S-201 - Stray Current and Corrosion Control Plan - General",
    "tf": -7616.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606546",
    "code": "OL_RSSOM_DE_510300",
    "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Liberty New Street",
    "tf": -7216.0,
    "ff": 0.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606413",
    "code": "OL_RSSOM_DE_510510",
    "name": "South Civil - S-111B - Stations \ufffd Structural - Cherry Street EEB",
    "tf": -7168.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606461",
    "code": "OL_RSSOM_DE_510750",
    "name": "South Civil - S-114B - Civil Structure \ufffd Building, Retaining Walls, Box Culverts - Liberty New Street",
    "tf": -6968.0,
    "ff": 2880.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606510",
    "code": "OL_RSSOM_DE_510050",
    "name": "South Civil - S-139A - Code Compliance Summary Preliminary Plan - Tunnels",
    "tf": -6488.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606534",
    "code": "OL_RSSOM_DE_510180",
    "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Tunnels",
    "tf": -6488.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606559",
    "code": "OL_RSSOM_DE_511240",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Liberty New Street",
    "tf": -6400.0,
    "ff": 2720.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606544",
    "code": "OL_RSSOM_DE_510280",
    "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Cherry Street EEB",
    "tf": -6000.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606404",
    "code": "OL_RSSOM_DE_510400",
    "name": "South Civil - S-111B - Stations \ufffd Structural - Exhibition Station",
    "tf": -5680.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606556",
    "code": "OL_RSSOM_DE_511210",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Ordnance Park EEB",
    "tf": -5424.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606547",
    "code": "OL_RSSOM_DE_511120",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Tunnels",
    "tf": -5416.0,
    "ff": 2720.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606555",
    "code": "OL_RSSOM_DE_511200",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Exhibition Portal/ESB",
    "tf": -5184.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606548",
    "code": "OL_RSSOM_DE_511130",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Exhibition Station",
    "tf": -5176.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606557",
    "code": "OL_RSSOM_DE_511220",
    "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Cherry Street EEB",
    "tf": -5168.0,
    "ff": 2720.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606423",
    "code": "OL_RSSOM_DE_509500",
    "name": "South Civil - S-112A - Stations and Facilities \ufffd Mechanical - Cherry Street EEB",
    "tf": -5016.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606445",
    "code": "OL_RSSOM_DE_509630",
    "name": "South Civil - S-113A - Stations and Facilities \ufffd Electrical - Cherry Street EEB",
    "tf": -5016.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606520",
    "code": "OL_RSSOM_DE_510150",
    "name": "South Civil - S-139A - Code Compliance Summary Preliminary Plan - Cherry Street EEB",
    "tf": -5016.0,
    "ff": 0.0,
    "status": "not_started",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606460",
    "code": "OL_RSSOM_DE_510740",
    "name": "South Civil - S-114B - Civil Structure \ufffd Building, Retaining Walls, Box Culverts - Ordnance Park EEB",
    "tf": -5008.0,
    "ff": 2880.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  },
  {
    "id": "1606570",
    "code": "OL_RSSOM_DE_511350",
    "name": "South Civil - S-208 - Soil Resistivity Survey - General",
    "tf": -4688.0,
    "ff": 2960.0,
    "status": "in_progress",
    "constraint": "FINISH_ON_OR_BEFORE"
  }
]
```
## Traceable activity evidence

The following source evidence covers the largest calendar residuals, most negative imported float, and representative constraints/unsupported types. Missing calculated dates, controlling predecessors/successors and anchor are explicitly null because the calculation failed. Constraint control is not fabricated as a relationship. Hypotheses are labeled rather than claimed as causes.
### 1606403 / OL_RSSOM_DE_509370

```json
{
  "task_id": "1606403",
  "activity_code": "OL_RSSOM_DE_509370",
  "name": "South Civil - S-111A - Stations \ufffd Structural - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.2.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 2880.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2027-06-25 17:00:00",
    "late_start": "2023-10-07 08:00:00",
    "late_finish": "2024-09-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -7984.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-09-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3543599",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "1606403",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522947",
      "predecessor_activity_id": "1606403",
      "successor_activity_id": "1606413",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-09-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606568 / OL_RSSOM_DE_511330

```json
{
  "task_id": "1606568",
  "activity_code": "OL_RSSOM_DE_511330",
  "name": "South Civil - S-201 - Stray Current and Corrosion Control Plan - General",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.12",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2023-11-22 08:00:00",
    "late_finish": "2023-12-01 17:00:00",
    "actual_start": "2024-03-18 00:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -7616.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2023-12-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523055",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606568",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522926",
      "predecessor_activity_id": "1606568",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606568",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2023-12-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606546 / OL_RSSOM_DE_510300

```json
{
  "task_id": "1606546",
  "activity_code": "OL_RSSOM_DE_510300",
  "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Liberty New Street",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.1",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-01-11 08:00:00",
    "late_finish": "2024-01-30 17:00:00",
    "actual_start": "2025-04-14 08:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -7216.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-01-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523034",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606546",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3523007",
      "predecessor_activity_id": "1606546",
      "successor_activity_id": "1606559",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606546",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-01-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606413 / OL_RSSOM_DE_510510

```json
{
  "task_id": "1606413",
  "activity_code": "OL_RSSOM_DE_510510",
  "name": "South Civil - S-111B - Stations \ufffd Structural - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.2.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2027-06-26 08:00:00",
    "early_finish": "2027-07-15 17:00:00",
    "late_start": "2025-01-11 08:00:00",
    "late_finish": "2025-01-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -7168.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2025-01-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3522947",
      "predecessor_activity_id": "1606403",
      "successor_activity_id": "1606413",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522842",
      "predecessor_activity_id": "1606413",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2025-01-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606461 / OL_RSSOM_DE_510750

```json
{
  "task_id": "1606461",
  "activity_code": "OL_RSSOM_DE_510750",
  "name": "South Civil - S-114B - Civil Structure \ufffd Building, Retaining Walls, Box Culverts - Liberty New Street",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.5.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-02-11 08:00:00",
    "late_finish": "2024-03-01 17:00:00",
    "actual_start": "2024-08-08 00:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -6968.0,
  "imported_ff": 2880.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-03-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3522969",
      "predecessor_activity_id": "1606459",
      "successor_activity_id": "1606461",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522867",
      "predecessor_activity_id": "1606461",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606461",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-03-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606510 / OL_RSSOM_DE_510050

```json
{
  "task_id": "1606510",
  "activity_code": "OL_RSSOM_DE_510050",
  "name": "South Civil - S-139A - Code Compliance Summary Preliminary Plan - Tunnels",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.8.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-04-11 08:00:00",
    "late_finish": "2024-04-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -6488.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-04-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523022",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606510",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522995",
      "predecessor_activity_id": "1606510",
      "successor_activity_id": "1606522",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-04-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606534 / OL_RSSOM_DE_510180

```json
{
  "task_id": "1606534",
  "activity_code": "OL_RSSOM_DE_510180",
  "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Tunnels",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-04-11 08:00:00",
    "late_finish": "2024-04-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -6488.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-04-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523042",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606534",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3523015",
      "predecessor_activity_id": "1606534",
      "successor_activity_id": "1606547",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-04-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606559 / OL_RSSOM_DE_511240

```json
{
  "task_id": "1606559",
  "activity_code": "OL_RSSOM_DE_511240",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Liberty New Street",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-21 08:00:00",
    "early_finish": "2026-08-09 17:00:00",
    "late_start": "2024-05-12 08:00:00",
    "late_finish": "2024-05-31 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -6400.0,
  "imported_ff": 2720.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-05-31 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523007",
      "predecessor_activity_id": "1606546",
      "successor_activity_id": "1606559",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522905",
      "predecessor_activity_id": "1606559",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-05-31 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606544 / OL_RSSOM_DE_510280

```json
{
  "task_id": "1606544",
  "activity_code": "OL_RSSOM_DE_510280",
  "name": "South Civil - S-154A - Drainage and Stormwater Design Development - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-06-11 08:00:00",
    "late_finish": "2024-06-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -6000.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-06-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523045",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606544",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3523018",
      "predecessor_activity_id": "1606544",
      "successor_activity_id": "1606557",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-06-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606404 / OL_RSSOM_DE_510400

```json
{
  "task_id": "1606404",
  "activity_code": "OL_RSSOM_DE_510400",
  "name": "South Civil - S-111B - Stations \ufffd Structural - Exhibition Station",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.2.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2024-07-21 08:00:00",
    "late_finish": "2024-07-30 17:00:00",
    "actual_start": "2025-07-29 08:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5680.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-07-31 08:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3522938",
      "predecessor_activity_id": "1606394",
      "successor_activity_id": "1606404",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522835",
      "predecessor_activity_id": "1606404",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606404",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-07-31 08:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606556 / OL_RSSOM_DE_511210

```json
{
  "task_id": "1606556",
  "activity_code": "OL_RSSOM_DE_511210",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Ordnance Park EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2024-08-22 08:00:00",
    "late_finish": "2024-08-31 17:00:00",
    "actual_start": "2025-07-29 08:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5424.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-08-31 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523013",
      "predecessor_activity_id": "1606543",
      "successor_activity_id": "1606556",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522911",
      "predecessor_activity_id": "1606556",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606556",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-08-31 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606547 / OL_RSSOM_DE_511120

```json
{
  "task_id": "1606547",
  "activity_code": "OL_RSSOM_DE_511120",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Tunnels",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-21 08:00:00",
    "early_finish": "2026-08-09 17:00:00",
    "late_start": "2024-09-12 08:00:00",
    "late_finish": "2024-10-01 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5416.0,
  "imported_ff": 2720.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-10-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523015",
      "predecessor_activity_id": "1606534",
      "successor_activity_id": "1606547",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522914",
      "predecessor_activity_id": "1606547",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-10-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606555 / OL_RSSOM_DE_511200

```json
{
  "task_id": "1606555",
  "activity_code": "OL_RSSOM_DE_511200",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Exhibition Portal/ESB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2024-09-21 08:00:00",
    "late_finish": "2024-09-30 17:00:00",
    "actual_start": "2025-07-29 08:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5184.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-09-30 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523017",
      "predecessor_activity_id": "1606542",
      "successor_activity_id": "1606555",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522913",
      "predecessor_activity_id": "1606555",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606555",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-09-30 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606548 / OL_RSSOM_DE_511130

```json
{
  "task_id": "1606548",
  "activity_code": "OL_RSSOM_DE_511130",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Exhibition Station",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2024-09-22 08:00:00",
    "late_finish": "2024-10-01 17:00:00",
    "actual_start": "2025-07-29 00:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5176.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-10-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523016",
      "predecessor_activity_id": "1606535",
      "successor_activity_id": "1606548",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522915",
      "predecessor_activity_id": "1606548",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606548",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-10-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606557 / OL_RSSOM_DE_511220

```json
{
  "task_id": "1606557",
  "activity_code": "OL_RSSOM_DE_511220",
  "name": "South Civil - S-154B - Drainage and Stormwater Design Development - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.9.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-21 08:00:00",
    "early_finish": "2026-08-09 17:00:00",
    "late_start": "2024-10-13 08:00:00",
    "late_finish": "2024-11-01 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5168.0,
  "imported_ff": 2720.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-11-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523018",
      "predecessor_activity_id": "1606544",
      "successor_activity_id": "1606557",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522916",
      "predecessor_activity_id": "1606557",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-11-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606423 / OL_RSSOM_DE_509500

```json
{
  "task_id": "1606423",
  "activity_code": "OL_RSSOM_DE_509500",
  "name": "South Civil - S-112A - Stations and Facilities \ufffd Mechanical - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.3.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-10-12 08:00:00",
    "late_finish": "2024-10-31 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5016.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-10-31 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3536849",
      "predecessor_activity_id": "1603599",
      "successor_activity_id": "1606423",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522957",
      "predecessor_activity_id": "1606423",
      "successor_activity_id": "1606434",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-10-31 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606445 / OL_RSSOM_DE_509630

```json
{
  "task_id": "1606445",
  "activity_code": "OL_RSSOM_DE_509630",
  "name": "South Civil - S-113A - Stations and Facilities \ufffd Electrical - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.4.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-10-12 08:00:00",
    "late_finish": "2024-10-31 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5016.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-10-31 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3543600",
      "predecessor_activity_id": "1602594",
      "successor_activity_id": "1606445",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522967",
      "predecessor_activity_id": "1606445",
      "successor_activity_id": "1606456",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-10-31 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606520 / OL_RSSOM_DE_510150

```json
{
  "task_id": "1606520",
  "activity_code": "OL_RSSOM_DE_510150",
  "name": "South Civil - S-139A - Code Compliance Summary Preliminary Plan - Cherry Street EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.8.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-10-12 08:00:00",
    "late_finish": "2024-10-31 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5016.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-10-31 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523032",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606520",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3523005",
      "predecessor_activity_id": "1606520",
      "successor_activity_id": "1606532",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-10-31 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1606460 / OL_RSSOM_DE_510740

```json
{
  "task_id": "1606460",
  "activity_code": "OL_RSSOM_DE_510740",
  "name": "South Civil - S-114B - Civil Structure \ufffd Building, Retaining Walls, Box Culverts - Ordnance Park EEB",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.5.2",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-20 17:00:00",
    "late_start": "2024-10-13 08:00:00",
    "late_finish": "2024-11-01 17:00:00",
    "actual_start": "2025-04-14 08:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -5008.0,
  "imported_ff": 2880.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-11-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3522970",
      "predecessor_activity_id": "1606458",
      "successor_activity_id": "1606460",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522868",
      "predecessor_activity_id": "1606460",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606460",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-11-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1606570 / OL_RSSOM_DE_511350

```json
{
  "task_id": "1606570",
  "activity_code": "OL_RSSOM_DE_511350",
  "name": "South Civil - S-208 - Soil Resistivity Survey - General",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.DH.1.4.14",
  "status": "in_progress",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 80.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-10 17:00:00",
    "late_start": "2024-11-22 08:00:00",
    "late_finish": "2024-12-01 17:00:00",
    "actual_start": "2024-08-26 00:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": -4688.0,
  "imported_ff": 2960.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2024-12-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3523057",
      "predecessor_activity_id": "1606370",
      "successor_activity_id": "1606570",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3522928",
      "predecessor_activity_id": "1606570",
      "successor_activity_id": "1606371",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "planned_start_before_data_date",
      "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
      "severity": "INFORMATIONAL",
      "activity_id": "1606570",
      "relationship_id": null,
      "metadata": {
        "disposition": "INFORMATIONAL"
      }
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2024-12-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    }
  ]
}
```
### 1613568 / OL_RSSOM_530100

```json
{
  "task_id": "1613568",
  "activity_code": "OL_RSSOM_530100",
  "name": "FAI and Type Test - S-215 - Train Heating, Ventilation and Air Conditioning System - Train 1",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.3.6",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2027-04-26 08:00:00",
    "early_finish": "2027-05-25 08:00:00",
    "late_start": "2027-07-08 08:00:00",
    "late_finish": "2027-08-05 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 408.0,
  "imported_ff": 112.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3540853",
      "predecessor_activity_id": "1613516",
      "successor_activity_id": "1613568",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3540936",
      "predecessor_activity_id": "1605521",
      "successor_activity_id": "1613568",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3544074",
      "predecessor_activity_id": "1605518",
      "successor_activity_id": "1613568",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3544562",
      "predecessor_activity_id": "1613568",
      "successor_activity_id": "1614634",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1613568",
        "code": "OL_RSSOM_530100",
        "name": "FAI and Type Test - S-215 - Train Heating, Ventilation and Air Conditioning System - Train 1",
        "calendar_id": "11683",
        "start": "2027-04-26 08:00:00",
        "remaining": 160.0,
        "p6_finish": "2027-05-25 08:00:00",
        "calendar_finish": "2027-05-21 17:00:00",
        "variance_hours": -87.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1614295 / OL_RSSOM_530630

```json
{
  "task_id": "1614295",
  "activity_code": "OL_RSSOM_530630",
  "name": "FAI and Type Test - S-252.2 Train Gangway - Train 1",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.3.6",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2027-02-26 08:00:00",
    "early_finish": "2027-03-29 08:00:00",
    "late_start": "2027-07-08 08:00:00",
    "late_finish": "2027-08-05 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 728.0,
  "imported_ff": 432.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3543397",
      "predecessor_activity_id": "1614292",
      "successor_activity_id": "1614295",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3547357",
      "predecessor_activity_id": "1614915",
      "successor_activity_id": "1614295",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3544557",
      "predecessor_activity_id": "1614295",
      "successor_activity_id": "1614634",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1614295",
        "code": "OL_RSSOM_530630",
        "name": "FAI and Type Test - S-252.2 Train Gangway - Train 1",
        "calendar_id": "11683",
        "start": "2027-02-26 08:00:00",
        "remaining": 160.0,
        "p6_finish": "2027-03-29 08:00:00",
        "calendar_finish": "2027-03-25 17:00:00",
        "variance_hours": -87.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1613913 / OL_RSSOM_530290

```json
{
  "task_id": "1613913",
  "activity_code": "OL_RSSOM_530290",
  "name": "FAI and Type Test - S-217 - Brakes - Train 1",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.3.6",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2027-02-05 08:00:00",
    "early_finish": "2027-03-08 08:00:00",
    "late_start": "2027-07-08 08:00:00",
    "late_finish": "2027-08-05 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 840.0,
  "imported_ff": 544.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3541568",
      "predecessor_activity_id": "1613909",
      "successor_activity_id": "1613913",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3547361",
      "predecessor_activity_id": "1614827",
      "successor_activity_id": "1613913",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3544563",
      "predecessor_activity_id": "1613913",
      "successor_activity_id": "1614634",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1613913",
        "code": "OL_RSSOM_530290",
        "name": "FAI and Type Test - S-217 - Brakes - Train 1",
        "calendar_id": "11683",
        "start": "2027-02-05 08:00:00",
        "remaining": 160.0,
        "p6_finish": "2027-03-08 08:00:00",
        "calendar_finish": "2027-03-05 16:00:00",
        "variance_hours": -64.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1613916 / OL_RSSOM_530320

```json
{
  "task_id": "1613916",
  "activity_code": "OL_RSSOM_530320",
  "name": "FAI and Type Test - Bogie Frame - Train 1",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.3.6",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 160.0,
  "imported_dates": {
    "early_start": "2027-03-05 08:00:00",
    "early_finish": "2027-04-05 08:00:00",
    "late_start": "2027-08-13 08:00:00",
    "late_finish": "2027-09-10 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 888.0,
  "imported_ff": 592.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "37691048",
      "predecessor_activity_id": "1614833",
      "successor_activity_id": "1613916",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "37691053",
      "predecessor_activity_id": "1613912",
      "successor_activity_id": "1613916",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "37691062",
      "predecessor_activity_id": "1613916",
      "successor_activity_id": "17394664",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1613916",
        "code": "OL_RSSOM_530320",
        "name": "FAI and Type Test - Bogie Frame - Train 1",
        "calendar_id": "11683",
        "start": "2027-03-05 08:00:00",
        "remaining": 160.0,
        "p6_finish": "2027-04-05 08:00:00",
        "calendar_finish": "2027-04-02 16:00:00",
        "variance_hours": -64.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1604867 / OL_RSSOM_DE_101330

```json
{
  "task_id": "1604867",
  "activity_code": "OL_RSSOM_DE_101330",
  "name": "S-168C - Substantial Completion Certificate - Review by CA",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.1.3.9.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 152.0,
  "imported_dates": {
    "early_start": "2030-11-29 08:00:00",
    "early_finish": "2030-12-30 08:00:00",
    "late_start": "2031-03-04 08:00:00",
    "late_finish": "2031-03-28 16:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 504.0,
  "imported_ff": 504.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3508090",
      "predecessor_activity_id": "1604866",
      "successor_activity_id": "1604867",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3544763",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "1604867",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3534644",
      "predecessor_activity_id": "1604867",
      "successor_activity_id": "1600275",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1604867",
        "code": "OL_RSSOM_DE_101330",
        "name": "S-168C - Substantial Completion Certificate - Review by CA",
        "calendar_id": "11683",
        "start": "2030-11-29 08:00:00",
        "remaining": 152.0,
        "p6_finish": "2030-12-30 08:00:00",
        "calendar_finish": "2030-12-27 16:00:00",
        "variance_hours": -64.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1595892 / OL_RSSOM_13240

```json
{
  "task_id": "1595892",
  "activity_code": "OL_RSSOM_13240",
  "name": "OMSF MOW Building - TSSA for Boiler - Pre-Consultation Period",
  "wbs_path": "OL-RSSOM-PWS-Live.PLA.B.MOW.9.1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 360.0,
  "imported_dates": {
    "early_start": "2028-09-08 08:00:00",
    "early_finish": "2028-11-13 08:00:00",
    "late_start": "2030-02-20 08:00:00",
    "late_finish": "2030-04-24 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 2904.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3544840",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "1595892",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "14239069",
      "predecessor_activity_id": "1595891",
      "successor_activity_id": "1595892",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "15127979",
      "predecessor_activity_id": "1600096",
      "successor_activity_id": "1595892",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "3518351",
      "predecessor_activity_id": "1595892",
      "successor_activity_id": "1595893",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1595892",
        "code": "OL_RSSOM_13240",
        "name": "OMSF MOW Building - TSSA for Boiler - Pre-Consultation Period",
        "calendar_id": "11683",
        "start": "2028-09-08 08:00:00",
        "remaining": 360.0,
        "p6_finish": "2028-11-13 08:00:00",
        "calendar_finish": "2028-11-10 17:00:00",
        "variance_hours": -63.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 8804406 / OL_RSSOM_535210

```json
{
  "task_id": "8804406",
  "activity_code": "OL_RSSOM_535210",
  "name": "OMSF MOW Building - TSSA for Gas-Fired AHUs - Pre-Consultation Period",
  "wbs_path": "OL-RSSOM-PWS-Live.PLA.B.MOW.9.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 360.0,
  "imported_dates": {
    "early_start": "2028-09-08 08:00:00",
    "early_finish": "2028-11-13 08:00:00",
    "late_start": "2030-02-20 08:00:00",
    "late_finish": "2030-04-24 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 2904.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "19000156",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "8804406",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19000157",
      "predecessor_activity_id": "1595891",
      "successor_activity_id": "8804406",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19000158",
      "predecessor_activity_id": "1600096",
      "successor_activity_id": "8804406",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "19000149",
      "predecessor_activity_id": "8804406",
      "successor_activity_id": "8804407",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "8804406",
        "code": "OL_RSSOM_535210",
        "name": "OMSF MOW Building - TSSA for Gas-Fired AHUs - Pre-Consultation Period",
        "calendar_id": "11683",
        "start": "2028-09-08 08:00:00",
        "remaining": 360.0,
        "p6_finish": "2028-11-13 08:00:00",
        "calendar_finish": "2028-11-10 17:00:00",
        "variance_hours": -63.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 8804412 / OL_RSSOM_535270

```json
{
  "task_id": "8804412",
  "activity_code": "OL_RSSOM_535270",
  "name": "OMSF MOW Building - TSSA for Compressed Air System - Pre-Consultation Period",
  "wbs_path": "OL-RSSOM-PWS-Live.PLA.B.MOW.9.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 360.0,
  "imported_dates": {
    "early_start": "2028-09-08 08:00:00",
    "early_finish": "2028-11-13 08:00:00",
    "late_start": "2030-02-20 08:00:00",
    "late_finish": "2030-04-24 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 2904.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "19000168",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "8804412",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19000169",
      "predecessor_activity_id": "1595891",
      "successor_activity_id": "8804412",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19000170",
      "predecessor_activity_id": "1600096",
      "successor_activity_id": "8804412",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "19000161",
      "predecessor_activity_id": "8804412",
      "successor_activity_id": "8804413",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "8804412",
        "code": "OL_RSSOM_535270",
        "name": "OMSF MOW Building - TSSA for Compressed Air System - Pre-Consultation Period",
        "calendar_id": "11683",
        "start": "2028-09-08 08:00:00",
        "remaining": 360.0,
        "p6_finish": "2028-11-13 08:00:00",
        "calendar_finish": "2028-11-10 17:00:00",
        "variance_hours": -63.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1596861 / OL_RSSOM_CN_510890

```json
{
  "task_id": "1596861",
  "activity_code": "OL_RSSOM_CN_510890",
  "name": "Maint. Building - Steel Structure - Area 1 - Metal decking - High Roof",
  "wbs_path": "OL-RSSOM-PWS-Live.CON.OMSF.CW.MNT.BULD.STRUC.Area 1 (Rooms).RS1",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "3489",
  "calendar_name": "RSSOM_5d/w+H+Winter productivity (CJV)",
  "effective_duration": 120.0,
  "imported_dates": {
    "early_start": "2026-12-30 08:00:00",
    "early_finish": "2027-02-03 08:00:00",
    "late_start": "2027-04-06 08:00:00",
    "late_finish": "2027-04-26 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 336.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "29057259",
      "predecessor_activity_id": "1596855",
      "successor_activity_id": "1596861",
      "relationship_type": "FF",
      "lag_hours": 40.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "44458541",
      "predecessor_activity_id": "1596837",
      "successor_activity_id": "1596861",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3521403",
      "predecessor_activity_id": "1596861",
      "successor_activity_id": "1596864",
      "relationship_type": "FF",
      "lag_hours": 40.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "HARMLESS_METHODOLOGY_DIFFERENCE",
      "evidence": {
        "id": "1596861",
        "code": "OL_RSSOM_CN_510890",
        "name": "Maint. Building - Steel Structure - Area 1 - Metal decking - High Roof",
        "calendar_id": "3489",
        "start": "2026-12-30 08:00:00",
        "remaining": 120.0,
        "p6_finish": "2027-02-03 08:00:00",
        "calendar_finish": "2027-02-01 17:00:00",
        "variance_hours": -39.0,
        "working_variance_hours": -0.0,
        "boundary_equivalent": true,
        "next_working_equals_p6": true
      },
      "proven": true
    }
  ]
}
```
### 1612465 / OL_RSSOM_DE_539980

```json
{
  "task_id": "1612465",
  "activity_code": "OL_RSSOM_DE_539980",
  "name": "NP - S-212.23B - System Design Report - Emergency & Tunnel Lighting - Review by CA",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.14.66.2",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 160.016667,
  "imported_dates": {
    "early_start": "2026-09-02 08:00:00",
    "early_finish": "2026-10-01 08:01:00",
    "late_start": "2028-02-15 16:59:00",
    "late_finish": "2028-03-15 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 2919.983333,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3536107",
      "predecessor_activity_id": "1612464",
      "successor_activity_id": "1612465",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3536110",
      "predecessor_activity_id": "1612466",
      "successor_activity_id": "1612465",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3536111",
      "predecessor_activity_id": "1612465",
      "successor_activity_id": "1612467",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "1612465",
        "code": "OL_RSSOM_DE_539980",
        "name": "NP - S-212.23B - System Design Report - Emergency & Tunnel Lighting - Review by CA",
        "calendar_id": "11683",
        "start": "2026-09-02 08:00:00",
        "remaining": 160.016667,
        "p6_finish": "2026-10-01 08:01:00",
        "calendar_finish": "2026-10-01 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4618606 / OL_RSSOM_DE_563542

```json
{
  "task_id": "4618606",
  "activity_code": "OL_RSSOM_DE_563542",
  "name": "NP - I-103 (n) S&TCS to Civil Structures - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.18.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.033333,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:02:00",
    "late_start": "2030-12-16 16:58:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.966667,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10742582",
      "predecessor_activity_id": "1600228",
      "successor_activity_id": "4618606",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    },
    {
      "relationship_id": "12127820",
      "predecessor_activity_id": "4618601",
      "successor_activity_id": "4618606",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742327",
      "predecessor_activity_id": "4618606",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742540",
      "predecessor_activity_id": "4618606",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4618606",
        "code": "OL_RSSOM_DE_563542",
        "name": "NP - I-103 (n) S&TCS to Civil Structures - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.033333,
        "p6_finish": "2026-12-24 08:02:00",
        "calendar_finish": "2026-12-24 08:01:59.998800",
        "variance_hours": -3.333333333333333e-07,
        "working_variance_hours": -3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4639473 / OL_RSSOM_DE_563730

```json
{
  "task_id": "4639473",
  "activity_code": "OL_RSSOM_DE_563730",
  "name": "NP - I-103 (t) SCADA to FLS - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.19.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.016667,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:01:00",
    "late_start": "2030-12-16 16:59:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.983333,
  "imported_ff": 0.016667,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10528427",
      "predecessor_activity_id": "4639468",
      "successor_activity_id": "4639473",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742331",
      "predecessor_activity_id": "4639473",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742549",
      "predecessor_activity_id": "4639473",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4639473",
        "code": "OL_RSSOM_DE_563730",
        "name": "NP - I-103 (t) SCADA to FLS - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.016667,
        "p6_finish": "2026-12-24 08:01:00",
        "calendar_finish": "2026-12-24 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4639488 / OL_RSSOM_DE_563880

```json
{
  "task_id": "4639488",
  "activity_code": "OL_RSSOM_DE_563880",
  "name": "NP - I-103 (t) SCADA to FLS - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.26.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.016667,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:01:00",
    "late_start": "2030-12-16 16:59:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.983333,
  "imported_ff": 0.016667,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10528448",
      "predecessor_activity_id": "4639483",
      "successor_activity_id": "4639488",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742330",
      "predecessor_activity_id": "4639488",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742548",
      "predecessor_activity_id": "4639488",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4639488",
        "code": "OL_RSSOM_DE_563880",
        "name": "NP - I-103 (t) SCADA to FLS - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.016667,
        "p6_finish": "2026-12-24 08:01:00",
        "calendar_finish": "2026-12-24 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4639503 / OL_RSSOM_DE_564030

```json
{
  "task_id": "4639503",
  "activity_code": "OL_RSSOM_DE_564030",
  "name": "NP - I-103 (u) SCADA to BACS - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.27.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.016667,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:01:00",
    "late_start": "2030-12-16 16:59:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.983333,
  "imported_ff": 0.016667,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10528490",
      "predecessor_activity_id": "4639498",
      "successor_activity_id": "4639503",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742334",
      "predecessor_activity_id": "4639503",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742552",
      "predecessor_activity_id": "4639503",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4639503",
        "code": "OL_RSSOM_DE_564030",
        "name": "NP - I-103 (u) SCADA to BACS - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.016667,
        "p6_finish": "2026-12-24 08:01:00",
        "calendar_finish": "2026-12-24 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4639518 / OL_RSSOM_DE_564180

```json
{
  "task_id": "4639518",
  "activity_code": "OL_RSSOM_DE_564180",
  "name": "NP - I-103 (u) SCADA to BACS - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.28.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.016667,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:01:00",
    "late_start": "2030-12-16 16:59:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.983333,
  "imported_ff": 0.016667,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10528512",
      "predecessor_activity_id": "4639513",
      "successor_activity_id": "4639518",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742333",
      "predecessor_activity_id": "4639518",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742551",
      "predecessor_activity_id": "4639518",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4639518",
        "code": "OL_RSSOM_DE_564180",
        "name": "NP - I-103 (u) SCADA to BACS - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.016667,
        "p6_finish": "2026-12-24 08:01:00",
        "calendar_finish": "2026-12-24 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 4639533 / OL_RSSOM_DE_564330

```json
{
  "task_id": "4639533",
  "activity_code": "OL_RSSOM_DE_564330",
  "name": "NP - I-103 (v) Signage - C - C6ix Development/ Collaboration & North-PTUS Submission",
  "wbs_path": "OL-RSSOM-PWS-Live.DSE.AD.2.4.2.2.2.29.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 640.016667,
  "imported_dates": {
    "early_start": "2026-09-01 08:00:00",
    "early_finish": "2026-12-24 08:01:00",
    "late_start": "2030-12-16 16:59:00",
    "late_finish": "2031-04-14 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 8623.983333,
  "imported_ff": 0.016667,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "10528623",
      "predecessor_activity_id": "4639528",
      "successor_activity_id": "4639533",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742336",
      "predecessor_activity_id": "4639533",
      "successor_activity_id": "1600232",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742554",
      "predecessor_activity_id": "4639533",
      "successor_activity_id": "4577049",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "4639533",
        "code": "OL_RSSOM_DE_564330",
        "name": "NP - I-103 (v) Signage - C - C6ix Development/ Collaboration & North-PTUS Submission",
        "calendar_id": "11683",
        "start": "2026-09-01 08:00:00",
        "remaining": 640.016667,
        "p6_finish": "2026-12-24 08:01:00",
        "calendar_finish": "2026-12-24 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 1612449 / OL_RSSOM_PR_509550

```json
{
  "task_id": "1612449",
  "activity_code": "OL_RSSOM_PR_509550",
  "name": "Supplier Manufacturing/ Assembly - Emergency and Tunnel Lights - Mainline",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.2.1.5.3",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 1120.016667,
  "imported_dates": {
    "early_start": "2026-11-03 08:00:00",
    "early_finish": "2027-05-26 08:01:00",
    "late_start": "2028-04-17 16:59:00",
    "late_finish": "2028-11-06 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 2919.983333,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3536051",
      "predecessor_activity_id": "1612448",
      "successor_activity_id": "1612449",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3536052",
      "predecessor_activity_id": "1612449",
      "successor_activity_id": "1612450",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "1612449",
        "code": "OL_RSSOM_PR_509550",
        "name": "Supplier Manufacturing/ Assembly - Emergency and Tunnel Lights - Mainline",
        "calendar_id": "11683",
        "start": "2026-11-03 08:00:00",
        "remaining": 1120.016667,
        "p6_finish": "2027-05-26 08:01:00",
        "calendar_finish": "2027-05-26 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 1613469 / OL_RSSOM_PR_512750

```json
{
  "task_id": "1613469",
  "activity_code": "OL_RSSOM_PR_512750",
  "name": "Logistics / Transportation Time - (APCS) - 1st Batch Prototype (Pistoia, Italy) - 2 First Trains",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.2.1.1.8",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 720.033333,
  "imported_dates": {
    "early_start": "2026-12-31 08:00:00",
    "early_finish": "2027-05-11 08:02:00",
    "late_start": "2027-05-17 16:58:00",
    "late_finish": "2027-09-24 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 759.966667,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3539739",
      "predecessor_activity_id": "1613471",
      "successor_activity_id": "1613469",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3539738",
      "predecessor_activity_id": "1613469",
      "successor_activity_id": "1613470",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "1613469",
        "code": "OL_RSSOM_PR_512750",
        "name": "Logistics / Transportation Time - (APCS) - 1st Batch Prototype (Pistoia, Italy) - 2 First Trains",
        "calendar_id": "11683",
        "start": "2026-12-31 08:00:00",
        "remaining": 720.033333,
        "p6_finish": "2027-05-11 08:02:00",
        "calendar_finish": "2027-05-11 08:01:59.998800",
        "variance_hours": -3.333333333333333e-07,
        "working_variance_hours": -3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 1613483 / OL_RSSOM_PR_512780

```json
{
  "task_id": "1613483",
  "activity_code": "OL_RSSOM_PR_512780",
  "name": "Logistics / Transportation Time - Shipment - (APCS) - 2nd Batch (Hagerstown, Maryland, USA) - Remaining Trains",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.2.1.1.8",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 480.016667,
  "imported_dates": {
    "early_start": "2027-04-27 08:00:00",
    "early_finish": "2027-07-22 08:01:00",
    "late_start": "2027-10-04 16:59:00",
    "late_finish": "2027-12-30 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 887.983333,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3540387",
      "predecessor_activity_id": "1613485",
      "successor_activity_id": "1613483",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3540386",
      "predecessor_activity_id": "1613483",
      "successor_activity_id": "1613484",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "1613483",
        "code": "OL_RSSOM_PR_512780",
        "name": "Logistics / Transportation Time - Shipment - (APCS) - 2nd Batch (Hagerstown, Maryland, USA) - Remaining Trains",
        "calendar_id": "11683",
        "start": "2027-04-27 08:00:00",
        "remaining": 480.016667,
        "p6_finish": "2027-07-22 08:01:00",
        "calendar_finish": "2027-07-22 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 5083194 / OL_RSSOM_PR_518950

```json
{
  "task_id": "5083194",
  "activity_code": "OL_RSSOM_PR_518950",
  "name": "Factory Acceptance Testing (FAT) - OCC & BOCC, OMSF & Functional Section - DCS, MSN, (FOI) - Supply",
  "wbs_path": "OL-RSSOM-PWS-Live.PRC.2.1.1.9",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 320.016667,
  "imported_dates": {
    "early_start": "2027-01-14 08:00:00",
    "early_finish": "2027-03-12 08:01:00",
    "late_start": "2027-09-30 16:57:00",
    "late_finish": "2027-11-26 16:58:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 1439.95,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "11488301",
      "predecessor_activity_id": "5083193",
      "successor_activity_id": "5083194",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "11488302",
      "predecessor_activity_id": "5083194",
      "successor_activity_id": "5083195",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CALENDAR_DIFFERENCE",
      "evidence": {
        "id": "5083194",
        "code": "OL_RSSOM_PR_518950",
        "name": "Factory Acceptance Testing (FAT) - OCC & BOCC, OMSF & Functional Section - DCS, MSN, (FOI) - Supply",
        "calendar_id": "11683",
        "start": "2027-01-14 08:00:00",
        "remaining": 320.016667,
        "p6_finish": "2027-03-12 08:01:00",
        "calendar_finish": "2027-03-12 08:01:00.001200",
        "variance_hours": 3.333333333333333e-07,
        "working_variance_hours": 3.333333333333333e-07,
        "boundary_equivalent": false,
        "next_working_equals_p6": false
      },
      "proven": false
    }
  ]
}
```
### 1596011 / OL_RSSOM_CN_100260

```json
{
  "task_id": "1596011",
  "activity_code": "OL_RSSOM_CN_100260",
  "name": "OMSF - Utilities Preparatory - Bell - Telecom @ Thorncliffe Park Drive - LET-PRM0-00215",
  "wbs_path": "OL-RSSOM-PWS-Live.CON.OMSF.ACCESS.15.1",
  "status": "not_started",
  "type": "milestone",
  "raw_type": "TT_Mile",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2026-07-01 08:00:00",
    "late_start": "2030-09-10 08:00:00",
    "late_finish": "2030-09-10 08:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 12256.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "START_ON_OR_AFTER",
      "2025-01-01 00:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3514745",
      "predecessor_activity_id": "1599140",
      "successor_activity_id": "1596011",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19000038",
      "predecessor_activity_id": "1595634",
      "successor_activity_id": "1596011",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3508912",
      "predecessor_activity_id": "1596011",
      "successor_activity_id": "1596019",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3519257",
      "predecessor_activity_id": "1596011",
      "successor_activity_id": "1596217",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3519258",
      "predecessor_activity_id": "1596011",
      "successor_activity_id": "1596220",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "START_ON_OR_AFTER",
          "2025-01-01 00:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1596816 / OL_RSSOM_CN_528740

```json
{
  "task_id": "1596816",
  "activity_code": "OL_RSSOM_CN_528740",
  "name": "MOW Building - Final Cleaning",
  "wbs_path": "OL-RSSOM-PWS-Live.CON.OMSF.CW.MOW&TPSS.MOW.ROOF",
  "status": "not_started",
  "type": "task",
  "raw_type": "TT_Task",
  "calendar_id": "11683",
  "calendar_name": "RSSOM 5d/w+H",
  "effective_duration": 40.0,
  "imported_dates": {
    "early_start": "2028-05-12 08:00:00",
    "early_finish": "2028-05-18 17:00:00",
    "late_start": "2028-06-19 08:00:00",
    "late_finish": "2028-06-23 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 200.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_BEFORE",
      "2029-01-26 08:01:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3529512",
      "predecessor_activity_id": "1596815",
      "successor_activity_id": "1596816",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3529591",
      "predecessor_activity_id": "1596810",
      "successor_activity_id": "1596816",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3532379",
      "predecessor_activity_id": "1596816",
      "successor_activity_id": "1597614",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "19921685",
      "predecessor_activity_id": "1596816",
      "successor_activity_id": "1596045",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_BEFORE",
          "2029-01-26 08:01:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1599062 / OL_RSSOM_CN_113740

```json
{
  "task_id": "1599062",
  "activity_code": "OL_RSSOM_CN_113740",
  "name": "23. Pape Station - Substantial Completion",
  "wbs_path": "OL-RSSOM-PWS-Live.CON.3.4.43.2.3",
  "status": "not_started",
  "type": "finish_milestone",
  "raw_type": "TT_FinMile",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 0,
  "imported_dates": {
    "early_start": "2030-06-01 17:00:00",
    "early_finish": "2030-06-01 17:00:00",
    "late_start": "2030-06-17 17:00:00",
    "late_finish": "2030-06-17 17:00:00",
    "actual_start": null,
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 128.0,
  "imported_ff": 8.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "FINISH_ON_OR_AFTER",
      "2030-06-01 17:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3514678",
      "predecessor_activity_id": "1599139",
      "successor_activity_id": "1599062",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3515430",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1599690",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3515443",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1599688",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3530892",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1599810",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3530893",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1599792",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3534365",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1609436",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3534498",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1598912",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3534499",
      "predecessor_activity_id": "1599062",
      "successor_activity_id": "1598911",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "unsupported_constraint",
      "message": "Constraint is not implemented by this CPM increment.",
      "severity": "ERROR",
      "activity_id": "1599062",
      "relationship_id": null,
      "metadata": {}
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "FINISH_ON_OR_AFTER",
          "2030-06-01 17:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1598944 / OL_RSSOM_CN_100030

```json
{
  "task_id": "1598944",
  "activity_code": "OL_RSSOM_CN_100030",
  "name": "01c - Construction Staging and Laydown Property Access at Ft. York Triangle - SFYLD (Initial Part)",
  "wbs_path": "OL-RSSOM-PWS-Live.CON.3.4.41.3",
  "status": "complete",
  "type": "milestone",
  "raw_type": "TT_Mile",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 0,
  "imported_dates": {
    "early_start": "2026-07-01 00:01:00",
    "early_finish": "2026-07-01 00:01:00",
    "late_start": "2026-10-12 08:00:00",
    "late_finish": "2026-10-12 08:00:00",
    "actual_start": "2023-10-12 00:00:00",
    "actual_finish": "2023-10-12 00:00:00"
  },
  "calculated_dates": null,
  "imported_tf": null,
  "imported_ff": null,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      "START_ON_OR_BEFORE",
      "2023-10-01 00:00:00"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3536871",
      "predecessor_activity_id": "1599138",
      "successor_activity_id": "1598944",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3508540",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1598310",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3508541",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1598300",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3509646",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1598313",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3521065",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1598148",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3531435",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1598215",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3536866",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1612780",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3536874",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1612807",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3538893",
      "predecessor_activity_id": "1598944",
      "successor_activity_id": "1612146",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "unsupported_constraint",
      "message": "Constraint is not implemented by this CPM increment.",
      "severity": "ERROR",
      "activity_id": "1598944",
      "relationship_id": null,
      "metadata": {}
    }
  ],
  "categories": [
    {
      "category": "CONSTRAINT_HANDLING",
      "evidence": [
        [
          "START_ON_OR_BEFORE",
          "2023-10-01 00:00:00"
        ],
        [
          null,
          "None"
        ]
      ],
      "proven": "source presence; only unsupported tags prove validation rejection"
    }
  ]
}
```
### 1596002 / OL_RSSOM_262550

```json
{
  "task_id": "1596002",
  "activity_code": "OL_RSSOM_262550",
  "name": "Projectwide PLAA Efforts",
  "wbs_path": "OL-RSSOM-PWS-Live.PLA.0",
  "status": "in_progress",
  "type": "level_of_effort",
  "raw_type": "TT_LOE",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 9536.0,
  "imported_dates": {
    "early_start": "2026-07-01 08:00:00",
    "early_finish": "2029-10-04 17:00:00",
    "late_start": "2031-05-27 17:00:00",
    "late_finish": "2031-05-27 17:00:00",
    "actual_start": "2022-11-18 00:00:00",
    "actual_finish": null
  },
  "calculated_dates": null,
  "imported_tf": 4800.0,
  "imported_ff": 0.0,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [
    {
      "relationship_id": "3534955",
      "predecessor_activity_id": "1595628",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3534957",
      "predecessor_activity_id": "1595855",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3534958",
      "predecessor_activity_id": "1595717",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3534959",
      "predecessor_activity_id": "1595897",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3541977",
      "predecessor_activity_id": "1612283",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "3541980",
      "predecessor_activity_id": "1612135",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10485957",
      "predecessor_activity_id": "1612667",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10700842",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "15127956",
      "predecessor_activity_id": "6919088",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "19000155",
      "predecessor_activity_id": "8804411",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "19000167",
      "predecessor_activity_id": "8804417",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "19165550",
      "predecessor_activity_id": "8938050",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "21067240",
      "predecessor_activity_id": "9931161",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "21067251",
      "predecessor_activity_id": "9931167",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "25028391",
      "predecessor_activity_id": "11995232",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "25192644",
      "predecessor_activity_id": "12076535",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "27540169",
      "predecessor_activity_id": "13400502",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "31455014",
      "predecessor_activity_id": "15617391",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "32182332",
      "predecessor_activity_id": "16049259",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "32182333",
      "predecessor_activity_id": "16049264",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "32182334",
      "predecessor_activity_id": "16049269",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "32182335",
      "predecessor_activity_id": "16049280",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567610",
      "predecessor_activity_id": "17394668",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567611",
      "predecessor_activity_id": "17394672",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567612",
      "predecessor_activity_id": "17394676",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567710",
      "predecessor_activity_id": "17394719",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567720",
      "predecessor_activity_id": "17394725",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "34567721",
      "predecessor_activity_id": "17322954",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "35103992",
      "predecessor_activity_id": "17688671",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "35104011",
      "predecessor_activity_id": "17688696",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "35104216",
      "predecessor_activity_id": "17688850",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "36303856",
      "predecessor_activity_id": "18340310",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "38075719",
      "predecessor_activity_id": "19323810",
      "successor_activity_id": "1596002",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "loe_not_supported",
      "message": "LOE scheduling is unsupported.",
      "severity": "WARNING",
      "activity_id": "1596002",
      "relationship_id": null,
      "metadata": {
        "disposition": "EXCLUDE"
      }
    }
  ],
  "categories": [
    {
      "category": "UNSUPPORTED_P6_OPTION",
      "evidence": "TT_LOE",
      "proven": "rejected/excluded type, not a numerical difference"
    },
    {
      "category": "STATUS_PROGRESS_TREATMENT",
      "evidence": "Remaining-work policy differs in date basis from imported started Early Start",
      "proven": false
    },
    {
      "category": "OPEN_END",
      "evidence": {
        "open_start": false,
        "open_finish": true
      },
      "proven": "source topology only"
    }
  ]
}
```
### 1596230 / OL_RSSOM_262290

```json
{
  "task_id": "1596230",
  "activity_code": "OL_RSSOM_262290",
  "name": "Yard-WBW - General",
  "wbs_path": "OL-RSSOM-PWS-Live.3.15",
  "status": "complete",
  "type": "tt_wbs",
  "raw_type": "TT_WBS",
  "calendar_id": "3479",
  "calendar_name": "RSSOM_7d/w (no holidays)",
  "effective_duration": 0,
  "imported_dates": {
    "early_start": null,
    "early_finish": null,
    "late_start": null,
    "late_finish": null,
    "actual_start": "2025-01-01 08:00:00",
    "actual_finish": "2025-01-31 17:00:00"
  },
  "calculated_dates": null,
  "imported_tf": null,
  "imported_ff": null,
  "calculated_tf": null,
  "calculated_ff": null,
  "constraints": [
    [
      null,
      "None"
    ],
    [
      null,
      "None"
    ]
  ],
  "predecessors": [],
  "successors": [],
  "controlling_predecessor": null,
  "controlling_successor": null,
  "calculation_anchor": null,
  "diagnostics": [
    {
      "code": "unsupported_activity_type",
      "message": "Unknown or missing activity type.",
      "severity": "ERROR",
      "activity_id": "1596230",
      "relationship_id": null,
      "metadata": {
        "disposition": "ERROR"
      }
    }
  ],
  "categories": [
    {
      "category": "UNSUPPORTED_P6_OPTION",
      "evidence": "TT_WBS",
      "proven": "rejected/excluded type, not a numerical difference"
    },
    {
      "category": "OPEN_END",
      "evidence": {
        "open_start": true,
        "open_finish": true
      },
      "proven": "source topology only"
    }
  ]
}
```
## Complete validation diagnostic inventory

Every returned validation diagnostic is represented by its common message, severity, metadata and affected activity IDs below. No relationship-specific errors were returned. The source file and imported core were verified unchanged.
```json
{
  "code": "planned_start_before_data_date",
  "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
  "metadata": {
    "disposition": "INFORMATIONAL"
  },
  "severity": "INFORMATIONAL",
  "activity_ids": [
    "1595667",
    "1595673",
    "1595718",
    "1595722",
    "1595818",
    "1595866",
    "1595908",
    "1595938",
    "1596189",
    "1596761",
    "1600629",
    "1600639",
    "1600649",
    "1600733",
    "1600745",
    "1600765",
    "1600790",
    "1600970",
    "1601060",
    "1601075",
    "1601090",
    "1601105",
    "1601120",
    "1601240",
    "1601255",
    "1601405",
    "1601420",
    "1601540",
    "1601555",
    "1601570",
    "1601585",
    "1601600",
    "1601739",
    "1601797",
    "1601821",
    "1601825",
    "1601900",
    "1602020",
    "1602129",
    "1602219",
    "1602241",
    "1602245",
    "1602256",
    "1602260",
    "1602271",
    "1602275",
    "1602286",
    "1602290",
    "1602301",
    "1602305",
    "1602325",
    "1602350",
    "1602374",
    "1602380",
    "1602402",
    "1602410",
    "1602442",
    "1602450",
    "1602460",
    "1602520",
    "1602540",
    "1602560",
    "1602589",
    "1602604",
    "1602619",
    "1602634",
    "1602664",
    "1602709",
    "1602784",
    "1602799",
    "1602814",
    "1602829",
    "1602844",
    "1602859",
    "1602889",
    "1602904",
    "1602919",
    "1602934",
    "1602949",
    "1602964",
    "1602979",
    "1602994",
    "1603009",
    "1603084",
    "1603099",
    "1603114",
    "1603129",
    "1603144",
    "1603159",
    "1603174",
    "1603189",
    "1603204",
    "1603219",
    "1603234",
    "1603294",
    "1603324",
    "1603339",
    "1603354",
    "1603369",
    "1603384",
    "1603414",
    "1603429",
    "1603444",
    "1603459",
    "1603474",
    "1603489",
    "1603504",
    "1603519",
    "1603549",
    "1603594",
    "1603609",
    "1603624",
    "1603639",
    "1603654",
    "1603698",
    "1603713",
    "1603859",
    "1603919",
    "1604161",
    "1604208",
    "1604233",
    "1604299",
    "1604429",
    "1604440",
    "1604444",
    "1604455",
    "1604459",
    "1604470",
    "1604474",
    "1604514",
    "1604524",
    "1604544",
    "1604574",
    "1604584",
    "1604614",
    "1604624",
    "1604672",
    "1604682",
    "1604894",
    "1604962",
    "1605137",
    "1605148",
    "1605237",
    "1605270",
    "1605456",
    "1605611",
    "1605621",
    "1605645",
    "1605655",
    "1605665",
    "1605673",
    "1605685",
    "1605745",
    "1605769",
    "1605780",
    "1605785",
    "1605841",
    "1605852",
    "1605896",
    "1605925",
    "1605940",
    "1606030",
    "1606040",
    "1606086",
    "1606222",
    "1606233",
    "1606245",
    "1606404",
    "1606411",
    "1606412",
    "1606425",
    "1606432",
    "1606433",
    "1606447",
    "1606454",
    "1606455",
    "1606460",
    "1606461",
    "1606523",
    "1606530",
    "1606531",
    "1606546",
    "1606548",
    "1606555",
    "1606556",
    "1606568",
    "1606570",
    "1606626",
    "1606628",
    "1606690",
    "1606706",
    "1606737",
    "1606740",
    "1606741",
    "1606747",
    "1607009",
    "1607036",
    "1607042",
    "1607061",
    "1607077",
    "1607114",
    "1607118",
    "1607127",
    "1607130",
    "1607151",
    "1607156",
    "1607162",
    "1607229",
    "1607246",
    "1607250",
    "1607262",
    "1607268",
    "1607276",
    "1607279",
    "1607292",
    "1607304",
    "1607353",
    "1607407",
    "1607435",
    "1607508",
    "1607560",
    "1607561",
    "1607577",
    "1607594",
    "1607637",
    "1607719",
    "1607731",
    "1607738",
    "1607742",
    "1607758",
    "1607759",
    "1607773",
    "1607796",
    "1607815",
    "1607849",
    "1607863",
    "1611764",
    "1612432",
    "1612442",
    "1612463",
    "1612595",
    "1612766",
    "1612768",
    "1613074",
    "1613176",
    "1613261",
    "1613301",
    "1613321",
    "1613342",
    "1613396",
    "1613424",
    "1613436",
    "1613505",
    "1613553",
    "1613574",
    "1613579",
    "1613585",
    "1613591",
    "1613605",
    "1613609",
    "1613617",
    "1613621",
    "1613633",
    "1613637",
    "1613876",
    "1613944",
    "1614043",
    "1614047",
    "1614051",
    "1614058",
    "1614064",
    "1614067",
    "1614073",
    "1614079",
    "1614100",
    "1614106",
    "1614112",
    "1614266",
    "1614286",
    "1614459",
    "1614465",
    "1614479",
    "1614546",
    "1614552",
    "1614684",
    "1614694",
    "1614704",
    "1614795",
    "1614799",
    "1614917",
    "1615184",
    "1615186",
    "1615187",
    "1615188",
    "1615189",
    "1615190",
    "1615191",
    "1615192",
    "1615225",
    "1615253",
    "1615254",
    "1615255",
    "1615256",
    "1615257",
    "1615258",
    "1615259",
    "1615261",
    "1615262",
    "1615263",
    "1615264",
    "1615346",
    "1615358",
    "1615371",
    "4577064",
    "4577079",
    "4577109",
    "4577144",
    "4577154",
    "4577189",
    "4577199",
    "4577214",
    "4577229",
    "4577244",
    "4577259",
    "4577274",
    "4577289",
    "4577309",
    "4577324",
    "4577339",
    "4618449",
    "4618601",
    "4639461",
    "4639468",
    "4639483",
    "4639498",
    "4639513",
    "4639528",
    "4639543",
    "4639558",
    "4712276",
    "4712277",
    "4712278",
    "4712279",
    "4712280",
    "4712281",
    "4712284",
    "5083205",
    "5161350",
    "5245181",
    "5328460",
    "5328463",
    "5328464",
    "5328465",
    "5328466",
    "5328469",
    "5328470",
    "5328473",
    "5328474",
    "5328475",
    "5328476",
    "5328477",
    "5328478",
    "5328480",
    "5328482",
    "5328483",
    "5328494",
    "5328496",
    "5328497",
    "5328498",
    "5328502",
    "5328503",
    "5328510",
    "5328511",
    "5328512",
    "5328513",
    "5458170",
    "6143287",
    "6919087",
    "7544265",
    "7544272",
    "9815238",
    "10449962",
    "10779653",
    "10779661",
    "10779664",
    "11995221",
    "12076654",
    "12809689",
    "12809690",
    "12809704",
    "12809705",
    "12809709",
    "13042094",
    "13086859",
    "13086860",
    "13086886",
    "13087020",
    "13087141",
    "13087178",
    "13087695",
    "13087697",
    "13087706",
    "13087716",
    "13207119",
    "13766145",
    "13903522",
    "14140745",
    "14256573",
    "14256577",
    "14256581",
    "14256585",
    "14256589",
    "14256593",
    "14256597",
    "14256601",
    "14345661",
    "14549706",
    "14856043",
    "14856045",
    "14856046",
    "15038185",
    "15038187",
    "15038188",
    "15038190",
    "15328983",
    "15328985",
    "15639908",
    "15729588",
    "15729592",
    "16260474",
    "16260476",
    "17300373",
    "17394656",
    "17394682",
    "17394700",
    "17394703",
    "17394718",
    "17394724",
    "17394727",
    "17580040",
    "18102727",
    "18158156",
    "18363081",
    "18363094",
    "18387899",
    "18387902",
    "18387904",
    "18387905",
    "18387909",
    "18387912",
    "18387913",
    "18387914",
    "18387917",
    "18387918",
    "19105529",
    "19427824",
    "19750062",
    "19874731",
    "20054201",
    "20142592",
    "20142599",
    "20142602",
    "20165721",
    "20165723",
    "20165730",
    "20165734",
    "21314436",
    "21314438",
    "21314440",
    "21314442",
    "21364366",
    "21364368",
    "21450226",
    "21450228",
    "21450239",
    "21450241",
    "21450243",
    "21450246",
    "21985709",
    "21985911",
    "22273943",
    "22273948",
    "22273953",
    "22507707",
    "22593644",
    "22593651",
    "22765518",
    "22851449",
    "22851453",
    "22851455",
    "22901303",
    "22901305"
  ],
  "count": 492
}
```
```json
{
  "code": "loe_not_supported",
  "message": "LOE scheduling is unsupported.",
  "metadata": {
    "disposition": "EXCLUDE"
  },
  "severity": "WARNING",
  "activity_ids": [
    "1596002",
    "1596004",
    "1599195",
    "1599196",
    "1600728",
    "1600729",
    "1605320",
    "1605352",
    "1605358",
    "1605375",
    "1606814",
    "1611264",
    "1611515",
    "1611532",
    "1611795",
    "1611803",
    "1611812",
    "1611815",
    "1611819",
    "1611826",
    "1611835",
    "1611844",
    "1611846",
    "1611849",
    "1611856",
    "1611859",
    "1611864",
    "1611874",
    "1611881",
    "1611893",
    "1611894",
    "1611916",
    "1611921",
    "1611930",
    "1611938",
    "1611974",
    "1611983",
    "1612023",
    "1612035",
    "1612039",
    "1612043",
    "1612047",
    "1612051",
    "1612055",
    "9338916",
    "9338917",
    "11013601",
    "11013603",
    "11013605",
    "11013606",
    "11013607",
    "11013609",
    "11013610",
    "11013612",
    "11013613",
    "11013614",
    "13903525"
  ],
  "count": 57
}
```
```json
{
  "code": "unsupported_constraint",
  "message": "Constraint is not implemented by this CPM increment.",
  "metadata": {},
  "severity": "ERROR",
  "activity_ids": [
    "1596009",
    "1598944",
    "1599062",
    "1599074",
    "1599086",
    "1599134",
    "1599135",
    "1599136",
    "1599137",
    "1600291",
    "1600294",
    "1600295",
    "1600296",
    "1606505",
    "1606581",
    "1606582",
    "1606587",
    "1606589",
    "1606590",
    "1606591",
    "1606792",
    "1611939",
    "1611940",
    "1611941",
    "1611942",
    "1611943",
    "1611944",
    "1611945",
    "1611946",
    "1611947",
    "1611948",
    "1611949",
    "1611950",
    "1611951",
    "1611952",
    "1611953",
    "1611954",
    "1611955",
    "1611956",
    "1611957",
    "1611958",
    "1611959",
    "1611960",
    "1611961",
    "1611962",
    "1611963",
    "1611964",
    "1611965",
    "1611966",
    "1611967",
    "1611968",
    "1612777",
    "1612779",
    "1613478",
    "3938977",
    "3938978",
    "3938979",
    "3938980",
    "4577042",
    "6468592",
    "6713588",
    "8937998",
    "8937999",
    "8938000",
    "8938004",
    "13903401",
    "13903402",
    "13903407",
    "13903413",
    "13903419",
    "13903430",
    "13903446"
  ],
  "count": 72
}
```
```json
{
  "code": "unsupported_activity_type",
  "message": "Unknown or missing activity type.",
  "metadata": {
    "disposition": "ERROR"
  },
  "severity": "ERROR",
  "activity_ids": [
    "1596230",
    "1596263",
    "1596437",
    "1596438",
    "1596638",
    "1596760",
    "1596818",
    "1597406",
    "1597533",
    "18387903"
  ],
  "count": 10
}
```
Comparison capability diagnostics additionally include p6_scheduling_options_unobserved, p6_critical_definition_capability, progress_policy_capability and any source-presence diagnostics. These are warnings about possible differences, not calculated error attribution. Raw scheduling options were inspected outside the engine, without redesigning its canonical model.
## Validation and disposition

- Initial non-external baseline: 335 passed, 2 deselected, 1 existing warning.
- Focused CPM/calendar plus all reproductions: 299 passed, 1 deselected.
- Focused calendar suite: 79 passed, 1 deselected.
- Focused CPM suite: 209 passed.
- Complete locally runnable regression: pytest -q -m "not external_xer": 346 passed, 2 deselected, 1 existing warning.
- Existing external_xer selection: 2 failed, 346 deselected, 1 warning. Both still require absent sample_data/NRG00800.xer; they do not target this newly supplied project. The genuine file was separately imported and calculated as documented above, without substitution.
- DCMA Critical Path Test: NOT_EVALUATED. Immutable delay simulation has not been implemented/validated.
- CPLI: NOT_EVALUATED. Required completion and validated path-length inputs are not established.
- Readiness: controlled synthetic schedule-assurance calculations remain tested; this whole real project is NOT ready for supported end-to-end application CPM or P6-equivalence claims. Next blockers are explicit unsupported constraints, WBS summaries and LOE incident logic, followed by declared progress/Expected Finish, float and anchor compatibility policies. No automatic activation or further phase work is authorized by these findings.
Files created: tests/test_phase6b_reproductions.py; docs/phase6b_calibration_notes.md. Files modified: app/calendars/parser.py; app/importers/p6_normalization.py. No CPM formula module, protected calculation contract, importer schema, API or product reporting feature was changed.
