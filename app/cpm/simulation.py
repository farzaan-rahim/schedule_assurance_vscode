"""Immutable, complete-network CPM duration experiments; no DCMA dependencies."""
from copy import deepcopy
from dataclasses import dataclass,field,replace
from datetime import datetime
from math import isfinite
from app.cpm.config import CPMConfig
from app.cpm.models import CPMResult,CPMCompletionAnchor
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.calendars.working_time import working_hours_between
from app.importers.p6_normalization import normalize_activity_type


@dataclass(frozen=True)
class DurationSimulationResult:
    status: str='NOT_EVALUATED'
    source_config: CPMConfig | None=None
    selected_activity_id: str | None=None
    selected_activity_code: str | None=None
    original_effective_duration_hours: float | None=None
    simulated_effective_duration_hours: float | None=None
    duration_change_hours: float | None=None
    source_cpm_result: CPMResult | None=None
    simulated_cpm_result: CPMResult | None=None
    source_completion_anchor: CPMCompletionAnchor | None=None
    simulated_completion_anchor: CPMCompletionAnchor | None=None
    source_completion_timestamp: datetime | None=None
    simulated_completion_timestamp: datetime | None=None
    completion_movement_working_hours: float | None=None
    completion_movement_elapsed_hours: float | None=None
    completion_calendar_id: str | None=None
    anchor_policy: str='FIXED_ACTIVITY'
    critical_path_changes: dict=field(default_factory=dict)
    total_float_changes: tuple[dict,...]=()
    diagnostics: tuple[str,...]=()


def run_cpm(schedule,config):
    return CPMService().calculate(schedule,ScheduleGraph(schedule),config)


def ordinary_remaining(schedule,row):
    a=schedule.activities[row.activity_id]
    return (row.date_basis=='REMAINING_WORK' and row.effective_state!='COMPLETE'
        and row.effective_duration_hours>0 and row.effective_calendar_id in schedule.calendars
        and normalize_activity_type(a.raw_activity_type or a.activity_type)=='task')


def simulate_duration_change(schedule,activity_id,duration_delta_hours,cpm_config=None,*,anchor_policy='FIXED_ACTIVITY',completion_calendar_id=None):
    """Overlay the effective duration field on a private deep copy, then run CPM."""
    config=cpm_config or CPMConfig()
    audit=DurationSimulationResult(source_config=config,selected_activity_id=activity_id,duration_change_hours=duration_delta_hours,anchor_policy=anchor_policy)
    def stop(reason):return replace(audit,diagnostics=(reason,))
    if anchor_policy not in {'FIXED_ACTIVITY','RESELECT_TERMINAL'}:return stop('invalid_anchor_policy')
    if config.component_calculation_policy!='STRICT':return stop('complete_strict_cpm_required')
    if not isinstance(duration_delta_hours,(int,float)) or not isfinite(duration_delta_hours):return stop('invalid_duration_change')
    try:
        source=deepcopy(schedule);original=run_cpm(source,config)
        audit=replace(audit,source_cpm_result=original,source_completion_anchor=original.completion_anchor)
        if original.status!='CALCULATED':return stop('source_cpm_not_calculated')
        anchor=original.completion_anchor
        if anchor is None or anchor.activity_id is None:return stop('completion_anchor_unresolved')
        rows={r.activity_id:r for r in original.activity_results};row=rows.get(activity_id)
        audit=replace(audit,source_completion_timestamp=anchor.calculated_early_finish)
        if row is None or not ordinary_remaining(source,row):return stop('activity_not_supported_remaining_work')
        duration=row.effective_duration_hours+duration_delta_hours
        audit=replace(audit,selected_activity_code=row.activity_code,original_effective_duration_hours=row.effective_duration_hours,simulated_effective_duration_hours=duration)
        if not isfinite(duration) or duration<0:return stop('invalid_simulated_duration')
        overlay=deepcopy(source);a=overlay.activities[activity_id]
        if config.remaining_duration_preference and a.remaining_duration_hours is not None:a.remaining_duration_hours=duration
        elif a.original_duration_hours is not None:a.original_duration_hours=duration
        else:return stop('effective_duration_field_unresolved')
        locked=replace(config,completion_activity_id=anchor.activity_id,completion_activity_code=None,
            required_finish_activity_id=None,required_finish_activity_code=None,project_completion_timestamp=None) if anchor_policy=='FIXED_ACTIVITY' else config
        simulated=run_cpm(overlay,locked)
        audit=replace(audit,simulated_cpm_result=simulated,simulated_completion_anchor=simulated.completion_anchor)
        if simulated.status!='CALCULATED':return stop('simulation_cpm_not_calculated')
        after=simulated.completion_anchor
        if after is None or after.activity_id is None:return stop('simulated_completion_anchor_unresolved')
        if anchor_policy=='FIXED_ACTIVITY' and after.activity_id!=anchor.activity_id:return stop('completion_anchor_identity_changed')
        if after.activity_id!=anchor.activity_id and completion_calendar_id is None:return stop('anchor_change_requires_completion_calendar')
        start,end=anchor.calculated_early_finish,after.calculated_early_finish
        if start is None or end is None:return stop('completion_timestamp_unavailable')
        elapsed=(end-start).total_seconds()/3600
        audit=replace(audit,simulated_completion_timestamp=end,completion_movement_elapsed_hours=elapsed)
        cal_id=completion_calendar_id or rows[anchor.activity_id].effective_calendar_id
        if cal_id not in source.calendars:return stop('completion_calendar_unresolved')
        movement=working_hours_between(source.calendars[cal_id],start,end)
        new={r.activity_id:r for r in simulated.activity_results}
        changes=tuple(dict(activity_id=k,source_total_float_hours=v.calculated_total_float_hours,
            simulated_total_float_hours=new[k].calculated_total_float_hours,
            variance_hours=None if v.calculated_total_float_hours is None or new[k].calculated_total_float_hours is None else new[k].calculated_total_float_hours-v.calculated_total_float_hours)
            for k,v in sorted(rows.items()))
        return replace(audit,status='CALCULATED',completion_movement_working_hours=movement,completion_calendar_id=cal_id,
            total_float_changes=changes,critical_path_changes=dict(source=tuple(p.activity_ids for p in original.critical_paths),simulated=tuple(p.activity_ids for p in simulated.critical_paths),
                source_critical_activity_ids=tuple(r.activity_id for r in original.activity_results if r.calculated_critical),
                simulated_critical_activity_ids=tuple(r.activity_id for r in simulated.activity_results if r.calculated_critical)))
    except Exception as exc:
        return stop('simulation_error:'+type(exc).__name__+':'+str(exc))


