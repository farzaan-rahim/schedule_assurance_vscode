# Phase 6C real-project calculability evidence

Source: `sample_data/1414_RSM-RSM-CW-PWD-RPT-PRM0-00063_C01 Appendix.10 - OL-RSSOM-PWS_June 2026.xer`. SHA-256: `77ad15c128638db79792ab915301ba236785fd134768ecd98a6992072de23999`. Full ScheduleImportService import succeeded with 23,263 activities and 36,521 relationships; calendar, relationship and activity core hashes and the source hash were unchanged after both calculations. No filtered XER or replacement project was fabricated.
The protected [Phase 6 contract](phase6_calculation_contract.md) and [Phase 6B evidence](phase6b_calibration_notes.md) are preserved unchanged. The deliberate extension is documented in [Phase 6C calculability contract](phase6c_calculability_contract.md). No calendar/relationship-lag/float formula, imported value, persistence, API, UI or reporting feature was changed.

## Baseline and exact constraint inventory

Initial `pytest -q -m "not external_xer"`: **346 passed, 2 deselected, 1 existing warning**. The warning is the existing FastAPI/Starlette deprecation. All 72 previously unsupported findings have a date and are primary:
| Raw code | Canonical | Total | Complete | In progress | Not started | Primary | Secondary | Date present |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CS_MEOA | FINISH_ON_OR_AFTER | 71 | 55 | 0 | 16 | 71 | 0 | 71 |
| CS_MSOB | START_ON_OR_BEFORE | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
Full inventory, including the already supported constraints and three secondary entries:
| Raw | Canonical | Slot | Date exists | Status | Count |
|---|---|---|---|---|---:|
| CS_MEOA | FINISH_ON_OR_AFTER | primary | True | complete | 55 |
| CS_MEOA | FINISH_ON_OR_AFTER | primary | True | not_started | 16 |
| CS_MEOB | FINISH_ON_OR_BEFORE | primary | True | complete | 169 |
| CS_MEOB | FINISH_ON_OR_BEFORE | primary | True | in_progress | 20 |
| CS_MEOB | FINISH_ON_OR_BEFORE | primary | True | not_started | 49 |
| CS_MEOB | FINISH_ON_OR_BEFORE | secondary | True | complete | 3 |
| CS_MSOA | START_ON_OR_AFTER | primary | True | complete | 116 |
| CS_MSOA | START_ON_OR_AFTER | primary | True | not_started | 255 |
| CS_MSOB | START_ON_OR_BEFORE | primary | True | complete | 1 |
All constraints have usable imported dates; no missing-date exception was introduced. The 71 Finish On or After constraints occur on 37 raw finish milestones and 34 ordinary tasks. All three source primary/secondary combinations belong to completed history; the synthetic tests additionally exercise both active slots, zero-work milestones and conflicting windows.

## Constraint support decisions and semantics

