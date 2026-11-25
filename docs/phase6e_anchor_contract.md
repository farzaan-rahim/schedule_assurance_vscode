# Phase 6E: read-only completion authority investigation

Initial regression: 439 passed, 2 deselected, 1 existing warning. All six prior
Phase 6 calculation/progress/calibration documents were read and remain protected.
No calculation module, importer or existing anchor selector is modified.

## Policy before implementation

Nineteen proprietary-free authority/candidate/scope tests fail before the new
module exists. The new module is a read-only forensic domain helper, not a hook
into the scheduling engine. Existing synthetic terminal-selection behavior stays
unchanged. This stricter gate applies to real-P6 backward calibration authority.

Scheduled Finish is computed output. Must Finish By is a distinct optional
required finish. In XER, PROJECT.scd_end_date is Scheduled Finish and
PROJECT.plan_end_date is Must Finish By. Anticipated Finish is planning evidence;
baseline identifiers are not finish dates. Preserve exact raw field/value pairs,
blank versus absent fields, and independent activity constraints.

Authority comes only from explicit unique configured activity selectors, or
unique exact metadata type/value matches under an explicitly documented completion
role rule. Metadata labels/values found by keyword discovery alone are candidates,
not automatic authority. No default rule is invented for this export. Missing,
conflicting or duplicate explicit selectors cannot fall through to another choice.
Multiple authoritative matches remain unselected. An explicit required date alone
cannot identify a completion activity. Date/float agreement never confers authority.

Evidence classes: AUTHORITATIVE, STRONG_CANDIDATE, CANDIDATE, WEAK_CANDIDATE,
NOT_A_COMPLETION_CANDIDATE. No numerical confidence score or probability.
Strong means either an unfinished finish milestone with an explicit final/
substantial milestone taxonomy value, or an unfinished terminal finish milestone
with structured completion classification and Scheduled Finish agreement. Regional
handover classifications and general contractual labels remain contextual candidates.

Ranking is lexicographic: evidence class; role priority (final completion, terminal
aligned with Scheduled Finish, project-wide substantial completion, other
substantial completion, revenue service, other); project-wide classification;
Scheduled Finish agreement; unfinished before complete; terminal before nonterminal;
stable case-folded Activity code then internal ID. These are explicit ordinal
review priorities, not weighted confidence. Ranking never selects an anchor.
The existing noticed candidate receives no special ID/code handling.

A selected identity retains an independently supplied required date if one exists,
with its exact source. No imported late date, Total Float, or scheduled output is
reverse-engineered into a required date. A selected identity without a date does
not establish backward-calculation readiness. Graph ancestor scope is iterative
and excludes unrelated/post-anchor work; it is NOT a late-calculability result.
No dates, float or paths are calculated by this helper.

## Real-file stop gate

Inspect the genuine export, all Activity Code/UDF definitions and assigned values,
constraints, WBS context and terminal topology. A sole normal unfinished terminal,
coincident EF/LF, zero float, names or generic Key Milestone labels may establish
a strong candidate, but not contractual authority. If no declared authoritative
selector exists, preserve ANCHOR_NOT_SELECTED and stop real backward/float/path
validation. Valid Phase 6D early availability is not downgraded. Expected Finish
and LOE policies are unchanged. DCMA Critical Path Test and CPLI remain NOT_EVALUATED.

Oracle references:
- XER field identities: https://docs.oracle.com/cd/G48897_01/English/Mapping_and_Schema/xer_import_export_data_map_project/xer_import_export_data_map_project.pdf
- Finish/date meanings: https://docs.oracle.com/cd/G48897_01/p6help/en/47238.htm


## Authority data consistency regression

A further test demonstrated that a rule matching one of two contradictory values
on the same UDF must not certify authority. The field's values must be uniquely
consistent with the declared rule; otherwise a diagnostic is retained and the
metadata cannot authorize selection. Explicit selectors remain separate evidence.
Another regression requires ranking explanations to retain date agreement,
terminal/status and ordinal role priorities as well as class and lexical order.
No scheduling behavior is changed by either read-only safeguard.
