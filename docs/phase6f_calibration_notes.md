# Phase 6F: explicit Analysis Anchors and selected-milestone calibration

## Outcome and protected baseline

Initial `pytest -q -m "not external_xer"`: **506 passed, 2 deselected, 1 existing warning**.
Final: **556 passed, 2 deselected, 1 warning in 18.84s**. All existing tests remain
passing; 50 proprietary-free cases were added (41 domain/report/Excel and 9 API).
The existing warning is FastAPI/Starlette TestClient deprecation. External NRG00800
fixtures remain deselected and were not fabricated.

An explicit ANALYSIS_ANCHOR is implemented and used separately for the three requested
milestones. It answers a selected-endpoint question, not contractual completion.
**Completion authority remains NOT_ESTABLISHED for every real analysis.** No default
contractual milestone is introduced. The three analyses are not combined or ranked
as superior/authoritative.

The 55 protected existing files captured at the start, including prior Phase 6
calculation/calibration/progress/reporting documents and existing CPM/calendar/
comparison/health/DCMA modules, have unchanged SHA-256 values. Existing forward,
Retained Logic, backward, relationship, constraint, float and path mathematics were
not changed. New orchestration reuses the validated arithmetic functions. Original
files, legacy_reference and the controlled reporting fixtures were not modified.

## Source and explicit selections

| Item | Value |
| --- | --- |
| Genuine XER | C:\Github\schedule_assurance_vscode\sample_data\1414_RSM-RSM-CW-PWD-RPT-PRM0-00063_C01 Appendix.10 - OL-RSSOM-PWS_June 2026.xer |
| SHA-256 | 77ad15c128638db79792ab915301ba236785fd134768ecd98a6992072de23999 |
| Activities / relationships / WBS / calendars | 23,263 / 36,521 / 5,139 / 27 |
| Unchanged full-project reliable remaining ES/EF population | 874 |
| Canonical activity/relationship/calendar/options core unchanged | True |

| Selected Analysis Anchor | Internal ID | Name | Imported EF | Imported LF / selected backward timestamp | Timestamp source | Authority |
| --- | --- | --- | --- | --- | --- | --- |
| OL_RSSOM_WM_100160 | 1600284 | (vii) Completion of the Ontario Line Subway | 2031-05-27T17:00:00 | 2031-05-27T17:00:00 | CALIBRATION_IMPORTED_LATE_FINISH | NOT_ESTABLISHED |
| OL_RSSOM_WM_100150 | 1600276 | (xiv) Scheduled Final Completion Date (Final Completion) | 2031-05-27T17:00:00 | 2031-05-27T17:00:00 | CALIBRATION_IMPORTED_LATE_FINISH | NOT_ESTABLISHED |
| OL_RSSOM_WM_100130 | 1600275 | (xiii) Scheduled Substantial Completion Date | 2031-03-28T17:00:00 | 2031-03-28T17:00:00 | CALIBRATION_IMPORTED_LATE_FINISH | NOT_ESTABLISHED |

Each selection is EXPLICIT_ACTIVITY_CODE, selected by the Phase 6F caller request.
The source milestone's imported LF is deliberately chosen in CALIBRATION mode; it
is not an independently established required finish. All required_finish fields
remain None. The source PROJECT.plan_end_date (Must Finish By) remains blank.

Current source inspection confirms WM_100130 has primary CS_MEOB /
FINISH_ON_OR_BEFORE at 2031-03-28 17:00. WM_100150 and WM_100160 have neither constraint.
This corrects the earlier Phase 6E evidence narrative's statement that all three
were unconstrained; the prior documents are preserved. It is an observation correction,
not an importer or scheduling-formula change. A milestone's activity deadline is not
silently promoted to contractual project completion authority.

## Architecture, modes and suitability

AnalysisAnchorConfig has separate analysis_anchor_activity_code/internal_id and
configured_analysis_milestone fields. It does not reuse the old completion selectors.
AnalysisAnchor retains internal and visible identity, name/type, milestone status,
selection method/reason, caller identity, selected timestamp/source, imported EF/LF,
required finish, suitability diagnostics and independent contractual authority/evidence.

CompletionAuthorityRecord is separate. Selection never creates authority. An established
record must have separately supplied evidence; otherwise NOT_ESTABLISHED/UNKNOWN is
preserved. Public upload APIs do not accept a claim that selection establishes authority.

