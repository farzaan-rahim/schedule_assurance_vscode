# Phase 6F explicit analysis-anchor contract

Initial regression: 506 passed, 2 deselected, 1 existing warning.
All prior Phase 6 contracts/calibration/progress notes and Phase 6E reporting documents
were read and are protected. Existing pass/calendar/relationship/constraint/float/path
formulas remain unchanged. New synthetic tests were added first and initially failed
collection because the new analysis modules did not exist.

An ANALYSIS_ANCHOR is an explicit question endpoint, never automatic contractual
completion. A separate immutable CompletionAuthorityRecord retains its prior status
and evidence. Caller selection or a supplied deadline does not establish authority.
No candidate is selected by rank, name, date, float or sole-terminal heuristics.
Code ambiguity requires an internal ID. Missing/conflicting selectors do not fall back.
A configured milestone must be a milestone; normal tasks need explicit code/ID and
an informational suitability finding. LOE/WBS, missing identity/project/calendar or
unusable timestamps are controlled selection errors. Completed history is not a
remaining-work backward anchor.

CALIBRATION explicitly uses the selected source activity's imported LF, labelled
CALIBRATION_IMPORTED_LATE_FINISH, solely to examine propagation. It is not a required
finish. INDEPENDENT requires a caller finish or a separately established authoritative
finish; imported LF is never an implicit fallback. Datetimes remain naive project-local.

The complete upstream graph is traversed iteratively, preserving source relationships.
Only this selected dependency scope is backward-scheduled. Off-scope successor edges
are reported as outside the selected scope, not bypassed as global project logic:
late dates/TF are ANCHOR_RELATIVE, not assertions of complete-project P6 float.
The selected node acts as this analysis boundary even if it has downstream work.

Forward calculation reuses the unchanged Phase 6D directional service for P6 retained
options. Unsupported Expected Finish, LOE/WBS, invalid states/calendars/constraints,
external endpoints and cycles retain explicit reasons. Root backward uncertainty
propagates to predecessors, not downstream toward the selected boundary. A blocked
early predecessor alone does not invalidate an otherwise computable downstream late
bound. Valid early dates survive a blocked late bound. Completed actual segments are
historical only; an unfinished-to-completed bridge cannot supply a remaining-work
backward release. Progressed nonzero SS expired-lag inversion and progressed SF are
not implemented here and explicitly block the backward relationship. Supported FS/FF
remaining segments and not-started relationship types reuse existing reverse formulas.

Backward scheduling calls the existing backward_pass with the explicit selected finish
and eligible dependency view. Runtime late-duration/calendar/constraint/relationship
invariants run before publication. No imported dates supply blocked intermediate nodes.
TF uses the unchanged activity-calendar start-based formula, retains finish-based audit
and disagreement diagnostics, and requires reliable early and late values. FF requires
reliable original successor endpoint information, including off-scope successors; no
terminal/project-end convention is invented. Progressed SS/SF requiring unsupported
FF methodology are blocked. No imported FF substitution or negative-float clamp.

Date comparison categories are exact timestamp, exactly zero working-time separation,
configured elapsed tolerance, or difference; raw elapsed variance is always retained.
Float comparison preserves exact signed values and configured classification tolerance.
Excluded/history/blocked metric values do not enter comparable denominators.
Canonical imports have no authoritative P6 critical flag: any TF-threshold comparison
is explicitly a proxy, with raw scheduling-option differences disclosed. It is not a
claim about P6 Longest Path or critical-definition equivalence.

Connected APPLICATION_CALCULATED_CONTROLLING_PATH traces require reliable early/late/TF
records at the selected node and use calculated forward control edges. Existing bounded
iterative enumeration/ranking is reused with an eligibility ceiling covering all known
TF values, solely for controlling-path traversal; activity critical classification and
published config/TF remain unchanged. Paths retain ties, duration/lag sums, rank and
truncation. Missing control endpoints are explicit partial boundaries, not invented
network starts. A blocked selected early/TF endpoint produces no fabricated path.

Reporting consumes the completed analysis as an optional adapter: selected-anchor metadata,
summary rows and path section only. It does not alter other forensic comparison values.
No scheduling runs inside rendering or routes. Selections are not persisted. DCMA Critical
Path Test and CPLI remain NOT_EVALUATED; no simulation or other phase is introduced.

## Implemented verification and source-definition evidence

The completed evidence and file manifest are in phase6f_calibration_notes.md.
Final non-external regression: 556 passed, 2 deselected, 1 existing warning.
All 55 protected prior files are unchanged. Independent per-direction relationship
reasons and forward requirement/expired/residual-lag audit fields are retained.

A narrow read-only PROJECT helper identifies CT_TotFloat and critical_drtn_hr_cnt
without altering Schedule/importer or scheduling policy. P6 configured-state
reconstruction uses the source threshold and remains distinct from an exported
critical flag, application state, and controlling path. All three actual thresholds
are 0h; P6 FT_FF versus start-based application float remains visible. The current
source WM_100130 finish constraint is recorded explicitly in the new notes, correcting
an earlier evidence narrative without changing any protected methodology.
