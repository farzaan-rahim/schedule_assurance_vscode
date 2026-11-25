"""Explicit analysis identity is independent of contractual completion authority."""
from dataclasses import dataclass
from datetime import datetime

from app.calendars.working_time import next_working_time
from app.cpm.completion_evidence import investigate_completion_anchors
from app.cpm.models import CPMDiagnostic, CPMFindingSeverity
from app.importers.p6_normalization import normalize_activity_type, normalize_status


@dataclass(frozen=True)
class CompletionAuthorityRecord:
    status: str = 'NOT_ESTABLISHED'
    evidence: tuple[str, ...] = ()
    required_finish: datetime | None = None

    def __post_init__(self):
        if self.status not in {'ESTABLISHED','NOT_ESTABLISHED','UNKNOWN'}:
            raise ValueError('Unknown contractual authority status.')
        if self.status=='ESTABLISHED' and not self.evidence:
            raise ValueError('Established authority requires separately supplied evidence.')


@dataclass(frozen=True)
class AnalysisAnchorConfig:
    analysis_anchor_activity_code: str | None = None
    analysis_anchor_internal_id: str | None = None
    configured_analysis_milestone: str | None = None
    mode: str = 'CALIBRATION'
    required_finish: datetime | None = None
    selected_by: str | None = None
    selection_reason: str = 'Explicit caller-selected endpoint for analysis, not contractual completion.'
    project_id: str | None = None


@dataclass(frozen=True)
class AnalysisAnchor:
    activity_id: str
    activity_code: str
    activity_name: str
    activity_type: str
    milestone: bool
    selection_method: str
    selection_reason: str
    selected_timestamp: datetime
    timestamp_source: str
    selected_by: str | None
    selected_by_caller: bool
    contractual_authority_status: str
    authority_evidence: tuple[str, ...]
    suitability_diagnostics: tuple[CPMDiagnostic, ...]
    imported_early_finish: datetime | None
    imported_late_finish: datetime | None
    required_finish: datetime | None = None
    anchor_kind: str = 'ANALYSIS_ANCHOR'


class AnchorSelectionError(ValueError):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code=code
        self.details=details