- CALIBRATION: imported selected LF, explicitly labelled CALIBRATION_IMPORTED_LATE_FINISH.
  A conflicting caller finish is rejected rather than silently changing this mode.
- INDEPENDENT: caller required finish or separately established authoritative finish.
  Imported LF is never a fallback. Caller deadline source is CALLER_REQUIRED_FINISH;
  it still does not establish contractual authority.

Zero matches, ambiguous codes, conflicting ID/code selectors and absent selection are
controlled errors with no fallback. Internal identity/index/graph membership, selected
project, supported type, calendar and naive project-local timestamp are checked.
WBS Summary and LOE anchors are rejected. Completed history is not a remaining-work
anchor. Normal tasks require explicit code/internal ID and a non-milestone suitability
finding; configured milestone selection cannot silently choose a normal task.
Catalog suitability means selection inputs are usable, not that all dependency
calculations are guaranteed. The catalog explicitly says calculation_guaranteed=False.

## Directional calculability and scope

The complete upstream dependency network is traversed iteratively. Only that known
activity scope is scheduled backward. Original incident relationships are retained
for audit, including scope exits and unresolved endpoints. Scope exits are explicitly
OUTSIDE_ANALYSIS_SCOPE: they are not asserted to be irrelevant to global project CPM.
The result is ANCHOR_RELATIVE, not a project-wide float/completion calculation.

Local backward blockers propagate toward predecessors. They do not invalidate an
otherwise usable downstream late bound. A blocked early predecessor alone does not
invalidate a computable downstream late bound. Completed actual work remains
HISTORICAL_ONLY. An unfinished-to-completed bridge cannot supply an invented
remaining-work backward release. LOE/WBS remain excluded, and an upstream dependency
on their late boundary remains blocked. Expected Finish stays unsupported. Nonzero
progressed SS expired-lag inversion and progressed SF remain blocked in this mode;
Progress Override is not implemented. Supported remaining FS/FF propagation and
not-started relationship types use existing reverse formulas and remaining duration.

Every published late result passes calendar subtraction, valid boundary, backward
constraint and raw relationship checks. Failed invariants quarantine affected
predecessors before TF. TF requires reliable ES/LS and calendar; its primary formula
is unchanged activity-calendar start float, with finish float retained and any
method disagreement diagnosed. No averaging, P6 fitting or negative clamp occurs.
FF uses all original outgoing relationships, including off-scope successors, and
requires reliable supported early requirements. Missing external endpoints, completed
release uncertainty or unsupported progress prevent FF. No terminal FF convention or
imported substitute is invented.

Per-activity ES, EF, LS, LF, TF and FF availability is separate. Relationship forward
and backward statuses/reasons are separate; existing forward requirement timestamps,
expired lag and residual lag are copied unchanged, not recalculated. The compatibility
CPMResult is an internal arithmetic/result adapter; the public selected-analysis JSON
exposes ANALYSIS_ANCHOR and controlling_paths, never a project-completion claim.

## Real-project populations by selected anchor

| Anchor suffix | Upstream | Early remaining available | LS/LF available | Positive-duration late | Zero-duration late | TF available | FF available | Historical only | Excluded | Backward blocked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100160 | 15955 | 866 | 628 | 475 | 153 | 93 | 427 | 6999 | 18 | 8310 |
| 100150 | 13857 | 765 | 28 | 18 | 10 | 0 | 397 | 5782 | 14 | 8033 |
| 100130 | 13806 | 765 | 4075 | 3636 | 439 | 316 | 397 | 5760 | 14 | 3957 |

For each row, LS/LF available + historical + excluded + backward blocked equals
the complete upstream population. Early remaining availability is independent.
The full-project Phase 6D forward population stays 874; scoped early counts are
subsets, not regressions. Excluded real upstream records are LOE; the real WBS
summaries are isolated and outside these selected networks.

| Anchor suffix | Usable backward | Blocked backward | Historical relationship | Excluded endpoint | Scope exit | Forward usable among retained incident records |
| --- | --- | --- | --- | --- | --- | --- |
| 100160 | 812 | 19319 | 15938 | 166 | 165 | 1430 |
| 100150 | 29 | 18668 | 13308 | 155 | 1320 | 1344 |
| 100130 | 6945 | 11713 | 13276 | 155 | 1337 | 1344 |

The forward count above concerns retained incident records, including explicit scope-exit interfaces. Backward-usable counts concern only internal selected-scope relationships. No unrelated component is included as calculable selected work.

