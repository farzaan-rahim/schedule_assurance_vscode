# Phase 6E reporting: reference workbook structural inspection

Inspected the actual user-provided workbook read-only. It is a functional category reference, not a design or calculation template. No source workbook content was changed, and no branding, logos, proprietary wording, hidden formulas, styling or calculation logic was copied.

Filename: `1414_RSM-RSM-CW-PWD-RPT-PRM0-00066_C01 Appendix.08 - Works Schedule_Change Log Report_Sept 2026.xlsx`

SHA-256: `a6780eecd0e2180b22d92e8cc599203496e4e006ffcedec153f1ede30aa2be45`

## Sheet order and structure

All 27 worksheets are visible. The dimensions below include metadata and header rows; they are not change-record counts. No worksheet has frozen panes. Exactly three worksheets have auto-filters.

| Order | Sheet | Used rows | Used columns | Filter |
| --- | --- | --- | --- | --- |
| 1 | Projects | 11 | 15 | None |
| 2 | Activities | 81 | 10 | A9:J81 |
| 3 | Relationships | 1,408 | 6 | None |
| 4 | Resources | 53,261 | 11 | None |
| 5 | Calendars | 755 | 18 | None |
| 6 | Calendar Exceptions | 11,849 | 2 | None |
| 7 | Description | 121 | 13 | None |
| 8 | Activity-Type | 9 | 13 | None |
| 9 | Original-Duration | 206 | 13 | A9:M206 |
| 10 | Remaining-Duration | 823 | 13 | None |
| 11 | Total-Float | 5,554 | 13 | None |
| 12 | Calendar | 9 | 13 | None |
| 13 | Start | 5,246 | 13 | None |
| 14 | Finish | 5,598 | 13 | None |
| 15 | Early-Start | 20,755 | 13 | None |
| 16 | Early-Finish | 20,477 | 13 | None |
| 17 | Late-Start | 5,266 | 13 | None |
| 18 | Late-Finish | 4,854 | 13 | None |
| 19 | Activity-Status | 320 | 13 | None |
| 20 | Critical | 9 | 13 | None |
| 21 | Longest-Path | 9 | 13 | None |
| 22 | Primary-Constraint | 9 | 13 | None |
| 23 | Secondary-Constraint | 9 | 13 | None |
| 24 | Budget-Cost | 248 | 13 | A9:M248 |
| 25 | Actual-Cost | 188 | 13 | None |
| 26 | Remaining-Cost | 398 | 13 | None |
| 27 | Total-Cost | 247 | 13 | None |

## Shared metadata and headers

The first six rows identify the report, workbook, source schedule/activity population, comparison context, creation date and author. A category band is on row 8 and column headings generally on row 9. The source comparison is an August-labelled schedule versus a live update. The project sheet contains two version rows with Data Dates 2026-09-01 00:01 and 2026-10-01 00:01. These are reference-report versions, not the controlled sample XERs or the June calibration export.

Common activity context includes sequence, visible Activity ID, description, activity type, remaining duration, WBS code/name and source WBS context. The activity sheet distinguishes presence in the two versions. Relationship context includes predecessor and successor IDs/names followed by version comparison values. Resources, calendar definitions and exceptions have their own category-specific layouts.

On most 13-column change sheets, columns A:H are activity context. Column I carries the source value, K the difference, L a percentage where applicable, and M the target value; J is commonly a spacer. Repeated schedule labels in headings make roles less explicit than dedicated baseline/current/variance labels. The new implementation defines its own signed variance and percentage policies; no reference percentage sign convention or hidden formula is adopted.

## Formats and organization

Observed date formats include `mm-dd-yy` and `m/d/yy h:mm`; calendar time values use `h:mm AM/PM`. Percentage cells include `0%` alongside some text percentage displays. Many duration/float values use General formatting; project costs use a dollar-format code. Display formats and extreme source dates do not establish scheduling units, currency identity or contractual finish semantics.

The categories separate object membership/logic changes from individual field changes. Several sheets have only metadata and a header, which does not establish whether they were evaluated. The new system explicitly distinguishes supported empty sections from unavailable sections.

## Original Schedule Assurance design

The export uses a new summary and diagnostics sheet, original navy/teal header bands, descriptive baseline/current/unit headings, a five-row metadata area and row-6 column headers. Every sheet has a filter and frozen header rows. Activity context columns are frozen where present. Availability and classification are textual, with restrained status fills. It does not reproduce the reference layout, style, wording, logos, formulas or scoring. No working-day conversion or cost aggregation is inferred from the reference.
