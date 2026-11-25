# Phase 6D: retained forward-date calibration evidence

The protected Phase 6, 6B and 6C contracts are unchanged. This deliberate opt-in extension is specified in [phase6d_progress_contract.md](phase6d_progress_contract.md). Source: `C:\Github\schedule_assurance_vscode\sample_data\1414_RSM-RSM-CW-PWD-RPT-PRM0-00063_C01 Appendix.10 - OL-RSSOM-PWS_June 2026.xer`; SHA-256 `77ad15c128638db79792ab915301ba236785fd134768ecd98a6992072de23999`. Full genuine import and calculation verified source and canonical core immutability, including scheduling options. No source Activity was split or overwritten. Existing backward, float, path, calendar and constraint arithmetic is unchanged. No UI, reporting/export feature, persistence or simulation was added.

## Initial regression and protected documents

Initial complete non-external regression: **393 passed, 2 deselected, 1 existing warning**. Read and preserved: docs/phase6_calculation_contract.md, docs/phase6b_calibration_notes.md, docs/phase6c_calibration_notes.md, docs/phase6c_calculability_contract.md. Their verified SHA-256 values:
```json
{
  "phase6_calculation_contract.md": "28f9b93834727d716d53b089e2efeb8cedaaad8ebab7070e64a5144389ec5d26",
  "phase6b_calibration_notes.md": "965371509b0fa33134e914a6e55c5a7614f759852e751063fbade3b9b82feff5",
  "phase6c_calibration_notes.md": "a0b3f9ab867c4301129b69ea1f16bedc69978354d3592d39221158c1855c25bc",
  "phase6c_calculability_contract.md": "2d42e2a2248ed4055c746e952561060333d705b6915f7429c1f783ac347e24a8"
}
```


## Actual P6 options and canonical mapping

SCHEDOPTIONS is now parsed and mapped for the selected project into frozen P6SchedulingOptions. Typed properties drive the explicitly selected policy; raw_fields contains every original field/value as immutable pairs, not an arbitrary policy dictionary. Unknown booleans stay None with an import diagnostic; duplicate rows are not selected arbitrarily. Fields from other projects are not mixed. Existing STRICT/VALID_COMPONENTS defaults do not automatically activate P6 progress semantics.
| Setting | Actual P6 value | Current support | Phase 6D action |
|---|---|---|---|
| sched_retained_logic | Y | PARTIALLY_SUPPORTED | Explicit P6_RETAINED_LOGIC, forward remaining-work subset only |
| sched_progress_override | N | UNSUPPORTED when enabled | Never implement/activate; incompatible requested mode blocked |
| sched_lag_early_start_flag | Y | PARTIALLY_SUPPORTED | Nonnegative progressed SS expired lag from Early Start; alternative method blocked |
| sched_calendar_on_relationship_lag | rcal_Predecessor | SUPPORTED | Existing predecessor working calendar, no new arithmetic |
| sched_use_expect_end_flag | Y | UNSUPPORTED scheduling semantics | Preserve expect_end_date; block affected forward work, not replace with EF |
| sched_outer_depend_type | SD_Both | Internal relationships supported | No missing external endpoints in this file; no external dates fabricated |
| sched_setplantoforecast | N | Preservation supported | Do not overwrite planned dates |
| Actual Dates scheduling mode | No separate field in this table; retained=Y/override=N observed | UNSUPPORTED | Preserve actual segments, do not infer another mode |
| Remaining-duration recalculation | No identified SCHEDOPTIONS switch in export | Imported remaining hours supported | Preserve TASK.remain_drtn_hr_cnt and duration_type; no resource-driven recalculation |
| sched_use_project_end_date_for_float | Y | NOT_EVALUATED here | Raw preserved; no late/float anchor invented |
| sched_float_type | FT_FF | NOT_EVALUATED here | Raw preserved; no change to protected primary TF formula |
| Multiple path settings | Enabled, limited to 10 | NOT_EVALUATED here | No path calculation in forward-only scope |
Complete observed raw row and identified typed fields:
```json
{
  "project_id": "782",
  "retained_logic": true,
  "progress_override": false,
  "ss_lag_from_early_start": true,
  "use_expected_finish": true,
  "lag_calendar_policy": "PREDECESSOR",
  "external_relationship_policy": "BOTH",
  "set_planned_to_forecast": false,
  "raw_fields": [
    [
      "LevelPriorityList",
      "priority_type,ASC_BY_FIELD/ASC\u007f\u007f"
    ],
    [
      "enable_multiple_longest_path_calc",
      "Y"
    ],
    [
      "key_activity_for_multiple_longest_paths",
      ""
    ],
    [
      "level_all_rsrc_flag",
      "Y"
    ],
    [
      "level_float_thrs_cnt",
      "0"
    ],
    [
      "level_keep_sched_date_flag",
      "Y"
    ],
    [
      "level_outer_assign_flag",
      "N"
    ],
    [
      "level_outer_assign_priority",
      "5"
    ],
    [
      "level_over_alloc_pct",
      "25"
    ],
    [
      "level_within_float_flag",
      "N"
    ],
    [
      "limit_multiple_longest_path_calc",
      "Y"
    ],
    [
      "max_multiple_longest_path",
      "10"
    ],
    [
      "proj_id",
      "782"
    ],
    [
      "sched_calendar_on_relationship_lag",
      "rcal_Predecessor"
    ],
    [
      "sched_float_type",
      "FT_FF"
    ],
    [
      "sched_lag_early_start_flag",
      "Y"
    ],
    [
      "sched_open_critical_flag",
      "N"
    ],
    [
      "sched_outer_depend_type",
      "SD_Both"
    ],
    [
      "sched_progress_override",
      "N"
    ],
    [
      "sched_retained_logic",
      "Y"
    ],
    [
      "sched_setplantoforecast",
      "N"
    ],
    [
      "sched_use_expect_end_flag",
      "Y"
    ],
    [
      "sched_use_project_end_date_for_float",
      "Y"
    ],
    [
      "schedoptions_id",
      "1"
    ],
    [
      "use_total_float_multiple_longest_paths",
      "N"
    ]
  ]
}
```