@dataclass(frozen=True)
class CriticalPathTestConfig:
    delay_hours: float=8.0
    test_activity_id: str | None=None
    completion_calendar_id: str | None=None
    anchor_policy: str='FIXED_ACTIVITY'
    required_response_ratio: float=1.0
    response_tolerance: float=1e-9
    warning_response_tolerance: float=0.05


@dataclass(frozen=True)
class CriticalPathTestResult:
    status: str='NOT_EVALUATED'
    config: CriticalPathTestConfig=field(default_factory=CriticalPathTestConfig)
    selected_activity_id: str | None=None
    source_cpm_result: CPMResult | None=None
    cpm_config: CPMConfig | None=None
    selection_reason: str | None=None
    injected_delay_hours: float | None=None
    response_ratio: float | None=None
    simulation: DurationSimulationResult | None=None
    diagnostics: tuple[str,...]=()


class CriticalPathTestService:
    def evaluate(self,schedule,cpm_config=None,config=None):
        cfg=config or CriticalPathTestConfig();cp=cpm_config or CPMConfig()
        out=CriticalPathTestResult(config=cfg,cpm_config=cp,injected_delay_hours=cfg.delay_hours)
        def stop(reason):return replace(out,diagnostics=(reason,))
        numbers=(cfg.delay_hours,cfg.required_response_ratio,cfg.response_tolerance,cfg.warning_response_tolerance)
        if any(not isinstance(v,(int,float)) or not isfinite(v) for v in numbers) or cfg.delay_hours<=0 or cfg.required_response_ratio<=0 or not 0<=cfg.response_tolerance<=cfg.warning_response_tolerance:
            return stop('invalid_critical_path_test_configuration')
        try:
            source=run_cpm(deepcopy(schedule),cp)
            out=replace(out,source_cpm_result=source)
            if source.status!='CALCULATED' or cp.component_calculation_policy!='STRICT':return stop('source_cpm_not_calculated')
            if source.completion_anchor is None or source.completion_anchor.activity_id is None:return stop('completion_anchor_unresolved')
            paths=source.critical_paths
            if not paths or any(not p.trace_complete or p.truncated for p in paths) or any(s.truncated for s in source.path_statistics if s.classification=='CRITICAL'):
                return stop('complete_critical_controlling_path_unavailable')
            rows={r.activity_id:r for r in source.activity_results};distance={}
            for path in paths:
                for index,key in enumerate(path.activity_ids):
                    if ordinary_remaining(schedule,rows[key]) and rows[key].calculated_critical:distance[key]=max(distance.get(key,0),len(path.activity_ids)-1-index)
            if cfg.test_activity_id is not None:
                key=cfg.test_activity_id
                if key not in distance:return stop('explicit_test_activity_not_eligible')
                reason='EXPLICIT_ELIGIBLE_CRITICAL_ACTIVITY'
            else:
                if not distance:return stop('no_valid_test_activity')
                key=min(distance,key=lambda k:(-distance[k],rows[k].activity_code,k));reason='MOST_UPSTREAM_CRITICAL_POSITIVE_DURATION_THEN_LEXICAL_ID'
            simulation=simulate_duration_change(schedule,key,cfg.delay_hours,cp,anchor_policy=cfg.anchor_policy,completion_calendar_id=cfg.completion_calendar_id)
            out=replace(out,selected_activity_id=key,selection_reason=reason,simulation=simulation)
            if simulation.status!='CALCULATED':return stop('immutable_simulation_unavailable:'+','.join(simulation.diagnostics))
            relevant=[p for p in paths if key in p.activity_ids]
            ids={rows[k].effective_calendar_id for p in relevant for k in p.activity_ids}
            if len(ids)>1 and cfg.completion_calendar_id is None:return stop('mixed_calendars_require_explicit_completion_calendar')
            ratio=simulation.completion_movement_working_hours/cfg.delay_hours
            def inside(tolerance):
                return cfg.required_response_ratio-tolerance<=ratio<=cfg.required_response_ratio+tolerance
            status='PASS' if inside(cfg.response_tolerance) else 'WARNING' if inside(cfg.warning_response_tolerance) else 'FAIL'
            return replace(out,status=status,response_ratio=ratio)
        except Exception as exc:return stop('critical_path_test_error:'+type(exc).__name__+':'+str(exc))