## Blocked boundaries and reason counts

### OL_RSSOM_WM_100160

| Backward reason (non-additive) | Activities carrying reason |
| --- | --- |
| blocked_backward_successor | 8183 |
| expected_finish_unimplemented | 719 |
| completed_backward_bridge_unimplemented | 12 |
| backward_progressed_ss_unimplemented | 9 |

| Selected endpoint ES | EF | LS | LF | TF | FF | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| BLOCKED | BLOCKED | AVAILABLE | AVAILABLE | BLOCKED | BLOCKED | blocked_early_predecessor |

### OL_RSSOM_WM_100150

| Backward reason (non-additive) | Activities carrying reason |
| --- | --- |
| blocked_backward_successor | 8029 |
| expected_finish_unimplemented | 480 |
| completed_backward_bridge_unimplemented | 12 |
| backward_progressed_ss_unimplemented | 9 |

| Selected endpoint ES | EF | LS | LF | TF | FF | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| BLOCKED | BLOCKED | AVAILABLE | AVAILABLE | BLOCKED | BLOCKED | blocked_early_predecessor |

### OL_RSSOM_WM_100130

| Backward reason (non-additive) | Activities carrying reason |
| --- | --- |
| blocked_backward_successor | 3853 |
| expected_finish_unimplemented | 479 |
| completed_backward_bridge_unimplemented | 12 |
| backward_progressed_ss_unimplemented | 9 |

| Selected endpoint ES | EF | LS | LF | TF | FF | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| BLOCKED | BLOCKED | AVAILABLE | AVAILABLE | BLOCKED | BLOCKED | blocked_early_predecessor |

Reasons overlap; they are not additive disjoint populations. Expected Finish is
still unsupported for 720 ordinary unfinished activities globally; the selected
scopes contain 719, 480 and 479 respectively. No blocker was waived to create a
larger population. All three selected endpoints retain blocked early dates while
their explicit late boundary is calculable. Consequently their TF and controlling
paths remain blocked. Supported upstream late/float fragments are not presented
as a complete driving chain to an unresolved selected early endpoint.

## LS/LF/TF/FF agreement: availability-filtered populations

Default date tolerance = 0 seconds and float tolerance = 0 hours. Dates are
classified as EXACT_MATCH, exactly zero working-time separation, elapsed tolerance
match, or DIFFERENCE. Raw elapsed variance is retained even for working-equivalent
boundaries. Float uses exact signed values before classification tolerance.
Excluded/history/unavailable outputs do not enter comparable denominators. Missing
calculated counts below cover unfinished, non-excluded scope activities, independently
for each metric. Missing imported counts concern available calculation records.

| Anchor | Metric | Comparable | Exact | Working-equivalent | Tolerance | Differences | Missing imported | Missing calculated | Median absolute raw h | Maximum absolute raw h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100160 | late_start | 628 | 491 | 131 | 0 | 6 | 0 | 8310 | 0.0 | 64.0 |
| 100160 | late_finish | 628 | 497 | 131 | 0 | 0 | 0 | 8310 | 0.0 | 64.0 |
| 100160 | total_float | 93 | 93 | 0 | 0 | 0 | 0 | 8845 | 0.0 | 0.0 |
| 100160 | free_float | 427 | 427 | 0 | 0 | 0 | 0 | 8511 | 0.0 | 0.0 |
| 100150 | late_start | 28 | 23 | 5 | 0 | 0 | 0 | 8033 | 0.0 | 15.0 |
| 100150 | late_finish | 28 | 23 | 5 | 0 | 0 | 0 | 8033 | 0.0 | 15.0 |
| 100150 | total_float | 0 | 0 | 0 | 0 | 0 | 0 | 8061 | None | None |
| 100150 | free_float | 397 | 397 | 0 | 0 | 0 | 0 | 7664 | 0.0 | 0.0 |
| 100130 | late_start | 4075 | 2446 | 229 | 0 | 1400 | 0 | 3957 | 0.0 | 5055.0 |
| 100130 | late_finish | 4075 | 2447 | 229 | 0 | 1399 | 0 | 3957 | 0.0 | 5055.0 |
| 100130 | total_float | 316 | 153 | 0 | 0 | 163 | 0 | 7716 | 1.0 | 672.0 |
| 100130 | free_float | 397 | 397 | 0 | 0 | 0 | 0 | 7635 | 0.0 | 0.0 |