PROJECT last_recalc_date=2026-07-01 00:01 (Data Date); last_schedule_date=2026-07-03 15:29; apply_actuals_date blank, add_act_remain_flag=N, control_updates_flag=N. These raw project observations do not authorize new duration-update or Actual Dates scheduling assumptions. TASK duration_type is preserved informationally; remaining hours are imported inputs. Suspend/resume fields are preserved and would block unsupported work if populated; both populations are zero here.
Semantic authority: [Oracle scheduling settings](https://docs.oracle.com/cd/G48897_01/p6help/en/90519.htm) and [Oracle activity status/duration fields](https://docs.oracle.com/cd/G48897_01/p6help/en/90151.htm). No P6/Deltek proprietary code or scoring was copied.

## Out-of-sequence inventory: definitions and exact populations

The audit compares actual relationship endpoints using signed predecessor-calendar lag: FS=predecessor Actual Finish to successor Actual Start; SS=Actual Start to Actual Start; FF=Actual Finish to Actual Finish; SF=Actual Start to Actual Finish. A known actual target earlier than that requirement is an observed ordering/lag exception. For nonnegative lag, a progressed target with an unfinished/unstarted required source endpoint is separately classified. These are transparent audit classifications, not an imported authoritative P6 OOS flag. A valid SS overlap is never rejected merely because predecessor finish is later.
| Relationship | All observed exceptions | With either endpoint unfinished | Unfinished successor |
|---|---:|---:|---:|
| FS | 2090 | 193 | 190 |
| SS | 375 | 109 | 93 |
| FF | 166 | 1 | 0 |
| SF | 0 | 0 | 0 |
Total: **2,631 relationships / 3,167 endpoint activities**. Of these, 2,328 are complete-to-complete historical exceptions; 303 relationships / 442 activities involve unfinished work, and 283 relationships / 418 activities have unfinished successors. There are 549 observed valid SS overlaps, excluded from the exception population. Source has no SF or negative-lag relationships. Twelve positive SS relationships have in-progress predecessors; this eligibility population is not itself an OOS classification.
Exact pattern counts:
```json
{
  "FS/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR": 2058,
  "FF/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR": 156,
  "SS/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR": 350,
  "FS/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG": 26,
  "SS/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG": 25,
  "FS/TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL": 6,
  "FF/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG": 9,
  "FF/TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL": 1
}
```

Six FS cases have unfinished predecessors and already-started successors (three successors remain unfinished, three complete). One FF case has a completed successor while predecessor finish is not actual. Eight positive-FS lags from completed predecessors remain pending at Data Date; only two have positive lag work already consumed before Data Date. All eight, including zero-consumed examples, follow:
```json
[
  {
    "id": "3518448",
    "predecessor": "OL_RSSOM_PR_502570",
    "successor": "OL_RSSOM_PR_502580",
    "lag": 40.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-05 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-06 08:00:00"
  },
  {
    "id": "3519266",
    "predecessor": "OL_RSSOM_PR_506770",
    "successor": "OL_RSSOM_PR_506780",
    "lag": 16.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-02 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-03 08:00:00"
  },
  {
    "id": "3539445",
    "predecessor": "OL_RSSOM_PR_511100",
    "successor": "OL_RSSOM_PR_511110",
    "lag": 48.0,
    "actual_finish": "2026-06-29 17:00:00",
    "deadline": "2026-07-05 17:00:00",
    "elapsed_work_to_data_date": 8.0,
    "p6_remaining_start": "2026-07-06 08:00:00"
  },
  {
    "id": "3540807",
    "predecessor": "OL_RSSOM_PR_513250",
    "successor": "OL_RSSOM_PR_513260",
    "lag": 40.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-05 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-06 08:00:00"
  },
  {
    "id": "3541630",
    "predecessor": "OL_RSSOM_PR_516770",
    "successor": "OL_RSSOM_PR_516780",
    "lag": 160.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-20 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-21 08:00:00"
  },
  {
    "id": "3541637",
    "predecessor": "OL_RSSOM_PR_516830",
    "successor": "OL_RSSOM_PR_516840",
    "lag": 16.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-02 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-03 08:00:00"
  },
  {
    "id": "35104010",
    "predecessor": "OL_RSSOM_DE_5244781",
    "successor": "OL_RSSOM_DE_5244801",
    "lag": 592.0,
    "actual_finish": "2026-03-27 16:00:00",
    "deadline": "2026-07-14 17:00:00",
    "elapsed_work_to_data_date": 520.0,
    "p6_remaining_start": "2026-07-15 08:00:00"
  },
  {
    "id": "36424126",
    "predecessor": "OL_RSSOM_PR_5017581",
    "successor": "OL_RSSOM_PR_5017591",
    "lag": 40.0,
    "actual_finish": "2026-06-30 17:00:00",
    "deadline": "2026-07-05 17:00:00",
    "elapsed_work_to_data_date": 0.0,
    "p6_remaining_start": "2026-07-06 08:00:00"
  }
]
```

Representative evidence for every observed pattern, retaining statuses, actuals, remaining dates/durations and actual-endpoint requirement:
```json
{
  "relationship_id": "3506789",
  "type": "FS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1597395",
  "predecessor_code": "OL_RSSOM_CN_500130",
  "successor_id": "1597396",
  "successor_code": "OL_RSSOM_CN_500150",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2025-04-01 08:00:00",
  "pre_actual_finish": "2025-04-14 17:00:00",
  "suc_actual_start": "2025-04-14 08:00:00",
  "suc_actual_finish": "2025-04-21 17:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2025-04-14 17:00:00"
}
```

```json
{
  "relationship_id": "3506794",
  "type": "FS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1595639",
  "predecessor_code": "OL_RSSOM_PL_105150",
  "successor_id": "1595640",
  "successor_code": "OL_RSSOM_PL_105230",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2023-10-11 00:00:00",
  "pre_actual_finish": "2023-10-19 00:00:00",
  "suc_actual_start": "2023-10-18 00:00:00",
  "suc_actual_finish": "2023-10-19 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2023-10-19 00:00:00"
}
```

```json
{
  "relationship_id": "3507535",
  "type": "FF",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1604831",
  "predecessor_code": "OL_RSSOM_DE_100210",
  "successor_id": "1604832",
  "successor_code": "OL_RSSOM_DE_102990",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2023-05-01 00:00:00",
  "pre_actual_finish": "2023-05-26 17:00:00",
  "suc_actual_start": "2023-05-26 00:00:00",
  "suc_actual_finish": "2023-05-26 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2023-05-26 17:00:00"
}
```

```json
{
  "relationship_id": "3507552",
  "type": "FF",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1604948",
  "predecessor_code": "OL_RSSOM_DE_100360",
  "successor_id": "1604949",
  "successor_code": "OL_RSSOM_DE_102560",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2022-11-18 00:00:00",
  "pre_actual_finish": "2023-02-15 00:00:00",
  "suc_actual_start": "2023-02-14 00:00:00",
  "suc_actual_finish": "2023-02-14 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2023-02-15 00:00:00"
}
```

```json
{
  "relationship_id": "3512463",
  "type": "SS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1604962",
  "predecessor_code": "OL_RSSOM_DE_105110",
  "successor_id": "1604640",
  "successor_code": "OL_RSSOM_DE_109640",
  "predecessor_status": "in_progress",
  "successor_status": "complete",
  "pre_actual_start": "2024-11-04 00:00:00",
  "pre_actual_finish": null,
  "suc_actual_start": "2024-06-26 00:00:00",
  "suc_actual_finish": "2025-08-29 00:00:00",
  "pre_remaining_start": "2026-07-02 08:00:00",
  "pre_remaining_finish": "2026-09-30 17:00:00",
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 504.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2024-11-04 00:00:00"
}
```

```json
{
  "relationship_id": "3514299",
  "type": "SS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_PREDECESSOR",
  "lag": 0.0,
  "predecessor_id": "1598157",
  "predecessor_code": "OL_RSSOM_CN_100060",
  "successor_id": "1598158",
  "successor_code": "OL_RSSOM_CN_100070",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2026-04-09 08:00:00",
  "pre_actual_finish": "2026-04-10 17:00:00",
  "suc_actual_start": "2026-04-01 08:00:00",
  "suc_actual_finish": "2026-05-13 17:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2026-04-09 08:00:00"
}
```

```json
{
  "relationship_id": "3516888",
  "type": "FS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 320.0,
  "predecessor_id": "1604748",
  "predecessor_code": "OL_RSSOM_DE_100140",
  "successor_id": "1600317",
  "successor_code": "OL_RSSOM_DE_401470",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2023-07-12 00:00:00",
  "pre_actual_finish": "2023-11-20 00:00:00",
  "suc_actual_start": "2023-11-06 00:00:00",
  "suc_actual_finish": "2023-12-14 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2024-01-17 17:00:00"
}
```

```json
{
  "relationship_id": "3517424",
  "type": "SS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 24.0,
  "predecessor_id": "1596233",
  "predecessor_code": "OL_RSSOM_10130",
  "successor_id": "1596234",
  "successor_code": "OL_RSSOM_10140",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2024-09-16 00:00:00",
  "pre_actual_finish": "2024-09-20 00:00:00",
  "suc_actual_start": "2024-09-13 00:00:00",
  "suc_actual_finish": "2024-09-18 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2024-09-18 17:00:00"
}
```

```json
{
  "relationship_id": "3518515",
  "type": "FS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 80.0,
  "predecessor_id": "1607115",
  "predecessor_code": "OL_RSSOM_PR_504330",
  "successor_id": "1607116",
  "successor_code": "OL_RSSOM_PR_504340",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2025-06-01 08:00:00",
  "pre_actual_finish": "2025-07-30 17:00:00",
  "suc_actual_start": "2025-07-31 08:00:00",
  "suc_actual_finish": "2026-03-30 17:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2025-08-09 17:00:00"
}
```

```json
{
  "relationship_id": "3521062",
  "type": "SS",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 80.0,
  "predecessor_id": "1605314",
  "predecessor_code": "OL_RSSOM_DE_100480",
  "successor_id": "1605320",
  "successor_code": "OL_RSSOM_DE_100500",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2023-04-06 00:00:00",
  "pre_actual_finish": "2023-04-14 00:00:00",
  "suc_actual_start": "2023-03-17 00:00:00",
  "suc_actual_finish": "2025-05-15 17:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2023-04-20 17:00:00"
}
```

```json
{
  "relationship_id": "3532613",
  "type": "FS",
  "pattern": "TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL",
  "lag": 0.0,
  "predecessor_id": "1604233",
  "predecessor_code": "OL_RSSOM_DE_533850",
  "successor_id": "1604230",
  "successor_code": "OL_RSSOM_DE_103700",
  "predecessor_status": "in_progress",
  "successor_status": "complete",
  "pre_actual_start": "2024-03-29 00:00:00",
  "pre_actual_finish": null,
  "suc_actual_start": "2024-06-28 17:00:00",
  "suc_actual_finish": "2024-06-28 17:00:00",
  "pre_remaining_start": "2026-07-02 08:00:00",
  "pre_remaining_finish": "2026-09-30 17:00:00",
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 504.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": null
}
```

```json
{
  "relationship_id": "3544284",
  "type": "FF",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 40.0,
  "predecessor_id": "1596249",
  "predecessor_code": "OL_RSSOM_160410",
  "successor_id": "1596247",
  "successor_code": "OL_RSSOM_159990",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2024-09-30 00:00:00",
  "pre_actual_finish": "2024-10-21 00:00:00",
  "suc_actual_start": "2024-10-18 00:00:00",
  "suc_actual_finish": "2024-10-21 00:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2024-10-25 17:00:00"
}
```

```json
{
  "relationship_id": "26498800",
  "type": "FS",
  "pattern": "TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL",
  "lag": 0.0,
  "predecessor_id": "12809665",
  "predecessor_code": "OL_RSSOM_SS_180180",
  "successor_id": "12809700",
  "successor_code": "OL_RSSOM_SS_180530",
  "predecessor_status": "not_started",
  "successor_status": "complete",
  "pre_actual_start": null,
  "pre_actual_finish": null,
  "suc_actual_start": "2026-06-09 08:00:00",
  "suc_actual_finish": "2026-06-18 17:00:00",
  "pre_remaining_start": "2026-07-02 08:00:00",
  "pre_remaining_finish": "2026-07-09 17:00:00",
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 48.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": null
}
```

```json
{
  "relationship_id": "36035621",
  "type": "FF",
  "pattern": "ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG",
  "lag": 80.0,
  "predecessor_id": "12076702",
  "predecessor_code": "OL_RSSOM_DE_568650",
  "successor_id": "11235187",
  "successor_code": "OL_RSSOM_537340",
  "predecessor_status": "complete",
  "successor_status": "complete",
  "pre_actual_start": "2025-08-28 00:00:00",
  "pre_actual_finish": "2026-01-21 17:00:00",
  "suc_actual_start": "2025-04-21 17:00:00",
  "suc_actual_finish": "2025-04-21 17:00:00",
  "pre_remaining_start": null,
  "pre_remaining_finish": null,
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 0.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": "2026-02-04 17:00:00"
}
```

```json
{
  "relationship_id": "36345404",
  "type": "FF",
  "pattern": "TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL",
  "lag": 0.0,
  "predecessor_id": "11013601",
  "predecessor_code": "OL_RSSOM_536890",
  "successor_id": "18387890",
  "successor_code": "OL_RSSOM_DE_5247611",
  "predecessor_status": "in_progress",
  "successor_status": "complete",
  "pre_actual_start": "2023-02-13 00:00:00",
  "pre_actual_finish": null,
  "suc_actual_start": "2026-05-22 08:00:00",
  "suc_actual_finish": "2026-06-05 17:00:00",
  "pre_remaining_start": "2026-07-02 08:00:00",
  "pre_remaining_finish": "2026-08-06 17:00:00",
  "suc_remaining_start": null,
  "suc_remaining_finish": null,
  "pre_remaining_hours": 200.0,
  "suc_remaining_hours": 0.0,
  "required_actual_endpoint": null
}
```

Complete exception relationship-ID inventory, grouped by type and pattern (lookups use immutable source/hash above):

### FF/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG

3544284, 36035621, 36035629, 36035632, 36035633, 36035650, 36035651, 36035685, 36035686


### FF/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR

3507535, 3507552, 3507553, 3507666, 3508105, 3508115, 3516765, 3516767, 3520866, 3520909, 3520918, 3520920, 3522022, 3522369, 3530520, 3535837, 3535839, 3535841, 3535842, 3535875, 3535883, 3535889, 3535893, 3535895, 3535896, 3535902, 3535904, 3535906, 3535907, 3535910, 3535912, 3535914, 3535916, 3535917, 3535976, 3536446, 3536460, 3536585, 3536588, 3536593, 3536883, 3536884, 3537039, 3537040, 3537043, 3537044, 3537052, 3541557, 3541558, 3541578, 3541938, 3541943, 3541950, 3543663, 3543666, 3543741, 3543859, 3543860, 3545035, 3546695, 3546930, 3546931, 3546932, 3546933, 3546934, 3546935, 3546936, 3546937, 3546953, 3546955, 3546956, 3546957, 3546958, 3546959, 3546960, 3546961, 3546962, 3547217, 3547218, 3547220, 3547223, 3547447, 3547474, 3547555, 3547556, 3547557, 3547558, 3547559, 3547560, 3547561, 3547562, 3547563, 3547564, 3547565, 8980868, 9022515, 9487059, 10442516, 10485545, 10700640, 10700643, 10700646, 10700649, 10700652, 10700655, 10700658, 10700661, 10700664, 10700667, 10700670, 10700673, 10700676, 10700679, 10700682, 10700685, 10700688, 10700691, 10700694, 10700697, 10700700, 10700703, 10700706, 10700709, 10700712, 10701665, 11564659, 18960954, 18960955, 18960957, 18960964, 18960965, 20008882, 22282783, 22752757, 22752758, 23234655, 26989350, 26989352, 26989354, 26989356, 26989358, 26989360, 26989362, 26989385, 27835374, 28460051, 28460052, 28460053, 28460057, 28460058, 28460059, 28460060, 29021407, 36115948, 36424190, 36424194


### FF/TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL

36345404


### FS/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG

3516888, 3518515, 3518528, 3518530, 3538851, 3541887, 3543848, 3543849, 3544655, 10400152, 11406237, 15127959, 18999495, 25028376, 26498736, 26498807, 26498808, 31455013, 32308177, 32619115, 32619117, 33434914, 34567598, 34567702, 36115991, 36191202


### FS/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR

3506789, 3506794, 3506795, 3507405, 3507408, 3507422, 3507438, 3507439, 3507440, 3507443, 3507444, 3507471, 3507473, 3507477, 3507508, 3507545, 3507548, 3507596, 3507597, 3507599, 3507653, 3507680, 3507776, 3507778, 3507793, 3507794, 3507796, 3507797, 3507798, 3507800, 3507813, 3507815, 3507816, 3507817, 3507819, 3507821, 3507823, 3507826, 3507827, 3507829, 3507831, 3507832, 3507833, 3507835, 3507836, 3507837, 3507839, 3507841, 3507846, 3507847, 3507849, 3507857, 3507862, 3507865, 3507871, 3507876, 3507879, 3507882, 3507885, 3507891, 3507892, 3507893, 3507895, 3507902, 3507903, 3507905, 3507906, 3507907, 3507909, 3507910, 3507916, 3507917, 3507919, 3507927, 3507936, 3507937, 3507939, 3507966, 3507967, 3507969, 3507974, 3507975, 3507977, 3507982, 3507983, 3507985, 3507993, 3507995, 3507997, 3507998, 3508001, 3508007, 3508013, 3508017, 3508028, 3508029, 3508031, 3508032, 3508033, 3508034, 3508037, 3508042, 3508050, 3508061, 3508062, 3508093, 3508094, 3508097, 3508110, 3508119, 3508348, 3508363, 3508567, 3508568, 3508570, 3508572, 3508574, 3508680, 3508681, 3508682, 3508685, 3508694, 3508789, 3508791, 3508796, 3508802, 3508806, 3508815, 3508817, 3510314, 3511146, 3511147, 3511148, 3511160, 3511161, 3511163, 3511206, 3511220, 3511256, 3511285, 3511371, 3512971, 3512972, 3512974, 3512992, 3512993, 3512995, 3513001, 3513002, 3513004, 3513022, 3513024, 3513030, 3513031, 3513033, 3513066, 3513067, 3513069, 3513468, 3514511, 3514517, 3514524, 3514535, 3515132, 3515446, 3515448, 3515451, 3515454, 3515455, 3515461, 3515463, 3515658, 3515665, 3515666, 3515668, 3515670, 3515671, 3515673, 3515674, 3515677, 3515679, 3515686, 3515690, 3516589, 3516681, 3516683, 3516697, 3516725, 3516736, 3516744, 3516747, 3516889, 3516891, 3516892, 3516894, 3516930, 3516941, 3516942, 3516943, 3516944, 3516945, 3517168, 3517183, 3517207, 3517249, 3517404, 3517547, 3517912, 3517915, 3518067, 3518070, 3518210, 3518254, 3518264, 3518289, 3518311, 3518320, 3518343, 3518345, 3518346, 3518348, 3518350, 3518371, 3518373, 3518375, 3518396, 3518398, 3518400, 3518403, 3518405, 3518415, 3518417, 3518425, 3518427, 3518441, 3518442, 3518444, 3518447, 3518451, 3518453, 3518454, 3518465, 3518468, 3518488, 3518503, 3518504, 3518505, 3518509, 3518516, 3518517, 3518519, 3518522, 3518524, 3518525, 3518527, 3518531, 3518533, 3518534, 3518536, 3518540, 3518543, 3518548, 3518549, 3518551, 3518552, 3518555, 3518556, 3518559, 3518560, 3518562, 3518563, 3518564, 3518570, 3518572, 3518573, 3518580, 3518590, 3518592, 3518597, 3518935, 3518953, 3518955, 3518973, 3518976, 3519037, 3519066, 3519071, 3519186, 3519194, 3519202, 3519206, 3519207, 3519209, 3519213, 3519214, 3519217, 3519243, 3519277, 3519279, 3519320, 3519325, 3519326, 3519327, 3519328, 3519329, 3519330, 3519331, 3519332, 3519333, 3519334, 3519340, 3519343, 3519346, 3519348, 3519350, 3519351, 3519354, 3519356, 3519357, 3519359, 3519361, 3519367, 3519370, 3519387, 3519389, 3519455, 3519520, 3519526, 3519709, 3519710, 3519747, 3520081, 3520349, 3520351, 3520518, 3520548, 3520551, 3520553, 3520555, 3520560, 3520569, 3520580, 3520581, 3520589, 3520696, 3520768, 3520793, 3520821, 3520840, 3520845, 3520847, 3520854, 3520858, 3520862, 3520890, 3520894, 3520898, 3520902, 3520904, 3520907, 3520930, 3521025, 3521051, 3521054, 3521058, 3521067, 3521096, 3521098, 3521100, 3521111, 3521118, 3521120, 3521122, 3521128, 3521296, 3521299, 3521300, 3521328, 3521341, 3521343, 3521959, 3521966, 3521968, 3521974, 3522001, 3522009, 3522024, 3522027, 3522028, 3522030, 3522039, 3522046, 3522048, 3522049, 3522052, 3522053, 3522054, 3522055, 3522080, 3522083, 3522090, 3522093, 3522107, 3522341, 3522353, 3522356, 3522361, 3522368, 3522422, 3522756, 3522996, 3523019, 3523035, 3523036, 3523037, 3523038, 3523039, 3523797, 3523798, 3523957, 3524066, 3524144, 3524145, 3524147, 3524196, 3524197, 3524199, 3524797, 3524798, 3524803, 3524804, 3524938, 3524950, 3524956, 3524957, 3524958, 3528380, 3528631, 3528644, 3528645, 3528647, 3528648, 3528649, 3528651, 3528663, 3528665, 3528695, 3528851, 3528852, 3528854, 3528864, 3528886, 3528889, 3528890, 3528892, 3528940, 3528941, 3528943, 3528953, 3528954, 3528956, 3528957, 3528958, 3528960, 3528966, 3528974, 3528975, 3528977, 3528988, 3528990, 3528991, 3528992, 3528994, 3529021, 3529024, 3529025, 3529026, 3529028, 3529037, 3529038, 3529039, 3529041, 3529042, 3529043, 3529045, 3529051, 3529072, 3529073, 3529075, 3529076, 3529077, 3529079, 3529088, 3529174, 3529177, 3529178, 3529179, 3529181, 3529918, 3529936, 3529937, 3529992, 3529993, 3529994, 3529995, 3529996, 3529997, 3529998, 3530023, 3530063, 3530489, 3530490, 3531009, 3531010, 3531011, 3531012, 3531013, 3531049, 3531050, 3531052, 3531053, 3531054, 3531078, 3531082, 3531083, 3531084, 3531085, 3531086, 3531087, 3531089, 3531105, 3531106, 3531107, 3531110, 3531114, 3531115, 3531116, 3531117, 3531119, 3531122, 3531123, 3531124, 3531137, 3531139, 3531140, 3531878, 3531895, 3531919, 3532037, 3532039, 3532147, 3532192, 3532387, 3532557, 3532622, 3533096, 3533104, 3534326, 3534338, 3534353, 3534374, 3534428, 3534664, 3534736, 3534737, 3534747, 3534750, 3534852, 3534876, 3534932, 3535099, 3535100, 3535101, 3535102, 3535108, 3535109, 3535110, 3535111, 3535115, 3535126, 3535220, 3535415, 3535622, 3535623, 3535624, 3535625, 3535626, 3535627, 3535628, 3535629, 3535630, 3535632, 3535634, 3535636, 3535639, 3535640, 3535641, 3535642, 3535651, 3535652, 3535653, 3535654, 3535655, 3535656, 3535657, 3535689, 3535698, 3535705, 3535756, 3535757, 3535798, 3535799, 3535808, 3535835, 3535846, 3535847, 3535848, 3535849, 3535850, 3535851, 3535852, 3535853, 3535855, 3535856, 3535857, 3535858, 3535859, 3535860, 3535861, 3535862, 3535864, 3535865, 3535866, 3535867, 3535868, 3535869, 3535870, 3535871, 3535873, 3535878, 3535887, 3535890, 3535892, 3535894, 3535946, 3535998, 3535999, 3536009, 3536021, 3536159, 3536163, 3536207, 3536217, 3536218, 3536220, 3536250, 3536280, 3536294, 3536300, 3536305, 3536326, 3536416, 3536420, 3536422, 3536426, 3536457, 3536458, 3536459, 3536481, 3536512, 3536513, 3536525, 3536526, 3536534, 3536600, 3536643, 3536654, 3536725, 3536726, 3536734, 3536735, 3536738, 3536742, 3536744, 3536745, 3536748, 3536753, 3536755, 3536758, 3536759, 3536763, 3536765, 3536768, 3536769, 3536773, 3536813, 3536815, 3536818, 3536819, 3536821, 3536826, 3536827, 3536828, 3536834, 3536837, 3536838, 3536839, 3536841, 3536843, 3536845, 3536847, 3536848, 3536878, 3536879, 3536880, 3536881, 3536882, 3536885, 3536886, 3536887, 3536888, 3536904, 3536928, 3536929, 3536936, 3536937, 3536944, 3536945, 3537020, 3537060, 3537554, 3537789, 3537808, 3537845, 3537994, 3538034, 3538035, 3538036, 3538127, 3538133, 3538134, 3538138, 3538176, 3538177, 3538179, 3538189, 3538194, 3538203, 3538204, 3538228, 3538281, 3538391, 3538392, 3538393, 3538608, 3538609, 3538664, 3538665, 3538777, 3538778, 3538788, 3538789, 3538790, 3538791, 3538796, 3538825, 3538829, 3538857, 3538858, 3538958, 3538960, 3538961, 3538972, 3538986, 3539075, 3539079, 3539116, 3539117, 3539129, 3539249, 3539288, 3539302, 3539313, 3539315, 3539419, 3539424, 3539432, 3539436, 3539438, 3539439, 3539443, 3539448, 3539450, 3539486, 3539522, 3539580, 3539675, 3539676, 3539678, 3539692, 3539694, 3539708, 3539720, 3539722, 3540417, 3540764, 3540788, 3540789, 3540790, 3540806, 3540830, 3540832, 3540836, 3540837, 3540866, 3540881, 3540883, 3540884, 3540892, 3540910, 3540940, 3540955, 3540957, 3540975, 3540990, 3540992, 3541266, 3541267, 3541278, 3541288, 3541289, 3541296, 3541304, 3541306, 3541364, 3541367, 3541368, 3541369, 3541370, 3541371, 3541372, 3541379, 3541385, 3541395, 3541397, 3541401, 3541404, 3541406, 3541442, 3541459, 3541502, 3541532, 3541543, 3541545, 3541548, 3541555, 3541575, 3541586, 3541656, 3541657, 3541658, 3541659, 3541660, 3541663, 3541664, 3541665, 3541666, 3541667, 3541680, 3541681, 3541683, 3541684, 3541727, 3541728, 3541731, 3541744, 3541745, 3541763, 3541764, 3541773, 3541774, 3541780, 3541781, 3541786, 3541787, 3541796, 3541797, 3541807, 3541809, 3541825, 3541827, 3541841, 3541843, 3541849, 3541851, 3541868, 3541870, 3541878, 3541880, 3541889, 3541904, 3541906, 3541912, 3541914, 3541921, 3541923, 3541928, 3541929, 3541932, 3542096, 3542219, 3542221, 3542222, 3543138, 3543175, 3543357, 3543358, 3543360, 3543369, 3543372, 3543373, 3543374, 3543376, 3543378, 3543381, 3543382, 3543384, 3543427, 3543431, 3543441, 3543522, 3543597, 3543702, 3543709, 3543727, 3543728, 3543729, 3543730, 3543737, 3543738, 3543753, 3543784, 3543863, 3543866, 3543886, 3543891, 3543940, 3543941, 3543943, 3543953, 3543954, 3543955, 3544049, 3544050, 3544052, 3544058, 3544107, 3544168, 3544189, 3544192, 3544198, 3544301, 3544304, 3544311, 3544327, 3544351, 3544354, 3544356, 3544409, 3544431, 3544466, 3544512, 3544515, 3544531, 3544551, 3544604, 3544607, 3544610, 3544685, 3544695, 3544716, 3544895, 3544948, 3544954, 3544963, 3544988, 3545007, 3545064, 3545154, 3545161, 3545162, 3545169, 3545190, 3545191, 3545243, 3545252, 3545253, 3545366, 3545420, 3545424, 3545490, 3545510, 3545530, 3545541, 3545544, 3545547, 3545548, 3545549, 3545550, 3545553, 3545556, 3545557, 3545565, 3545581, 3545681, 3545682, 3545802, 3545804, 3545808, 3545811, 3545812, 3545864, 3545865, 3545872, 3545873, 3545893, 3545894, 3545950, 3545951, 3545970, 3545983, 3545995, 3545996, 3546010, 3546011, 3546024, 3546031, 3546036, 3546037, 3546122, 3546140, 3546172, 3546230, 3546259, 3546295, 3546328, 3546334, 3546428, 3546491, 3546497, 3546524, 3546529, 3546541, 3546571, 3546582, 3546590, 3546598, 3546607, 3546615, 3546619, 3546623, 3546644, 3546648, 3546650, 3546698, 3546726, 3546728, 3546756, 3546763, 3546983, 3547033, 3547034, 3547035, 3547039, 3547040, 3547041, 3547042, 3547043, 3547044, 3547045, 3547046, 3547047, 3547048, 3547049, 3547085, 3547086, 3547087, 3547088, 3547089, 3547090, 3547091, 3547092, 3547093, 3547188, 3547219, 3547221, 3547253, 3547366, 3547367, 3547372, 3547464, 3547466, 3547468, 3547471, 3547479, 3547487, 3547489, 3547491, 3547496, 3547522, 3547523, 3547524, 3547525, 3547526, 3547527, 3547528, 3547529, 3547530, 3547531, 3547532, 3547667, 3547671, 3547679, 3547681, 3547684, 3547734, 3547736, 3547738, 3547746, 3547751, 3547784, 3547785, 3547786, 3547787, 3547788, 3547789, 3547790, 3547791, 3547792, 3547803, 3547819, 3547905, 3547909, 3548026, 3548037, 3548038, 3548039, 3548040, 3548043, 3548044, 3548045, 3548046, 3548048, 3548049, 3548050, 3548051, 3548053, 3548054, 3548055, 3548056, 3548077, 3548078, 3548080, 3548081, 3548097, 3548122, 3548123, 3548124, 3548134, 3548135, 3548136, 3548137, 3548138, 3548202, 3548206, 3548260, 3548262, 3548319, 3548324, 4946677, 4946678, 4946679, 4946680, 4946681, 4946682, 4946683, 4946684, 4946685, 4946686, 4946687, 8777327, 8980752, 8980754, 8980763, 8980765, 8980766, 8980769, 8980770, 8980771, 8980775, 8980776, 8980779, 8980781, 8980782, 8980783, 8980785, 8980788, 8980805, 8980806, 8980807, 8980808, 8980861, 8980869, 9022516, 9022592, 9022632, 9022635, 9022636, 9022638, 9022639, 9022641, 9022642, 9022644, 9022646, 9022647, 9022648, 9022650, 9022651, 9022653, 9022654, 9022656, 9022657, 9022659, 9022661, 9022662, 9022664, 9349093, 9349474, 10442505, 10442507, 10442514, 10442515, 10442520, 10442521, 10442522, 10442523, 10442524, 10442527, 10442528, 10442529, 10484092, 10484093, 10484098, 10484099, 10484107, 10484108, 10484109, 10484110, 10484111, 10528120, 10528121, 10592529, 10595335, 10700029, 10700164, 10700277, 10700288, 10700290, 10700305, 10700307, 10700310, 10700398, 10700399, 10700404, 10700405, 10700406, 10700407, 10700408, 10700607, 10700609, 10700610, 10700611, 10700613, 10700614, 10700616, 10700618, 10700619, 10700620, 10700622, 10700623, 10700625, 10700626, 10700637, 10700638, 10700641, 10700642, 10700644, 10700645, 10700647, 10700648, 10700650, 10700651, 10700653, 10700654, 10700656, 10700657, 10700659, 10700660, 10700662, 10700663, 10700665, 10700666, 10700668, 10700669, 10700671, 10700672, 10700674, 10700675, 10700677, 10700678, 10700680, 10700681, 10700683, 10700684, 10700686, 10700687, 10700689, 10700690, 10700692, 10700693, 10700695, 10700696, 10700698, 10700699, 10700701, 10700702, 10700704, 10700705, 10700707, 10700708, 10700710, 10700711, 10700940, 10700943, 10700944, 10700945, 10701052, 10701053, 10701171, 10701204, 10701206, 10701219, 10701220, 10701221, 10701264, 10701265, 10701664, 10742624, 10846542, 11406227, 11444414, 11444421, 11444424, 11564669, 11564671, 11564677, 11564681, 11564688, 11564698, 11564749, 11564750, 11564757, 11564758, 11564763, 11564764, 11564765, 11564769, 11640738, 11678765, 11678775, 11678805, 11716724, 11716726, 11716731, 11716732, 11929529, 11929531, 12124773, 12124862, 12124864, 12124871, 12126367, 12127799, 12127851, 12127859, 12127866, 12249016, 12249017, 12249022, 13551046, 13594819, 13965475, 14004331, 14239050, 14239057, 14239087, 14239114, 14239115, 14280581, 14280583, 14322059, 14322062, 14322063, 14322064, 14322065, 14322069, 14322070, 14322071, 14322072, 14322073, 14322075, 14322076, 14322077, 14322081, 14322082, 14322083, 14322084, 14322088, 14322149, 14322151, 14322174, 14322175, 14322176, 14322177, 14403759, 14403760, 14403761, 14403764, 14403786, 14403794, 14403795, 14403797, 14403798, 14403799, 14403800, 14403801, 14403803, 14403804, 14403805, 14403806, 14403807, 14403808, 14403809, 14403811, 14403812, 14403813, 14403815, 14403816, 14403817, 14403818, 14403819, 14403821, 14403823, 14403825, 14403828, 14403830, 14403832, 14403833, 14403834, 14403835, 14403839, 14403840, 14403842, 14403843, 14403846, 14403850, 14403851, 14403854, 14403855, 14403861, 14403862, 14403863, 14403864, 14403881, 14403882, 14403883, 14479894, 14479897, 14631506, 14631511, 15127958, 15441505, 15643353, 15643392, 15766707, 15886590, 15886603, 15886606, 15886614, 15886636, 15886640, 15886645, 16007021, 16086553, 16086557, 16086582, 16086583, 16086584, 16130294, 16130306, 16130307, 16130323, 16130328, 16130331, 16288334, 16288335, 16412881, 16412882, 16412902, 16412905, 16412908, 16412909, 16412911, 16602594, 16603212, 16603213, 16603214, 16603238, 16603239, 16603250, 16920276, 17019924, 18960947, 18960949, 18960950, 18999501, 18999502, 18999503, 18999504, 18999506, 18999507, 18999508, 18999516, 18999709, 18999710, 18999713, 18999714, 18999715, 19165494, 19165497, 19165498, 19165501, 19165503, 19165504, 19165505, 19165527, 19165545, 19165547, 19165580, 19165581, 19165582, 19165583, 19165584, 19165710, 19165711, 19165713, 19165719, 19165720, 19165721, 19175211, 19175212, 19175217, 19767724, 19767728, 19767792, 19767793, 19767794, 19767796, 19767797, 19806196, 19806208, 19806282, 19806283, 19806285, 19806317, 19806318, 19806329, 19806344, 19806354, 19806366, 19806377, 19844726, 19844738, 19844747, 19844753, 19844755, 19883228, 20817224, 21028940, 21028967, 21028968, 21067237, 21067248, 21067250, 21067309, 21067319, 21192349, 21193808, 21193813, 21324040, 21362632, 21401109, 21401110, 21531376, 21531377, 21531380, 21531381, 21531382, 21531384, 21531385, 21531387, 21531388, 21531389, 21531391, 21531393, 21531394, 21531396, 21531398, 21531399, 21531401, 21531402, 21531403, 21618343, 21618345, 21618347, 21656872, 21656874, 22004572, 22081365, 22081528, 22081648, 22118398, 22118399, 22118401, 22118402, 23190166, 23190169, 23234652, 23234653, 23467772, 23467773, 23467777, 23467778, 23467779, 23467780, 23467782, 23467783, 23467786, 23467787, 23467789, 23467791, 23504849, 23504850, 23504853, 23504855, 23504856, 23592303, 23592304, 23595995, 23596006, 23596025, 23596026, 23596030, 23596032, 23596033, 23596036, 23596059, 23596066, 23596067, 23596068, 24261477, 24261481, 24261483, 24261486, 24261492, 24261493, 24261494, 24261507, 24261508, 24261512, 24261524, 25028317, 25028321, 25028324, 25028330, 25028334, 25028336, 25028338, 25028342, 25028345, 25028367, 25192697, 25192699, 25192700, 25192702, 25192703, 25192707, 25192711, 25192712, 25192714, 25192723, 25192743, 25192757, 25192760, 25192767, 25192768, 25192771, 25192774, 25192775, 25192777, 25192779, 25192781, 25192783, 25192784, 25192787, 25192789, 25192791, 25192796, 25192798, 25192799, 25192800, 25192801, 25192805, 25192806, 25192812, 25192815, 25192819, 25318639, 25318642, 25318643, 25318645, 25318647, 25318648, 25318652, 25318654, 25318656, 25318658, 25318660, 25318663, 25318664, 25318666, 25318668, 25318669, 25318672, 25318675, 25318676, 25318679, 25318680, 25318683, 25318684, 25318688, 25318689, 25318692, 25318693, 25318696, 25318697, 25318699, 25318702, 25318705, 25318706, 25318709, 25355713, 25504020, 26498821, 26498822, 26498827, 26498828, 26904041, 26904104, 26904108, 26904110, 26904113, 26904114, 26950666, 26950667, 26950668, 26950678, 26989372, 26989375, 26989376, 26989377, 26989379, 26989380, 26989381, 26989382, 26989383, 26989384, 26989415, 26989417, 26989419, 26989535, 26989544, 26989582, 26989612, 26989727, 26989734, 26990387, 26990401, 26990406, 26990666, 26990667, 26990668, 26990669, 26990670, 26990671, 26990672, 26990673, 26990674, 26990675, 26993019, 27101917, 27101927, 27101937, 27101938, 27101939, 27101943, 27101947, 27101951, 27101953, 27101956, 27184717, 27184729, 27184735, 27184745, 27184754, 27184756, 27184758, 27184759, 27184764, 27190092, 27190112, 27226081, 27261914, 27261923, 27763870, 28215071, 28215090, 28459895, 28459903, 28459904, 28459908, 28459915, 28459918, 28459924, 28459928, 28459929, 28459931, 28459937, 28459938, 28459939, 28459942, 28459944, 28460068, 28460085, 28460110, 28460111, 28460177, 28496298, 28795047, 28795049, 28866668, 28866669, 28866671, 28866673, 28866685, 29057239, 29093529, 29093530, 29093531, 29129622, 29165705, 29201784, 29201785, 29201787, 29201835, 29201836, 29201839, 29201840, 29201842, 29201844, 29201848, 29201852, 29201856, 29201858, 29201859, 29273890, 29273891, 29273927, 29273928, 29273955, 29538587, 29811673, 29811676, 29811680, 29811684, 29996638, 29996639, 29996644, 29996657, 29996668, 29996673, 29996677, 29996692, 29996696, 29996699, 29996790, 30196571, 30196575, 30196579, 30430541, 30430544, 30964243, 30964250, 30964292, 31000633, 31037156, 31037161, 31037163, 31037166, 31109686, 31372395, 31455009, 31455011, 31491234, 31527476, 31527478, 31636192, 31636249, 31636303, 32019671, 32019675, 32019705, 32102356, 32102359, 32182339, 32538977, 32538995, 32619096, 32619102, 32619108, 32619114, 33236990, 33236995, 33237011, 33237015, 33237018, 33237110, 33317207, 33317208, 33436433, 33436537, 33436595, 33473282, 34412012, 34412014, 34412019, 34412021, 34412023, 34412025, 34412027, 34412041, 34567527, 34567535, 34567546, 34567547, 34567549, 34567551, 34567578, 34567637, 34567639, 34567640, 34567648, 34567649, 34567652, 34567660, 34567661, 34567662, 34567663, 34567664, 34567668, 34567674, 34567682, 34567683, 34567685, 34567686, 34567687, 34567688, 34567690, 34567695, 34567696, 34567716, 34567722, 34567725, 34567730, 34567731, 34567732, 34567734, 34567738, 34567739, 34567744, 34567745, 34891145, 34938697, 36115951, 36191201, 36193977, 36303866, 36303967, 36303968, 36303970, 36303983, 36303991, 36304005, 36345396, 36345401, 36424122, 36424123, 36504318, 38313889, 39174250, 39567472, 39567476, 39567478, 39650179, 39650183, 39686707, 39686830, 39686831, 39686990, 41392783, 41691661, 41691666, 41774689, 41774690, 41927559, 41927744, 41927890, 42091116, 43763373, 43763374, 43763401, 43916544, 43916576, 44375547, 44458411, 44458597, 44458846, 44458919


### FS/TARGET_PROGRESSED_SOURCE_ENDPOINT_NOT_ACTUAL

3532613, 26498800, 26989364, 36504319, 44458839, 44539337


### SS/ACTUAL_ENDPOINT_BEFORE_POSITIVE_LAG

3517424, 3521062, 3523230, 3524809, 3524811, 3524812, 3524813, 3524814, 3534442, 3535310, 21324048, 26498738, 26498739, 26498740, 26498741, 26498742, 27190241, 29165704, 29428798, 32178893, 32619103, 32619110, 33436471, 34567538, 41465774


### SS/ACTUAL_ENDPOINT_BEFORE_PREDECESSOR

3512463, 3514299, 3516873, 3520609, 3521029, 3521072, 3521073, 3521074, 3521076, 3521077, 3521078, 3521080, 3521081, 3521087, 3521214, 3521353, 3521989, 3522015, 3522057, 3522059, 3522061, 3523232, 3524090, 3524212, 3529297, 3529679, 3534325, 3534942, 3536329, 3536331, 3536333, 3536335, 3536336, 3536338, 3536340, 3536345, 3536346, 3536348, 3536350, 3536352, 3536354, 3536355, 3536358, 3536428, 3536429, 3536430, 3536431, 3536432, 3536433, 3536542, 3536543, 3536544, 3536545, 3536546, 3536547, 3536548, 3536549, 3536550, 3536551, 3536552, 3536553, 3536554, 3536555, 3536556, 3536557, 3536558, 3536559, 3536560, 3536561, 3536562, 3536610, 3536611, 3536612, 3536613, 3536614, 3536615, 3536619, 3536621, 3536622, 3536623, 3536624, 3536629, 3536630, 3536649, 3536729, 3538136, 3538137, 3538846, 3539262, 3539263, 3539264, 3539265, 3539540, 3541531, 3542074, 3542249, 3543237, 3543270, 3543271, 3543435, 3543457, 3543748, 3543793, 3544341, 3544342, 3544343, 3544344, 3544345, 3544346, 3544373, 3544377, 3544378, 3544456, 3544654, 3544970, 3544978, 3545004, 3545022, 3545025, 3546682, 3546683, 3546684, 3546685, 3546686, 3546687, 3546688, 3546689, 3546690, 3546691, 3546692, 3546982, 3546984, 3546995, 3546996, 3546997, 3546998, 3546999, 3547000, 3547001, 3547002, 3547003, 3547004, 3547018, 3547019, 3547020, 3547021, 3547022, 3547023, 3547024, 3547025, 3547026, 3547027, 3547031, 3547036, 3547037, 3547038, 3547050, 3547051, 3547052, 3547053, 3547054, 3547055, 3547056, 3547057, 3547058, 3547059, 3547060, 3547061, 3547062, 3547063, 3547064, 3547065, 3547066, 3547067, 3547068, 3547069, 3547450, 3547521, 3547610, 3547638, 3548070, 8980802, 8980803, 8980846, 9835015, 9835016, 9835021, 10400148, 10400534, 10400536, 10400537, 10400538, 10400539, 10400540, 10400541, 10400542, 10400544, 10400545, 10400546, 10400547, 10400548, 10400549, 10400550, 10400551, 10400552, 10400553, 10400555, 10400556, 10400557, 10400558, 10400559, 10400561, 10400562, 10400563, 10400564, 10400565, 10400569, 10400570, 12127731, 12127874, 12127875, 15886639, 16603245, 16603248, 19000046, 19844844, 19844848, 19883190, 19883213, 19921631, 20008881, 21192316, 21192337, 21192340, 21192343, 21192346, 21192649, 21618316, 21618319, 21618322, 21618325, 21618331, 21618334, 21618337, 21618340, 21618373, 21618376, 21618379, 23190404, 23190406, 23190408, 23190410, 23190411, 23190412, 23190414, 23190415, 23190418, 23190420, 23190422, 23190424, 23190426, 23190428, 23190430, 23190432, 23190434, 23190436, 23190437, 23190439, 23190441, 23190443, 23190445, 23190449, 23190451, 23190453, 23190455, 23190627, 23190628, 23190629, 23190630, 23190631, 23190632, 23190633, 23190634, 23190635, 23190636, 23190637, 23190639, 23190640, 23190641, 23190642, 23190643, 23190644, 23190645, 23190646, 23190647, 23190648, 23190649, 23190650, 23190651, 23190652, 23190653, 23190654, 23190887, 23190888, 23190889, 23190890, 23190891, 23190892, 23190894, 23190895, 23190896, 23190897, 23190898, 23190899, 23190900, 23190902, 23190903, 23190904, 23190905, 23190906, 23190908, 23190910, 23190911, 23190912, 23190913, 23190914, 24261497, 26498762, 26498796, 26989485, 26989516, 26990655, 26990665, 26993029, 27226074, 27226075, 28215062, 28215063, 28215089, 29201834, 29201838, 29201843, 29201847, 29201853, 29201857, 29466392, 33555921, 33555922, 36424127, 41927748


## Retained remaining-work rule and actual history

Activate explicitly with CPMConfig(component_calculation_policy="DIRECTIONAL_FORWARD", progress_scheduling_policy="P6_RETAINED_LOGIC"). Matching typed retained=Y/override=N is required. No Progress Override or Actual Dates mode is implemented. The existing iterative forward pass is reused through an optional requirement hook; its default policy is unchanged. New internal progress snapshots retain Actual Start/Finish, Data Date, observed-through date, imported Remaining Start/Finish and remaining hours. Observed-through Data Date is never fabricated as Actual Finish. Canonical Activities remain single immutable source records.
FS uses actual predecessor finish when complete, otherwise calculated remaining finish, plus predecessor-calendar lag. Remaining work is bounded by Data Date and all predecessor requirements. A completed-predecessor lag partly consumed before Data Date is represented by its absolute lagged finish, avoiding replay of the full lag from Data Date. SS with an in-progress predecessor and observed Early Start policy uses expired=clip(calendar_work(Actual Start, Data Date),0,lag); residual=lag-expired; requirement=calculated predecessor remaining ES+residual calendar work. Complete/not-started start endpoints retain existing handling. Progressed negative SS and progressed SF remain explicitly unsupported. FF remaining-finish requirements reuse the existing exact calendar inverse. Both constraint slots continue supplying their already-supported forward bounds; backward-only constraints are not claimed as applied.
Imported remaining dates are preserved evidence, not hidden release constraints. Ordinary unfinished retained work requires populated remaining hours and remaining-duration preference. Missing hours/original preference is blocked in this scope, rather than substituting original duration under a P6 label. Existing legacy fallback configuration is unchanged. Every returned early date passed duration, Data Date, calendar boundary, forward-constraint and relationship requirement audits. Late/float/path code is not called.
No progressed positive-SS relationship enters the final forward-usable population: those twelve source cases remain behind unsupported upstream conditions, principally Expected Finish. The expired-lag rule is synthetically validated and consistent with the earlier read-only source example (704h lag, 680h expired, 24h residual), but end-to-end real-file validation of that specific option remains incomplete. It is not claimed as established by the 874-activity agreement population.

All 40 progress cases pass; six parser/mapper cases pass. Manually derived cases use explicit 9h and split-shift calendars: completed Friday 16:00 + 4h lag permits Monday 11:00; Friday 15:00 actual start to Monday Data Date expires 2h of a 5h SS lag, leaving a Monday 11:00 requirement; split shifts/holiday cases independently verify expired work. Tests cover already-started successors, unfinished predecessors, multiple predecessors, completed successors, FF remaining duration, unsupported SF/options, exact history preservation, controlled invariant corruption, and 1,101-node iterative repeated runs.

## Real-evidence availability defect and conservative correction

The first prototype run returned 955 remaining records: 745 exact ES/EF pairs and 210 differences, maximum absolute difference 2215.983333333333h. The largest trace was unfinished task 1604233 (Expected Finish 2026-09-30) -> completed 1604230 (Actual Finish 2024-06-28) -> completed 1604231 (Actual Finish 2026-01-30) -> unfinished 1604234. Both completed records have imported early endpoints 2026-09-30; TASKPRED 3508811.aref is also 2026-09-30. The prototype treated actual history as a universally certified release and lost unresolved prospective retained logic through that completed chain.
Two proprietary-free reductions failed before correction, using only generic P -> completed H -> C and fixed January dates. The documented correction separates actual-date availability from future release availability. Completed actuals stay valid and unchanged, but releases reached from blocked/excluded work or unfinished FS/FF endpoints are marked FORWARD_BOUNDARY_BLOCKED until those bridge semantics are implemented. That uncertainty travels through completed chains and blocks affected unfinished descendants. No imported early proxy or aref replaces any calculated date. A prior draft test asserting that exclusion uncertainty disappears at completed history was strengthened to require that the history survives while the prospective release remains blocked.
This is an availability defect correction within the new forward scope, not a P6-specific formula fit. The graph/status rule is independent of raw variance and withheld 81 records, including 60 exact matches as well as 21 differences. There are 173 completed records whose historical dates remain available but prospective retained releases are unimplemented. Full P6 completed-proxy derivation remains a blocker.

## Expected Finish inventory and evidence

Exact source field is TASK.expect_end_date, preserved as Activity.expected_finish. No new date overwrite or duration rederivation is introduced. Imported TASK.restart_date/reend_date are now preserved as remaining_start/remaining_finish. Expected Finish use is explicitly enabled in SCHEDOPTIONS.
```json
{
  "count": 720,
  "by_status": {
    "in_progress": 519,
    "not_started": 201
  },
  "by_type": {
    "task": 720
  },
  "by_calendar": {
    "11683": 566,
    "3489": 35,
    "15907": 3,
    "3479": 98,
    "10485": 1,
    "3480": 17
  },
  "constraint_presence": {
    "false": 719,
    "true": 1
  },
  "relationship_incidence": {
    "(True, True)": 720
  }
}
```

All 720 are unfinished ordinary tasks: 519 in progress and 201 not started. All have incoming and outgoing relationships; 719 have no constraint and one has a constraint. Expected Finish equals imported EF on 588 tasks, is earlier on 53, and later on 79. Equality does not prove the forecast caused the scheduled date; existing remaining hours may already reflect P6 scheduling. Other dates can be stale or dominated by logic. A counterfactual P6 reschedule is not available to establish conflict-resolution/duration-update semantics. Therefore enabled or unknown use remains BLOCKED, including downstream dependencies. Explicitly disabled use preserves the field informationally and does not apply it; this behavior is synthetically tested.
Examples cover matching and differing forecasts with populated remaining duration, remaining dates and imported EF:
```json
{
  "id": "1595667",
  "code": "OL_RSSOM_262510",
  "name": "OMSF Site Wide - COT-PL Site Plan Review - Complete Package Submission (After Sch. 10 closed)",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 4,
  "successors": 1,
  "expected_finish": "2027-01-05 17:00:00",
  "remaining_start": "2026-07-02 08:00:00",
  "remaining_finish": "2027-01-05 17:00:00",
  "remaining_duration": 1024.0,
  "imported_es": "2026-07-02 08:00:00",
  "imported_ef": "2027-01-05 17:00:00",
  "expected_equals_ef": true,
  "expected_ef_variance_hours": 0.0,
  "duration_only_finish": "2027-01-05 17:00:00"
}
```

```json
{
  "id": "1595718",
  "code": "OL_RSSOM_161970",
  "name": "OMSF - TW Service Connection - Thorncliffe Service Connection - Package Preparation by PCo",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 11,
  "successors": 1,
  "expected_finish": "2026-11-13 17:00:00",
  "remaining_start": "2026-07-02 08:00:00",
  "remaining_finish": "2026-11-13 17:00:00",
  "remaining_duration": 752.0,
  "imported_es": "2026-07-02 08:00:00",
  "imported_ef": "2026-11-13 17:00:00",
  "expected_equals_ef": true,
  "expected_ef_variance_hours": 0.0,
  "duration_only_finish": "2026-11-13 17:00:00"
}
```

```json
{
  "id": "1595818",
  "code": "OL_RSSOM_12560",
  "name": "OMSF Maint. Building - COT-TB Building Permit - Final Determination by IA (90d + review) - (After SPR Completion)",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 8,
  "successors": 1,
  "expected_finish": "2026-07-17 17:00:00",
  "remaining_start": "2026-09-29 08:00:00",
  "remaining_finish": "2027-02-17 17:00:00",
  "remaining_duration": 776.0,
  "imported_es": "2026-09-29 08:00:00",
  "imported_ef": "2027-02-17 17:00:00",
  "expected_equals_ef": false,
  "expected_ef_variance_hours": -5160.0,
  "duration_only_finish": "2027-02-17 17:00:00"
}
```

```json
{
  "id": "1595866",
  "code": "OL_RSSOM_13040",
  "name": "OMSF MOW Building - COT-TB Building Permit - Final Determination by IA (30d + review)",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 9,
  "successors": 1,
  "expected_finish": "2026-07-17 17:00:00",
  "remaining_start": "2026-09-29 08:00:00",
  "remaining_finish": "2027-02-17 17:00:00",
  "remaining_duration": 776.0,
  "imported_es": "2026-09-29 08:00:00",
  "imported_ef": "2027-02-17 17:00:00",
  "expected_equals_ef": false,
  "expected_ef_variance_hours": -5160.0,
  "duration_only_finish": "2027-02-17 17:00:00"
}
```

```json
{
  "id": "1604208",
  "code": "OL_RSSOM_DE_518350",
  "name": "I-104 - Physical Security - B - Resubmission 2nd",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 1,
  "successors": 5,
  "expected_finish": "2026-08-06 08:00:00",
  "remaining_start": "2026-07-02 08:00:00",
  "remaining_finish": "2026-08-05 17:00:00",
  "remaining_duration": 192.0,
  "imported_es": "2026-07-02 08:00:00",
  "imported_ef": "2026-08-05 17:00:00",
  "expected_equals_ef": false,
  "expected_ef_variance_hours": 15.0,
  "duration_only_finish": "2026-08-05 17:00:00"
}
```

```json
{
  "id": "1605655",
  "code": "OL_RSSOM_DE_114410",
  "name": "S-226B - Gauge Analysis - Comments Review-2nd Submission",
  "status": "in_progress",
  "type": "task",
  "calendar": "11683",
  "constraint_present": false,
  "predecessors": 1,
  "successors": 4,
  "expected_finish": "2026-07-24 08:00:00",
  "remaining_start": "2026-07-02 08:00:00",
  "remaining_finish": "2026-07-23 17:00:00",
  "remaining_duration": 128.0,
  "imported_es": "2026-07-02 08:00:00",
  "imported_ef": "2026-07-23 17:00:00",
  "expected_equals_ef": false,
  "expected_ef_variance_hours": 15.0,
  "duration_only_finish": "2026-07-23 17:00:00"
}
```


## LOE boundaries and directional availability

The original LOE audit remains one isolated, 38 incoming-only and 18 with outgoing logic. All 57 LOE calculations remain excluded, as do ten isolated WBS summaries. A -> LOE does not block A early dates; late/float cannot use an unimplemented LOE boundary. LOE -> B blocks B early dates and unfinished downstream dependents; no edge is bypassed. A completed record reached from that uncertainty retains actual history, but does not certify a future retained release. Synthetic cases cover each direction. No LOE duration or summary dates were calculated.
Per-node flags are EARLY_DATES_CALCULATED/BLOCKED, LATE_DATES_BLOCKED and FLOAT_BLOCKED, with excluded records separately identified. forward_boundary_status distinguishes preserved history from an uncertified release. Per-relationship forward_status distinguishes usable, blocked, historical-only and excluded target; backward_status remains BLOCKED because this is a forward-only calculation. Blocking predecessor IDs retain the dependency trail. Original weak component identities/summaries are preserved for audit, without indiscriminately blocking their early dates.

## Final genuine-project disposition

| Population | Count |
|---|---:|
| Reliable remaining-work ES/EF | 874 |
| Of these, positive remaining duration | 583 |
| Preserved completed-history ES/EF | 14242 |
| Total available ES/EF records | 15116 |
| Early-date blocked activities | 8080 |
| Excluded activities | 67 |
| Completed actuals with blocked prospective release | 173 |
| Forward-usable relationships | 1437 |
| Forward-blocked relationships | 23663 |
| Historical-only relationships | 11152 |
| Relationships into excluded targets | 269 |
| Total original relationships preserved | 36521 |
Overall PARTIALLY_CALCULATED. All returned records lack late/float evaluation in this mode; PARTIALLY_CALCULATED is a direction-specific availability statement, not provisional numbers disguised as full CPM. Remaining-work results comprise 528 not-started tasks, 62 in-progress tasks and 284 milestones. Counts of overlapping blocking reasons, not disjoint populations:
```json
{
  "blocked_early_predecessor": 7551,
  "blocked_retained_boundary": 53,
  "expected_finish_unimplemented": 720,
  "loe_not_supported": 57,
  "completed_retained_boundary_unimplemented": 173,
  "wbs_summary_not_scheduled": 10
}
```

Returned diagnostic code counts:
```json
{
  "historical_constraint_not_applied": 344,
  "planned_start_before_data_date": 492,
  "loe_not_supported": 57,
  "wbs_summary_not_scheduled": 10,
  "expected_finish_unimplemented": 720,
  "completed_retained_boundary_unimplemented": 173,
  "late_and_float_not_evaluated": 1
}
```


## ES and EF comparison: valid remaining-work population only

Variance is calculated minus imported, in elapsed hours. Source and calculated values remain distinct. Excluded/blocked nodes and all 14,242 historical actual spans are absent from the denominator. Tolerance remains 0 seconds, classification-only; raw variances are not rounded or modified. Tolerance matches include exact matches.
| Metric | Comparable | Exact | Within tolerance | Different | Imported missing | Calculated missing | Median absolute h | Maximum absolute h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| early_start | 874 | 685 | 685 | 189 | 0 | 0 | 0.0 | 31.983333333333334 |
| early_finish | 874 | 685 | 685 | 189 | 0 | 0 | 0.0 | 31.983333333333334 |
All 189 differing records for each metric have zero effective duration and exactly zero working hours between imported and calculated timestamps on their own activity calendar. This is a separate exact boundary-equivalence observation, not an elapsed tolerance or reclassification as MATCH. All 583 positive-duration activities match both ES and EF exactly in this valid population. The protected convention retains Data Date for zero-work events, including non-working instants; P6 source commonly stamps the next work opening. No normalization formula was changed to improve agreement, and raw relationship inequalities are still independently audited.
LS/LF/TF/FF and critical-state agreement are NOT_EVALUATED. No authoritative completion anchor, simulated delay or path is implied by early-date agreement.

## Largest final discrepancies and evidence

The following top 20 for each metric are ordered by absolute raw variance, then stable visible code/internal ID. Every final entry is ZERO_WORK_BOUNDARY_REPRESENTATION with exactly zero calendar working-time variance. This classification describes the observed representation, not a blanket license to ignore date inequalities.

### early_start

| Internal ID / code | Calendar | Duration h | Imported timestamp | Calculated timestamp | Raw variance h |
|---|---|---:|---|---|---:|
| 13207170 / OL_RSSOM_538430 | 3480 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 1605645 / OL_RSSOM_DE_118960 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 1605665 / OL_RSSOM_DE_118980 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 8937999 / OL_RSSOM_DE_567010 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 8938002 / OL_RSSOM_DE_567030 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395993 / OL_RSSOM_DE_EGS_MS_1000 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395994 / OL_RSSOM_DE_EGS_MS_1010 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395995 / OL_RSSOM_DE_EGS_MS_1020 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395997 / OL_RSSOM_DE_EGS_MS_1040 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396007 / OL_RSSOM_DE_PTU_MS_1140 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396008 / OL_RSSOM_DE_PTU_MS_1150 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396009 / OL_RSSOM_DE_PTU_MS_1160 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396010 / OL_RSSOM_DE_PTU_MS_1170 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396011 / OL_RSSOM_DE_PTU_MS_1180 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396012 / OL_RSSOM_DE_PTU_MS_1190 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396013 / OL_RSSOM_DE_PTU_MS_1200 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809689 / OL_RSSOM_SS_180420 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809690 / OL_RSSOM_SS_180430 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809704 / OL_RSSOM_SS_180570 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809705 / OL_RSSOM_SS_180580 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |

### early_finish

| Internal ID / code | Calendar | Duration h | Imported timestamp | Calculated timestamp | Raw variance h |
|---|---|---:|---|---|---:|
| 13207170 / OL_RSSOM_538430 | 3480 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 1605645 / OL_RSSOM_DE_118960 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 1605665 / OL_RSSOM_DE_118980 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 8937999 / OL_RSSOM_DE_567010 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 8938002 / OL_RSSOM_DE_567030 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395993 / OL_RSSOM_DE_EGS_MS_1000 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395994 / OL_RSSOM_DE_EGS_MS_1010 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395995 / OL_RSSOM_DE_EGS_MS_1020 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4395997 / OL_RSSOM_DE_EGS_MS_1040 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396007 / OL_RSSOM_DE_PTU_MS_1140 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396008 / OL_RSSOM_DE_PTU_MS_1150 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396009 / OL_RSSOM_DE_PTU_MS_1160 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396010 / OL_RSSOM_DE_PTU_MS_1170 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396011 / OL_RSSOM_DE_PTU_MS_1180 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396012 / OL_RSSOM_DE_PTU_MS_1190 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 4396013 / OL_RSSOM_DE_PTU_MS_1200 | 11683 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809689 / OL_RSSOM_SS_180420 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809690 / OL_RSSOM_SS_180430 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809704 / OL_RSSOM_SS_180570 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
| 12809705 / OL_RSSOM_SS_180580 | 10485 | 0.0 | 2026-07-02 08:00:00 | 2026-07-01 00:01:00 | -31.983333333333334 |
Detailed unique activity evidence for those rankings (actual/progress/remaining dates, source constraints, controlling predecessors, all incident relationships, raw comparison and availability):
```json
{
  "activity": {
    "activity_id": "13207170",
    "activity_code": "OL_RSSOM_538430",
    "activity_name": "RS System Design - SDS ESAC A Submission",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "3480",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2028-11-09 17:00:00",
    "imported_late_finish": "2028-11-09 17:00:00",
    "imported_total_float_hours": 4744.0,
    "imported_free_float_hours": 4008.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "2969248",
  "predecessors": [
    {
      "relationship_id": "27190117",
      "predecessor_activity_id": "13087138",
      "successor_activity_id": "13207170",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    }
  ],
  "successors": [
    {
      "relationship_id": "27190165",
      "predecessor_activity_id": "13207170",
      "successor_activity_id": "11013608",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "13207170",
      "code": "OL_RSSOM_538430",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "13207170",
      "code": "OL_RSSOM_538430",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM_5d/w+H-1",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / PRC Procurement & Manufacturing / 3 Vehicle Procurement/Manufacturing & Factory testing / 8 Rolling Stock Summary Activities",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "1605645",
    "activity_code": "OL_RSSOM_DE_118960",
    "activity_name": "S-225B - Train Interior Layout Comments Review-2nd Submission",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2026-09-24 17:00:00",
    "imported_late_finish": "2026-09-24 17:00:00",
    "imported_total_float_hours": 472.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "1605645",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2026-02-27 08:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2026-02-27 08:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "443065",
  "predecessors": [
    {
      "relationship_id": "3515455",
      "predecessor_activity_id": "1605643",
      "successor_activity_id": "1605645",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3515764",
      "predecessor_activity_id": "1605645",
      "successor_activity_id": "1606323",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3545571",
      "predecessor_activity_id": "1605645",
      "successor_activity_id": "1614856",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3546342",
      "predecessor_activity_id": "1605645",
      "successor_activity_id": "1615012",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "1605645",
      "code": "OL_RSSOM_DE_118960",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "1605645",
      "code": "OL_RSSOM_DE_118960",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 1 Overall Design (Including South & OMSF & SUSS & North) / 3 Plans & Design Submittals / 99 S-225 - Train Interior Layout / 2 S-225B - Train Interior Layout",
    "planned_start": "2026-03-26 08:00",
    "planned_finish": "2026-04-16 17:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "1605665",
    "activity_code": "OL_RSSOM_DE_118980",
    "activity_name": "S-227B - Train - Passenger Flow and Evacuation Analysis - Comments Review-2nd Submission",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2026-11-10 17:00:00",
    "imported_late_finish": "2026-11-10 17:00:00",
    "imported_total_float_hours": 728.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "1605665",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2026-02-23 16:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2026-02-23 16:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "443069",
  "predecessors": [
    {
      "relationship_id": "3515457",
      "predecessor_activity_id": "1605663",
      "successor_activity_id": "1605665",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "3515818",
      "predecessor_activity_id": "1605665",
      "successor_activity_id": "1600225",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3545603",
      "predecessor_activity_id": "1605665",
      "successor_activity_id": "1614864",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "3546361",
      "predecessor_activity_id": "1605665",
      "successor_activity_id": "1615016",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "1605665",
      "code": "OL_RSSOM_DE_118980",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "1605665",
      "code": "OL_RSSOM_DE_118980",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 1 Overall Design (Including South & OMSF & SUSS & North) / 3 Plans & Design Submittals / 101 S-227 - Train - Passenger Flow and Evacuation Analysis / 2 S-227B - Train \ufffd Passenger Flow and Evacuation Analysis",
    "planned_start": "2026-03-09 16:00",
    "planned_finish": "2026-03-30 16:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "8937999",
    "activity_code": "OL_RSSOM_DE_567010",
    "activity_name": "I-302B - PTUS-Equipment Room Layout - Development no later than eight hundred forty (840) days following FC",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-05-27 17:00:00",
    "imported_late_finish": "2031-05-27 17:00:00",
    "imported_total_float_hours": 9840.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [
      "FINISH_ON_OR_AFTER"
    ],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      "FINISH_ON_OR_AFTER",
      "2025-03-06 17:00:00"
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "2455302",
  "predecessors": [
    {
      "relationship_id": "19165493",
      "predecessor_activity_id": "1600278",
      "successor_activity_id": "8937999",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "19165485",
      "predecessor_activity_id": "8937999",
      "successor_activity_id": "8938002",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "8937999",
      "code": "OL_RSSOM_DE_567010",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "8937999",
      "code": "OL_RSSOM_DE_567010",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / DH Design Handovers / 2 North Handovers / 2 PA Schedule 43 - Appendix A - Part B - Critical North Civil Infrastructure Data / 2 PTUS",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "8938002",
    "activity_code": "OL_RSSOM_DE_567030",
    "activity_name": "I-302B - Equipment Room Layout - Submittal Review by RSSOM Project Co",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-05-27 17:00:00",
    "imported_late_finish": "2031-05-27 17:00:00",
    "imported_total_float_hours": 9840.0,
    "imported_free_float_hours": 2664.0,
    "controlling_predecessor_ids": [
      "8937999"
    ],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [
      "19165485"
    ],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "NOT_STARTED_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [
      {
        "relationship_id": "19165485",
        "predecessor_id": "8937999",
        "predecessor_code": "OL_RSSOM_DE_567010",
        "successor_id": "8938002",
        "successor_code": "OL_RSSOM_DE_567030",
        "relationship_type": "FS",
        "lag_hours": 0.0,
        "lag_calendar_policy": "PREDECESSOR",
        "lag_calendar_id": "11683",
        "direction": "FORWARD",
        "requirement_kind": "EARLY_START",
        "required_timestamp": "2026-07-01 00:01:00",
        "tied": false,
        "controlling": true,
        "qualification_reason": "RETAINED_REMAINING_ENDPOINT",
        "relationship_free_float_hours": null
      }
    ],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "2455302",
  "predecessors": [
    {
      "relationship_id": "19165485",
      "predecessor_activity_id": "8937999",
      "successor_activity_id": "8938002",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "31636188",
      "predecessor_activity_id": "8938002",
      "successor_activity_id": "1600229",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "8938002",
      "code": "OL_RSSOM_DE_567030",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "8938002",
      "code": "OL_RSSOM_DE_567030",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / DH Design Handovers / 2 North Handovers / 2 PA Schedule 43 - Appendix A - Part B - Critical North Civil Infrastructure Data / 2 PTUS",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4395993",
    "activity_code": "OL_RSSOM_DE_EGS_MS_1000",
    "activity_name": "Tranche 1a- Guideway and Advanced Civils- Critical",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-04-14 17:00:00",
    "imported_late_finish": "2031-04-14 17:00:00",
    "imported_total_float_hours": 9600.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249422",
  "predecessors": [
    {
      "relationship_id": "10400571",
      "predecessor_activity_id": "1600760",
      "successor_activity_id": "4395993",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400572",
      "predecessor_activity_id": "1600805",
      "successor_activity_id": "4395993",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400573",
      "predecessor_activity_id": "1600985",
      "successor_activity_id": "4395993",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10739392",
      "predecessor_activity_id": "4395993",
      "successor_activity_id": "4733075",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4395993",
      "code": "OL_RSSOM_DE_EGS_MS_1000",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4395993",
      "code": "OL_RSSOM_DE_EGS_MS_1000",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 1 Elevated Structure / 1 Elevated Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4395994",
    "activity_code": "OL_RSSOM_DE_EGS_MS_1010",
    "activity_name": "Tranche 1b- Guideway and Advanced Civils- Critical",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-04-14 17:00:00",
    "imported_late_finish": "2031-04-14 17:00:00",
    "imported_total_float_hours": 9600.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249422",
  "predecessors": [
    {
      "relationship_id": "10400574",
      "predecessor_activity_id": "1601705",
      "successor_activity_id": "4395994",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400575",
      "predecessor_activity_id": "1601720",
      "successor_activity_id": "4395994",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10739393",
      "predecessor_activity_id": "4395994",
      "successor_activity_id": "4733075",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4395994",
      "code": "OL_RSSOM_DE_EGS_MS_1010",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4395994",
      "code": "OL_RSSOM_DE_EGS_MS_1010",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 1 Elevated Structure / 1 Elevated Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4395995",
    "activity_code": "OL_RSSOM_DE_EGS_MS_1020",
    "activity_name": "Tranche 2- Northern Station- Critical",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-04-14 17:00:00",
    "imported_late_finish": "2031-04-14 17:00:00",
    "imported_total_float_hours": 9600.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249422",
  "predecessors": [
    {
      "relationship_id": "10400576",
      "predecessor_activity_id": "1600925",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400577",
      "predecessor_activity_id": "1600940",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400578",
      "predecessor_activity_id": "1600955",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400579",
      "predecessor_activity_id": "1601135",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400580",
      "predecessor_activity_id": "1601150",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400581",
      "predecessor_activity_id": "1601165",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400582",
      "predecessor_activity_id": "1601285",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400583",
      "predecessor_activity_id": "1601300",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400584",
      "predecessor_activity_id": "1601315",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400585",
      "predecessor_activity_id": "1601450",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400586",
      "predecessor_activity_id": "1601465",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400587",
      "predecessor_activity_id": "1601480",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400588",
      "predecessor_activity_id": "1601615",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400589",
      "predecessor_activity_id": "1601630",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400590",
      "predecessor_activity_id": "1601645",
      "successor_activity_id": "4395995",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10739394",
      "predecessor_activity_id": "4395995",
      "successor_activity_id": "4733075",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4395995",
      "code": "OL_RSSOM_DE_EGS_MS_1020",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4395995",
      "code": "OL_RSSOM_DE_EGS_MS_1020",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 1 Elevated Structure / 1 Elevated Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4395997",
    "activity_code": "OL_RSSOM_DE_EGS_MS_1040",
    "activity_name": "Tranche 3- Center Stations- Critical",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-04-14 17:00:00",
    "imported_late_finish": "2031-04-14 17:00:00",
    "imported_total_float_hours": 9600.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249422",
  "predecessors": [
    {
      "relationship_id": "10400591",
      "predecessor_activity_id": "1600820",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400592",
      "predecessor_activity_id": "1600835",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400593",
      "predecessor_activity_id": "1601030",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400594",
      "predecessor_activity_id": "1601045",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400595",
      "predecessor_activity_id": "1601180",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400596",
      "predecessor_activity_id": "1601195",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400597",
      "predecessor_activity_id": "1601345",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400598",
      "predecessor_activity_id": "1601360",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400599",
      "predecessor_activity_id": "1601510",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    },
    {
      "relationship_id": "10400600",
      "predecessor_activity_id": "1601525",
      "successor_activity_id": "4395997",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "10739396",
      "predecessor_activity_id": "4395997",
      "successor_activity_id": "4733075",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4395997",
      "code": "OL_RSSOM_DE_EGS_MS_1040",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4395997",
      "code": "OL_RSSOM_DE_EGS_MS_1040",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 1 Elevated Structure / 1 Elevated Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396007",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1140",
    "activity_name": "1a - Gerrard Portal, Minton Portal -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701465",
      "predecessor_activity_id": "1600740",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701466",
      "predecessor_activity_id": "4577059",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701467",
      "predecessor_activity_id": "1600785",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701468",
      "predecessor_activity_id": "4577104",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701469",
      "predecessor_activity_id": "1600965",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701470",
      "predecessor_activity_id": "4577149",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701471",
      "predecessor_activity_id": "1601535",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701472",
      "predecessor_activity_id": "4639460",
      "successor_activity_id": "4396007",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742289",
      "predecessor_activity_id": "4396007",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742395",
      "predecessor_activity_id": "4396007",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396007",
      "code": "OL_RSSOM_DE_PTU_MS_1140",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396007",
      "code": "OL_RSSOM_DE_PTU_MS_1140",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396008",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1150",
    "activity_name": "1b - Gerrard Portal, Minton Portal -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10700805",
      "predecessor_activity_id": "1601055",
      "successor_activity_id": "4396008",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10700807",
      "predecessor_activity_id": "4577194",
      "successor_activity_id": "4396008",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10700808",
      "predecessor_activity_id": "4577209",
      "successor_activity_id": "4396008",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10700809",
      "predecessor_activity_id": "4577269",
      "successor_activity_id": "4396008",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10700810",
      "predecessor_activity_id": "4577284",
      "successor_activity_id": "4396008",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742290",
      "predecessor_activity_id": "4396008",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742396",
      "predecessor_activity_id": "4396008",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396008",
      "code": "OL_RSSOM_DE_PTU_MS_1150",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396008",
      "code": "OL_RSSOM_DE_PTU_MS_1150",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396009",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1160",
    "activity_name": "2a - Pape Guideway and Sammon Crossover -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701491",
      "predecessor_activity_id": "4712268",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701492",
      "predecessor_activity_id": "4712270",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701493",
      "predecessor_activity_id": "4712269",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701494",
      "predecessor_activity_id": "4712271",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701495",
      "predecessor_activity_id": "4712272",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701496",
      "predecessor_activity_id": "1601595",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701497",
      "predecessor_activity_id": "4712273",
      "successor_activity_id": "4396009",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742291",
      "predecessor_activity_id": "4396009",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742397",
      "predecessor_activity_id": "4396009",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396009",
      "code": "OL_RSSOM_DE_PTU_MS_1160",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396009",
      "code": "OL_RSSOM_DE_PTU_MS_1160",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396010",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1170",
    "activity_name": "2b - Pape Guideway and Sammon Crossover -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701506",
      "predecessor_activity_id": "1601115",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701507",
      "predecessor_activity_id": "4712275",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701508",
      "predecessor_activity_id": "4618444",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701509",
      "predecessor_activity_id": "4618596",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701510",
      "predecessor_activity_id": "4639538",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701511",
      "predecessor_activity_id": "4639553",
      "successor_activity_id": "4396010",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742292",
      "predecessor_activity_id": "4396010",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742398",
      "predecessor_activity_id": "4396010",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396010",
      "code": "OL_RSSOM_DE_PTU_MS_1170",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396010",
      "code": "OL_RSSOM_DE_PTU_MS_1170",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396011",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1180",
    "activity_name": "3 - Cosburn Station -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701514",
      "predecessor_activity_id": "1601100",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701516",
      "predecessor_activity_id": "1601250",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701517",
      "predecessor_activity_id": "1601415",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701518",
      "predecessor_activity_id": "1601580",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701519",
      "predecessor_activity_id": "4577224",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701520",
      "predecessor_activity_id": "4577239",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701521",
      "predecessor_activity_id": "4577254",
      "successor_activity_id": "4396011",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742293",
      "predecessor_activity_id": "4396011",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742399",
      "predecessor_activity_id": "4396011",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396011",
      "code": "OL_RSSOM_DE_PTU_MS_1180",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396011",
      "code": "OL_RSSOM_DE_PTU_MS_1180",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396012",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1190",
    "activity_name": "4 - Pape Station -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701523",
      "predecessor_activity_id": "1601085",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701524",
      "predecessor_activity_id": "1601235",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701525",
      "predecessor_activity_id": "1601400",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701526",
      "predecessor_activity_id": "1601565",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701527",
      "predecessor_activity_id": "4639478",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701528",
      "predecessor_activity_id": "4639508",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701529",
      "predecessor_activity_id": "4639523",
      "successor_activity_id": "4396012",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742294",
      "predecessor_activity_id": "4396012",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742400",
      "predecessor_activity_id": "4396012",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396012",
      "code": "OL_RSSOM_DE_PTU_MS_1190",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396012",
      "code": "OL_RSSOM_DE_PTU_MS_1190",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "4396013",
    "activity_code": "OL_RSSOM_DE_PTU_MS_1200",
    "activity_name": "5- Bain EEB -Phase A",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "11683",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2031-02-13 17:00:00",
    "imported_late_finish": "2031-02-13 17:00:00",
    "imported_total_float_hours": 9280.0,
    "imported_free_float_hours": 336.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "MILESTONE",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": null,
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": null,
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": null,
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "1249423",
  "predecessors": [
    {
      "relationship_id": "10701531",
      "predecessor_activity_id": "1601070",
      "successor_activity_id": "4396013",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701532",
      "predecessor_activity_id": "1601550",
      "successor_activity_id": "4396013",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10701533",
      "predecessor_activity_id": "4639493",
      "successor_activity_id": "4396013",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "successors": [
    {
      "relationship_id": "10742295",
      "predecessor_activity_id": "4396013",
      "successor_activity_id": "1600231",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    },
    {
      "relationship_id": "10742401",
      "predecessor_activity_id": "4396013",
      "successor_activity_id": "4577042",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "4396013",
      "code": "OL_RSSOM_DE_PTU_MS_1200",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "4396013",
      "code": "OL_RSSOM_DE_PTU_MS_1200",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_NotStart",
    "raw_activity_type": "TT_FinMile",
    "calendar_name": "RSSOM 5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / DSE Design/Engineering / AD PA Schedule 10 - Appendix A - Minimum Works Submittals / 2 North Design / 4 Interface Control Documents / 2 NP - I-103 - NP Interface Control Documents (Project Co to North Civil Contractors)- EXT / 2 Tunnel Structure / 1 Tunnel Structure Milestones",
    "planned_start": "2026-07-02 08:00",
    "planned_finish": "2026-07-02 08:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "12809689",
    "activity_code": "OL_RSSOM_SS_180420",
    "activity_name": "SUSS - Architectural and Urban Design Quality",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "10485",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2029-03-14 17:00:00",
    "imported_late_finish": "2029-03-14 17:00:00",
    "imported_total_float_hours": 5424.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "12809689",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2025-10-22 00:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2025-10-22 00:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "3406263",
  "predecessors": [
    {
      "relationship_id": "26498791",
      "predecessor_activity_id": "12809668",
      "successor_activity_id": "12809689",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    }
  ],
  "successors": [
    {
      "relationship_id": "26498771",
      "predecessor_activity_id": "12809689",
      "successor_activity_id": "12809669",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "12809689",
      "code": "OL_RSSOM_SS_180420",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "12809689",
      "code": "OL_RSSOM_SS_180420",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM_5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 5 System Assurance / 2 Security Deliverables / 2 System Design Security Submission / 7 Design Reviews / 3.1 Phase B Design Reviews / 3.1.2 Security Risk Assessments (SRA) / 3.1.2.3 Full SRA Review:",
    "planned_start": "2025-10-14 08:00",
    "planned_finish": "2025-10-14 17:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "12809690",
    "activity_code": "OL_RSSOM_SS_180430",
    "activity_name": "SUSS - Building Structures - Structural",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "10485",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2029-08-16 17:00:00",
    "imported_late_finish": "2029-08-16 17:00:00",
    "imported_total_float_hours": 6280.0,
    "imported_free_float_hours": 104.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "12809690",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2025-10-31 00:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2025-10-31 00:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "3406263",
  "predecessors": [
    {
      "relationship_id": "26498792",
      "predecessor_activity_id": "12809668",
      "successor_activity_id": "12809690",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    }
  ],
  "successors": [
    {
      "relationship_id": "26624930",
      "predecessor_activity_id": "12809690",
      "successor_activity_id": "12809709",
      "relationship_type": "FF",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FF"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "12809690",
      "code": "OL_RSSOM_SS_180430",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "12809690",
      "code": "OL_RSSOM_SS_180430",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM_5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 5 System Assurance / 2 Security Deliverables / 2 System Design Security Submission / 7 Design Reviews / 3.1 Phase B Design Reviews / 3.1.2 Security Risk Assessments (SRA) / 3.1.2.3 Full SRA Review:",
    "planned_start": "2025-10-14 08:00",
    "planned_finish": "2025-10-14 17:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "12809704",
    "activity_code": "OL_RSSOM_SS_180570",
    "activity_name": "OMSF Site Risk Assessment",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "10485",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2029-08-16 17:00:00",
    "imported_late_finish": "2029-08-16 17:00:00",
    "imported_total_float_hours": 6280.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "12809704",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2025-10-09 00:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2025-10-09 00:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "3406267",
  "predecessors": [
    {
      "relationship_id": "26498807",
      "predecessor_activity_id": "12809647",
      "successor_activity_id": "12809704",
      "relationship_type": "FS",
      "lag_hours": 88.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "26498809",
      "predecessor_activity_id": "12809704",
      "successor_activity_id": "12809706",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    },
    {
      "relationship_id": "33746891",
      "predecessor_activity_id": "12809704",
      "successor_activity_id": "12809711",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "12809704",
      "code": "OL_RSSOM_SS_180570",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "12809704",
      "code": "OL_RSSOM_SS_180570",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM_5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 5 System Assurance / 2 Security Deliverables / 2 System Design Security Submission / 6 Plan Development / 4.4 Security Risk Assessment Report",
    "planned_start": "2025-11-03 08:00",
    "planned_finish": "2025-11-03 17:00"
  }
}
```

```json
{
  "activity": {
    "activity_id": "12809705",
    "activity_code": "OL_RSSOM_SS_180580",
    "activity_name": "SUSS Site Risk Assessment",
    "effective_duration_hours": 0.0,
    "effective_calendar_id": "10485",
    "calculated_early_start": "2026-07-01 00:01:00",
    "calculated_early_finish": "2026-07-01 00:01:00",
    "calculated_late_start": null,
    "calculated_late_finish": null,
    "calculated_total_float_hours": null,
    "calculated_free_float_hours": null,
    "calculated_critical": false,
    "calculated_near_critical": false,
    "imported_early_start": "2026-07-02 08:00:00",
    "imported_early_finish": "2026-07-02 08:00:00",
    "imported_late_start": "2029-08-16 17:00:00",
    "imported_late_finish": "2029-08-16 17:00:00",
    "imported_total_float_hours": 6280.0,
    "imported_free_float_hours": 0.0,
    "controlling_predecessor_ids": [],
    "controlling_successor_ids": [],
    "controlling_relationship_ids": [],
    "controlling_constraint": null,
    "applied_constraints": [],
    "diagnostics": [
      {
        "code": "planned_start_before_data_date",
        "message": "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.",
        "severity": "INFORMATIONAL",
        "activity_id": "12809705",
        "relationship_id": null,
        "metadata": {
          "disposition": "INFORMATIONAL"
        }
      }
    ],
    "calculated_start_float_hours": null,
    "calculated_finish_float_hours": null,
    "total_float_method": "ACTIVITY_CALENDAR_START",
    "relationship_free_float_hours": [],
    "imported_critical": false,
    "imported_critical_basis": "IMPORTED_TOTAL_FLOAT_THRESHOLD",
    "critical_disagreement": null,
    "effective_state": "IN_PROGRESS_REMAINING_WORK",
    "date_basis": "REMAINING_WORK",
    "effective_finish_anchor": null,
    "imported_actual_start": "2025-10-09 00:00:00",
    "imported_actual_finish": null,
    "progress_state": {
      "actual_start": "2025-10-09 00:00:00",
      "actual_finish": null,
      "data_date": "2026-07-01 00:01:00",
      "observed_through": "2026-07-01 00:01:00",
      "imported_remaining_start": "2026-07-02 08:00:00",
      "imported_remaining_finish": "2026-07-02 08:00:00",
      "remaining_duration_hours": 0.0
    },
    "early_date_status": "EARLY_DATES_CALCULATED",
    "late_date_status": "LATE_DATES_BLOCKED",
    "float_status": "FLOAT_BLOCKED",
    "controlling_relationships": [],
    "controlling_constraints": []
  },
  "variance_hours": -31.983333333333334,
  "source_constraints": [
    [
      null,
      null
    ],
    [
      null,
      null
    ]
  ],
  "wbs_id": "3406267",
  "predecessors": [
    {
      "relationship_id": "26498808",
      "predecessor_activity_id": "12809647",
      "successor_activity_id": "12809705",
      "relationship_type": "FS",
      "lag_hours": 96.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "successors": [
    {
      "relationship_id": "26498810",
      "predecessor_activity_id": "12809705",
      "successor_activity_id": "12809706",
      "relationship_type": "SS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_SS"
    },
    {
      "relationship_id": "33746892",
      "predecessor_activity_id": "12809705",
      "successor_activity_id": "12809711",
      "relationship_type": "FS",
      "lag_hours": 0.0,
      "raw_relationship_type": "PR_FS"
    }
  ],
  "classification": "ZERO_WORK_BOUNDARY_REPRESENTATION",
  "evidence": [
    {
      "id": "12809705",
      "code": "OL_RSSOM_SS_180580",
      "metric": "early_start",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    },
    {
      "id": "12809705",
      "code": "OL_RSSOM_SS_180580",
      "metric": "early_finish",
      "duration": 0.0,
      "imported": "2026-07-02 08:00:00",
      "calculated": "2026-07-01 00:01:00",
      "elapsed_variance_hours": -31.983333333333334,
      "working_variance_hours": -0.0,
      "equivalent": true
    }
  ],
  "source_identity": {
    "raw_status": "TK_Active",
    "raw_activity_type": "TT_Task",
    "calendar_name": "RSSOM_5d/w+H",
    "wbs_path": "OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 5 System Assurance / 2 Security Deliverables / 2 System Design Security Submission / 6 Plan Development / 4.4 Security Risk Assessment Report",
    "planned_start": "2025-11-03 08:00",
    "planned_finish": "2025-11-03 17:00"
  }
}
```


## Completion-anchor candidates: no selection

Original terminal population remains approximately 7,200. A read-only scan of milestone names, all imported Activity Code values/types, UDF definitions/assigned values, project fields and constraints identified 59 name-filter candidates. None is automatically contractual. Strong candidate 1600284 / OL_RSSOM_WM_100160, "(vii) Completion of the Ontario Line Subway", is a terminal finish milestone with imported EF 2031-05-27 17:00 equal to PROJECT.scd_end_date. PROJECT.plan_end_date (required finish) is blank; no explicit configured anchor exists. Source schedule-option multiple-path ending key is blank.
Associated codes include Key Milestones, Major Milestones, Active Activity, Project Wide and Work Milestone. UDF labels include Primary Critical Path and Key Milestones, but Source Contract is TBC. These support review of a candidate, not an authoritative contractual selection or proof of calculated P6 Longest Path. No latest-terminal heuristic is applied.
```json
{
  "codes": [
    [
      "Ontario Line_TES",
      "Traction and Power System"
    ],
    [
      "Ontario Line_Communications",
      "Communication Systems"
    ],
    [
      "Ontario Line_Signalling",
      "Signalling System"
    ],
    [
      "Ontario Line_PSD",
      "Platform Screen Door System"
    ],
    [
      "Ontario Line_OCS",
      "Overhead Catenary"
    ],
    [
      "Ontario Line_Vehicle",
      "Vehicle"
    ],
    [
      "Ontario Line_Depot",
      "Depot Equipments"
    ],
    [
      "Ontario Line_SCADA WP",
      "SCADA WP"
    ],
    [
      "Ontario Line_Physical Sec. WP",
      "Physical Securtity WP"
    ],
    [
      "Ontario Line_Cyber Sec. WP",
      "Cyber Security WP"
    ],
    [
      "RSSOM 11.MS",
      "Key Milestones"
    ],
    [
      "*OL_RSSOM_ABS",
      "Major Milestones"
    ],
    [
      "SUBPROG - Subway Projects",
      "Ontario Line"
    ],
    [
      "SUBPROG - Project Sub-Phase",
      "Major Milestones"
    ],
    [
      "SUBPROG - Main Responsibility",
      "Project Co. (P3)"
    ],
    [
      "SUBPROG - Sub-Responsibility",
      "Project Co. \ufffd Contractor"
    ],
    [
      "SUBPROG - Vertical Alignment",
      "Project-Wide"
    ],
    [
      "*OL_RSSOM_SUBPROG _ Entity/ Subsystem",
      "General"
    ],
    [
      "*OL_RSSOM_Module of Work Location",
      "Project Wide"
    ],
    [
      "SUBPROG  \ufffd  SCC JV Partners",
      "GEN"
    ],
    [
      "*OL_RSSOM_ Lead Organization",
      "Design Build Joint Venture"
    ],
    [
      "*OL_RSSOM_ Mob payment",
      "Not Mob Payment"
    ],
    [
      "*OL_RSSOM_Activity Work Type",
      "Key Milestones"
    ],
    [
      "*OL_RSSOM_Active/Retired",
      "Active Activity"
    ],
    [
      "OL_RSSOM_WBS_Level 01",
      "Work Milestone"
    ]
  ],
  "udfs": [
    [
      "OL_RSSOM_Longest Path (Critical path)",
      "Primary Critical Path"
    ],
    [
      "OL_RSSOM_03_Organization",
      "Project Co"
    ],
    [
      "OL_RSSOM_04_Department",
      "Key Milestones"
    ],
    [
      "OL_RSSOM_01_Source Contract",
      "TBC"
    ],
    [
      "OL_RSSOM_Risk_Shortest Expected",
      "0"
    ],
    [
      "Subprog Ol Main area legacy Code",
      "OLMA02"
    ],
    [
      "Longest Duration",
      "0"
    ],
    [
      "OL_RSSOM_Sub contractors",
      "GNR"
    ],
    [
      "MSP Activity ID",
      "114"
    ]
  ]
}
```

All name-filter candidate IDs/codes with source finish/constraint/terminal evidence:
```json
[
  {
    "id": "1595909",
    "code": "OL_RSSOM_13470",
    "name": "OMSF TPSS Building - COT-TB Building Permit - Permit Issuance by IA - (After SPR Completion)",
    "type": "finish_milestone",
    "imported_ef": "2027-02-17 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597598",
    "code": "OL_RSSOM_14800",
    "name": "Completion of OMSF Utility Works",
    "type": "finish_milestone",
    "imported_ef": "2028-08-14 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597605",
    "code": "OL_RSSOM_14830",
    "name": "Completion of Works near CP Track (estimated)",
    "type": "finish_milestone",
    "imported_ef": "2028-01-10 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597608",
    "code": "OL_RSSOM_14840",
    "name": "Completion of Gatehouse Building Works",
    "type": "finish_milestone",
    "imported_ef": "2029-05-07 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597599",
    "code": "OL_RSSOM_14860",
    "name": "Completion of OMSF Fencing & Landscaping Works",
    "type": "finish_milestone",
    "imported_ef": "2029-05-14 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597616",
    "code": "OL_RSSOM_14900",
    "name": "Completion of Maintenance Building Works",
    "type": "finish_milestone",
    "imported_ef": "2029-06-14 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597617",
    "code": "OL_RSSOM_14920",
    "name": "Completion of Retaining Wall",
    "type": "finish_milestone",
    "imported_ef": "2026-08-05 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597614",
    "code": "OL_RSSOM_14930",
    "name": "Completion of MOW Building Works",
    "type": "finish_milestone",
    "imported_ef": "2028-05-18 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597612",
    "code": "OL_RSSOM_14950",
    "name": "Completion of TPSS Building Works",
    "type": "finish_milestone",
    "imported_ef": "2028-05-09 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597606",
    "code": "OL_RSSOM_14970",
    "name": "Completion of Utility Relocation Works (THESL and Beanfield)",
    "type": "finish_milestone",
    "imported_ef": "2026-09-02 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1596009",
    "code": "OL_RSSOM_160370",
    "name": "Completion of Retaining Walls Parallel to Beth Nealson Dr. - VD - 0031 - VD Received - Descopped",
    "type": "finish_milestone",
    "imported_ef": "2026-07-01 00:01:00",
    "constraints": [
      [
        "FINISH_ON_OR_AFTER",
        "2024-10-31 17:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600234",
    "code": "OL_RSSOM_260410",
    "name": "Detailed Design Packages Completion - OMSF",
    "type": "finish_milestone",
    "imported_ef": "2026-09-03 08:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600202",
    "code": "OL_RSSOM_260810",
    "name": "OMSF - Site Wide - T&C - Completion of Gas main SAT",
    "type": "finish_milestone",
    "imported_ef": "2028-01-28 16:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597602",
    "code": "OL_RSSOM_262350",
    "name": "Completion of OMSF Trackworks",
    "type": "finish_milestone",
    "imported_ef": "2028-08-18 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1597620",
    "code": "OL_RSSOM_262370",
    "name": "Completion of OMSF Road Bridge Works",
    "type": "finish_milestone",
    "imported_ef": "2028-11-02 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1611794",
    "code": "OL_RSSOM_262410",
    "name": "Completion of Environmental Submittals",
    "type": "finish_milestone",
    "imported_ef": "2031-04-02 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1612778",
    "code": "OL_RSSOM_529290",
    "name": "SUSS - Completion of External Inputs",
    "type": "finish_milestone",
    "imported_ef": "2026-07-01 00:01:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": true
  },
  {
    "id": "1614227",
    "code": "OL_RSSOM_530570",
    "name": "Completion of Works on Stabling Area",
    "type": "finish_milestone",
    "imported_ef": "2028-09-25 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1614229",
    "code": "OL_RSSOM_530580",
    "name": "Completion of OMSF Demolition Works",
    "type": "finish_milestone",
    "imported_ef": "2026-08-18 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1614335",
    "code": "OL_RSSOM_530720",
    "name": "Detailed Design Packages Completion - SUSS",
    "type": "finish_milestone",
    "imported_ef": "2026-09-01 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "7417009",
    "code": "OL_RSSOM_533910",
    "name": "Completion of Maintenance Building Area Oustide of Building Footprint",
    "type": "finish_milestone",
    "imported_ef": "2028-07-19 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598942",
    "code": "OL_RSSOM_CN_103460",
    "name": "01 - East Harbour Station \ufffd Substantial Completion - NEHCS",
    "type": "milestone",
    "imported_ef": "2028-07-24 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-07-24 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598951",
    "code": "OL_RSSOM_CN_103540",
    "name": "07 - Completion of Lower Don Yard Bridge Superstructure - NGWDY",
    "type": "milestone",
    "imported_ef": "2028-07-24 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-07-24 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599057",
    "code": "OL_RSSOM_CN_104830",
    "name": "20b. Gerrard Portal - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2028-09-18 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-09-18 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599058",
    "code": "OL_RSSOM_CN_104840",
    "name": "20c. Bain Street EEB - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2028-09-18 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-09-18 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599082",
    "code": "OL_RSSOM_CN_104910",
    "name": "35b. Minton Place Portal - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2028-09-18 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-09-18 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598960",
    "code": "OL_RSSOM_CN_106020",
    "name": "1. Exhibition - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2028-11-01 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2028-11-01 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599094",
    "code": "OL_RSSOM_CN_108290",
    "name": "45. Flemingdon Park Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2029-02-01 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2029-02-01 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599104",
    "code": "OL_RSSOM_CN_108300",
    "name": "52. Science Centre Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2029-02-01 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2029-02-01 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599069",
    "code": "OL_RSSOM_CN_108430",
    "name": "28b. Pape Crossover - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2029-02-07 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2029-02-07 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599040",
    "code": "OL_RSSOM_CN_113480",
    "name": "08. Leslieville Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-01-01 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-01-01 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599049",
    "code": "OL_RSSOM_CN_113490",
    "name": "15. Gerrard Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-01-01 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-01-01 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598973",
    "code": "OL_RSSOM_CN_113670",
    "name": "09. King/Bathurst Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598982",
    "code": "OL_RSSOM_CN_113680",
    "name": "16. Queen/Spadina Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598990",
    "code": "OL_RSSOM_CN_113690",
    "name": "23. Osgoode Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598999",
    "code": "OL_RSSOM_CN_113700",
    "name": "30. Queen Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599007",
    "code": "OL_RSSOM_CN_113710",
    "name": "44. Corktown Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599018",
    "code": "OL_RSSOM_CN_113720",
    "name": "37. Moss Park Station - Substantial Completion",
    "type": "milestone",
    "imported_ef": "2030-03-22 08:00:00",
    "constraints": [
      [
        "START_ON_OR_AFTER",
        "2030-03-22 00:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599062",
    "code": "OL_RSSOM_CN_113740",
    "name": "23. Pape Station - Substantial Completion",
    "type": "finish_milestone",
    "imported_ef": "2030-06-01 17:00:00",
    "constraints": [
      [
        "FINISH_ON_OR_AFTER",
        "2030-06-01 17:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599074",
    "code": "OL_RSSOM_CN_113750",
    "name": "30. Cosburn Station - Substantial Completion",
    "type": "finish_milestone",
    "imported_ef": "2030-06-01 17:00:00",
    "constraints": [
      [
        "FINISH_ON_OR_AFTER",
        "2030-06-01 17:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1599086",
    "code": "OL_RSSOM_CN_113760",
    "name": "37. Thorncliffe Park Station - Substantial Completion",
    "type": "finish_milestone",
    "imported_ef": "2030-06-01 17:00:00",
    "constraints": [
      [
        "FINISH_ON_OR_AFTER",
        "2030-06-01 17:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1598149",
    "code": "OL_RSSOM_CN_529170",
    "name": "Completion of SUSS Civil Works - Including the Outside Infrastructure of the Building - VD - 0026 - OTG TSA",
    "type": "finish_milestone",
    "imported_ef": "2028-02-18 16:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1604860",
    "code": "OL_RSSOM_DE_101180",
    "name": "S-168A - Substantial Completion Submittals - Submission to CA",
    "type": "finish_milestone",
    "imported_ef": "2030-11-28 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1604863",
    "code": "OL_RSSOM_DE_101190",
    "name": "S-168B - Final Completion Submittals - Submission to CA",
    "type": "finish_milestone",
    "imported_ef": "2031-01-14 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1604866",
    "code": "OL_RSSOM_DE_101200",
    "name": "S-168C - Substantial Completion Certificate - Submission to CA",
    "type": "finish_milestone",
    "imported_ef": "2030-12-30 08:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1604888",
    "code": "OL_RSSOM_DE_533710",
    "name": "S-175 - Envision Coversheets - \ufffdNo Comment\ufffd status obtained for Substantial Completion",
    "type": "finish_milestone",
    "imported_ef": "2030-04-15 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "13207225",
    "code": "OL_RSSOM_VD_545650",
    "name": "LET-PRM0-00362 - Notice of Delay & Compensation Event - Additional PLAA Completion Requirement at 4 Thorncliffe Dr.",
    "type": "finish_milestone",
    "imported_ef": "2026-07-01 00:01:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "13207226",
    "code": "OL_RSSOM_VD_545660",
    "name": "LET-PRM0-00365 - Notice of Delay & Compensation Event - Additional PLAA Completion Req. at 4 Thorncliffe Dr. 1st Update",
    "type": "finish_milestone",
    "imported_ef": "2026-07-01 00:01:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600283",
    "code": "OL_RSSOM_WM_100030",
    "name": "(vi) Completion of all Works on the CP Rail Corridor Lands",
    "type": "finish_milestone",
    "imported_ef": "2028-01-10 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600282",
    "code": "OL_RSSOM_WM_100050",
    "name": "(v) Completion of the Utility Work",
    "type": "finish_milestone",
    "imported_ef": "2028-10-23 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600286",
    "code": "OL_RSSOM_WM_100070",
    "name": "(ix) Completion by PCo of any applicable obligations pursuant to Schedule 42 \ufffd South Civil Infra Access and Handover",
    "type": "finish_milestone",
    "imported_ef": "2030-03-25 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600285",
    "code": "OL_RSSOM_WM_100080",
    "name": "(viii) Completion by Project Co of any applicable obligations pursuant to Schedule 41 \ufffd Early Works Handover",
    "type": "finish_milestone",
    "imported_ef": "2030-05-24 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600287",
    "code": "OL_RSSOM_WM_100090",
    "name": "(x) Completion by PCo of any applicable obligations pursuant to Schedule 43 \ufffd North Civil Infra Access and Handover",
    "type": "finish_milestone",
    "imported_ef": "2030-05-24 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600288",
    "code": "OL_RSSOM_WM_100100",
    "name": "(xi) Completion of the New Third Party Infrastructure",
    "type": "finish_milestone",
    "imported_ef": "2030-05-24 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600277",
    "code": "OL_RSSOM_WM_100120",
    "name": "Start of Revenue Service Demonstration",
    "type": "milestone",
    "imported_ef": "2031-02-12 08:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600275",
    "code": "OL_RSSOM_WM_100130",
    "name": "(xiii) Scheduled Substantial Completion Date",
    "type": "finish_milestone",
    "imported_ef": "2031-03-28 17:00:00",
    "constraints": [
      [
        "FINISH_ON_OR_BEFORE",
        "2031-03-28 17:00:00"
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600276",
    "code": "OL_RSSOM_WM_100150",
    "name": "(xiv) Scheduled Final Completion Date (Final Completion)",
    "type": "finish_milestone",
    "imported_ef": "2031-05-27 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  },
  {
    "id": "1600284",
    "code": "OL_RSSOM_WM_100160",
    "name": "(vii) Completion of the Ontario Line Subway",
    "type": "finish_milestone",
    "imported_ef": "2031-05-27 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": true
  },
  {
    "id": "1600220",
    "code": "OL_RSSOM_WM_300620",
    "name": "Design and Documentation Finish - Post Substantial Completion Project Wide",
    "type": "finish_milestone",
    "imported_ef": "2030-10-18 17:00:00",
    "constraints": [
      [
        null,
        null
      ],
      [
        null,
        null
      ]
    ],
    "terminal": false
  }
]
```


## Tests, file manifest and remaining gates

Before implementation: six parser/mapper tests failed, then passed after narrow mapping; 21 initial progress/directional cases failed, then passed. Later failing reductions verified early invariants, global failures, duration reliability, directional constraint provenance, genuine component identity and the completed-release gap. Final new coverage: 40 progress/directional cases plus six scheduling-option/mapper cases = 46. All prior 393 tests remain passing. No existing protected tests were weakened to obtain a larger population.
| Command / suite | Exact result |
|---|---|
| Initial complete non-external regression | 393 passed, 2 deselected, 1 warning |
| Final pytest -q -m "not external_xer" | 439 passed, 2 deselected, 1 warning |
| Focused all CPM including progress | 296 passed |
| Focused new progress/options | 46 passed |
| Focused existing FS/SS/FF/SF/lag/relationship selection | 61 passed, 7 deselected |
| Focused calendars | 79 passed, 1 deselected |
| Calendars/import/normalization/options aggregate | 114 passed, 2 deselected, 1 warning |
The seven focused relationship deselections are other cases included in the complete regression; the full non-external suite deselects only the two legacy external_xer tests requiring absent NRG00800.xer. This genuine project was separately imported and calculated through ScheduleImportService/CPMService, not substituted for that fixture. The existing warning remains FastAPI/Starlette TestClient deprecation. No Ruff was run or installed.
Created: app/models/scheduling_options.py; app/cpm/progress.py; app/cpm/directional.py; tests/test_p6_scheduling_options.py; tests/test_cpm_progress.py; docs/phase6d_progress_contract.md; docs/phase6d_calibration_notes.md.
Modified this increment: app/models/schedule.py; app/importers/xer_parser.py; app/importers/schedule_mapper.py; app/cpm/config.py; app/cpm/models.py; app/cpm/service.py; app/cpm/validation.py; app/cpm/forward_pass.py (optional requirement hook, default unchanged); app/cpm/comparison.py (observed typed-option diagnostics). Prior Phase 6B/6C working-tree changes remain intact. No original_files or legacy_reference work was performed.
Remaining LS/LF/TF/FF blockers: Expected Finish conflict/duration-update semantics, prospective retained release through completed chains, remaining unsupported progress options, LOE-derived backward boundaries, and a defensible explicitly selected completion/required-finish basis. Backward progress semantics must be separately specified/tested before labeling their output P6-compatible. Existing default domain calculations remain available for their protected supported contract; the new P6 forward mode deliberately does not call backward, float or path code.
DCMA Critical Path Test = NOT_EVALUATED (immutable controlled delay simulation absent). CPLI = NOT_EVALUATED (required completion/validated path-length inputs absent). No automatic next phase, persistence, UI, report generator, simulation or forbidden feature was started.
