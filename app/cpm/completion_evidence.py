"""Read-only completion evidence and authority gate; never schedules activities.

Ranking is ordinal and transparent, not a confidence score. Existing application
anchor selection and CPM mathematics are intentionally untouched.
"""
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from app.cpm.config import CPMConfig
from app.cpm.models import CPMDiagnostic, CPMFindingSeverity
from app.importers.p6_normalization import normalize_activity_type, normalize_status


class CompletionEvidenceClass(str, Enum):
    AUTHORITATIVE = 'AUTHORITATIVE'
    STRONG_CANDIDATE = 'STRONG_CANDIDATE'
    CANDIDATE = 'CANDIDATE'
    WEAK_CANDIDATE = 'WEAK_CANDIDATE'
    NOT_A_COMPLETION_CANDIDATE = 'NOT_A_COMPLETION_CANDIDATE'


@dataclass(frozen=True)
class ProjectFinishEvidence:
    table_name: str
    object_id: str
    field_name: str
    raw_value: str
    semantic_role: str
    parsed_date: datetime | None = None


@dataclass(frozen=True)
class CompletionMetadataRule:
    source: str
    type_id: str
    expected_value: str
    authority_source: str

    def __post_init__(self):
        if self.source not in {'UDF', 'ACTIVITY_CODE'} or not all(isinstance(v, str) and v.strip() for v in (self.type_id, self.expected_value, self.authority_source)):
            raise ValueError('Authority requires an explicit type/value rule and documented authority source.')


@dataclass(frozen=True)
class CompletionMetadataEvidence:
    source: str
    type_id: str
    type_name: str
    value: str | None
    value_id: str | None = None
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompletionConstraintEvidence:
    slot: str
    constraint_type: str | None
    constraint_date: datetime | None
    raw_type: str | None


@dataclass(frozen=True)
class ImportedCompletionEvidence:
    planned_start: datetime | None
    planned_finish: datetime | None
    early_start: datetime | None
    early_finish: datetime | None
    late_start: datetime | None
    late_finish: datetime | None
    actual_start: datetime | None
    actual_finish: datetime | None
    total_float_hours: float | None
    free_float_hours: float | None


@dataclass(frozen=True)
class ProjectDateAgreement:
    project_field: ProjectFinishEvidence
    activity_endpoint: str
    activity_date: datetime


@dataclass(frozen=True)
class CompletionAnchorCandidate:
    activity_id: str
    activity_code: str
    activity_name: str
    activity_type: str | None
    status: str | None
    wbs_id: str | None
    wbs_path: tuple[str, ...]
    predecessor_count: int
    successor_count: int
    terminal: bool
    milestone: bool
    finish_milestone: bool
    completion_role: str
    project_wide_classification: bool
    imported: ImportedCompletionEvidence
    constraints: tuple[CompletionConstraintEvidence, ...]
    activity_codes: tuple[CompletionMetadataEvidence, ...]
    udfs: tuple[CompletionMetadataEvidence, ...]
    project_date_agreements: tuple[ProjectDateAgreement, ...]
    evidence_sources: tuple[str, ...]
    evidence_class: CompletionEvidenceClass
    authority_sources: tuple[str, ...] = ()
    rank: int = 0
    ranking_reason: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompletionAnchorInvestigation:
    selection_status: str
    candidates: tuple[CompletionAnchorCandidate, ...]
    selected_activity_id: str | None
    selected_activity_code: str | None
    selected_date: datetime | None
    selected_date_source: str | None
    required_finish: datetime | None
    project_fields: tuple[ProjectFinishEvidence, ...]
    diagnostics: tuple[CPMDiagnostic, ...]


_TERMS = ('contractual', 'key milestone', 'completion', 'substantial', 'revenue service',
          'final acceptance', 'project finish', 'major milestone', 'work milestone')


def _text(value):
    return ' '.join((value or '').casefold().replace('_', ' ').split())