| Constraint | Before | After | Pass / decision |
|---|---|---|---|
| Start On or After | SUPPORTED | SUPPORTED | Forward start lower bound |
| Finish On or Before | SUPPORTED | SUPPORTED | Backward finish upper bound |
| Finish On or After | IMPLEMENTABLE | SUPPORTED | Forward finish lower bound, exact calendar inverse |
| Start On or Before | IMPLEMENTABLE | SUPPORTED | Backward start upper bound, exact calendar inverse |
| Supported constraint on completed history | VALIDATION_ONLY | VALIDATION_ONLY | Validate date and preserve actuals; informational, no history rescheduling |
| Mandatory Start/Finish | UNSUPPORTED | UNSUPPORTED | Hard overrides require separate semantics, never substituted with soft bounds |
| Start On / Finish On / ALAP / unknown tags | UNSUPPORTED | UNSUPPORTED | Not enabled in this increment |
Oracle [raw identities](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/26/p6-cpp/constraintselectiondescriptions-101902a.html) identify codes. Operational behavior comes from [Finish On or After](https://docs.oracle.com/cd/G48902_01/client_help/en_US/finish_on_or_after_constraint.htm), [Start On or Before](https://docs.oracle.com/cd/G48902_01/client_help/en_US/start_on_or_before_constraint.htm), and [Professional constraint types](https://docs.oracle.com/cd/F88968_01/client_help/en_US/types_of_constraints.htm). The supplied CPP mapping has justification labels that differ from Professional hard/soft classification; Mandatory overrides are not inferred from those labels.
Both slots contribute independent bounds. Forward uses max of all lower bounds and network/Data Date; backward uses min of all upper bounds and successor/finish bounds. FNET uses existing `start_for_finish_not_before`, SNLB uses existing `finish_for_start_not_after`; no calendar arithmetic is duplicated. Structured constraint control retains each controlling cause. Conflicting soft windows emit `conflicting_constraint_window` while preserving negative float, rather than silently replacing a bound or manufacturing a hard override. New raw endpoint invariants check these bounds before float.

## Ten WBS Summary records

Oracle describes WBS summaries as rollups of activities sharing WBS scope, rather than independent fixed-duration tasks. See [activity types](https://docs.oracle.com/cd/G48897_01/p6help/en/47261.htm). TT_WBS now normalizes to `wbs_summary`; the ten source records all have zero incoming/outgoing relationships. No normal CPM activity depends on them. All ten are EXCLUDED and preserved, with explicit `wbs_summary_not_scheduled`. No summary duration or WBS aggregation calculation is invented.
| Internal ID / Activity code | Status | WBS ID / path | Pred | Succ | Types | Normal dependents |
|---|---|---|---:|---:|---|---:|
| 1596230 / OL_RSSOM_262290 | complete | 1089191: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 15 Retired Activities for Jan'2025 | 0 | 0 | none | 0 |
| 1596263 / OL_RSSOM_262310 | complete | 1089191: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 15 Retired Activities for Jan'2025 | 0 | 0 | none | 0 |
| 1596437 / OL_RSSOM_262300 | complete | 1089191: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 15 Retired Activities for Jan'2025 | 0 | 0 | none | 0 |
| 1596438 / OL_RSSOM_262280 | not_started | 441641: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / CON Construction & Installation / OMSF OMSF / CW OMSF - Civil & Trackwork / TEST OMSF - Test Track Area / GATE Gatehouse building | 0 | 0 | none | 0 |
| 1596638 / OL_RSSOM_262270 | in_progress | 441649: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / CON Construction & Installation / OMSF OMSF / CW OMSF - Civil & Trackwork / MOW&TPSS OMSF - TPSS & MOW Buildings Area / TPSS TPSS Building | 0 | 0 | none | 0 |
| 1596760 / OL_RSSOM_262260 | in_progress | 441656: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / CON Construction & Installation / OMSF OMSF / CW OMSF - Civil & Trackwork / MOW&TPSS OMSF - TPSS & MOW Buildings Area / MOW MOW Building | 0 | 0 | none | 0 |
| 1596818 / OL_RSSOM_262250 | in_progress | 441658: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / CON Construction & Installation / OMSF OMSF / CW OMSF - Civil & Trackwork / MNT OMSF - Maintenance Building Area / BULD Maintenance Building | 0 | 0 | none | 0 |
| 1597406 / OL_RSSOM_262330 | complete | 1089191: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 15 Retired Activities for Jan'2025 | 0 | 0 | none | 0 |
| 1597533 / OL_RSSOM_262320 | complete | 1089191: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 15 Retired Activities for Jan'2025 | 0 | 0 | none | 0 |
| 18387903 / OL_RSSOM_536650 | complete | 4449502: OL-RSSOM-PWS-Live Ontario Line Subway RSSOM Project - Progress Works Schedule - Live / 3 Retired Activities / 28 Retired Activities for Feb'2026 | 0 | 0 | none | 0 |
A linked summary is not treated as a network boundary. STRICT still rejects incident exclusion; scoped mode blocks its component. Isolated known informational exclusions do not require a working calendar because no date arithmetic is performed for them; no calendar fallback is supplied. Included activities retain missing/unusable calendar errors.

## 57 LOE records and network effects

Oracle activity-type documentation identifies LOE as having duration derived from dependent activities. The [P6/Prime mapping](https://docs.oracle.com/cd/E75426_01/English/Mapping_and_Schema/p6_pro_prime_import_export_data_map_prime_sync/p6_pro_prime_import_export_data_map_prime_sync.pdf) establishes TT_LOE identity. No fixed-duration LOE or full hammock scheduling is implemented.
Status: 42 in progress, 11 not started, four complete. Topology: one isolated, 38 incoming-only sinks, 18 with outgoing logic; all 18 have normal-work successors. Calendar IDs: 3479 (33), 11683 (13), 3480 (10), 3487 (1). All 57 are EXCLUDED, not removed. The 56 linked LOE produce `excluded_network_endpoint` roots; components are withheld. Incoming-only records are not asserted to drive early dates, but a reliable full late-date/float component finish cannot be established from an unimplemented LOE endpoint. No unvalidated LOE-derived boundary is substituted. In this real file, all linked LOE share the component already blocked by the 18 outgoing LOE, Expected Finish and progress gates.
| ID / Activity code | Status | Calendar | Original h | Remaining h | Pred | Succ | Relationship types | Normal predecessor / successor count |
|---|---|---|---:|---:|---:|---:|---|---|
| 1596002 / OL_RSSOM_262550 | in_progress | 3479 | 20376.0 | 9536.0 | 33 | 0 | {'FF': 33} | 33 / 0 |
| 1596004 / OL_RSSOM_262560 | in_progress | 11683 | 16800.0 | 9520.0 | 1 | 1 | {'FS': 2} | 1 / 1 |
| 1599195 / OL_RSSOM_262460 | in_progress | 3479 | 8733.916667 | 13856.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1599196 / OL_RSSOM_262470 | in_progress | 3479 | 24424.0 | 13856.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1600728 / OL_RSSOM_262480 | in_progress | 11683 | 21600.0 | 8224.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1600729 / OL_RSSOM_262490 | complete | 11683 | 480.0 | 0.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1605320 / OL_RSSOM_DE_100500 | complete | 11683 | 320.0 | 0.0 | 20 | 0 | {'SS': 16, 'FF': 4} | 20 / 0 |
| 1605352 / OL_RSSOM_DE_402995 | complete | 11683 | 240.0 | 0.0 | 20 | 0 | {'SS': 17, 'FF': 3} | 20 / 0 |
| 1605358 / OL_RSSOM_DE_412980 | not_started | 11683 | 5744.0 | 5744.0 | 8 | 0 | {'FF': 7, 'FS': 1} | 8 / 0 |
| 1605375 / OL_RSSOM_DE_513420 | in_progress | 11683 | 14240.0 | 8632.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1606814 / OL_RSSOM_PR_501650 | not_started | 11683 | 6312.0 | 6312.0 | 2 | 1 | {'SS': 2, 'FF': 1} | 2 / 1 |
| 1611264 / OL_RSSOM_PS_001080 | in_progress | 3487 | 8080.0 | 4560.0 | 2 | 1 | {'FS': 1, 'SS': 1, 'FF': 1} | 2 / 1 |
| 1611515 / OL_RSSOM_PS_005670 | in_progress | 11683 | 15600.0 | 8632.0 | 1 | 1 | {'FS': 1, 'FF': 1} | 1 / 1 |
| 1611532 / OL_RSSOM_PS_003510 | in_progress | 11683 | 10032.0 | 8632.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 1611795 / OL_RSSOM_DE_100320 | in_progress | 3479 | 24472.0 | 13896.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611803 / OL_RSSOM_DE_500440 | in_progress | 3479 | 960.0 | 8640.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611812 / OL_RSSOM_DE_500130 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611815 / OL_RSSOM_DE_500160 | in_progress | 3479 | 480.0 | 13896.0 | 4 | 0 | {'FF': 1, 'SS': 3} | 4 / 0 |
| 1611819 / OL_RSSOM_DE_500620 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611826 / OL_RSSOM_DE_500220 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611835 / OL_RSSOM_DE_500775 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611844 / OL_RSSOM_DE_500330 | in_progress | 3479 | 480.0 | 11984.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611846 / OL_RSSOM_DE_500030 | in_progress | 3479 | 480.0 | 13896.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611849 / OL_RSSOM_DE_500370 | in_progress | 3479 | 480.0 | 8640.0 | 3 | 0 | {'FF': 2, 'SS': 1} | 3 / 0 |
| 1611856 / OL_RSSOM_DE_500080 | in_progress | 3479 | 240.0 | 13896.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611859 / OL_RSSOM_DE_500110 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611864 / OL_RSSOM_DE_500510 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611874 / OL_RSSOM_DE_500655 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611881 / OL_RSSOM_DE_500230 | in_progress | 3479 | 480.0 | 11984.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611893 / OL_RSSOM_DE_500010 | complete | 11683 | 168.0 | 0.0 | 0 | 0 | {} | 0 / 0 |
| 1611894 / OL_RSSOM_DE_500040 | in_progress | 3479 | 13104.0 | 8640.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611916 / OL_RSSOM_DE_500865 | in_progress | 3479 | 12448.0 | 8640.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611921 / OL_RSSOM_DE_500585 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611930 / OL_RSSOM_DE_500690 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611938 / OL_RSSOM_DE_500240 | in_progress | 3479 | 13912.0 | 11984.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1611974 / OL_RSSOM_DE_500810 | in_progress | 3479 | 480.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1611983 / OL_RSSOM_DE_500340 | in_progress | 3479 | 480.0 | 11984.0 | 2 | 0 | {'SS': 1, 'FF': 1} | 2 / 0 |
| 1612023 / OL_RSSOM_DE_511770 | in_progress | 3479 | 20560.0 | 11984.0 | 2 | 0 | {'FF': 1, 'SS': 1} | 2 / 0 |
| 1612035 / OL_RSSOM_DE_511930 | in_progress | 3479 | 21600.0 | 11984.0 | 2 | 0 | {'FF': 1, 'SS': 1} | 2 / 0 |
| 1612039 / OL_RSSOM_DE_511970 | in_progress | 3479 | 13872.0 | 4256.0 | 2 | 0 | {'FF': 1, 'SS': 1} | 2 / 0 |
| 1612043 / OL_RSSOM_DE_512010 | in_progress | 3479 | 13872.0 | 4256.0 | 2 | 0 | {'FF': 1, 'SS': 1} | 2 / 0 |
| 1612047 / OL_RSSOM_DE_512050 | in_progress | 3479 | 14816.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1612051 / OL_RSSOM_DE_512090 | in_progress | 3479 | 14816.0 | 5200.0 | 3 | 0 | {'SS': 1, 'FF': 2} | 3 / 0 |
| 1612055 / OL_RSSOM_DE_512130 | in_progress | 3479 | 12784.0 | 11984.0 | 2 | 0 | {'FF': 1, 'SS': 1} | 2 / 0 |
| 9338916 / OL_RSSOM_DE_567330 | in_progress | 11683 | 48.0 | 8632.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 9338917 / OL_RSSOM_DE_567340 | in_progress | 3479 | 720.0 | 12568.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 11013601 / OL_RSSOM_536890 | in_progress | 3480 | 1320.0 | 200.0 | 55 | 5 | {'SS': 55, 'FF': 5} | 55 / 5 |
| 11013603 / OL_RSSOM_536910 | in_progress | 3480 | 2944.0 | 984.0 | 25 | 43 | {'SS': 25, 'FF': 43} | 25 / 43 |
| 11013605 / OL_RSSOM_536930 | not_started | 3480 | 825.0 | 825.0 | 2 | 1 | {'FS': 2, 'FF': 1} | 2 / 1 |
| 11013606 / OL_RSSOM_536940 | not_started | 3480 | 488.0 | 488.0 | 3 | 1 | {'FS': 3, 'FF': 1} | 3 / 1 |
| 11013607 / OL_RSSOM_536950 | not_started | 3480 | 864.0 | 864.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 11013609 / OL_RSSOM_536970 | not_started | 3480 | 824.0 | 824.0 | 2 | 1 | {'FS': 2, 'FF': 1} | 2 / 1 |
| 11013610 / OL_RSSOM_536980 | not_started | 3480 | 480.0 | 480.0 | 1 | 1 | {'FS': 1, 'FF': 1} | 1 / 1 |
| 11013612 / OL_RSSOM_537000 | not_started | 3480 | 5256.0 | 5256.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 11013613 / OL_RSSOM_537010 | not_started | 3480 | 4008.0 | 4008.0 | 1 | 1 | {'SS': 1, 'FF': 1} | 1 / 1 |
| 11013614 / OL_RSSOM_537020 | not_started | 3480 | 320.0 | 320.0 | 1 | 1 | {'FS': 1, 'FF': 1} | 1 / 1 |
| 13903525 / OL_RSSOM_PR_520380 | not_started | 11683 | 8792.0 | 8792.0 | 1 | 1 | {'FS': 1, 'FF': 1} | 1 / 1 |

## Historical planned-start audit

| Canonical status | Findings | Disposition |
|---|---:|---|
| complete | 0 | Completed actuals are separately preserved |
| in progress | 492 | INFORMATIONAL historical planned dates |
| not started | 0 | No finding in this population |
All 492 have Actual Start, no Actual Finish, non-negative remaining duration and populated raw Remaining Start/Finish. All 492 Remaining Starts are at/after Data Date 2026-07-01 00:01. Of these, 447 have Planned Finish before Data Date; 425 have Expected Finish. No invalid actual-date state was established in this population. A historical planned start itself does not cause exclusion or a fatal diagnostic. Forward remaining-work scheduling continues to use Data Date and calculated logic/duration, preserving historical planned/actual values. Imported raw restart/reend were audited read-only; they are not silently promoted to scheduling constraints.
Representative rows, including every required date field:
```json
[
  {
    "id": "1595667",
    "code": "OL_RSSOM_262510",
    "name": "OMSF Site Wide - COT-PL Site Plan Review - Complete Package Submission (After Sch. 10 closed)",
    "status": "in_progress",
    "wbs": "441115",
    "calendar": "11683",
    "original": 640.0,
    "remaining": 1024.0,
    "planned_start": "2025-09-25 08:00:00",
    "planned_finish": "2026-01-20 17:00:00",
    "actual_start": "2024-05-09 08:00:00",
    "actual_finish": "None",
    "restart": "2026-07-02 08:00",
    "reend": "2027-01-05 17:00",
    "expected": "2027-01-05 17:00:00",
    "es": "2026-07-02 08:00:00",
    "ef": "2027-01-05 17:00:00",
    "predecessors": 4,
    "successors": 1,
    "relationship_types": {
      "FS": 2,
      "FF": 3
    },
    "normal_predecessors": [
      "1595665",
      "7172744",
      "4711913",
      "17688665"
    ],
    "normal_successors": [
      "15373785"
    ]
  },
  {
    "id": "1595673",
    "code": "OL_RSSOM_10400",
    "name": "OMSF Site Wide - COT-TB Site Services Permit - Final Determination by IA (30d + multiple review cycles)",
    "status": "in_progress",
    "wbs": "441116",
    "calendar": "11683",
    "original": 720.0,
    "remaining": 776.0,
    "planned_start": "2025-03-13 16:00:00",
    "planned_finish": "2025-07-22 16:00:00",
    "actual_start": "2024-12-13 16:00:00",
    "actual_finish": "None",
    "restart": "2026-09-29 08:00",
    "reend": "2027-02-17 17:00",
    "expected": "None",
    "es": "2026-09-29 08:00:00",
    "ef": "2027-02-17 17:00:00",
    "predecessors": 4,
    "successors": 1,
    "relationship_types": {
      "FS": 2,
      "FF": 3
    },
    "normal_predecessors": [
      "1595672",
      "1604760",
      "1605339",
      "1595668"
    ],
    "normal_successors": [
      "1595674"
    ]
  },
  {
    "id": "1595718",
    "code": "OL_RSSOM_161970",
    "name": "OMSF - TW Service Connection - Thorncliffe Service Connection - Package Preparation by PCo",
    "status": "in_progress",
    "wbs": "441128",
    "calendar": "11683",
    "original": 40.0,
    "remaining": 752.0,
    "planned_start": "2025-11-24 08:00:00",
    "planned_finish": "2025-11-28 17:00:00",
    "actual_start": "2025-05-16 08:00:00",
    "actual_finish": "None",
    "restart": "2026-07-02 08:00",
    "reend": "2026-11-13 17:00",
    "expected": "2026-11-13 17:00:00",
    "es": "2026-07-02 08:00:00",
    "ef": "2026-11-13 17:00:00",
    "predecessors": 11,
    "successors": 1,
    "relationship_types": {
      "FS": 6,
      "FF": 6
    },
    "normal_predecessors": [
      "1614565",
      "1605338",
      "4711909",
      "4711907",
      "4711911",
      "10175288",
      "10175290",
      "10175292",
      "17784108",
      "17784110",
      "17784112"
    ],
    "normal_successors": [
      "1595719"
    ]
  },
  {
    "id": "1595722",
    "code": "OL_RSSOM_162030",
    "name": "OMSF - TW Service Connection - Beth Nealson Service Connection - Package Preparation by PCo",
    "status": "in_progress",
    "wbs": "441129",
    "calendar": "11683",
    "original": 40.0,
    "remaining": 752.0,
    "planned_start": "2025-11-24 08:00:00",
    "planned_finish": "2025-11-28 17:00:00",
    "actual_start": "2025-05-16 08:00:00",
    "actual_finish": "None",
    "restart": "2026-07-02 08:00",
    "reend": "2026-11-13 17:00",
    "expected": "2026-11-13 17:00:00",
    "es": "2026-07-02 08:00:00",
    "ef": "2026-11-13 17:00:00",
    "predecessors": 11,
    "successors": 1,
    "relationship_types": {
      "FS": 6,
      "FF": 6
    },
    "normal_predecessors": [
      "1614565",
      "1605338",
      "4711905",
      "4711903",
      "4711901",
      "10175282",
      "10175286",
      "10175284",
      "17784112",
      "17784110",
      "17784108"
    ],
    "normal_successors": [
      "1595723"
    ]
  },
  {
    "id": "1595818",
    "code": "OL_RSSOM_12560",
    "name": "OMSF Maint. Building - COT-TB Building Permit - Final Determination by IA (90d + review) - (After SPR Completion)",
    "status": "in_progress",
    "wbs": "441145",
    "calendar": "11683",
    "original": 960.0,
    "remaining": 776.0,
    "planned_start": "2025-01-20 08:00:00",
    "planned_finish": "2025-07-10 17:00:00",
    "actual_start": "2024-12-09 00:00:00",
    "actual_finish": "None",
    "restart": "2026-09-29 08:00",
    "reend": "2027-02-17 17:00",
    "expected": "2026-07-17 17:00:00",
    "es": "2026-09-29 08:00:00",
    "ef": "2027-02-17 17:00:00",
    "predecessors": 8,
    "successors": 1,
    "relationship_types": {
      "FS": 6,
      "FF": 3
    },
    "normal_predecessors": [
      "1595817",
      "1596000",
      "1614640",
      "1614642",
      "1615050",
      "1614666",
      "1614573",
      "1595668"
    ],
    "normal_successors": [
      "1595819"
    ]
  }
]
```

Complete affected-activity inventory (internal IDs and codes) for these 492 informational findings:
- 1595667 / OL_RSSOM_262510
- 1595673 / OL_RSSOM_10400
- 1595718 / OL_RSSOM_161970
- 1595722 / OL_RSSOM_162030
- 1595818 / OL_RSSOM_12560
- 1595866 / OL_RSSOM_13040
- 1595908 / OL_RSSOM_13460
- 1595938 / OL_RSSOM_13880
- 1596189 / OL_RSSOM_159708
- 1596761 / OL_RSSOM_CN_500890
- 1600629 / OL_RSSOM_DE_410631
- 1600639 / OL_RSSOM_DE_410661
- 1600649 / OL_RSSOM_DE_410691
- 1600733 / OL_RSSOM_DE_200050
- 1600745 / OL_RSSOM_DE_202060
- 1600765 / OL_RSSOM_DE_205870
- 1600790 / OL_RSSOM_DE_202090
- 1600970 / OL_RSSOM_DE_202150
- 1601060 / OL_RSSOM_DE_522190
- 1601075 / OL_RSSOM_DE_522340
- 1601090 / OL_RSSOM_DE_522490
- 1601105 / OL_RSSOM_DE_522640
- 1601120 / OL_RSSOM_DE_522790
- 1601240 / OL_RSSOM_DE_526540
- 1601255 / OL_RSSOM_DE_526690
- 1601405 / OL_RSSOM_DE_523840
- 1601420 / OL_RSSOM_DE_523990
- 1601540 / OL_RSSOM_DE_524890
- 1601555 / OL_RSSOM_DE_525040
- 1601570 / OL_RSSOM_DE_525190
- 1601585 / OL_RSSOM_DE_525340
- 1601600 / OL_RSSOM_DE_525490
- 1601739 / OL_RSSOM_DE_530950
- 1601797 / OL_RSSOM_DE_531380
- 1601821 / OL_RSSOM_DE_527570
- 1601825 / OL_RSSOM_DE_527610
- 1601900 / OL_RSSOM_DE_528960
- 1602020 / OL_RSSOM_DE_530160
- 1602129 / OL_RSSOM_DE_532150
- 1602219 / OL_RSSOM_DE_533050
- 1602241 / OL_RSSOM_DE_200890
- 1602245 / OL_RSSOM_DE_201560
- 1602256 / OL_RSSOM_DE_533910
- 1602260 / OL_RSSOM_DE_533950
- 1602271 / OL_RSSOM_DE_534060
- 1602275 / OL_RSSOM_DE_534100
- 1602286 / OL_RSSOM_DE_534210
- 1602290 / OL_RSSOM_DE_534250
- 1602301 / OL_RSSOM_DE_534360
- 1602305 / OL_RSSOM_DE_534400
- 1602325 / OL_RSSOM_DE_200100
- 1602350 / OL_RSSOM_DE_204120
- 1602374 / OL_RSSOM_DE_207300
- 1602380 / OL_RSSOM_DE_205760
- 1602402 / OL_RSSOM_DE_206890
- 1602410 / OL_RSSOM_DE_205740
- 1602442 / OL_RSSOM_DE_206930
- 1602450 / OL_RSSOM_DE_206620
- 1602460 / OL_RSSOM_DE_406220
- 1602520 / OL_RSSOM_DE_411470
- 1602540 / OL_RSSOM_DE_109810
- 1602560 / OL_RSSOM_DE_109830
- 1602589 / OL_RSSOM_DE_114250
- 1602604 / OL_RSSOM_DE_114270
- 1602619 / OL_RSSOM_DE_114290
- 1602634 / OL_RSSOM_DE_501100
- 1602664 / OL_RSSOM_DE_501400
- 1602709 / OL_RSSOM_DE_501850
- 1602784 / OL_RSSOM_DE_113600
- 1602799 / OL_RSSOM_DE_112620
- 1602814 / OL_RSSOM_DE_112030
- 1602829 / OL_RSSOM_DE_503100
- 1602844 / OL_RSSOM_DE_114700
- 1602859 / OL_RSSOM_DE_503250
- 1602889 / OL_RSSOM_DE_503550
- 1602904 / OL_RSSOM_DE_503700
- 1602919 / OL_RSSOM_DE_503850
- 1602934 / OL_RSSOM_DE_504000
- 1602949 / OL_RSSOM_DE_504150
- 1602964 / OL_RSSOM_DE_504300
- 1602979 / OL_RSSOM_DE_504450
- 1602994 / OL_RSSOM_DE_504600
- 1603009 / OL_RSSOM_DE_116620
- 1603084 / OL_RSSOM_DE_506850
- 1603099 / OL_RSSOM_DE_507000
- 1603114 / OL_RSSOM_DE_507150
- 1603129 / OL_RSSOM_DE_507300
- 1603144 / OL_RSSOM_DE_507450
- 1603159 / OL_RSSOM_DE_507600
- 1603174 / OL_RSSOM_DE_112650
- 1603189 / OL_RSSOM_DE_108440
- 1603204 / OL_RSSOM_DE_504750
- 1603219 / OL_RSSOM_DE_504900
- 1603234 / OL_RSSOM_DE_505050
- 1603294 / OL_RSSOM_DE_505650
- 1603324 / OL_RSSOM_DE_505950
- 1603339 / OL_RSSOM_DE_506100
- 1603354 / OL_RSSOM_DE_112670
- 1603369 / OL_RSSOM_DE_115010
- 1603384 / OL_RSSOM_DE_507750
- 1603414 / OL_RSSOM_DE_508050
- 1603429 / OL_RSSOM_DE_508200
- 1603444 / OL_RSSOM_DE_508350
- 1603459 / OL_RSSOM_DE_508500
- 1603474 / OL_RSSOM_DE_508650
- 1603489 / OL_RSSOM_DE_508800
- 1603504 / OL_RSSOM_DE_508950
- 1603519 / OL_RSSOM_DE_509100
- 1603549 / OL_RSSOM_DE_105330
- 1603594 / OL_RSSOM_DE_108990
- 1603609 / OL_RSSOM_DE_109010
- 1603624 / OL_RSSOM_DE_112230
- 1603639 / OL_RSSOM_DE_114490
- 1603654 / OL_RSSOM_DE_112740
- 1603698 / OL_RSSOM_DE_109050
- 1603713 / OL_RSSOM_DE_111300
- 1603859 / OL_RSSOM_DE_513660
- 1603919 / OL_RSSOM_DE_513960
- 1604161 / OL_RSSOM_DE_517880
- 1604208 / OL_RSSOM_DE_518350
- 1604233 / OL_RSSOM_DE_533850
- 1604299 / OL_RSSOM_DE_116930
- 1604429 / OL_RSSOM_DE_102280
- 1604440 / OL_RSSOM_DE_533270
- 1604444 / OL_RSSOM_DE_533310
- 1604455 / OL_RSSOM_DE_533420
- 1604459 / OL_RSSOM_DE_533460
- 1604470 / OL_RSSOM_DE_533570
- 1604474 / OL_RSSOM_DE_533610
- 1604514 / OL_RSSOM_DE_119870
- 1604524 / OL_RSSOM_DE_115450
- 1604544 / OL_RSSOM_DE_115470
- 1604574 / OL_RSSOM_DE_119890
- 1604584 / OL_RSSOM_DE_115510
- 1604614 / OL_RSSOM_DE_120230
- 1604624 / OL_RSSOM_DE_115540
- 1604672 / OL_RSSOM_DE_119720
- 1604682 / OL_RSSOM_DE_113770
- 1604894 / OL_RSSOM_DE_408842
- 1604962 / OL_RSSOM_DE_105110
- 1605137 / OL_RSSOM_DE_115410
- 1605148 / OL_RSSOM_DE_512690
- 1605237 / OL_RSSOM_DE_102900
- 1605270 / OL_RSSOM_DE_102420
- 1605456 / OL_RSSOM_DE_102480
- 1605611 / OL_RSSOM_DE_113440
- 1605621 / OL_RSSOM_DE_112800
- 1605645 / OL_RSSOM_DE_118960
- 1605655 / OL_RSSOM_DE_114410
- 1605665 / OL_RSSOM_DE_118980
- 1605673 / OL_RSSOM_DE_112530
- 1605685 / OL_RSSOM_DE_108110
- 1605745 / OL_RSSOM_DE_115180
- 1605769 / OL_RSSOM_DE_113680
- 1605780 / OL_RSSOM_DE_100590
- 1605785 / OL_RSSOM_DE_111490
- 1605841 / OL_RSSOM_DE_118320
- 1605852 / OL_RSSOM_DE_512520
- 1605896 / OL_RSSOM_DE_401740
- 1605925 / OL_RSSOM_DE_402100
- 1605940 / OL_RSSOM_DE_402220
- 1606030 / OL_RSSOM_DE_405460
- 1606040 / OL_RSSOM_DE_405360
- 1606086 / OL_RSSOM_DE_406620
- 1606222 / OL_RSSOM_DE_413290
- 1606233 / OL_RSSOM_DE_115200
- 1606245 / OL_RSSOM_DE_512580
- 1606404 / OL_RSSOM_DE_510400
- 1606411 / OL_RSSOM_DE_510470
- 1606412 / OL_RSSOM_DE_510500
- 1606425 / OL_RSSOM_DE_510520
- 1606432 / OL_RSSOM_DE_510590
- 1606433 / OL_RSSOM_DE_510600
- 1606447 / OL_RSSOM_DE_510630
- 1606454 / OL_RSSOM_DE_510700
- 1606455 / OL_RSSOM_DE_510710
- 1606460 / OL_RSSOM_DE_510740
- 1606461 / OL_RSSOM_DE_510750
- 1606523 / OL_RSSOM_DE_511010
- 1606530 / OL_RSSOM_DE_511080
- 1606531 / OL_RSSOM_DE_511090
- 1606546 / OL_RSSOM_DE_510300
- 1606548 / OL_RSSOM_DE_511130
- 1606555 / OL_RSSOM_DE_511200
- 1606556 / OL_RSSOM_DE_511210
- 1606568 / OL_RSSOM_DE_511330
- 1606570 / OL_RSSOM_DE_511350
- 1606626 / OL_RSSOM_DE_518570
- 1606628 / OL_RSSOM_DE_518610
- 1606690 / OL_RSSOM_DE_518950
- 1606706 / OL_RSSOM_DE_519010
- 1606737 / OL_RSSOM_DE_520050
- 1606740 / OL_RSSOM_DE_520080
- 1606741 / OL_RSSOM_DE_520090
- 1606747 / OL_RSSOM_DE_519220
- 1607009 / OL_RSSOM_PR_509140
- 1607036 / OL_RSSOM_PR_507790
- 1607042 / OL_RSSOM_PR_507670
- 1607061 / OL_RSSOM_PR_505220
- 1607077 / OL_RSSOM_PR_503970
- 1607114 / OL_RSSOM_PR_101010
- 1607118 / OL_RSSOM_PR_101020
- 1607127 / OL_RSSOM_PR_504520
- 1607130 / OL_RSSOM_PR_101060
- 1607151 / OL_RSSOM_PR_504760
- 1607156 / OL_RSSOM_PR_504880
- 1607162 / OL_RSSOM_PR_505060
- 1607229 / OL_RSSOM_PR_502680
- 1607246 / OL_RSSOM_PR_507910
- 1607250 / OL_RSSOM_PR_502860
- 1607262 / OL_RSSOM_PR_502970
- 1607268 / OL_RSSOM_PR_503020
- 1607276 / OL_RSSOM_PR_503080
- 1607279 / OL_RSSOM_PR_503160
- 1607292 / OL_RSSOM_PR_503220
- 1607304 / OL_RSSOM_PR_508080
- 1607353 / OL_RSSOM_PR_505260
- 1607407 / OL_RSSOM_PR_505010
- 1607435 / OL_RSSOM_PR_509100
- 1607508 / OL_RSSOM_PR_300030
- 1607560 / OL_RSSOM_PR_300600
- 1607561 / OL_RSSOM_PR_301030
- 1607577 / OL_RSSOM_PR_300500
- 1607594 / OL_RSSOM_PR_300260
- 1607637 / OL_RSSOM_PR_301730
- 1607719 / OL_RSSOM_PR_302120
- 1607731 / OL_RSSOM_PR_301520
- 1607738 / OL_RSSOM_PR_301360
- 1607742 / OL_RSSOM_PR_301740
- 1607758 / OL_RSSOM_PR_300690
- 1607759 / OL_RSSOM_PR_301700
- 1607773 / OL_RSSOM_PR_301260
- 1607796 / OL_RSSOM_PR_300730
- 1607815 / OL_RSSOM_PR_301240
- 1607849 / OL_RSSOM_PR_300380
- 1607863 / OL_RSSOM_PR_300620
- 1611764 / OL_RSSOM_PS_60420
- 1612432 / OL_RSSOM_DE_539590
- 1612442 / OL_RSSOM_DE_539690
- 1612463 / OL_RSSOM_DE_539960
- 1612595 / OL_RSSOM_DE_541460
- 1612766 / OL_RSSOM_PR_509375
- 1612768 / OL_RSSOM_PR_509355
- 1613074 / OL_RSSOM_529830
- 1613176 / OL_RSSOM_529880
- 1613261 / OL_RSSOM_PR_510570
- 1613301 / OL_RSSOM_PR_510970
- 1613321 / OL_RSSOM_PR_511170
- 1613342 / OL_RSSOM_PR_511340
- 1613396 / OL_RSSOM_PR_511990
- 1613424 / OL_RSSOM_PR_512270
- 1613436 / OL_RSSOM_PR_512390
- 1613505 / OL_RSSOM_PR_513000
- 1613553 / OL_RSSOM_PR_513440
- 1613574 / OL_RSSOM_PR_513610
- 1613579 / OL_RSSOM_PR_513660
- 1613585 / OL_RSSOM_PR_513720
- 1613591 / OL_RSSOM_PR_513780
- 1613605 / OL_RSSOM_PR_513920
- 1613609 / OL_RSSOM_PR_513960
- 1613617 / OL_RSSOM_PR_514040
- 1613621 / OL_RSSOM_PR_514080
- 1613633 / OL_RSSOM_PR_514240
- 1613637 / OL_RSSOM_PR_514280
- 1613876 / OL_RSSOM_PR_516230
- 1613944 / OL_RSSOM_PR_516720
- 1614043 / OL_RSSOM_PR_517710
- 1614047 / OL_RSSOM_PR_517750
- 1614051 / OL_RSSOM_PR_517790
- 1614058 / OL_RSSOM_PR_517860
- 1614064 / OL_RSSOM_PR_517920
- 1614067 / OL_RSSOM_PR_517950
- 1614073 / OL_RSSOM_PR_518010
- 1614079 / OL_RSSOM_PR_518070
- 1614100 / OL_RSSOM_PR_518280
- 1614106 / OL_RSSOM_PR_518340
- 1614112 / OL_RSSOM_PR_518400
- 1614266 / OL_RSSOM_DE_547950
- 1614286 / OL_RSSOM_DE_5247481
- 1614459 / OL_RSSOM_531270
- 1614465 / OL_RSSOM_531310
- 1614479 / OL_RSSOM_DE_549130
- 1614546 / OL_RSSOM_PR_518680
- 1614552 / OL_RSSOM_PR_518740
- 1614684 / OL_RSSOM_DE_551100
- 1614694 / OL_RSSOM_DE_551200
- 1614704 / OL_RSSOM_DE_551300
- 1614795 / OL_RSSOM_DE_551680
- 1614799 / OL_RSSOM_DE_551720
- 1614917 / OL_RSSOM_DE_5247541
- 1615184 / OL_RSSOM_DE_555440
- 1615186 / OL_RSSOM_DE_555460
- 1615187 / OL_RSSOM_DE_555470
- 1615188 / OL_RSSOM_DE_555480
- 1615189 / OL_RSSOM_DE_555490
- 1615190 / OL_RSSOM_DE_555500
- 1615191 / OL_RSSOM_DE_555510
- 1615192 / OL_RSSOM_DE_555520
- 1615225 / OL_RSSOM_PR_518880
- 1615253 / OL_RSSOM_DE_555880
- 1615254 / OL_RSSOM_DE_555890
- 1615255 / OL_RSSOM_DE_555900
- 1615256 / OL_RSSOM_DE_555910
- 1615257 / OL_RSSOM_DE_555920
- 1615258 / OL_RSSOM_DE_555930
- 1615259 / OL_RSSOM_DE_555940
- 1615261 / OL_RSSOM_DE_555960
- 1615262 / OL_RSSOM_DE_555970
- 1615263 / OL_RSSOM_DE_555980
- 1615264 / OL_RSSOM_DE_555990
- 1615346 / OL_RSSOM_DE_556810
- 1615358 / OL_RSSOM_DE_556930
- 1615371 / OL_RSSOM_DE_557060
- 4577064 / OL_RSSOM_DE_558400
- 4577079 / OL_RSSOM_DE_558550
- 4577109 / OL_RSSOM_DE_558850
- 4577144 / OL_RSSOM_DE_559200
- 4577154 / OL_RSSOM_DE_559300
- 4577189 / OL_RSSOM_DE_559650
- 4577199 / OL_RSSOM_DE_559750
- 4577214 / OL_RSSOM_DE_559900
- 4577229 / OL_RSSOM_DE_560050
- 4577244 / OL_RSSOM_DE_560200
- 4577259 / OL_RSSOM_DE_560350
- 4577274 / OL_RSSOM_DE_560500
- 4577289 / OL_RSSOM_DE_560650
- 4577309 / OL_RSSOM_DE_560850
- 4577324 / OL_RSSOM_DE_561000
- 4577339 / OL_RSSOM_DE_561150
- 4618449 / OL_RSSOM_DE_563170
- 4618601 / OL_RSSOM_DE_563482
- 4639461 / OL_RSSOM_DE_563610
- 4639468 / OL_RSSOM_DE_563680
- 4639483 / OL_RSSOM_DE_563830
- 4639498 / OL_RSSOM_DE_563980
- 4639513 / OL_RSSOM_DE_564130
- 4639528 / OL_RSSOM_DE_564280
- 4639543 / OL_RSSOM_DE_564430
- 4639558 / OL_RSSOM_DE_564580
- 4712276 / OL_RSSOM_DE_565715
- 4712277 / OL_RSSOM_DE_565745
- 4712278 / OL_RSSOM_DE_565730
- 4712279 / OL_RSSOM_DE_565760
- 4712280 / OL_RSSOM_DE_565775
- 4712281 / OL_RSSOM_DE_565790
- 4712284 / OL_RSSOM_DE_565820
- 5083205 / OL_RSSOM_PR_519050
- 5161350 / OL_RSSOM_PR_519190
- 5245181 / OL_RSSOM_CN_530250
- 5328460 / OL_RSSOM_532540
- 5328463 / OL_RSSOM_532570
- 5328464 / OL_RSSOM_532580
- 5328465 / OL_RSSOM_532590
- 5328466 / OL_RSSOM_532600
- 5328469 / OL_RSSOM_532630
- 5328470 / OL_RSSOM_532640
- 5328473 / OL_RSSOM_532670
- 5328474 / OL_RSSOM_532680
- 5328475 / OL_RSSOM_532690
- 5328476 / OL_RSSOM_532700
- 5328477 / OL_RSSOM_532710
- 5328478 / OL_RSSOM_532720
- 5328480 / OL_RSSOM_532740
- 5328482 / OL_RSSOM_532760
- 5328483 / OL_RSSOM_532770
- 5328494 / OL_RSSOM_532880
- 5328496 / OL_RSSOM_532900
- 5328497 / OL_RSSOM_532910
- 5328498 / OL_RSSOM_532920
- 5328502 / OL_RSSOM_532960
- 5328503 / OL_RSSOM_532970
- 5328510 / OL_RSSOM_533040
- 5328511 / OL_RSSOM_533050
- 5328512 / OL_RSSOM_533060
- 5328513 / OL_RSSOM_533070
- 5458170 / OL_RSSOM_DE_566280
- 6143287 / OL_RSSOM_533240
- 6919087 / OL_RSSOM_PL_105660
- 7544265 / OL_RSSOM_534850
- 7544272 / OL_RSSOM_534920
- 9815238 / OL_RSSOM_DE_567350
- 10449962 / OL_RSSOM_PR_520130
- 10779653 / OL_RSSOM_DE_567740
- 10779661 / OL_RSSOM_DE_567820
- 10779664 / OL_RSSOM_DE_567850
- 11995221 / OL_RSSOM_537920
- 12076654 / OL_RSSOM_DE_568310
- 12809689 / OL_RSSOM_SS_180420
- 12809690 / OL_RSSOM_SS_180430
- 12809704 / OL_RSSOM_SS_180570
- 12809705 / OL_RSSOM_SS_180580
- 12809709 / OL_RSSOM_SS_180620
- 13042094 / OL_RSSOM_DE_569170
- 13086859 / OL_RSSOM_SS_103560
- 13086860 / OL_RSSOM_SS_102120
- 13086886 / OL_RSSOM_SS_115050
- 13087020 / OL_RSSOM_SS_118830
- 13087141 / OL_RSSOM_SS_120200
- 13087178 / OL_RSSOM_SS_119120
- 13087695 / OL_RSSOM_SS_180680
- 13087697 / OL_RSSOM_SS_180700
- 13087706 / OL_RSSOM_SS_180790
- 13087716 / OL_RSSOM_SS_180890
- 13207119 / OL_RSSOM_538420
- 13766145 / OL_RSSOM_PR_520350
- 13903522 / OL_RSSOM_DE_570040
- 14140745 / OL_RSSOM_538640
- 14256573 / OL_RSSOM_CN_5243530
- 14256577 / OL_RSSOM_CN_5243570
- 14256581 / OL_RSSOM_CN_5243610
- 14256585 / OL_RSSOM_CN_5243650
- 14256589 / OL_RSSOM_CN_5243690
- 14256593 / OL_RSSOM_CN_5243730
- 14256597 / OL_RSSOM_CN_5243770
- 14256601 / OL_RSSOM_CN_5243810
- 14345661 / OL_RSSOM_PR_520420
- 14549706 / OL_RSSOM_CN_5243900
- 14856043 / OL_RSSOM_PR_520450
- 14856045 / OL_RSSOM_PR_520470
- 14856046 / OL_RSSOM_PR_520480
- 15038185 / OL_RSSOM_PR_520570
- 15038187 / OL_RSSOM_DE_570490
- 15038188 / OL_RSSOM_DE_570500
- 15038190 / OL_RSSOM_DE_570520
- 15328983 / OL_RSSOM_DE_570550
- 15328985 / OL_RSSOM_DE_570570
- 15639908 / OL_RSSOM_CN_5243960
- 15729588 / OL_RSSOM_DE_570780
- 15729592 / OL_RSSOM_DE_570820
- 16260474 / OL_RSSOM_539920
- 16260476 / OL_RSSOM_DE_570940
- 17300373 / OL_RSSOM_DE_571330
- 17394656 / OL_RSSOM_DE_571410
- 17394682 / OL_RSSOM_DE_571450
- 17394700 / OL_RSSOM_DE_5244431
- 17394703 / OL_RSSOM_DE_5244461
- 17394718 / OL_RSSOM_5244350
- 17394724 / OL_RSSOM_5244390
- 17394727 / OL_RSSOM_DE_5244521
- 17580040 / OL_RSSOM_DE_5244591
- 18102727 / OL_RSSOM_DE_5246411
- 18158156 / OL_RSSOM_DE_5246441
- 18363081 / OL_RSSOM_DE_548150
- 18363094 / OL_RSSOM_DE_5246532
- 18387899 / OL_RSSOM_531420
- 18387902 / OL_RSSOM_531450
- 18387904 / OL_RSSOM_5245200
- 18387905 / OL_RSSOM_5245210
- 18387909 / OL_RSSOM_5245250
- 18387912 / OL_RSSOM_5245280
- 18387913 / OL_RSSOM_5245290
- 18387914 / OL_RSSOM_5245300
- 18387917 / OL_RSSOM_5245330
- 18387918 / OL_RSSOM_5245340
- 19105529 / OL_RSSOM_CN_5244260
- 19427824 / OL_RSSOM_PR_300650
- 19750062 / OL_RSSOM_DE_5481831
- 19874731 / OL_RSSOM_DE_5481851
- 20054201 / OL_RSSOM_DE_5481881
- 20142592 / OL_RSSOM_DE_5481931
- 20142599 / OL_RSSOM_DE_5481991
- 20142602 / OL_RSSOM_DE_5482021
- 20165721 / OL_RSSOM_DE_570055
- 20165723 / OL_RSSOM_DE_5482031
- 20165730 / OL_RSSOM_DE_5482071
- 20165734 / OL_RSSOM_SS_800270
- 21314436 / OL_RSSOM_DE_5482091
- 21314438 / OL_RSSOM_DE_5482111
- 21314440 / OL_RSSOM_DE_5482131
- 21314442 / OL_RSSOM_DE_5482151
- 21364366 / OL_RSSOM_DE_5482171
- 21364368 / OL_RSSOM_DE_5482191
- 21450226 / OL_RSSOM_DE_5482211
- 21450228 / OL_RSSOM_DE_5482231
- 21450239 / OL_RSSOM_DE_5482251
- 21450241 / OL_RSSOM_DE_5482271
- 21450243 / OL_RSSOM_DE_5482291
- 21450246 / OL_RSSOM_DE_5482311
- 21985709 / OL_RSSOM_5245530
- 21985911 / OL_RSSOM_5245550
- 22273943 / OL_RSSOM_DE_5482361
- 22273948 / OL_RSSOM_DE_5482411
- 22273953 / OL_RSSOM_DE_5482461
- 22507707 / OL_RSSOM_DE_5482561
- 22593644 / OL_RSSOM_DE_5482651
- 22593651 / OL_RSSOM_SS_800320
- 22765518 / OL_RSSOM_DE_5482691
- 22851449 / OL_RSSOM_DE_5247635
- 22851453 / OL_RSSOM_DE_5482771
- 22851455 / OL_RSSOM_DE_5482791
- 22901303 / OL_RSSOM_DE_5482811
- 22901305 / OL_RSSOM_DE_5482831

## Retained Logic and progressed SS evidence

Observed raw options remain Retained Logic=Y, Progress Override=N, SS lag early-start=Y. [Oracle scheduling settings](https://docs.oracle.com/cd/G48897_01/p6help/en/90519.htm) describe progress and expired SS lag behavior. No option was silently enabled or interpreted as permission to override logic.
Six FS relationships have an unfinished predecessor and a successor that has actually begun (three successors complete, three in progress). Source and local requirements follow. These are local checks using imported predecessor remaining dates, not whole-network CPM outputs:
```json
[
  {
    "relationship_id": "3508252",
    "type": "SS",
    "lag": 704.0,
    "predecessor": "OL_RSSOM_PR_301030",
    "successor": "OL_RSSOM_PR_301110",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "imported_pre_remaining_start": "2026-07-02 08:00:00",
    "imported_pre_remaining_finish": "2027-02-24 17:00:00",
    "imported_suc_remaining_start": "2026-07-07 08:00:00",
    "imported_suc_remaining_finish": "2027-01-20 17:00:00",
    "pre_actual_start": "2026-03-02 08:00:00",
    "suc_actual_start": "None",
    "local_application_remaining_start_requirement": "2026-11-06 08:00:00",
    "actual_start_to_data_date_work_hours": 680.0
  },
  {
    "relationship_id": "26989364",
    "type": "FS",
    "lag": 0.0,
    "predecessor": "OL_RSSOM_SS_103560",
    "successor": "OL_RSSOM_SS_174570",
    "pre_calendar": "3480",
    "suc_calendar": "3480",
    "imported_pre_remaining_start": "2026-07-02 08:00:00",
    "imported_pre_remaining_finish": "2026-08-28 17:00:00",
    "imported_suc_remaining_start": "2026-08-31 08:00:00",
    "imported_suc_remaining_finish": "2026-09-28 17:00:00",
    "pre_actual_start": "2025-02-03 00:00:00",
    "suc_actual_start": "2026-06-16 08:00:00",
    "local_application_remaining_start_requirement": "2026-08-31 08:00:00",
    "actual_start_to_data_date_work_hours": 2832.0
  },
  {
    "relationship_id": "44458839",
    "type": "FS",
    "lag": 0.0,
    "predecessor": "OL_RSSOM_DE_5482821",
    "successor": "OL_RSSOM_PR_300500",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "imported_pre_remaining_start": "2026-07-27 08:00:00",
    "imported_pre_remaining_finish": "2026-08-24 17:00:00",
    "imported_suc_remaining_start": "2026-08-25 08:00:00",
    "imported_suc_remaining_finish": "2026-10-28 17:00:00",
    "pre_actual_start": "None",
    "suc_actual_start": "2026-06-15 08:00:00",
    "local_application_remaining_start_requirement": "2026-08-25 08:00:00",
    "actual_start_to_data_date_work_hours": null
  },
  {
    "relationship_id": "44539337",
    "type": "FS",
    "lag": 0.0,
    "predecessor": "OL_RSSOM_5244360",
    "successor": "OL_RSSOM_534920",
    "pre_calendar": "11683",
    "suc_calendar": "11683",
    "imported_pre_remaining_start": "2026-08-13 08:00:00",
    "imported_pre_remaining_finish": "2026-08-14 17:00:00",
    "imported_suc_remaining_start": "2026-07-02 08:00:00",
    "imported_suc_remaining_finish": "2026-09-03 17:00:00",
    "pre_actual_start": "None",
    "suc_actual_start": "2025-11-01 08:00:00",
    "local_application_remaining_start_requirement": "2026-08-17 08:00:00",
    "actual_start_to_data_date_work_hours": null
  }
]
```

There are 12 positive-SS-lag relationships with an in-progress predecessor. For relationship 3508252, predecessor Actual Start is 2026-03-02 08:00, Data Date is 2026-07-01 00:01, predecessor Remaining Start is 2026-07-02 08:00, lag=704h, and actual-start-to-Data-Date calendar work=680h. The application full-lag local bound is 2026-11-06 08:00. Source successor Remaining Start is 2026-07-07 08:00. A read-only expired-lag illustration leaves 24h; adding that work to July 2 reaches July 6 close, then successor normalization reaches July 7 opening. This is consistent with the documented option and demonstrates a capability difference; it is not deployed scheduling code or proof that every progressed relation follows that rule.
FS 26989364 and 44458839 locally match retained remaining-work bounds despite earlier Actual Starts. FS 44539337 has imported successor Remaining Start July 2 before the predecessor finish August 14; the application local bound is August 17. Expected Finish is populated on that successor. The snapshot alone does not establish whether Expected Finish, stale scheduling state, or another P6 behavior explains this apparent inconsistency. No source-specific exception or Progress Override is introduced.
Policy decision: no global rejection merely because Retained Logic exists. The conservative scoped mode blocks the weak component of observed out-of-sequence FS and progressed positive-SS-lag cases, retaining relationship evidence and root IDs. In-progress status alone is not fatal; ordinary valid progress retains the application remaining-work policy and capability warning. Unrelated components can calculate. STRICT keeps the established application REMAINING_FROM_DATA_DATE methodology and capability diagnostics; its results must not be relabeled P6-equivalent. Fully supporting retained/expired-lag behavior requires separately designed and tested semantics.

## Expected Finish evidence and disposition

The canonical Activity already preserves `expected_finish` from `expect_end_date`. Existing mapper and capability tests remain green; no importer schema change was necessary. Source option is enabled, with 720 dates (519 in progress, 201 not started). 588 equal imported EF; 132 differ. Equality alone does not prove the option caused the date: remaining duration may already reflect the last P6 schedule. Five duration-only differences among this population consist of three +/-0.0012s residuals and two equivalent finish-boundary representations. No counterfactual P6 reschedule with Expected Finish disabled is available, so material causation cannot be proven from this export alone.
Representative matching and nonmatching values are retained below. Scheduling by Expected Finish is not implemented. Every unfinished record with that value is a root of component uncertainty in VALID_COMPONENTS; it is BLOCKED (not deleted or treated as an ordinary unaffected task).
```json
[
  {
    "id": "1595667",
    "code": "OL_RSSOM_262510",
    "name": "OMSF Site Wide - COT-PL Site Plan Review - Complete Package Submission (After Sch. 10 closed)",
    "status": "in_progress",
    "wbs": "441115",
    "calendar": "11683",
    "original": 640.0,
    "remaining": 1024.0,
    "planned_start": "2025-09-25 08:00:00",
    "planned_finish": "2026-01-20 17:00:00",
    "actual_start": "2024-05-09 08:00:00",
    "actual_finish": "None",
    "restart": "2026-07-02 08:00",
    "reend": "2027-01-05 17:00",
    "expected": "2027-01-05 17:00:00",
    "es": "2026-07-02 08:00:00",
    "ef": "2027-01-05 17:00:00",
    "predecessors": 4,
    "successors": 1,
    "relationship_types": {
      "FS": 2,
      "FF": 3
    },
    "normal_predecessors": [
      "1595665",
      "7172744",
      "4711913",
      "17688665"
    ],
    "normal_successors": [
      "15373785"
    ],
    "expected_equals_ef": true,
    "duration_only_finish": "2027-01-05 17:00:00"
  },
  {
    "id": "1595718",
    "code": "OL_RSSOM_161970",
    "name": "OMSF - TW Service Connection - Thorncliffe Service Connection - Package Preparation by PCo",
    "status": "in_progress",
    "wbs": "441128",
    "calendar": "11683",
    "original": 40.0,
    "remaining": 752.0,
    "planned_start": "2025-11-24 08:00:00",
    "planned_finish": "2025-11-28 17:00:00",
    "actual_start": "2025-05-16 08:00:00",
    "actual_finish": "None",
    "restart": "2026-07-02 08:00",
    "reend": "2026-11-13 17:00",
    "expected": "2026-11-13 17:00:00",
    "es": "2026-07-02 08:00:00",
    "ef": "2026-11-13 17:00:00",
    "predecessors": 11,
    "successors": 1,
    "relationship_types": {
      "FS": 6,
      "FF": 6
    },
    "normal_predecessors": [
      "1614565",
      "1605338",
      "4711909",
      "4711907",
      "4711911",
      "10175288",
      "10175290",
      "10175292",
      "17784108",
      "17784110",
      "17784112"
    ],
    "normal_successors": [
      "1595719"
    ],
    "expected_equals_ef": true,
    "duration_only_finish": "2026-11-13 17:00:00"
  },
  {
    "id": "1595818",
    "code": "OL_RSSOM_12560",
    "name": "OMSF Maint. Building - COT-TB Building Permit - Final Determination by IA (90d + review) - (After SPR Completion)",
    "status": "in_progress",
    "wbs": "441145",
    "calendar": "11683",
    "original": 960.0,
    "remaining": 776.0,
    "planned_start": "2025-01-20 08:00:00",
    "planned_finish": "2025-07-10 17:00:00",
    "actual_start": "2024-12-09 00:00:00",
    "actual_finish": "None",
    "restart": "2026-09-29 08:00",
    "reend": "2027-02-17 17:00",
    "expected": "2026-07-17 17:00:00",
    "es": "2026-09-29 08:00:00",
    "ef": "2027-02-17 17:00:00",
    "predecessors": 8,
    "successors": 1,
    "relationship_types": {
      "FS": 6,
      "FF": 3
    },
    "normal_predecessors": [
      "1595817",
      "1596000",
      "1614640",
      "1614642",
      "1615050",
      "1614666",
      "1614573",
      "1595668"
    ],
    "normal_successors": [
      "1595819"
    ],
    "expected_equals_ef": false,
    "duration_only_finish": "2027-02-17 17:00:00"
  },
  {
    "id": "1595866",
    "code": "OL_RSSOM_13040",
    "name": "OMSF MOW Building - COT-TB Building Permit - Final Determination by IA (30d + review)",
    "status": "in_progress",
    "wbs": "441153",
    "calendar": "11683",
    "original": 960.0,
    "remaining": 776.0,
    "planned_start": "2025-01-20 08:00:00",
    "planned_finish": "2025-07-10 17:00:00",
    "actual_start": "2024-12-09 00:00:00",
    "actual_finish": "None",
    "restart": "2026-09-29 08:00",
    "reend": "2027-02-17 17:00",
    "expected": "2026-07-17 17:00:00",
    "es": "2026-09-29 08:00:00",
    "ef": "2027-02-17 17:00:00",
    "predecessors": 9,
    "successors": 1,
    "relationship_types": {
      "FS": 7,
      "FF": 3
    },
    "normal_predecessors": [
      "1595865",
      "1596000",
      "1614640",
      "1614642",
      "1615050",
      "1614666",
      "3938950",
      "1614573",
      "1595668"
    ],
    "normal_successors": [
      "1595867"
    ],
    "expected_equals_ef": false,
    "duration_only_finish": "2027-02-17 17:00:00"
  }
]
```


## Component calculability design and real-project outcome

Opt in explicitly with `CPMConfig(component_calculation_policy="VALID_COMPONENTS")`. STRICT remains default. Iterative weak components isolate uncertainty in both forward and backward directions; a node downstream of a blocker or upstream through late/float dependencies is not fully reliable. No inferred boundary or deleted relationship reconnects the network. Both passes, raw relationship audits and all date invariants must succeed before a component produces dates/float. Local runtime failures quarantine the component and retry the unaffected remainder. Global datetime/configuration/Data Date failures remain global blockers.
Per-activity and relationship dispositions reference component records containing root IDs and reason codes. CALCULATED, EXCLUDED and BLOCKED are activity states. PARTIALLY_CALCULATED is the aggregate of safe components plus withheld scope; no per-activity provisional dates are emitted, so partially_calculated_activity_count is explicitly zero. Source records remain intact. A partial result has no project completion, selected anchor or controlling path. An implicit shared PROJECT_FINISH cannot be constructed across blocked components; a configured required finish remains explicit and valid.
| Real-project disposition | Count |
|---|---:|
| Calculated completed history | 7150 |
| Calculated remaining work | 0 |
| Partially calculated activities | 0 |
| Excluded WBS Summary | 10 |
| Excluded LOE | 57 |
| Blocked activities | 16046 |
| Calculable relationships | 0 |
| Blocked relationships | 36521 |
The input has 7,162 components: 7,161 isolated records and one component of 16,102 activities. Ten isolated summaries and one isolated LOE are excluded. The other 7,150 isolated records are completed history. The large component contains 56 excluded LOE plus 16,046 blocked records. Hence overall result is PARTIALLY_CALCULATED, not evidence of a valid remaining-work scheduling population. All 72 unsupported-constraint findings are resolved. STRICT now fails specifically on incident excluded logic, with 67 exclusion warnings, 492 historical-planned-start information messages and 344 constraint-slot historical information messages.
Scoped diagnostic counts (multiple reasons may apply to one activity; do not sum as disjoint populations):
```json
{
  "INFORMATIONAL/historical_constraint_not_applied": 344,
  "INFORMATIONAL/planned_start_before_data_date": 492,
  "WARNING/loe_not_supported": 57,
  "WARNING/wbs_summary_not_scheduled": 10,
  "ERROR/unconfirmed_expected_finish": 720,
  "ERROR/excluded_network_endpoint": 56,
  "ERROR/unconfirmed_progress_methodology": 18,
  "INFORMATIONAL/completed_float_not_applicable": 7150,
  "WARNING/completion_anchor_ambiguous": 1
}
```

Blocked component root causes are excluded_network_endpoint, unconfirmed_expected_finish and unconfirmed_progress_methodology. There are 56 incident-exclusion roots and 720 Expected Finish roots. Progress roots are limited to evidenced out-of-sequence FS and progressed positive-SS-lag cases; ordinary in-progress status remains a capability diagnostic, not an automatic blocker. The exact diagnostic/unique-root counts follow. Dependency propagation withholds the rest of that component. The result retains all individual root IDs and per-node component references.
```json
{
  "progress_conditions": {
    "PROGRESSED_POSITIVE_SS_LAG": 12,
    "OUT_OF_SEQUENCE_FS": 6
  },
  "unique_progress_roots": 14,
  "all_blocked_component_root_union": 780
}
```


## Agreement reporting: no remaining-work denominator

The comparison layer retains 7,150 literal historical imported/calculated pairs, restricted to actually returned results. They contrast preserved actual spans with imported early/late placeholders; these are not a valid remaining-work P6 calibration population. No excluded or blocked activity is in those records. Calibration filters further by `date_basis=REMAINING_WORK`; that population is empty. The following counts are zero observations, not 0% agreement. Median/maximum are unavailable, not zero.
| Metric | Eligible | Comparable | Exact observations | Within tolerance observations | Difference observations | Imported/calculated missing within eligible population | Median / max abs h |
|---|---:|---:|---:|---:|---:|---|---|
| early_start | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
| early_finish | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
| late_start | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
| late_finish | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
| total_float | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
| free_float | 0 | 0 | 0 | 0 | 0 | 0 / 0 (empty population) | NOT_EVALUATED |
Tolerances remain 0 seconds / 0 hours. No stored variance was rounded or changed. Critical agreement and global largest-discrepancy rankings remain NOT_EVALUATED for remaining work. The local independent calendar/relationship evidence from Phase 6B is retained and not substituted for network CPM agreement.

## Completion-anchor investigation

The original graph has 7,200 terminals. Latest terminal finish milestone `1600284 / OL_RSSOM_WM_100160`, “(vii) Completion of the Ontario Line Subway”, has imported EF 2031-05-27 17:00, equal to PROJECT.scd_end_date. This makes it a defensible candidate for explicit review, not an automatic contractual anchor. PROJECT.plan_end_date is blank; no explicit configured completion selector exists, and the multiple-float-path ending key is blank. Per-activity finish deadlines do not by themselves identify contractual project completion.
Read-only scanning of all UDFTYPE and ACTVTYPE names containing completion/finish/anchor found the definitions below. Reporting/forecast date labels and a rolling-stock finish-code family do not establish a contractual completion selector. A differently named field could still require project-owner interpretation; no hidden code/UDF was promoted to an anchor.
```json
[
  {
    "table": "UDFTYPE",
    "udf_type_id": "2194",
    "table_name": "TASK",
    "udf_type_name": "user_field_2194",
    "udf_type_label": "CJV_02_Reporting Finish",
    "logical_data_type": "FT_END_DATE",
    "super_flag": "N",
    "indicator_expression": "",
    "summary_indicator_expression": "",
    "export_flag": ""
  },
  {
    "table": "UDFTYPE",
    "udf_type_id": "2214",
    "table_name": "TASK",
    "udf_type_name": "user_field_2214",
    "udf_type_label": "RSSOM No FInish",
    "logical_data_type": "FT_END_DATE",
    "super_flag": "N",
    "indicator_expression": "",
    "summary_indicator_expression": "",
    "export_flag": ""
  },
  {
    "table": "UDFTYPE",
    "udf_type_id": "9996",
    "table_name": "TASK",
    "udf_type_name": "user_field_9996",
    "udf_type_label": "CJV - Date.BLFinish",
    "logical_data_type": "FT_END_DATE",
    "super_flag": "N",
    "indicator_expression": "",
    "summary_indicator_expression": "",
    "export_flag": ""
  },
  {
    "table": "UDFTYPE",
    "udf_type_id": "10474",
    "table_name": "TASK",
    "udf_type_name": "user_field_10474",
    "udf_type_label": "DBJV Finish Forecast",
    "logical_data_type": "FT_TEXT",
    "super_flag": "N",
    "indicator_expression": "",
    "summary_indicator_expression": "",
    "export_flag": ""
  },
  {
    "table": "ACTVTYPE",
    "actv_code_type_id": "67379",
    "actv_short_len": "7",
    "seq_num": "49361",
    "actv_code_type": "Rolling Stock ABS Codes for Finishes MST",
    "proj_id": "",
    "wbs_id": "",
    "actv_code_type_scope": "AS_Global",
    "export_flag": ""
  }
]
```

No project anchor is selected; scoped status is INCOMPLETE_NETWORK. Independent historical component finishes are not contractual anchors. DCMA Critical Path Test and CPLI remain NOT_EVALUATED.

## Tests, files and stopping point

All behavioral extensions were reduced to proprietary-free synthetic cases first. Initial new constraint/WBS suite: 11 failed, four passed. Initial component suite: 18 failed (explicit policy not yet present). Further tests exposed and corrected validation-order/status edges within the new extension before completion. There are 47 added cases (21 constraint/exclusion/invariant cases, 26 component cases). They cover both constraint slots, compatible/conflicting bounds and negative float, weekend generalized inverses, milestones, hard-constraint rejection, completed actual preservation, calendar rejection before bound arithmetic, isolated/linked WBS and LOE, uncertainty in both dependency directions, cycles/missing endpoints, Expected Finish/progress gates, global errors, runtime relationship rejection, shared finish bounds, deterministic repeated results, and an iterative 1,101-node quarantine plus independent work. Existing 1,101-activity path, fan and calendar cases are retained.
| Command / suite | Result |
|---|---|
| Initial local regression | 346 passed, 2 deselected, 1 warning |
| Final `pytest -q -m "not external_xer"` | 393 passed, 2 deselected, 1 warning |
| Focused CPM including new constraints/components | 256 passed |
| Calendar/import/normalization plus prior reproductions | 108 passed, 2 deselected, 1 warning |
| New constraint/component suites | 47 passed |
| Separate focused calendars | 79 passed, 1 deselected |
Existing external tests still target absent NRG00800.xer and remain deselected; the new genuine project was separately imported/recalculated through the real service, not substituted for NRG. The warning remains unchanged. No Ruff was installed or run.
Created this increment: app/cpm/calculability.py; tests/test_cpm_constraints.py; tests/test_cpm_components.py; docs/phase6c_calculability_contract.md; docs/phase6c_calibration_notes.md. Modified this increment: app/cpm/activity_state.py, backward_pass.py, comparison.py, config.py, constraint_math.py, forward_pass.py, models.py, service.py, validation.py; app/importers/p6_normalization.py. Prior Phase 6B parser/normalizer/test/note edits were preserved; neither protected contract was rewritten.
Remaining blockers: validated treatment of incident LOE-derived boundaries, progressed/expired SS lag and retained logic, Expected Finish behavior, and explicit completion/float-anchor policy for the connected component. The next step requires separate semantics and failing synthetic reductions, not options switched on to increase agreement. No full real-project scheduling or P6 equivalence claim is justified yet. Controlled supported synthetic calculations remain validated. DCMA Critical Path Test is NOT_EVALUATED (immutable delay simulation absent); CPLI is NOT_EVALUATED (required completion/path-length methodology inputs not established). No automatic next phase, API, persistence, UI, reporting feature or other forbidden scope was started.
