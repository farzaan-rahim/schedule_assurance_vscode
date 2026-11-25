# Phase 6E: completion-anchor evidence and stop decision

## Decision and scope

**ANCHOR_NOT_SELECTED. No authoritative completion identity is established by this export.**
There are three strong review candidates, not three authorized anchors. No real-project
backward calculation, float calculation, critical-state comparison or controlling-path
validation was run in this increment. Ranking does not choose an anchor.

The prior Phase 6D forward result remains intact: 874 reliable remaining-work ES/EF
results, including 583 positive-duration activities matching both imported P6 dates
exactly; 189 zero-duration events have exactly working-time-equivalent boundaries.
Raw elapsed variances remain distinct from working-hour equivalence. No validated
calendar, progress, forward/backward, relationship, constraint, float or path policy changed.

This is a repository calibration evidence note, not a reporting feature.

## Source and reproducibility

| Item | Value |
| --- | --- |
| Source | C:\Github\schedule_assurance_vscode\sample_data\1414_RSM-RSM-CW-PWD-RPT-PRM0-00063_C01 Appendix.10 - OL-RSSOM-PWS_June 2026.xer |
| SHA-256 | 77ad15c128638db79792ab915301ba236785fd134768ecd98a6992072de23999 |
| Project ID/code | 782 / OL-RSSOM-PWS-Live |
| Root WBS project name | Ontario Line Subway RSSOM Project - Progress Works Schedule - Live |
| Activities / relationships / WBS / calendars | 23,263 / 36,521 / 5,139 / 27 |
| Data Date (PROJECT.last_recalc_date) | 2026-07-01 00:01 |
| PROJECT.last_schedule_date | 2026-07-03 15:29 |
| Imported activities/relationships/options unchanged by investigation | True |

All activities, assigned Activity Codes/UDFs, primary/secondary finish constraints,
project fields, root WBS dates and terminal topology were inspected through the existing
parser, canonical mapper, Phase 5A metadata helpers and ScheduleGraph. No source data
was synthesized. Six existing Phase 6 contracts were read and their SHA-256 values
were checked unchanged. The genuine XER hash was checked unchanged. The absent
NRG00800.xer fixture remains absent and external tests remain deselected.

## Exact project-level evidence

| Table.object | Raw P6 field | Raw value (JSON) | Interpretation |
| --- | --- | --- | --- |
| PROJECT.782 | plan_end_date | "" | REQUIRED_PROJECT_FINISH |
| PROJECT.782 | scd_end_date | "2031-05-27 17:00" | SCHEDULED_FINISH_OUTPUT |
| PROJECT.782 | plan_start_date | "2022-09-06 00:00" | PLANNED_START |
| PROJECT.782 | fcst_start_date | "" | FORECAST_START |
| PROJECT.782 | base_proj_id | "3120" | BASELINE_REFERENCE |
| PROJECT.782 | base_proj_id1 | "" | BASELINE_REFERENCE |
| PROJECT.782 | base_proj_id2 | "" | BASELINE_REFERENCE |
| PROJECT.782 | sum_base_proj_id | "1344" | BASELINE_REFERENCE |
| PROJECT.782 | source_proj_id | "" | SOURCE_PROJECT_REFERENCE |
| PROJECT.782 | orig_proj_id | "" | ORIGINAL_PROJECT_REFERENCE |
| PROJECT.782 | baselines_to_export | "" | BASELINE_EXPORT_SETTING |
| PROJECT.782 | baseline_names_to_export | "" | BASELINE_EXPORT_SETTING |
| PROJECT.782 | use_project_baseline_flag | "Y" | BASELINE_SETTING |
| PROJECT.782 | last_baseline_update_date | "" | BASELINE_UPDATE_TIMESTAMP |
| PROJWBS.440826 | anticip_start_date | "" | ANTICIPATED_START |
| PROJWBS.440826 | anticip_end_date | "" | ANTICIPATED_FINISH |