def _matched(label, value):
    if _text(value) in {'', 'no', 'n', 'false', '0', 'tbc', 'n/a', 'none', 'not applicable'} or _text(value).startswith('not '):
        return ()
    text = _text(label) + ' ' + _text(value)
    return tuple(term for term in _TERMS if term in text)


def project_finish_evidence(project_row, root_wbs_rows=()):
    """Preserve actual exported fields; absent columns are never fabricated.

    plan_end_date is Must Finish By, not the computed scd_end_date. References
    to baseline projects are identifiers, not missing dates coerced to numbers.
    """
    roles = {'plan_end_date': 'REQUIRED_PROJECT_FINISH', 'scd_end_date': 'SCHEDULED_FINISH_OUTPUT',
             'plan_start_date': 'PLANNED_START', 'fcst_start_date': 'FORECAST_START',
             'base_proj_id': 'BASELINE_REFERENCE', 'base_proj_id1': 'BASELINE_REFERENCE',
             'base_proj_id2': 'BASELINE_REFERENCE', 'sum_base_proj_id': 'BASELINE_REFERENCE',
             'source_proj_id': 'SOURCE_PROJECT_REFERENCE', 'orig_proj_id': 'ORIGINAL_PROJECT_REFERENCE',
             'baselines_to_export': 'BASELINE_EXPORT_SETTING', 'baseline_names_to_export': 'BASELINE_EXPORT_SETTING',
             'use_project_baseline_flag': 'BASELINE_SETTING', 'last_baseline_update_date': 'BASELINE_UPDATE_TIMESTAMP'}
    fields = []
    def add(table, key, name, value, role):
        parsed = None
        if value and role not in {'BASELINE_REFERENCE', 'BASELINE_EXPORT_SETTING', 'BASELINE_SETTING', 'SOURCE_PROJECT_REFERENCE', 'ORIGINAL_PROJECT_REFERENCE'}:
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                pass  # Preserve malformed evidence, never turn it into a scheduling date.
        fields.append(ProjectFinishEvidence(table, key, name, value, role, parsed))
    for name, role in roles.items():
        if name in project_row:
            add('PROJECT', project_row.get('proj_id', ''), name, project_row[name], role)
    for row in root_wbs_rows:
        if row.get('proj_node_flag') == 'Y' and row.get('proj_id') == project_row.get('proj_id'):
            for name, role in [('anticip_start_date', 'ANTICIPATED_START'), ('anticip_end_date', 'ANTICIPATED_FINISH')]:
                if name in row:
                    add('PROJWBS', row.get('wbs_id', ''), name, row[name], role)
    return tuple(fields)


def _metadata(schedule, a):
    codes, udfs = [], []
    for assignment in schedule.get_activity_code_assignments(a.activity_id):
        d = schedule.activity_code_types.get(assignment.activity_code_type_id)
        v = schedule.activity_code_values.get(assignment.activity_code_id)
        if d and v:
            codes.append(CompletionMetadataEvidence('ACTIVITY_CODE', d.activity_code_type_id, d.name,
                v.name, v.activity_code_id, _matched(d.name, v.name)))
    for v in schedule.get_activity_udf_values(a.activity_id):
        d = schedule.udf_definitions.get(v.udf_type_id)
        if d:
            value = v.raw_string_value
            if value is None:
                value = v.text_value if v.text_value is not None else v.code_value
                if value is None and v.numeric_value is not None:
                    value = str(v.numeric_value)
                if value is None and v.date_value is not None:
                    value = v.date_value.isoformat(sep=' ')
            label = d.label or d.name
            udfs.append(CompletionMetadataEvidence('UDF', d.udf_type_id, label, value,
                matched_terms=_matched(label, value)))
    return tuple(sorted(codes, key=lambda e:(e.type_id, e.value_id or ''))), tuple(sorted(udfs, key=lambda e:(e.type_id, e.value or '')))


