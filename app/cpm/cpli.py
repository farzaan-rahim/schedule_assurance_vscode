"""Required-finish and connected-path-based CPLI; no imported float substitution."""
from copy import deepcopy
from dataclasses import dataclass,field,replace
from datetime import datetime
from math import isfinite
from app.cpm.config import CPMConfig
from app.cpm.models import CPMResult,CPMPath
from app.cpm.simulation import run_cpm
from app.cpm.selected_analysis import _trace_selected
from app.graph.schedule_graph import ScheduleGraph
from app.calendars.working_time import working_hours_between


@dataclass(frozen=True)
class CPLIConfig:
    required_finish: datetime | None=None
    common_calendar_id: str | None=None
    path_length_method: str='EXISTING_PATH_DURATION'
    pass_threshold: float=1.0
    warning_threshold: float=0.95


@dataclass(frozen=True)
class CPLIResult:
    status: str='NOT_EVALUATED'
    config: CPLIConfig=field(default_factory=CPLIConfig)
    cpm_config: CPMConfig | None=None
    critical_path_length_hours: float | None=None
    total_float_hours: float | None=None
    native_anchor_total_float_hours: float | None=None
    required_finish: datetime | None=None
    calculated_finish: datetime | None=None
    required_finish_source: str | None=None
    float_source: str | None=None
    calendar_id: str | None=None
    numerator_hours: float | None=None
    denominator_hours: float | None=None
    value: float | None=None
    formula: str='(CPL_hours + selected_anchor_deadline_float_hours) / CPL_hours'
    formula_version: str='APPLICATION-CPLI-V1'
    source_cpm_result: CPMResult | None=None
    cpm_result: CPMResult | None=None
    selected_path: CPMPath | None=None
    paths: tuple[CPMPath,...]=()
    sum_effective_activity_duration_hours: float | None=None
    relationship_lag_contribution_hours: float | None=None
    diagnostics: tuple[str,...]=()


class CPLIService:
    def calculate(self,schedule,cpm_config=None,config=None):
        cp=cpm_config or CPMConfig();cfg=config or CPLIConfig();out=CPLIResult(config=cfg,cpm_config=cp)
        def stop(reason):return replace(out,diagnostics=(reason,))
        if any(not isinstance(v,(int,float)) or not isfinite(v) for v in (cfg.pass_threshold,cfg.warning_threshold)) or not 0<=cfg.warning_threshold<=cfg.pass_threshold:
            return stop('invalid_cpli_thresholds')
        if cfg.path_length_method not in {'EXISTING_PATH_DURATION','COMMON_CALENDAR_WORKING_SPAN'}:return stop('unsupported_cpl_method')
        if cfg.common_calendar_id is not None and cfg.path_length_method!='COMMON_CALENDAR_WORKING_SPAN':return stop('explicit_common_calendar_method_required')
        try:
            source=deepcopy(schedule);original=run_cpm(source,cp);out=replace(out,source_cpm_result=original)
            if original.status!='CALCULATED' or cp.component_calculation_policy!='STRICT':return stop('source_cpm_not_calculated')
            anchor=original.completion_anchor
            if anchor is None or anchor.activity_id is None:return stop('completion_anchor_unresolved')
            graph=ScheduleGraph(source)
            if graph.successor_relationships.get(anchor.activity_id):return stop('cpli_requires_terminal_completion_anchor')
            a=source.activities[anchor.activity_id]
            required=cfg.required_finish or cp.required_project_finish
            provenance='CONFIGURED_CPLI_REQUIRED_FINISH' if cfg.required_finish is not None else 'CONFIGURED_CPM_REQUIRED_FINISH'
            if cfg.required_finish is not None and cp.required_project_finish is not None and cfg.required_finish!=cp.required_project_finish:return stop('conflicting_configured_required_finishes')
            if required is None:
                dates={stamp for kind,stamp in ((a.primary_constraint_type,a.primary_constraint_date),(a.secondary_constraint_type,a.secondary_constraint_date)) if kind=='FINISH_ON_OR_BEFORE' and stamp is not None}
                if len(dates)>1:return stop('ambiguous_required_finish_constraints')
                if dates:required=next(iter(dates));provenance='SELECTED_ANCHOR_FINISH_ON_OR_BEFORE_CONSTRAINT'
            if required is None:return stop('required_finish_missing')
            out=replace(out,required_finish=required,required_finish_source=provenance)
            if not isinstance(required,datetime):return stop('invalid_required_finish')
            locked=replace(cp,completion_activity_id=anchor.activity_id,completion_activity_code=None,project_completion_timestamp=None,
                required_finish_activity_id=None,required_finish_activity_code=None,required_project_finish=required)
            result=run_cpm(deepcopy(source),locked);out=replace(out,cpm_result=result)
            if result.status!='CALCULATED':return stop('required_finish_cpm_not_calculated')
            rows={r.activity_id:r for r in result.activity_results};row=rows[anchor.activity_id]
            out=replace(out,calculated_finish=row.calculated_early_finish,native_anchor_total_float_hours=row.calculated_total_float_hours)
            if row.date_basis!='REMAINING_WORK' or row.calculated_total_float_hours is None:return stop('anchor_remaining_float_unavailable')
            paths,stats,diags,status=_trace_selected(result,ScheduleGraph(result.schedule),result.completion_anchor)
            out=replace(out,paths=paths)
            if not paths or any(p.truncated or not p.trace_complete for p in paths) or any(s.truncated for s in stats):return stop('complete_controlling_paths_required')
            native=source.calendars[row.effective_calendar_id]
            if working_hours_between(native,row.calculated_late_finish,required)!=0:return stop('required_finish_not_effective_anchor_deadline')
            common=cfg.path_length_method=='COMMON_CALENDAR_WORKING_SPAN'
            cal_id=cfg.common_calendar_id if common else row.effective_calendar_id
            if cal_id not in source.calendars:return stop('calculation_calendar_unresolved')
            calendar=source.calendars[cal_id];lengths=[]
            for path in paths:
                length=working_hours_between(calendar,path.start_timestamp,path.finish_timestamp) if common else path.duration_hours
                if length is None:return stop('path_length_not_meaningful_without_common_calendar_method')
                if not common and {rows[k].effective_calendar_id for k in path.activity_ids}!={cal_id}:return stop('path_and_anchor_calendars_differ')
                lengths.append((length,path))
            length,path=min(lengths,key=lambda item:(-item[0],item[1].rank))
            out=replace(out,selected_path=path,critical_path_length_hours=length,denominator_hours=length,calendar_id=cal_id,
                sum_effective_activity_duration_hours=path.sum_effective_activity_duration_hours,relationship_lag_contribution_hours=path.relationship_lag_contribution_hours)
            if length<=0:return stop('nonpositive_critical_path_length')
            if common:
                tf=working_hours_between(calendar,row.calculated_early_finish,required);basis='COMMON_CALENDAR_REQUIRED_FINISH_MARGIN'
            else:
                if row.calculated_start_float_hours!=row.calculated_finish_float_hours:return stop('anchor_float_methods_disagree')
                tf=row.calculated_total_float_hours;basis='CALCULATED_ANCHOR_ACTIVITY_CALENDAR_START'
            numerator=length+tf;value=numerator/length
            status='PASS' if value>=cfg.pass_threshold else 'WARNING' if value>=cfg.warning_threshold else 'FAIL'
            return replace(out,status=status,total_float_hours=tf,float_source=basis,numerator_hours=numerator,value=value)
        except Exception as exc:return stop('cpli_error:'+type(exc).__name__+':'+str(exc))