`PROJECT.plan_end_date` is P6 **Must Finish By**, not a populated planned-finish
promise inferred from its field name. It is blank. `PROJECT.scd_end_date` is computed
Scheduled Finish: **2031-05-27 17:00**. Oracle distinguishes these concepts in its
[XER mapping](https://docs.oracle.com/cd/G48897_01/English/Mapping_and_Schema/xer_import_export_data_map_project/xer_import_export_data_map_project.pdf)
and [P6 date-field help](https://docs.oracle.com/cd/G48897_01/p6help/en/47238.htm).
A computed maximum finish is evidence of the P6 calculation end, not by itself
contractual authority or a global required-finish instruction.

There is no separate forecast-finish, target-finish or baseline-finish date column
in this exported PROJECT row. `fcst_start_date` is a start field. The baseline IDs
3120 and 1344 reference projects whose dated records are not included among the
single exported PROJECT row. They are not dates. All 5,139 PROJWBS anticipated
finish values are blank, including root WBS 440826. Blank and absent remain distinct.

The existing SCHEDOPTIONS interpretation (per-project-end float enabled and P6's
FT_FF float setting) is unchanged. Scheduled Finish and milestone imported LF/TF
corroborate a P6 mathematical end; neither proves a contractual anchor. No float
formula or deadline is reverse-engineered from those results.

## Terminal population

7,200 terminals span 73 WBS nodes: 7,160 completed history and 40 unfinished. Only one unfinished terminal is a normal finish milestone; the other 39 are LOE/WBS Summary. Being the sole normal unfinished terminal does not establish contractual authority.

| Canonical type | Status | Count |
| --- | --- | --- |
| finish_milestone | complete | 1072 |
| finish_milestone | not_started | 1 |
| level_of_effort | complete | 4 |
| level_of_effort | in_progress | 34 |
| level_of_effort | not_started | 1 |
| milestone | complete | 6 |
| task | complete | 6072 |
| wbs_summary | complete | 6 |
| wbs_summary | in_progress | 3 |
| wbs_summary | not_started | 1 |

### Terminal grouping by WBS (all 73 groups)

| WBS internal ID | Code | Name | Terminals |
| --- | --- | --- | --- |
| 1249421 | 16 | Retired Activities for Feb'2025 | 1572 |
| 440880 | 4 | Retired Activities for Mar'2024 | 893 |
| 440881 | 5 | Retired Activities for Apr'2024 | 867 |
| 440884 | 8 | Retired Activities for Jul'2024 | 606 |
| 440888 | 13 | Retired Activities for Nov'2024 | 481 |
| 3418675 | 24 | Retired Activities for Oct'25 | 466 |
| 440883 | 7 | Retired Activities for Jun'2024 | 442 |
| 2197502 | 20 | Retired Activities for Jun'2025 | 266 |
| 440878 | 1 | Retired Activities for Jan'2024 | 255 |
| 440879 | 3 | Retired Activities for Feb'2024 | 170 |
| 440886 | 10 | Retired Activities for Sep'2024 | 156 |
| 440877 | 2 | Retired Activities for the Transition of PWS BL01 and the Approved BL02 - November' 2023 | 113 |
| 4570914 | 29 | Retired Activities for Mar'2026 | 107 |
| 3635471 | 25 | Retired Activities for Nov'25 | 104 |
| 440882 | 6 | Retired Activities for May'2024 | 87 |
| 440889 | 14 | Retired Activities for Dec'2024 | 73 |
| 1354777 | 17 | Retired Activities for Mar'2025 | 66 |
| 2914132 | 22 | Retired Activities for Aug'2025 | 59 |
| 5031785 | 30 | Retired Activities for Apr'2026 | 53 |
| 5400534 | 31 | Retired Activities for May'2026 | 51 |
| 3203430 | 23 | Retired Activities for Sep'25 | 46 |
| 440885 | 9 | Retired Activities for Aug'2024 | 39 |
| 1676470 | 18 | Retired Activities for Apr'2025 | 38 |
| 2761859 | 21 | Retired Activities for Jul'2025 | 37 |
| 1881399 | 19 | Retired Activities for May'2025 | 30 |
| 440887 | 12 | Retired Activities for Oct'2024 | 18 |
| 3896048 | 26 | Retired Activities for Dec'25 | 15 |
| 4213045 | 27 | Retired Activities for Jan'2026 | 13 |
| 4449502 | 28 | Retired Activities for Feb'2026 | 13 |
| 5635303 | 32 | Retired Activities for Jun'2026 | 10 |
| 1089191 | 15 | Retired Activities for Jan'2025 | 6 |
| 440876 | 11 | Retired Activities between Baseline REV 00 and Rev 01 | 5 |
| 440859 | AD | PA Schedule 10 - Appendix A - Minimum Works Submittals | 2 |
| 440922 | 5 | General | 2 |
| 440844 | 0 | General | 1 |
| 440856 | 1 | Key Milestones | 1 |
| 441103 | 18 | S-172 - Environmental Management System | 1 |
| 441521 | g | g - Environmental Audit Report | 1 |
| 441523 | m | m - Designated Substances and Hazardous Materials Management Plan | 1 |
| 441524 | p | p - Environmental Conditions Summary | 1 |
| 441525 | s | s - Erosion and Sediment Control Plan | 1 |
| 441526 | v | v - Flood Hazard Analysis | 1 |
| 441528 | bb | bb - Archaeological Risk Management Plan | 1 |
| 441530 | gg | gg - Construction Air Quality Management Plan | 1 |
| 441531 | c | c - Documentation of qualifications of Environmental Positions | 1 |
| 441532 | e | e - Annual Environmental Compliance Monitoring Report | 1 |
| 441533 | h | h - Documentation of qualification of Independent Environmental Consultant | 1 |
| 441534 | k | k - Spill Prevention and Response Plan | 1 |
| 441536 | q | q - Soil and Excavated Material Management Plan | 1 |
| 441537 | t | t - Well Decommissioning and Protection Plan | 1 |
| 441538 | w | w - Construction Noise and Vibration Management Plan | 1 |
| 441542 | d | d - Additional Environmental Reports | 1 |
| 441543 | f | f - Monthly Environmental Report | 1 |
| 441547 | r | r - Soil Importation Plan | 1 |
| 441548 | u | u - Groundwater Management and Dewatering Plan | 1 |
| 441549 | x | x - Weekly Construction Noise and Vibration Monitoring Report | 1 |
| 441551 | dd | dd - Integrated Vegetation Management Plan | 1 |
| 441553 | hh | hh - Weekly Construction Air Quality Monitoring Report | 1 |
| 441569 | 15 | Salt Management Plan | 1 |
| 441572 | 17 | Process for managing and responding to air quality concerns | 1 |
| 441573 | 18 | Turtle surveys | 1 |
| 441574 | 19 | Bird and nest survey | 1 |
| 441575 | 21 | Flood Contingency Plan | 1 |
| 441576 | 22 | Flood Impact Assesment | 1 |
| 441577 | 23 | Quantitative assessment to update the construction mitigation plan | 1 |
| 441641 | GATE | Gatehouse building | 1 |
| 441649 | TPSS | TPSS Building | 1 |
| 441656 | MOW | MOW Building | 1 |
| 441658 | BULD | Maintenance Building | 1 |
| 442094 | 84 | S-129 - GIMP Monthly Reports | 1 |
| 443023 | 1 | S-156A - Pre-Construction Condition Survey Report - OMSF - CONTINUOUS | 1 |
| 443025 | 3 | S-156C - Post-Construction Condition Survey Report - OMSF - CONTINUOUS | 1 |
| 444392 | 4 | S-153A (d) - the Boundary Monuments Inventory Report - CONTINUOUS | 1 |

### Terminal finish-date grouping (imported Early Finish, not Actual Finish)

| Imported EF | Status | Type | Count |
| --- | --- | --- | --- |
| 2026-07-01 00:01:00 | complete | MILESTONE | 1078 |
| 2026-07-01 00:01:00 | complete | ORDINARY_TASK | 6072 |
| 2026-12-24 17:00:00 | in_progress | wbs_summary | 1 |
| 2027-12-14 17:00:00 | in_progress | level_of_effort | 2 |
| 2028-04-10 17:00:00 | in_progress | level_of_effort | 12 |
| 2028-05-18 17:00:00 | in_progress | wbs_summary | 1 |
| 2029-05-07 17:00:00 | not_started | wbs_summary | 1 |
| 2029-06-14 17:00:00 | in_progress | level_of_effort | 4 |
| 2029-06-14 17:00:00 | in_progress | wbs_summary | 1 |
| 2029-06-14 17:00:00 | not_started | level_of_effort | 1 |
| 2029-10-04 17:00:00 | in_progress | level_of_effort | 1 |
| 2030-08-06 17:00:00 | in_progress | level_of_effort | 8 |
| 2030-10-18 17:00:00 | in_progress | level_of_effort | 1 |
| 2031-03-28 17:00:00 | in_progress | level_of_effort | 2 |
| 2031-04-02 17:00:00 | in_progress | level_of_effort | 4 |
| 2031-05-27 17:00:00 | not_started | MILESTONE | 1 |
| None | complete | level_of_effort | 4 |
| None | complete | wbs_summary | 6 |

The 7,150 completed ordinary/milestone terminal early finishes equal the Data Date in this export. They are imported scheduling fields, not evidence that historical Actual Finish occurred at that instant; actual dates are retained separately. Ten completed LOE/WBS terminals lack imported EF.

### Terminal imported Total Float grouping (hours)

| TF hours | Status | Type | Count |
| --- | --- | --- | --- |
| 0.0 | in_progress | level_of_effort | 2 |
| 0.0 | not_started | MILESTONE | 1 |
| 1208.0 | in_progress | level_of_effort | 1 |
| 1400.0 | in_progress | wbs_summary | 1 |
| 1535.0 | in_progress | level_of_effort | 7 |
| 1600.0 | in_progress | wbs_summary | 1 |
| 3352.0 | not_started | level_of_effort | 1 |
| 4256.0 | not_started | wbs_summary | 1 |
| 440.0 | in_progress | level_of_effort | 4 |
| 480.0 | in_progress | level_of_effort | 1 |
| 4800.0 | in_progress | level_of_effort | 1 |
| 4832.0 | in_progress | level_of_effort | 12 |
| 4879.0 | in_progress | level_of_effort | 4 |
| 4879.0 | in_progress | wbs_summary | 1 |
| 5096.0 | in_progress | level_of_effort | 2 |
| None | complete | MILESTONE | 1078 |
| None | complete | ORDINARY_TASK | 6072 |
| None | complete | level_of_effort | 4 |
| None | complete | wbs_summary | 6 |

Terminal TF is missing for 7,160, zero for 3, positive for 37 and negative for none. Zero float alone is not authority.

### Terminal constraint grouping

| Primary/secondary canonical constraint tuple | Status | Type | Count |
| --- | --- | --- | --- |
| ('FINISH_ON_OR_AFTER',) | complete | MILESTONE | 2 |
| ('FINISH_ON_OR_AFTER',) | complete | ORDINARY_TASK | 30 |
| ('START_ON_OR_AFTER', 'FINISH_ON_OR_BEFORE') | complete | ORDINARY_TASK | 2 |
| ('START_ON_OR_AFTER',) | complete | MILESTONE | 3 |
| ('START_ON_OR_AFTER',) | complete | ORDINARY_TASK | 76 |
| () | complete | MILESTONE | 1073 |
| () | complete | ORDINARY_TASK | 5964 |
| () | complete | level_of_effort | 4 |
| () | complete | wbs_summary | 6 |
| () | in_progress | level_of_effort | 34 |
| () | in_progress | wbs_summary | 3 |
| () | not_started | MILESTONE | 1 |
| () | not_started | level_of_effort | 1 |
| () | not_started | wbs_summary | 1 |

### Terminal Activity Code classifications relevant to completion review

| Code type | Assigned value | Status | Activity type | Count |
| --- | --- | --- | --- | --- |
| *OL_RSSOM_ Civil Contractor | Don Valley Crossing | complete | MILESTONE | 21 |
| *OL_RSSOM_ Civil Contractor | Don Valley Crossing | complete | ORDINARY_TASK | 66 |
| *OL_RSSOM_ Civil Contractor | Elevated Guidway and Stations | complete | MILESTONE | 144 |
| *OL_RSSOM_ Civil Contractor | Elevated Guidway and Stations | complete | ORDINARY_TASK | 433 |
| *OL_RSSOM_ Civil Contractor | Ontartio Transit Group (South Civil) | complete | MILESTONE | 66 |
| *OL_RSSOM_ Civil Contractor | Ontartio Transit Group (South Civil) | complete | ORDINARY_TASK | 266 |
| *OL_RSSOM_ Civil Contractor | Pape Tunnel & Underground Stations | complete | MILESTONE | 152 |
| *OL_RSSOM_ Civil Contractor | Pape Tunnel & Underground Stations | complete | ORDINARY_TASK | 503 |
| *OL_RSSOM_ABS | Major Milestones | not_started | MILESTONE | 1 |
| *OL_RSSOM_ABS | Supplier/ Sub-contractor Mobilization | complete | ORDINARY_TASK | 6 |
| *OL_RSSOM_Active/Retired | Active Activity | complete | level_of_effort | 3 |
| *OL_RSSOM_Active/Retired | Active Activity | in_progress | level_of_effort | 34 |
| *OL_RSSOM_Active/Retired | Active Activity | in_progress | wbs_summary | 3 |
| *OL_RSSOM_Active/Retired | Active Activity | not_started | MILESTONE | 1 |
| *OL_RSSOM_Active/Retired | Active Activity | not_started | level_of_effort | 1 |
| *OL_RSSOM_Active/Retired | Active Activity | not_started | wbs_summary | 1 |
| *OL_RSSOM_Active/Retired | Retired Activity | complete | MILESTONE | 1078 |
| *OL_RSSOM_Active/Retired | Retired Activity | complete | ORDINARY_TASK | 6072 |
| *OL_RSSOM_Active/Retired | Retired Activity | complete | level_of_effort | 1 |
| *OL_RSSOM_Active/Retired | Retired Activity | complete | wbs_summary | 6 |
| *OL_RSSOM_Activity Work Type | Key Milestones | not_started | MILESTONE | 1 |
| *OL_RSSOM_Module of Work Location | Project Wide | complete | MILESTONE | 611 |
| *OL_RSSOM_Module of Work Location | Project Wide | complete | ORDINARY_TASK | 3728 |
| *OL_RSSOM_Module of Work Location | Project Wide | complete | level_of_effort | 1 |
| *OL_RSSOM_Module of Work Location | Project Wide | in_progress | level_of_effort | 31 |
| *OL_RSSOM_Module of Work Location | Project Wide | not_started | MILESTONE | 1 |
| AC: Discipline Group | Material Contracts (Make & Buy) | complete | MILESTONE | 1 |
| AC: Discipline Group | Material Contracts (Make & Buy) | complete | ORDINARY_TASK | 1 |
| AC: Discipline Group | Sub Contracts | complete | ORDINARY_TASK | 3 |
| AC: Discipline Group | Technical Contracts (PTS) | complete | MILESTONE | 4 |
| AC: Discipline Group | Technical Contracts (PTS) | complete | ORDINARY_TASK | 26 |
| OL_RSSOM_WBS_Level 01 | Work Milestone | not_started | MILESTONE | 1 |
| P-Procurement Contractor Code | Asphalt Paving & Flatwork | complete | ORDINARY_TASK | 16 |
| P-Procurement Contractor Code | Building Foundations | complete | ORDINARY_TASK | 1 |
| P-Procurement Contractor Code | Civil Works | complete | ORDINARY_TASK | 38 |
| P-Procurement Contractor Code | Demolition | complete | ORDINARY_TASK | 1 |
| P-Procurement Contractor Code | Earthworks | complete | ORDINARY_TASK | 2 |
| P-Procurement Contractor Code | Electrical Works (Building Overall) | complete | ORDINARY_TASK | 6 |
| P-Procurement Contractor Code | Ground Improvement Works | complete | ORDINARY_TASK | 10 |
| P-Procurement Contractor Code | Saw Cutting | complete | ORDINARY_TASK | 4 |
| P-Procurement Contractor Code | Site Electrical Works | complete | ORDINARY_TASK | 51 |
| P-Procurement Contractor Code | Steel Reinforcement | complete | ORDINARY_TASK | 18 |
| P-Procurement Contractor Code | Structural Metal Works | complete | ORDINARY_TASK | 12 |
| P-Procurement Contractor Code | Trackwork - Aluminothermic Welding | complete | ORDINARY_TASK | 24 |
| P-Procurement Contractor Code | Trackwork - Rail & Substructure Installation | complete | ORDINARY_TASK | 4 |
| P-Procurement Contractor Code | Walmsley Brook Works | complete | ORDINARY_TASK | 5 |
| P-Procurement Contractor Code | Wet Utilities | complete | ORDINARY_TASK | 9 |
| P-Subcontractor Name - Contractor | ERRITT CONSTRUCTION LTD | complete | ORDINARY_TASK | 4 |
| P-Subcontractor Name - Contractor | GREEN INFRASTRUCTURE PARTNERS INC. (GIP) | complete | ORDINARY_TASK | 1 |
| P-Subcontractor Name - Contractor | YORK1 DEMOLITION� | complete | ORDINARY_TASK | 1 |
| RSSOM 08.Package_Sub-Code | Project Wide | complete | ORDINARY_TASK | 12 |
| RSSOM 11.MS | Key Milestones | not_started | MILESTONE | 1 |
| RSSOM 12.Major Location | Project Wide Packages | complete | MILESTONE | 17 |
| RSSOM 12.Major Location | Project Wide Packages | complete | ORDINARY_TASK | 218 |
| RSSOM 12.Major Location | Project Wide Packages | complete | level_of_effort | 2 |
| RSSOM 12.Major Location | Project Wide Packages | in_progress | level_of_effort | 32 |
| SUBPROG  �  SCC CA Code | CONTRACTOR PROFESSIONAL SERVICES.ENGINEERING.FINAL DESIGN | complete | MILESTONE | 738 |
| SUBPROG  �  SCC CA Code | CONTRACTOR PROFESSIONAL SERVICES.ENGINEERING.FINAL DESIGN | complete | ORDINARY_TASK | 2392 |
| SUBPROG  �  SCC CA Code | CONTRACTOR PROFESSIONAL SERVICES.START-UP.TESTING AND COMMISSIONING | complete | MILESTONE | 126 |
| SUBPROG  �  SCC CA Code | CONTRACTOR PROFESSIONAL SERVICES.START-UP.TESTING AND COMMISSIONING | complete | ORDINARY_TASK | 1977 |
| SUBPROG - Main Responsibility | Contracting Authority (CA) Metrolinx/IO | complete | MILESTONE | 6 |
| SUBPROG - Main Responsibility | Contracting Authority (CA) Metrolinx/IO | complete | ORDINARY_TASK | 1074 |
| SUBPROG - Main Responsibility | Design-Bid-Build (DBB)/Other Contractors | complete | MILESTONE | 1 |
| SUBPROG - Main Responsibility | Design-Bid-Build (DBB)/Other Contractors | complete | ORDINARY_TASK | 7 |
| SUBPROG - Project Sub-Phase | Interface Milestones (e.g., between Contracts) | complete | MILESTONE | 29 |
| SUBPROG - Project Sub-Phase | Interface Milestones (e.g., between Contracts) | complete | ORDINARY_TASK | 99 |
| SUBPROG - Project Sub-Phase | Major Milestones | not_started | MILESTONE | 1 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Engineering and Design | complete | MILESTONE | 879 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Engineering and Design | complete | ORDINARY_TASK | 3375 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Engineering and Design | complete | level_of_effort | 4 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Engineering and Design | in_progress | level_of_effort | 31 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Engineering and Design | not_started | level_of_effort | 1 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Permits and Approvals | complete | MILESTONE | 15 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Permits and Approvals | complete | ORDINARY_TASK | 85 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Procurement of Materials and Equipment | complete | MILESTONE | 5 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Procurement of Materials and Equipment | complete | ORDINARY_TASK | 255 |
| SUBPROG - Project Sub-Phase | Project Co./Contractor Procurement of Services | complete | ORDINARY_TASK | 30 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | complete | MILESTONE | 11 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | complete | ORDINARY_TASK | 438 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | complete | wbs_summary | 5 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | in_progress | level_of_effort | 2 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | in_progress | wbs_summary | 3 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | not_started | MILESTONE | 1 |
| SUBPROG - Sub-Responsibility | Project Co. � Contractor | not_started | wbs_summary | 1 |
| SUBPROG - Vertical Alignment | Project-Wide | complete | MILESTONE | 1056 |
| SUBPROG - Vertical Alignment | Project-Wide | complete | ORDINARY_TASK | 5698 |
| SUBPROG - Vertical Alignment | Project-Wide | complete | level_of_effort | 4 |
| SUBPROG - Vertical Alignment | Project-Wide | in_progress | level_of_effort | 34 |
| SUBPROG - Vertical Alignment | Project-Wide | not_started | MILESTONE | 1 |
| SUBPROG - Vertical Alignment | Project-Wide | not_started | level_of_effort | 1 |
| SUBPROG-OL-Subcontractor | ABB | complete | MILESTONE | 87 |
| SUBPROG-OL-Subcontractor | ABB | complete | ORDINARY_TASK | 287 |
| SUBPROG-OL-Subcontractor | Alten/NTT Data | complete | MILESTONE | 2 |
| SUBPROG-OL-Subcontractor | Alten/NTT Data | complete | ORDINARY_TASK | 9 |
| SUBPROG-OL-Subcontractor | Hitachi | complete | MILESTONE | 1 |
| SUBPROG-OL-Subcontractor | IT Soft | complete | ORDINARY_TASK | 3 |
| SUBPROG-OL-Subcontractor | Kineton/Intecs | complete | MILESTONE | 2 |
| SUBPROG-OL-Subcontractor | Kineton/Intecs | complete | ORDINARY_TASK | 8 |
| SUBPROG-OL-Subcontractor | QCA | complete | ORDINARY_TASK | 1 |
| SUBPROG-OL-Subcontractor | Radwin/Gematica/Axians/VDS Rail | complete | ORDINARY_TASK | 1 |
| SUBPROG-OL-Subcontractor | STE | complete | ORDINARY_TASK | 2 |
| SUBPROG-OL-Subcontractor | TBD | complete | ORDINARY_TASK | 1 |
| SUBPROG-OL-Subcontractor | TG Baker Americas | complete | ORDINARY_TASK | 2 |
| SUBPROG-OL-Subcontractor | TSO | complete | ORDINARY_TASK | 1 |
| SUBPROG-OL-Subcontractor | Willowglen | complete | ORDINARY_TASK | 2 |
| Work Package | Contracting Authority PLAA's | complete | ORDINARY_TASK | 6 |

Counts above are assignment incidences, not mutually exclusive populations. All assigned classifications were inspected (1,270 type/value/status/type groups); the table shows completion, scope and active/retired groups. General system/discipline labels do not confer contractual authority. The terminal population is dominated by unrelated completed content, so treating all terminals as one completion boundary would be misleading.

## Finish-constraint evidence

| Raw code | Canonical constraint | Slot | Status | Count |
| --- | --- | --- | --- | --- |
| CS_MEOA | FINISH_ON_OR_AFTER | PRIMARY | complete | 55 |
| CS_MEOA | FINISH_ON_OR_AFTER | PRIMARY | not_started | 16 |
| CS_MEOB | FINISH_ON_OR_BEFORE | PRIMARY | complete | 169 |
| CS_MEOB | FINISH_ON_OR_BEFORE | PRIMARY | in_progress | 20 |
| CS_MEOB | FINISH_ON_OR_BEFORE | PRIMARY | not_started | 49 |
| CS_MEOB | FINISH_ON_OR_BEFORE | SECONDARY | complete | 3 |

312 finish-constraint slots occur on 311 activities: 241 Finish On or Before
(CS_MEOB: 238 primary, 3 secondary) and 71 Finish On or After (CS_MEOA, primary).
Upper finish limits range from 2023-08-24 17:00 to 2031-03-28 17:00. No finish
constraint equals the project Scheduled Finish on 2031-05-27. No Mandatory Finish,
Finish On or populated project Must Finish By appears. Finish On or After is a
lower bound, not a project completion deadline. None of the three strong candidates
has either a primary or secondary constraint. Local activity constraints remain
separate from contractual identity and a global required finish.

## Activity Code and UDF evidence

The existing Phase 5A assignment model was used, not a name-only heuristic.
The milestone family contains 68 unfinished milestones with Key/Work Milestone
classifications; narrower RSSOM 11.MS / Key Milestones has 16 assignments.
Two especially specific classifications are SUBPROG - Milestones / Final Completion
(type 6645, value 177932) on WM_100150, and Substantial Completion (value 177930)
on WM_100130, one assignment each. These specify stages but do not explicitly
nominate which is the authorized project backward anchor.

Other contextual evidence includes Work Milestone (87 assignments), Major Milestones
(117 under Project Sub-Phase and 183 under ABS), regional Access Handover Dates /
Substantial Completion (18), and Discipline Group Completion Milestones (32).
Contractual vehicle-delivery/acceptance labels identify delivery boundaries rather
than a unique project-final authority. Revenue-service and regional substantial-
completion template values are also contextual candidates. They are not silently
promoted to global completion roles.

The Department UDF includes Contractual (13 assignments) and Key Milestones (16).
Neither uniquely declares final project completion. Each of the three strong candidates
has Source Contract = TBC. Their Primary Critical Path UDF is imported descriptive
evidence, not an authoritative P6 driving-path representation.

| Project UDF type ID | Label | Value |
| --- | --- | --- |
| 2129 | Description | RSSOM |
| 2201 | Project Name- NH | OL |

These are all project UDF values. Neither declares completion authority or a required finish. No metadata authority rule or explicit configured completion selector was supplied for this file; this investigation does not invent one from keywords.

## Ranked review candidates

3,310 discovery records: 0 AUTHORITATIVE, 3 STRONG_CANDIDATE, 341 CANDIDATE and 2,966 WEAK_CANDIDATE. Discovery is deliberately broad and includes historical milestones; count is not a claim of 3,310 plausible project completions. The top 20 follow.

| Rank | Activity code | Name | Class | EF | LF | TF h | Pred / succ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | OL_RSSOM_WM_100150 | (xiv) Scheduled Final Completion Date (Final Completion) | STRONG_CANDIDATE | 2031-05-27 17:00:00 | 2031-05-27 17:00:00 | 0.0 | 12 / 1 |
| 2 | OL_RSSOM_WM_100160 | (vii) Completion of the Ontario Line Subway | STRONG_CANDIDATE | 2031-05-27 17:00:00 | 2031-05-27 17:00:00 | 0.0 | 4 / 0 |
| 3 | OL_RSSOM_WM_100130 | (xiii) Scheduled Substantial Completion Date | STRONG_CANDIDATE | 2031-03-28 17:00:00 | 2031-03-28 17:00:00 | 0.0 | 52 / 5 |
| 4 | OL_RSSOM_CN_103460 | 01 - East Harbour Station � Substantial Completion - NEHCS | CANDIDATE | 2028-07-24 08:00:00 | 2030-05-27 08:00:00 | 5376.0 | 1 / 1 |
| 5 | OL_RSSOM_CN_104830 | 20b. Gerrard Portal - Substantial Completion | CANDIDATE | 2028-09-18 08:00:00 | 2029-10-18 08:00:00 | 3160.0 | 1 / 12 |
| 6 | OL_RSSOM_CN_104840 | 20c. Bain Street EEB - Substantial Completion | CANDIDATE | 2028-09-18 08:00:00 | 2030-10-25 08:00:00 | 6136.0 | 1 / 2 |
| 7 | OL_RSSOM_CN_104910 | 35b. Minton Place Portal - Substantial Completion | CANDIDATE | 2028-09-18 08:00:00 | 2030-10-03 08:00:00 | 5960.0 | 1 / 5 |
| 8 | OL_RSSOM_CN_106020 | 1. Exhibition - Substantial Completion | CANDIDATE | 2028-11-01 08:00:00 | 2030-01-17 08:00:00 | 3536.0 | 1 / 7 |
| 9 | OL_RSSOM_CN_108290 | 45. Flemingdon Park Station - Substantial Completion | CANDIDATE | 2029-02-01 08:00:00 | 2030-02-28 08:00:00 | 3136.0 | 1 / 4 |
| 10 | OL_RSSOM_CN_108300 | 52. Science Centre Station - Substantial Completion | CANDIDATE | 2029-02-01 08:00:00 | 2030-06-18 08:00:00 | 4016.0 | 1 / 4 |
| 11 | OL_RSSOM_CN_108430 | 28b. Pape Crossover - Substantial Completion | CANDIDATE | 2029-02-07 08:00:00 | 2030-05-27 08:00:00 | 3792.0 | 1 / 2 |
| 12 | OL_RSSOM_CN_113480 | 08. Leslieville Station - Substantial Completion | CANDIDATE | 2030-01-01 08:00:00 | 2030-02-15 08:00:00 | 360.0 | 1 / 5 |
| 13 | OL_RSSOM_CN_113490 | 15. Gerrard Station - Substantial Completion | CANDIDATE | 2030-01-01 08:00:00 | 2030-02-15 08:00:00 | 360.0 | 1 / 6 |
| 14 | OL_RSSOM_CN_113670 | 09. King/Bathurst Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 6 |
| 15 | OL_RSSOM_CN_113680 | 16. Queen/Spadina Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 6 |
| 16 | OL_RSSOM_CN_113690 | 23. Osgoode Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 5 |
| 17 | OL_RSSOM_CN_113700 | 30. Queen Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 4 |
| 18 | OL_RSSOM_CN_113710 | 44. Corktown Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 7 |
| 19 | OL_RSSOM_CN_113720 | 37. Moss Park Station - Substantial Completion | CANDIDATE | 2030-03-22 08:00:00 | 2030-05-27 08:00:00 | 528.0 | 1 / 4 |
| 20 | OL_RSSOM_CN_113740 | 23. Pape Station - Substantial Completion | CANDIDATE | 2030-06-01 17:00:00 | 2030-06-17 17:00:00 | 128.0 | 1 / 7 |

The three strong candidates form a coherent staged chain:

- OL_RSSOM_WM_100130 (Substantial Completion, 2031-03-28 17:00) to
  OL_RSSOM_WM_100150 (Final Completion, 2031-05-27 17:00): FS +480 hours,
  relationship 3507050.
- OL_RSSOM_WM_100150 to OL_RSSOM_WM_100160 (Ontario Line completion,
  2031-05-27 17:00): FS zero lag, relationship 3516547.

All three are not-started finish milestones with imported TF zero. Final Completion
has 12 predecessors/1 successor; Substantial Completion has 52/5; the aggregate
Ontario Line completion has 4/0. This is evidence of related completion stages,
not permission to decide which stage is the contractual completion anchor.

Ranking is explicit ordinal review policy: evidence class; final completion before
terminal Scheduled-Finish-aligned completion before project-wide substantial
completion, other substantial completion, revenue service and other contexts;
project-wide classification; Scheduled Finish agreement; unfinished; terminal;
stable Activity code/internal ID. There are no hidden weights or confidence score,
and no special handling of WM_100160. Names aid discovery only.

## OL_RSSOM_WM_100160 forensic record

| Field | Evidence |
| --- | --- |
| Internal ID / Activity code | 1600284 / OL_RSSOM_WM_100160 |
| Name | (vii) Completion of the Ontario Line Subway |
| Type / raw type | finish_milestone / TT_FinMile |
| Status / raw status | not_started / TK_NotStart |
| WBS ID | 440856 |
| WBS path | OL-RSSOM-PWS-Live: Ontario Line Subway RSSOM Project - Progress Works Schedule - Live > 1: Work Milestone > 1: Key Milestones |
| Calendar ID | 11683 |
| Original / remaining duration hours | 0 / 0 |
| Predecessors / successors / terminal | 4 / 0 / True |
| Primary constraint | None |
| Secondary constraint | None |
| Conclusion | STRONG_CANDIDATE |

| Imported field | Value |
| --- | --- |
| planned_start | 2031-05-27 17:00:00 |
| planned_finish | 2031-05-27 17:00:00 |
| early_start | 2031-05-27 17:00:00 |
| early_finish | 2031-05-27 17:00:00 |
| late_start | 2031-05-27 17:00:00 |
| late_finish | 2031-05-27 17:00:00 |
| actual_start | None |
| actual_finish | None |
| total_float_hours | 0.0 |
| free_float_hours | 0.0 |

### Exact source TASK date fields

| Raw P6 TASK field | Raw value (JSON) |
| --- | --- |
| act_end_date | "" |
| act_start_date | "" |
| create_date | "2025-07-03 15:16" |
| cstr_date | "" |
| early_end_date | "2031-05-27 17:00" |
| early_start_date | "2031-05-27 17:00" |
| expect_end_date | "" |
| external_early_start_date | "" |
| external_late_end_date | "" |
| late_end_date | "2031-05-27 17:00" |
| late_start_date | "2031-05-27 17:00" |
| post_pess_finish_date | "" |
| post_pess_start_date | "" |
| pre_pess_finish_date | "" |
| pre_pess_start_date | "" |
| reend_date | "2031-05-27 17:00" |
| rem_late_end_date | "2031-05-27 17:00" |
| rem_late_start_date | "2031-05-27 17:00" |
| restart_date | "2031-05-27 17:00" |
| resume_date | "" |
| suspend_date | "" |
| target_end_date | "2031-05-27 17:00" |
| target_start_date | "2031-05-27 17:00" |
| update_date | "2026-06-29 17:38" |

### All assigned Activity Codes

| Type ID | Type name | Value ID | Value |
| --- | --- | --- | --- |
| 4392 | Ontario Line_TES | 127485 | Traction and Power System |
| 4393 | Ontario Line_Communications | 127488 | Communication Systems |
| 4394 | Ontario Line_Signalling | 127487 | Signalling System |
| 4395 | Ontario Line_PSD | 127486 | Platform Screen Door System |
| 4396 | Ontario Line_OCS | 127489 | Overhead Catenary |
| 4397 | Ontario Line_Vehicle | 127490 | Vehicle |
| 4398 | Ontario Line_Depot | 127491 | Depot Equipments |
| 4401 | Ontario Line_SCADA WP | 127496 | SCADA WP |
| 4402 | Ontario Line_Physical Sec. WP | 127495 | Physical Securtity WP |
| 4403 | Ontario Line_Cyber Sec. WP | 127497 | Cyber Security WP |
| 4438 | RSSOM 11.MS | 128119 | Key Milestones |
| 6642 | *OL_RSSOM_ABS | 177854 | Major Milestones |
| 6643 | SUBPROG - Subway Projects | 177867 | Ontario Line |
| 6644 | SUBPROG - Project Sub-Phase | 177868 | Major Milestones |
| 6646 | SUBPROG - Main Responsibility | 177939 | Project Co. (P3) |
| 6647 | SUBPROG - Sub-Responsibility | 177952 | Project Co. � Contractor |
| 6648 | SUBPROG - Vertical Alignment | 177975 | Project-Wide |
| 6649 | *OL_RSSOM_SUBPROG _ Entity/ Subsystem | 177995 | General |
| 6658 | *OL_RSSOM_Module of Work Location | 178160 | Project Wide |
| 6667 | SUBPROG  �  SCC JV Partners | 178264 | GEN |
| 6671 | *OL_RSSOM_ Lead Organization | 178288 | Design Build Joint Venture |
| 6672 | *OL_RSSOM_ Mob payment | 178330 | Not Mob Payment |
| 6673 | *OL_RSSOM_Activity Work Type | 178368 | Key Milestones |
| 6674 | *OL_RSSOM_Active/Retired | 178379 | Active Activity |
| 6684 | OL_RSSOM_WBS_Level 01 | 178588 | Work Milestone |

### All assigned UDFs

| Type ID | Label | Value |
| --- | --- | --- |
| 2160 | OL_RSSOM_Longest Path (Critical path) | Primary Critical Path |
| 2171 | OL_RSSOM_03_Organization | Project Co |
| 2176 | OL_RSSOM_04_Department | Key Milestones |
| 2179 | OL_RSSOM_01_Source Contract | TBC |
| 2182 | OL_RSSOM_Risk_Shortest Expected | 0 |
| 2202 | Subprog Ol Main area legacy Code | OLMA02 |
| 2205 | Longest Duration | 0 |
| 2206 | OL_RSSOM_Sub contractors | GNR |
| 8959 | MSP Activity ID | 114 |

### Incoming relationships

| Relationship ID | Predecessor internal ID | Successor internal ID | Type | Lag hours |
| --- | --- | --- | --- | --- |
| 3516547 | 1600276 | 1600284 | FS | 0.0 |
| 3534458 | 1611794 | 1600284 | FS | 0.0 |
| 3534459 | 1600245 | 1600284 | FS | 0.0 |
| 3534862 | 1600220 | 1600284 | FS | 0.0 |

There are no outgoing relationships. Planned, early and late finish all agree with
PROJECT.scd_end_date; no required-finish or anticipated-finish value is available.
This is **STRONG_CANDIDATE**, because it is an unfinished terminal finish milestone
with structured Key/Major Milestone and project-wide classifications and exact
Scheduled Finish agreement. It is not AUTHORITATIVE: no explicit selector, documented
contractual completion role, project required finish, or unambiguous completion UDF
is present. Source Contract is TBC. Zero TF/FF and Primary Critical Path labels do
not remedy the authority gap. No actual date is overwritten.

## Real backward/float stop gate and availability

Selection status: ANCHOR_NOT_SELECTED. Selected activity, selected date, date source
and required project finish are None. Diagnostic: completion_authority_not_established.
The authority-gated ancestor scope is empty; this is a stop decision, not evidence
that the underlying network contains no predecessors.

LS/LF calculability, backward-usable/blocked relationships, LS/LF agreement, TF/FF
agreement, critical-state agreement and APPLICATION_CALCULATED_CONTROLLING_PATH
validation are **NOT_EVALUATED for real-project calibration**. No excluded or blocked
activity enters a comparison denominator. No zero-match statistic is fabricated.
Synthetic backward/float/path tests remain valid. Reliable early results retain
their separate availability even though no real late/float population is authorized.

A documented authoritative selector/role and defensible completion-date semantics
are needed next. After that, anchor-connected scope must still be filtered by
unresolved backward dependencies and availability. The new ancestor helper establishes
graph scope only, not calculability. Expected Finish remains unsupported for 720
ordinary unfinished activities; LOE remains excluded. Those dependencies may still
block late/float work even after completion authority is provided. No new Expected
Finish evidence established scheduling semantics in this increment.

DCMA Critical Path Test = NOT_EVALUATED (immutable delay simulation is absent).
CPLI = NOT_EVALUATED (separately validated required-finish/path-length methodology
is still required). No further phase was started.

## Implementation and synthetic verification

Only four new files are introduced by this increment; existing dirty repository
changes from earlier phases are preserved:

- app/cpm/completion_evidence.py: immutable evidence models, exact raw project fields,
  deterministic ranking, explicit authority gate and iterative ancestor-only scope.
- tests/test_completion_evidence.py: 24 proprietary-free cases.
- docs/phase6e_anchor_contract.md: read-only authority/ranking/stop methodology.
- docs/phase6e_anchor_evidence.md: this evidence record.

No existing file is modified in this increment. The helper is not wired into or
used to change the validated CPM service/anchor/calculation behavior.

Nineteen initial tests failed before the module existed. Additional failing
regressions proved that contradictory values on a declared UDF must not certify
authority and that ranking explanations must preserve all ordinal priorities.
The final 24 tests cover authoritative metadata rules, unique/conflicting UDFs,
Activity Code candidate evidence, explicit selectors, invalid/conflicting selectors,
multiple strong candidates with no selection, required project finish distinct
from scheduled output, date-only no identity, unsupported anchor types, source
immutability, determinism, anchor-only predecessor scope and a 1,102-node iterative
chain without recursion. Authority selects identity only; it does not certify
scheduling readiness or manufacture a missing required date.

| Validation | Exact result |
| --- | --- |
| Initial `pytest -q -m "not external_xer"` | 439 passed, 2 deselected, 1 warning |
| New `pytest -q tests/test_completion_evidence.py` | 24 passed |
| Focused CPM (all `tests/test_cpm*.py`, plus completion evidence) | 320 passed |
| Focused calendars, `-m "not external_xer"` | 79 passed, 1 deselected |
| Final `pytest -q -m "not external_xer"` | 463 passed, 2 deselected, 1 warning |

The warning is the existing FastAPI/TestClient deprecation. Focused CPM includes
anchors, paths, comparison, progress, relationships, constraints and component tests.
No expectations were weakened, external fixtures fabricated, or unrelated tests skipped.