def _wbs_path(schedule, key):
    path, seen = [], set()
    while key and key not in seen and key in schedule.wbs_nodes:
        seen.add(key)
        w = schedule.wbs_nodes[key]
        path.append(w.wbs_code + ': ' + w.wbs_name)
        key = w.parent_wbs_id
    return tuple(reversed(path))


def _role(evidence):
    # Semantic role uses explicit classification values; names never confer authority.
    values = [_text(e.value) for e in evidence if e.matched_terms]
    if any(v == 'final completion' or v == 'contractual completion' for v in values):
        return 'FINAL_COMPLETION'
    if any(v == 'substantial completion' for v in values):
        return 'SUBSTANTIAL_COMPLETION'
    if any('revenue service' in v for v in values):
        return 'REVENUE_SERVICE'
    return 'COMPLETION_CONTEXT'


def investigate_completion_anchors(schedule, graph, project_fields=(), config=None, metadata_rules=()):
    """Classify evidence without executing CPM or selecting by rank/date/float."""
    config = config or CPMConfig()
    diagnostics = []
    explicit_sources = {}
    explicit_selection = None
    selector_invalid = False
    groups = [(config.completion_activity_id, config.completion_activity_code, 'CONFIGURED_COMPLETION_ACTIVITY'),
              (config.required_finish_activity_id, config.required_finish_activity_code, 'CONFIGURED_REQUIRED_FINISH_ACTIVITY')]
    for aid, code, source in groups:
        if aid is None and code is None:
            continue
        matches = [a.activity_id for a in schedule.activities.values() if (aid is None or a.activity_id == aid) and (code is None or a.activity_code == code)]
        if len(matches) != 1 or (explicit_selection is not None and explicit_selection != matches[0]):
            selector_invalid = True
            diagnostics.append(CPMDiagnostic('invalid_configured_completion_authority', 'Explicit selectors must identify the same unique activity; no fallback is permitted.', CPMFindingSeverity.WARNING,
                metadata={'activity_id': aid, 'activity_code': code, 'matches': tuple(sorted(matches))}))
        else:
            explicit_selection = matches[0]
            explicit_sources.setdefault(matches[0], []).append(source)
    candidates = []
    for a in schedule.activities.values():
        codes, udfs = _metadata(schedule, a)
        authority = list(explicit_sources.get(a.activity_id, ()))
        for rule in metadata_rules:
            values = {e.value for e in codes + udfs if e.source == rule.source and e.type_id == rule.type_id}
            if rule.expected_value in values:
                if len(values) == 1:
                    authority.append(f'{rule.source}:{rule.type_id}={rule.expected_value}; {rule.authority_source}')
                else:
                    diagnostics.append(CPMDiagnostic('conflicting_completion_metadata_values',
                        'A declared authority field has conflicting values on this activity; no value was chosen.',
                        CPMFindingSeverity.WARNING, activity_id=a.activity_id,
                        metadata={'source': rule.source, 'type_id': rule.type_id,
                                  'values': tuple(sorted(values, key=lambda v: v or ''))}))
        kind = normalize_activity_type(a.raw_activity_type or a.activity_type)
        status = normalize_status(a.raw_status or a.status)
        milestone = kind in {'milestone', 'finish_milestone', 'start_milestone', 'generic_milestone'}
        finish = kind == 'finish_milestone'
        terminal = not graph.successor_relationships.get(a.activity_id)
        structured = tuple(e for e in codes + udfs if e.matched_terms)
        name_match = any(t in _text(a.activity_name) for t in _TERMS)
        if not (authority or milestone or structured or name_match):
            continue
        imported = ImportedCompletionEvidence(*(getattr(a, name) for name in (
            'planned_start', 'planned_finish', 'early_start', 'early_finish', 'late_start', 'late_finish',
            'actual_start', 'actual_finish', 'total_float_hours', 'free_float_hours')))
        constraints = tuple(CompletionConstraintEvidence(slot, kind, stamp, raw) for slot, kind, stamp, raw in (
            ('PRIMARY', a.primary_constraint_type, a.primary_constraint_date, a.raw_primary_constraint_type),
            ('SECONDARY', a.secondary_constraint_type, a.secondary_constraint_date, a.raw_secondary_constraint_type)) if kind is not None or stamp is not None)
        agreements = tuple(ProjectDateAgreement(field, endpoint, value) for field in project_fields
            if field.parsed_date is not None and field.semantic_role in {'REQUIRED_PROJECT_FINISH', 'SCHEDULED_FINISH_OUTPUT', 'ANTICIPATED_FINISH'}
            for endpoint, value in [('early_finish', a.early_finish), ('late_finish', a.late_finish), ('planned_finish', a.planned_finish)] if value is not None and value == field.parsed_date)
        scheduled_match = any(e.project_field.semantic_role == 'SCHEDULED_FINISH_OUTPUT' and e.activity_endpoint == 'early_finish' for e in agreements)
        project_wide = any(_text(e.value).replace('-', ' ') in {'project wide', 'work milestone', 'work milestones', 'project milestones'} for e in structured + codes)
        role = _role(structured)
        milestone_taxonomy = any('milestone' in _text(e.type_name) and _text(e.value) in {'final completion', 'substantial completion', 'contractual completion'} for e in structured)
        if authority:
            evidence_class = CompletionEvidenceClass.AUTHORITATIVE
        elif finish and status != 'complete' and (milestone_taxonomy or (terminal and scheduled_match and structured)):
            evidence_class = CompletionEvidenceClass.STRONG_CANDIDATE
        elif structured or (milestone and status != 'complete' and (name_match or terminal)):
            evidence_class = CompletionEvidenceClass.CANDIDATE
        else:
            evidence_class = CompletionEvidenceClass.WEAK_CANDIDATE
        evidence_sources = tuple(label for present, label in [
            (bool(name_match), 'ACTIVITY_NAME_DISCOVERY'), (bool(codes and any(e.matched_terms for e in codes)), 'ACTIVITY_CODE_CLASSIFICATION'),
            (bool(udfs and any(e.matched_terms for e in udfs)), 'UDF_CLASSIFICATION'), (bool(agreements), 'PROJECT_DATE_AGREEMENT'),
            (bool(constraints), 'ACTIVITY_CONSTRAINT'), (terminal, 'TERMINAL'), (milestone, 'MILESTONE_TYPE'),
            (a.total_float_hours == 0, 'IMPORTED_ZERO_FLOAT_INFORMATION_ONLY'), (bool(authority), 'EXPLICIT_AUTHORITY')]
            if present)
        candidates.append(CompletionAnchorCandidate(a.activity_id, a.activity_code, a.activity_name, kind, status,
            a.wbs_id, _wbs_path(schedule, a.wbs_id), len(graph.predecessor_relationships.get(a.activity_id, ())), len(graph.successor_relationships.get(a.activity_id, ())),
            terminal, milestone, finish, role, project_wide, imported, constraints, codes, udfs, agreements, evidence_sources, evidence_class, tuple(authority)))
    def rank_key(c):
        class_order = {CompletionEvidenceClass.AUTHORITATIVE:0, CompletionEvidenceClass.STRONG_CANDIDATE:1,
                       CompletionEvidenceClass.CANDIDATE:2, CompletionEvidenceClass.WEAK_CANDIDATE:3}
        scheduled = any(e.project_field.semantic_role == 'SCHEDULED_FINISH_OUTPUT' and e.activity_endpoint == 'early_finish' for e in c.project_date_agreements)
        role_order = (0 if c.completion_role == 'FINAL_COMPLETION' else (1 if scheduled and c.terminal else
                      (2 if c.completion_role == 'SUBSTANTIAL_COMPLETION' and c.project_wide_classification else
                      (3 if c.completion_role == 'SUBSTANTIAL_COMPLETION' else (4 if c.completion_role == 'REVENUE_SERVICE' else 5)))))
        return (class_order[c.evidence_class], role_order, not c.project_wide_classification, not scheduled,
                c.status == 'complete', not c.terminal, c.activity_code.casefold(), c.activity_id)
    candidates.sort(key=rank_key)
    candidates = tuple(replace(c, rank=i, ranking_reason=(c.evidence_class.value,
        f'ROLE_PRIORITY_{rank_key(c)[1]}_{c.completion_role}',
        'PROJECT_WIDE_CLASSIFICATION' if c.project_wide_classification else 'NO_PROJECT_WIDE_CLASSIFICATION',
        'SCHEDULED_FINISH_AGREEMENT' if not rank_key(c)[3] else 'NO_SCHEDULED_FINISH_AGREEMENT',
        'COMPLETED_HISTORY' if c.status == 'complete' else 'UNFINISHED',
        'TERMINAL' if c.terminal else 'NONTERMINAL',
        'STABLE_LEXICAL_CODE_ID_TIEBREAK')) for i, c in enumerate(candidates, 1))
    by_id = {c.activity_id:c for c in candidates}
    authoritative = [c.activity_id for c in candidates if c.evidence_class == CompletionEvidenceClass.AUTHORITATIVE]
    selected = None
    status = 'ANCHOR_NOT_SELECTED'
    if selector_invalid:
        status = 'INVALID_CONFIGURED_ANCHOR'
    elif explicit_selection:
        selected = explicit_selection
    elif len(authoritative) == 1:
        selected = authoritative[0]
    elif len(authoritative) > 1:
        diagnostics.append(CPMDiagnostic('ambiguous_completion_authority', 'Multiple declared authority matches; ranking is not a selection.', CPMFindingSeverity.WARNING, metadata={'activity_ids':tuple(sorted(authoritative))}))
    if selected:
        if by_id[selected].activity_type in {'level_of_effort', 'wbs_summary'}:
            diagnostics.append(CPMDiagnostic('unsupported_completion_anchor_type', 'Authority identity does not make an unsupported activity schedulable.', CPMFindingSeverity.WARNING, activity_id=selected))
            selected = None
        else:
            status = 'ANCHOR_SELECTED'
    required = config.required_project_finish
    if required is None:
        dates = {e.parsed_date for e in project_fields if e.semantic_role == 'REQUIRED_PROJECT_FINISH' and e.parsed_date is not None}
        required = next(iter(dates)) if len(dates) == 1 else None
    date = required if selected else None
    source = ('CONFIGURED_REQUIRED_PROJECT_FINISH' if config.required_project_finish is not None else 'EXPORTED_PROJECT_MUST_FINISH_BY') if date is not None else None
    if selected is None:
        diagnostics.append(CPMDiagnostic('completion_authority_not_established', 'Candidates, scheduled output dates, float and activity constraints do not by themselves authorize real-project backward validation.', CPMFindingSeverity.INFORMATIONAL))
    return CompletionAnchorInvestigation(status, candidates, selected, by_id[selected].activity_code if selected else None,
        date, source, required, tuple(project_fields), tuple(diagnostics))


def anchor_ancestor_scope(schedule, graph, investigation):
    """Graph scope ONLY, not a promise of late-date/float calculability.

    Requires selected authority, excludes unrelated and post-anchor activities,
    and does not execute backward calculation or manufacture missing endpoints.
    """
    if investigation.selection_status != 'ANCHOR_SELECTED' or investigation.selected_activity_id not in schedule.activities:
        return ()
    queue, seen = deque([investigation.selected_activity_id]), {investigation.selected_activity_id}
    while queue:
        key = queue.popleft()
        for r in graph.predecessor_relationships.get(key, ()):
            if r.predecessor_activity_id in schedule.activities and r.predecessor_activity_id not in seen:
                seen.add(r.predecessor_activity_id)
                queue.append(r.predecessor_activity_id)
    return tuple(sorted(seen))