The 64h raw maximum for WM_100160 and 15h for WM_100150 include non-working
boundary representations. They are not corresponding amounts of working-time
error. The six strict LS differences for WM_100160 are 0.0012 seconds each.
WM_100150 has no TF comparison population; 0 comparable is NOT_EVALUATED, not
observed zero agreement. WM_100130 has genuine scope-relative date/TF differences;
they remain visible rather than being eliminated through anchor or formula tuning.

## Critical-state comparison and P6 settings

| Raw source field | Value | Treatment |
| --- | --- | --- |
| critical_drtn_hr_cnt | 0 | Read-only evidence; no hidden policy activation |
| plan_end_date |  | Read-only evidence; no hidden policy activation |
| scd_end_date | 2031-05-27 17:00 | Read-only evidence; no hidden policy activation |
| critical_path_type | CT_TotFloat | Read-only evidence; no hidden policy activation |

A narrow read-only source helper preserves the selected PROJECT's
critical_path_type=CT_TotFloat and critical_drtn_hr_cnt=0 as typed evidence without
changing the canonical importer. Oracle documents [critical float limits and critical
path type](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/26/p6-ws-ref/projectfields-42399a.html)
and the [less-than-or-equal threshold rule](https://docs.oracle.com/cd/F74771_01/client_help/en_US/set_the_float_time_for_identifying_critical_activities.htm).
The reported P6 state is reconstructed from imported TF using that known threshold;
no exported authoritative activity critical flag is claimed. Application threshold
remains visible at 0h. Critical-state agreement alone does not validate float magnitude
or a complete path.

| Anchor | TF-state comparable | Configured-definition agreements | Application-only critical | P6-definition-only critical | Threshold comparison |
| --- | --- | --- | --- | --- | --- |
| 100160 | 93 | 93 | 0 | 0 | EQUIVALENT_THRESHOLDS |
| 100150 | 0 | 0 | 0 | 0 | EQUIVALENT_THRESHOLDS |
| 100130 | 316 | 316 | 0 | 0 | EQUIVALENT_THRESHOLDS |

Observed SCHEDOPTIONS still includes FT_FF (P6 finish-float methodology),
sched_use_project_end_date_for_float=Y, multiple-longest-path calculation enabled,
maximum 10 and use_total_float_multiple_longest_paths=N. These raw options are
preserved diagnostic evidence. Application primary TF remains start-based, and
selected dependency-scope bounds differ from a complete project's boundaries.
No P6 multiple-float-path or Longest Path equivalence is asserted.

## Discrepancy categories and supporting evidence

Categories are hypotheses except directly verified source arithmetic facts:

- SOURCE_DURATION_PRECISION: WM_100160's six LS residuals are exactly +/-0.0012s.
  Imported remaining durations 640.033333 / 640.016667h differ from the working span
  between minute-resolution imported LS/LF. Shared subtraction exactly follows the
  exported hours. Precision loss during export is a supported explanation, not a
  claim about unavailable internal P6 precision. No rounding correction is made.
- WORKING_BOUNDARY_EQUIVALENCE: working_hours_between is exactly zero despite raw
  elapsed separation. This is demonstrated calendar equivalence, not tolerance.
- SELECTED_SCOPE_VS_PROJECT_BOUNDARY: WM_100130's later relative dates have evidence
  of omitted scope-exit successor bounds. A local imported-bound agreement supports
  this explanation; it is not proof of the sole cause of every project mismatch.
- FLOAT_METHODOLOGY_DIFFERENCE: P6 FT_FF versus protected application start float is
  a known capability difference, not automatically the cause of each variance.
- UNSUPPORTED_BOUNDARY / UNKNOWN: Expected Finish, LOE, completed retained bridges
  and progressed SS are not assigned calculated values. Unproven remaining causes
  remain unproven rather than being declared implementation defects.

No proven defect in protected CPM mathematics was found. New orchestration safety
issues were caught synthetically: external successor omission in the FF gate,
forward-cycle descendants incorrectly blocking independent late propagation, and
loss of forward relationship audit fields. These were corrected in new code only.

### Six strict WM_100160 LS precision differences

| Internal ID | Activity code | Imported LS | Calculated LS | Raw variance h | Remaining h | Imported late span working h |
| --- | --- | --- | --- | --- | --- | --- |
| 4618606 | OL_RSSOM_DE_563542 | 2030-12-16T16:58:00 | 2030-12-16T16:58:00.001200 | 3.333333333333333e-07 | 640.033333 | 640.0333333333333 |
| 4639473 | OL_RSSOM_DE_563730 | 2030-12-16T16:59:00 | 2030-12-16T16:58:59.998800 | -3.333333333333333e-07 | 640.016667 | 640.0166666666667 |
| 4639488 | OL_RSSOM_DE_563880 | 2030-12-16T16:59:00 | 2030-12-16T16:58:59.998800 | -3.333333333333333e-07 | 640.016667 | 640.0166666666667 |
| 4639503 | OL_RSSOM_DE_564030 | 2030-12-16T16:59:00 | 2030-12-16T16:58:59.998800 | -3.333333333333333e-07 | 640.016667 | 640.0166666666667 |
| 4639518 | OL_RSSOM_DE_564180 | 2030-12-16T16:59:00 | 2030-12-16T16:58:59.998800 | -3.333333333333333e-07 | 640.016667 | 640.0166666666667 |
| 4639533 | OL_RSSOM_DE_564330 | 2030-12-16T16:59:00 | 2030-12-16T16:58:59.998800 | -3.333333333333333e-07 | 640.016667 | 640.0166666666667 |

Synthetic precision regression: subtracting 2.016667h from 2026-01-05 11:00
on a 9h weekday calendar returns 08:58:59.998800. The imported comparison minute
08:59 differs by -0.0012s. At default zero tolerance it remains DIFFERENCE; an
explicit 0.01s comparison tolerance changes classification only. Raw variance and
calculated dates stay identical. Production/default tolerances were not increased.

### Largest true WM_100130 discrepancies

#### late_start

| Internal ID | Activity code | Imported | Calculated | Raw variance h | Working variance h |
| --- | --- | --- | --- | --- | --- |
| 1602243 | OL_RSSOM_DE_201170 | 2030-07-18T17:00:00 | 2031-02-14T08:00:00 | 5055.0 | 1152.0 |
| 1602242 | OL_RSSOM_DE_201540 | 2030-07-19T08:00:00 | 2031-02-14T08:00:00 | 5040.0 | 1152.0 |
| 1604868 | OL_RSSOM_DE_120620 | 2029-11-16T08:00:00 | 2030-04-15T08:00:00 | 3600.0 | 816.0 |
| 1604870 | OL_RSSOM_DE_120630 | 2029-11-16T08:00:00 | 2030-04-15T08:00:00 | 3600.0 | 816.0 |
| 1604869 | OL_RSSOM_DE_120680 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1604871 | OL_RSSOM_DE_120690 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1600249 | OL_RSSOM_WM_300140 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1600250 | OL_RSSOM_WM_300440 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1597592 | OL_RSSOM_160250 | 2030-11-13T08:00:00 | 2031-03-17T08:00:00 | 2976.0 | 672.0 |
| 1597605 | OL_RSSOM_14830 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1597617 | OL_RSSOM_14920 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1597620 | OL_RSSOM_262370 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1612667 | OL_RSSOM_262870 | 2030-11-29T08:00:00 | 2031-03-27T08:00:00 | 2832.0 | 640.0 |
| 1612664 | OL_RSSOM_262840 | 2030-07-11T17:00:00 | 2030-11-06T08:00:00 | 2823.0 | 640.0 |
| 1612662 | OL_RSSOM_262820 | 2030-05-01T08:00:00 | 2030-08-26T08:00:00 | 2808.0 | 640.0 |
| 1612663 | OL_RSSOM_262830 | 2030-07-05T08:00:00 | 2030-10-30T08:00:00 | 2808.0 | 640.0 |
| 1612665 | OL_RSSOM_262850 | 2030-07-12T08:00:00 | 2030-11-06T08:00:00 | 2808.0 | 640.0 |
| 1600633 | OL_RSSOM_DE_410640 | 2030-04-24T08:00:00 | 2030-08-19T08:00:00 | 2808.0 | 640.0 |
| 1600643 | OL_RSSOM_DE_410670 | 2030-04-24T08:00:00 | 2030-08-19T08:00:00 | 2808.0 | 640.0 |
| 1600653 | OL_RSSOM_DE_410700 | 2030-04-24T08:00:00 | 2030-08-19T08:00:00 | 2808.0 | 640.0 |

#### late_finish

| Internal ID | Activity code | Imported | Calculated | Raw variance h | Working variance h |
| --- | --- | --- | --- | --- | --- |
| 1602243 | OL_RSSOM_DE_201170 | 2030-07-18T17:00:00 | 2031-02-14T08:00:00 | 5055.0 | 1152.0 |
| 1602242 | OL_RSSOM_DE_201540 | 2030-08-16T17:00:00 | 2031-03-14T16:00:00 | 5039.0 | 1152.0 |
| 1604869 | OL_RSSOM_DE_120680 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1604871 | OL_RSSOM_DE_120690 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1600249 | OL_RSSOM_WM_300140 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1600250 | OL_RSSOM_WM_300440 | 2030-10-31T17:00:00 | 2031-03-28T17:00:00 | 3552.0 | 816.0 |
| 1604868 | OL_RSSOM_DE_120620 | 2030-10-31T17:00:00 | 2031-03-28T16:00:00 | 3551.0 | 816.0 |
| 1604870 | OL_RSSOM_DE_120630 | 2030-10-31T17:00:00 | 2031-03-28T16:00:00 | 3551.0 | 816.0 |
| 1597605 | OL_RSSOM_14830 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1597617 | OL_RSSOM_14920 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1597592 | OL_RSSOM_160250 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1597620 | OL_RSSOM_262370 | 2030-11-26T17:00:00 | 2031-03-28T16:00:00 | 2927.0 | 672.0 |
| 1612666 | OL_RSSOM_262860 | 2030-11-28T17:00:00 | 2031-03-26T17:00:00 | 2832.0 | 640.0 |
| 1612664 | OL_RSSOM_262840 | 2030-07-11T17:00:00 | 2030-11-06T08:00:00 | 2823.0 | 640.0 |
| 1612662 | OL_RSSOM_262820 | 2030-07-04T17:00:00 | 2030-10-29T17:00:00 | 2808.0 | 640.0 |
| 1612663 | OL_RSSOM_262830 | 2030-07-11T17:00:00 | 2030-11-05T17:00:00 | 2808.0 | 640.0 |
| 1612667 | OL_RSSOM_262870 | 2030-12-02T17:00:00 | 2031-03-28T16:00:00 | 2783.0 | 640.0 |
| 1612665 | OL_RSSOM_262850 | 2030-07-22T17:00:00 | 2030-11-14T17:00:00 | 2760.0 | 640.0 |
| 1600631 | OL_RSSOM_DE_410634 | 2030-03-25T17:00:00 | 2030-07-18T17:00:00 | 2760.0 | 640.0 |
| 1600635 | OL_RSSOM_DE_410637 | 2030-04-23T17:00:00 | 2030-08-16T17:00:00 | 2760.0 | 640.0 |

#### total_float

| Internal ID | Activity code | Imported | Calculated | Raw variance h | Working variance h |
| --- | --- | --- | --- | --- | --- |
| 1597617 | OL_RSSOM_14920 | 8656.0 | 9328.0 | 672.0 | None |
| 13719348 | OL_RSSOM_PR_520260 | 7072.0 | 7464.0 | 392.0 | None |
| 13719344 | OL_RSSOM_PR_520270 | 7072.0 | 7464.0 | 392.0 | None |
| 13719345 | OL_RSSOM_PR_520280 | 7072.0 | 7464.0 | 392.0 | None |
| 13719346 | OL_RSSOM_PR_520290 | 7072.0 | 7464.0 | 392.0 | None |
| 13719347 | OL_RSSOM_PR_520300 | 7072.0 | 7464.0 | 392.0 | None |
| 13719343 | OL_RSSOM_PR_520310 | 7072.0 | 7464.0 | 392.0 | None |
| 1596011 | OL_RSSOM_CN_100260 | 12256.0 | 12592.0 | 336.0 | None |
| 1596012 | OL_RSSOM_CN_100270 | 12256.0 | 12592.0 | 336.0 | None |
| 1596013 | OL_RSSOM_CN_100280 | 12256.0 | 12592.0 | 336.0 | None |
| 1596014 | OL_RSSOM_CN_100290 | 12256.0 | 12592.0 | 336.0 | None |
| 1596015 | OL_RSSOM_CN_100300 | 12256.0 | 12592.0 | 336.0 | None |
| 1596016 | OL_RSSOM_CN_100310 | 12256.0 | 12592.0 | 336.0 | None |
| 1596017 | OL_RSSOM_CN_100320 | 12256.0 | 12592.0 | 336.0 | None |
| 1596018 | OL_RSSOM_CN_100330 | 12256.0 | 12592.0 | 336.0 | None |
| 1596019 | OL_RSSOM_CN_100360 | 12256.0 | 12592.0 | 336.0 | None |
| 1596209 | OL_RSSOM_159726 | 8416.0 | 8656.0 | 240.0 | None |
| 1596210 | OL_RSSOM_159727 | 8416.0 | 8656.0 | 240.0 | None |
| 1596211 | OL_RSSOM_159728 | 8416.0 | 8656.0 | 240.0 | None |
| 1596212 | OL_RSSOM_159729 | 8416.0 | 8656.0 | 240.0 | None |

Representative scope evidence: OL_RSSOM_DE_201170 has imported LS/LF
2030-07-18 17:00 and selected-scope calculated LS/LF 2031-02-14 08:00 (+5055 elapsed h).
Its FS successor OL_RSSOM_DE_201540 is inside the selected scope. That successor
has an outgoing zero-lag FS relationship to OL_RSSOM_DE_202820 outside the
Substantial Completion upstream scope. The outside successor imported LS is
2030-08-19 08:00, consistent with a predecessor finish at the preceding Friday
2030-08-16 17:00 after calendar closing normalization; that matches DE_201540's
imported LF. Its selected-scope LF is instead 2031-03-14 16:00. These imported
successor dates were inspected as evidence only, never used as calculation proxies.

Other recorded scope-exit examples include WM_300440 -> PS_005570 and
OL_RSSOM_14830 -> DE_105600. The largest TF variance is OL_RSSOM_14920:
imported 8656h, calculated anchor-relative 9328h, +672h. A supported scope/methodology
explanation is retained; no project-specific exception or date-fitting rule is added.

## Connected controlling paths, bounds and limitations

Public label: APPLICATION_CALCULATED_CONTROLLING_PATH, never P6 Longest Path.
Only calculated FORWARD controlling edges are traced to the selected endpoint.
Ties, deterministic rank, ordered identities/relationships, signed lag sum,
effective activity-hour sum, min/max TF, constraint/data/history boundaries and
truncation are preserved. Existing bounded iterative enumeration/ranking is reused.
An internal traversal eligibility ceiling admits all known TF on controlling edges;
it does not change activity criticality or published thresholds. Positive-float
controlling traces are explicitly labelled controlling, not critical.

The three real analyses have zero certified controlling paths because selected
ES/EF/TF remain unavailable. This is BLOCKED, not evidence of no network path.
No disconnected zero-float activity list is substituted.

Synthetic F1/F2/F3 selections independently produce 2/4/6 activity scopes and one
connected controlling path each, with manually defensible 10:00/12:00/14:00 endpoints.
Required finish at 12:00 for F3 preserves -2h float. A later independent finish
preserves positive float without labelling activities critical. A tied diamond
returns both branches; a one-path cap reports truncation. A 1,102-node network
and path run iteratively without recursion failure. Mixed-calendar/duration/lag
mathematics remains covered by the protected CPM suite and new selected-wrapper
FS/SS/FF/SF and signed-lag cases.

## Reporting, Excel and UI contract

The existing ForensicChangeReport receives a completed SelectedAnchorAnalysis
through an optional adapter. It adds selected anchor/method/timestamp/source/mode,
preserves independent completion authority, updates Report Summary and replaces
only the Application Calculated Controlling Paths section. Other forensic sections
are equality-tested unchanged. Existing A1500/A1700/A1200/A1300 acceptance cases
remain passing. Default report requests still select no anchor.

Path rows include anchor code/name/authority/source, path ID/rank/sequence, activity
visible/internal identity/name/WBS, predecessor relationship/type/signed lag,
calculated ES/EF/LS/LF/TF/criticality, availability and completeness/truncation.
Blocked results retain an explicit reason rather than a blank sheet. Excel's
metadata band says Selected Analysis Anchor and never declares contractual project
completion. Dates remain typed; the 29-sheet layout and other calculations remain.

A synthetic selected F3 demonstration workbook is saved at
outputs/phase6f-selected-analysis/Selected Analysis Anchor - Synthetic F3.xlsx.
It is explicitly synthetic, not a substitute for the genuine project or NRG fixture.
Its six path records and authority metadata were verified through openpyxl and
rendered for visual QA. All sheet previews were rendered; the spreadsheet tool
again returned nonzero during teardown after successful rendering, without a render
diagnostic. Production XLSX creation/reopen tests pass; desktop Excel was not tested.

Selected-analysis JSON schema 1.0 contains analysis_anchor, independent completion
status, mode, per-anchor summary, activity_results, directional_availability for
activities and relationships, controlling_paths/path_statistics/status, blocked
boundaries, comparisons and diagnostics. It omits Schedule and internal CPMResult
objects. Candidate catalog has evidence, identity/type/WBS/date context, suitability,
selection methods and pagination; selected_analysis_anchor remains None until a caller
chooses. All nulls, raw signed variances and per-metric availability remain explicit.

## Thin API contracts

- POST /api/schedules/cpm/analysis-anchors: multipart file=.xer, offset/limit query
  (default 500, maximum 5000). Returns candidate evidence/suitability and source
  critical-definition evidence; does not select or schedule.
- POST /api/schedules/cpm/analyze-anchor: multipart file, activity_code and/or
  internal_id, mode CALIBRATION/INDEPENDENT, required_finish for independent mode,
  optional selected_by/selection_reason. Returns completed selected-analysis JSON.
- Existing forensic preview/Excel routes optionally accept
  analysis_anchor_activity_code, analysis_anchor_internal_id, analysis_mode and
  analysis_required_finish. Their default behavior is unchanged. The reporting
  service imports each file once, compares, optionally analyzes the selected current
  endpoint, and projects the completed report. Calculations are outside handlers.

Wrong extension returns 415; invalid/not-found/ambiguous/unsuitable selection or
missing independent finish returns structured 422; size limits return 413. Source
uploads are capped at 100 MiB and temporary files are cleaned up. No selection,
report or schedule is persisted. Independent authority is not established by a form
field. No database, UI, simulation, Monte Carlo, leveling, earned value or AI is added.

## Tests, files and final status

The initial tests failed collection before the new implementation existed. New
focused failures then demonstrated the missing FF external-endpoint gate, missing
optional report API integration, incorrect reverse availability for forward cycle
descendants, and missing forward audit projection. These were reduced/proprietary-
free cases and fixed only in new orchestration/projection code. No existing test
expectation was weakened and no protected arithmetic was changed.

| Check | Exact result |
| --- | --- |
| Initial complete non-external | 506 passed, 2 deselected, 1 warning in 14.48s |
| Focused CPM/anchor/path/progress/reporting/Excel/API before final audit case | 412 passed, 1 warning in 18.76s |
| Final audit-preservation regression in isolation | 1 passed, 40 deselected in 0.40s |
| Final pytest -q -m "not external_xer" | 556 passed, 2 deselected, 1 warning in 18.84s |
| Protected existing file SHA-256 checks | 55 unchanged |
| git diff --check | Passed |

Created:
- app/cpm/analysis_anchors.py
- app/cpm/analysis_comparison.py
- app/cpm/analysis_io.py
- app/cpm/analysis_serialization.py
- app/cpm/selected_analysis.py
- app/reporting/analysis_adapter.py
- app/api/cpm_analysis.py
- tests/test_analysis_anchors.py
- tests/test_analysis_anchor_api.py
- docs/phase6f_analysis_contract.md
- docs/phase6f_calibration_notes.md
- outputs/phase6f-selected-analysis/Selected Analysis Anchor - Synthetic F3.xlsx

Modified in this increment:
- app/main.py: register the new selected-analysis router.
- app/reporting/models.py: optional analysis metadata fields.
- app/reporting/builder.py: optional completed-analysis adapter.
- app/reporting/excel_renderer.py: dynamic Selected Analysis Anchor metadata text.
- app/reporting/service.py: opt-in selected analysis outside routes/rendering.
- app/api/reports.py: optional selected-analysis request inputs and controlled errors.

Earlier working-tree changes are preserved; no protected existing CPM module,
requirements, source XER/reference workbook or sample fixture is changed.

Remaining limitations: Expected Finish scheduling, remaining backward SS expired-lag
semantics, progressed SF, completed retained bridges, LOE-derived boundaries,
project-wide versus selected-scope float semantics, direct P6 critical/Longest Path
flag equivalence and source duration precision. No authoritative project completion
was designated. The current implementation supports controlled explicit relative
analysis and transparent partial availability, not complete P6 reproduction.

DCMA Critical Path Test = NOT_EVALUATED (immutable delay simulation is absent).
CPLI = NOT_EVALUATED (its required-finish/path-length methodology is separately scoped).
No next phase is started.