def resolve_analysis_anchor(schedule, graph, config, *, authority=None):
    authority=authority or CompletionAuthorityRecord()
    def fail(code,message,**details):
        raise AnchorSelectionError(code,message,**details)
    if config.mode not in {'CALIBRATION','INDEPENDENT'}:
        fail('invalid_analysis_mode','Mode must be CALIBRATION or INDEPENDENT.')
    for value in (config.analysis_anchor_activity_code,config.analysis_anchor_internal_id,config.configured_analysis_milestone):
        if value is not None and (not isinstance(value,str) or not value.strip()):
            fail('invalid_analysis_selector','Selectors must be nonempty strings.')
    code=config.analysis_anchor_activity_code
    key=config.analysis_anchor_internal_id
    configured=code is None and key is None and config.configured_analysis_milestone is not None
    if configured:code=config.configured_analysis_milestone
    if code is None and key is None:
        fail('analysis_anchor_required','Explicit analysis activity identity is required; no fallback is selected.')
    matches=[a for a in schedule.activities.values() if (key is None or a.activity_id==key) and (code is None or a.activity_code==code)]
    if not matches:
        fail('analysis_anchor_selector_conflict' if key and code else 'analysis_anchor_not_found',
             'Analysis selectors do not identify one activity; no fallback.',activity_id=key,activity_code=code)
    if len(matches)>1:
        fail('analysis_anchor_ambiguous','Activity code is not unique; select an explicit internal ID.',candidate_ids=tuple(sorted(a.activity_id for a in matches)))
    a=matches[0]
    if schedule.activities_by_id.get(a.activity_id) is not a or graph.schedule is not schedule or a.activity_id not in graph.activities_by_id:
        fail('unresolvable_analysis_identity','Canonical identity or graph reachability is unresolved.')
    if (not schedule.project or a.project_id!=schedule.project.project_id
            or config.project_id is not None and config.project_id!=schedule.project.project_id):
        fail('analysis_anchor_wrong_project','Analysis activity must belong to the selected project.')
    kind=normalize_activity_type(a.raw_activity_type or a.activity_type)
    milestone=kind in {'milestone','generic_milestone','start_milestone','finish_milestone'}
    if kind not in {'task','milestone','generic_milestone','start_milestone','finish_milestone'} or configured and not milestone:
        fail('unsuitable_analysis_anchor','Analysis anchor must be a supported milestone or an explicitly selected ordinary activity.',activity_type=kind)
    if normalize_status(a.raw_status or a.status)=='complete':
        fail('historical_analysis_anchor','Completed actual history is not a remaining-work backward anchor.')
    if config.mode=='CALIBRATION':
        if config.required_finish is not None:
            fail('conflicting_analysis_timestamp','Calibration explicitly uses imported Late Finish; use INDEPENDENT for a caller finish.')
        stamp=a.late_finish;source='CALIBRATION_IMPORTED_LATE_FINISH';required=None
    else:
        required=config.required_finish
        if required is None and authority.status=='ESTABLISHED':required=authority.required_finish
        if required is None:
            fail('analysis_required_finish_missing','INDEPENDENT analysis requires an explicit caller finish or separately authoritative finish; imported LF is not substituted.')
        stamp=required;source='CALLER_REQUIRED_FINISH' if config.required_finish is not None else 'SEPARATELY_AUTHORITATIVE_FINISH'
    if not isinstance(stamp,datetime) or stamp.tzinfo is not None:
        fail('analysis_anchor_timestamp_unusable','A usable naive project-local backward timestamp is required.')
    cal=schedule.calendars.get(a.calendar_id)
    if cal is None:
        fail('analysis_anchor_calendar_missing','Selected activity calendar is unresolved.')
    try:
        if any(getattr(d.severity,'value',d.severity)=='error' for d in cal.diagnostics):raise ValueError('Calendar has import errors.')
        next_working_time(cal,stamp)
    except (ValueError,IndexError,TypeError) as exc:
        fail('analysis_anchor_calendar_unusable',str(exc))
    findings=() if milestone else (CPMDiagnostic('analysis_anchor_not_milestone',
        'Caller deliberately selected a normal activity; this is not a project completion designation.',CPMFindingSeverity.INFORMATIONAL,a.activity_id),)
    method='CONFIGURED_ANALYSIS_MILESTONE' if configured else 'EXPLICIT_INTERNAL_ID' if key is not None else 'EXPLICIT_ACTIVITY_CODE'
    return AnalysisAnchor(a.activity_id,a.activity_code,a.activity_name,kind,milestone,method,config.selection_reason,
        stamp,source,config.selected_by,True,authority.status,authority.evidence,findings,a.early_finish,a.late_finish,required)


def analysis_anchor_catalog(schedule,graph):
    evidence=investigate_completion_anchors(schedule,graph)
    candidates=[]
    for c in evidence.candidates:
        if not c.milestone:continue
        try:
            anchor=resolve_analysis_anchor(schedule,graph,AnalysisAnchorConfig(analysis_anchor_internal_id=c.activity_id))
            findings=anchor.suitability_diagnostics;suitable=True
        except AnchorSelectionError as exc:
            findings=(CPMDiagnostic(exc.code,str(exc),CPMFindingSeverity.WARNING,c.activity_id),);suitable=False
        candidates.append(dict(activity_id=c.activity_id,activity_code=c.activity_code,activity_name=c.activity_name,
            activity_type=c.activity_type,status=c.status,wbs_path=c.wbs_path,terminal=c.terminal,
            imported_early_finish=c.imported.early_finish,imported_late_finish=c.imported.late_finish,
            evidence_class=c.evidence_class,evidence_sources=c.evidence_sources,activity_codes=c.activity_codes,udfs=c.udfs,
            suitable_for_calibration=suitable,suitability_diagnostics=findings,selection_requires_caller=True,
            independent_mode_requires_finish=True,calculation_guaranteed=False,predecessor_count=c.predecessor_count,successor_count=c.successor_count))
    return dict(schema_version='1.0',completion_authority_status='NOT_ESTABLISHED',selected_analysis_anchor=None,
        selection_methods=('EXPLICIT_ACTIVITY_CODE','EXPLICIT_INTERNAL_ID','CONFIGURED_ANALYSIS_MILESTONE'),
        candidates=tuple(candidates),count=len(candidates),normal_activity_selection='Explicit code/internal ID only; normal activities are not completion candidates.')
