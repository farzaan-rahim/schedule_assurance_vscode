"""Selected dependency-scope orchestration over protected CPM arithmetic."""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace
from datetime import datetime

from app.calendars.working_time import is_working_time, previous_working_time, subtract_working_hours
from app.cpm.activity_state import activity_decision
from app.cpm.analysis_anchors import AnalysisAnchor, resolve_analysis_anchor
from app.cpm.analysis_comparison import compare_selected
from app.cpm.backward_pass import backward_pass
from app.cpm.config import CPMConfig
from app.cpm.criticality import classify_criticality
from app.cpm.float_calculation import free_float_details, total_float
from app.cpm.models import (CPMActivityResult, CPMActivityCalculability, CPMAnchor, CPMCompletionAnchor, CPMResult,
    CPMConstraintControl, CPMDiagnostic, CPMFindingSeverity, CPMProgressState, CPMRelationshipControl, CPMRelationshipCalculability)
from app.cpm.paths import _enumerate
from app.cpm.service import CPMService
from app.cpm.validation import validate_pass_relationships
from app.graph.schedule_graph import ScheduleGraph
from app.importers.p6_normalization import normalize_status


@dataclass(frozen=True)
class AnalysisActivityDisposition:
    activity_id: str
    activity_code: str
    late_status: str
    reason_codes: tuple[str, ...]
    es_availability: str
    ef_availability: str
    ls_availability: str
    lf_availability: str
    total_float_availability: str
    free_float_availability: str


@dataclass(frozen=True)
class AnalysisRelationshipDisposition:
    relationship_id: str
    predecessor_id: str
    successor_id: str
    forward_status: str
    backward_status: str
    reason_codes: tuple[str, ...]
    forward_reason_codes: tuple[str, ...] = ()
    backward_reason_codes: tuple[str, ...] = ()
    forward_requirement_timestamp: datetime | None = None
    expired_lag_hours: float | None = None
    remaining_lag_hours: float | None = None


@dataclass(frozen=True)
class SelectedAnchorAnalysis:
    anchor: AnalysisAnchor
    mode: str
    upstream_activity_ids: tuple[str, ...]
    activity_dispositions: tuple[AnalysisActivityDisposition, ...]
    relationship_dispositions: tuple[AnalysisRelationshipDisposition, ...]
    cpm_result: CPMResult
    summary: dict
    comparisons: tuple[dict, ...]
    path_status: str
    blocked_boundaries: tuple[dict, ...]
    diagnostics: tuple[CPMDiagnostic, ...]


def _upstream(graph, key):
    seen={key};queue=deque([key])
    while queue:
        for r in graph.predecessor_relationships.get(queue.popleft(),()):
            if r.predecessor_activity_id not in seen:
                seen.add(r.predecessor_activity_id);queue.append(r.predecessor_activity_id)
    return seen


class SelectedAnchorService:
    def analyze(self,schedule,graph,selection,*,engine_config=None,forward_result=None,authority=None,critical_definition=None):
        anchor=resolve_analysis_anchor(schedule,graph,selection,authority=authority)
        config=engine_config or CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
        if config.component_calculation_policy!='DIRECTIONAL_FORWARD' or config.progress_scheduling_policy!='P6_RETAINED_LOGIC':
            raise ValueError('Selected P6 analysis requires the protected opt-in directional retained forward policy.')
        if forward_result is not None and (forward_result.schedule is not schedule or forward_result.calculation_config!=config):
            raise ValueError('Reused forward result must belong to this schedule and exact calculation configuration.')
        forward=forward_result or CPMService().calculate(schedule,graph,config)
        scope=_upstream(graph,anchor.activity_id)
        active_states={};excluded=set();history=set();blocked=defaultdict(set)
        diagnostics=list(anchor.suitability_diagnostics)
        diagnostics.extend(replace(d,metadata={**d.metadata,'source_direction':'FORWARD_VALIDATION'}) for d in forward.diagnostics if d.code!='late_and_float_not_evaluated' and (d.activity_id in scope or d.activity_id is None and d.relationship_id is None))
        prior={a.activity_id:a for a in forward.activity_results}
        activity_avail={a.activity_id:a for a in forward.activity_calculability}
        relation_avail={r.relationship_id:r for r in forward.relationship_calculability}
        data_date=schedule.project.data_date
        def issue(code,message,key=None,rel=None,severity=CPMFindingSeverity.WARNING,**metadata):
            diagnostics.append(CPMDiagnostic(code,message,severity,key,rel,metadata))
        roots=defaultdict(set);global_roots=set()
        for d in forward.diagnostics:
            if d.severity!=CPMFindingSeverity.ERROR:continue
            if d.activity_id:
                # Forward topological leftovers include descendants of a cycle;
                # reverse traversal must determine its own unresolved population.
                if d.code!='forward_cycle':roots[d.activity_id].add(d.code)
            elif d.relationship_id is None and d.code!='circular_logic':global_roots.add(d.code)
        for key in sorted(scope):
            a=schedule.activities[key]
            state,findings,disposition=activity_decision(a,config,data_date)
            if disposition=='EXCLUDE':excluded.add(key);blocked[key].update(d.code for d in findings)
            elif state and state[1]=='COMPLETE':history.add(key)
            elif state:
                active_states[key]=state;blocked[key].update(roots[key]|global_roots)
            else:blocked[key].update(d.code for d in findings)
            if key not in excluded and key not in history:
                if a.calendar_id not in schedule.calendars:blocked[key].add('missing_activity_calendar')
                if state is None:blocked[key].add('invalid_activity_state')
        # Never invert unimplemented retained/progress relationships as ordinary static logic.
        for r in schedule.relationships:
            p,q=r.predecessor_activity_id,r.successor_activity_id
            if p not in scope:continue
            if q not in schedule.activities:
                blocked[p].add('external_backward_endpoint');continue
            if q not in scope:continue  # Explicit selected-boundary scope; recorded below.
            if q in history and p not in history and p not in excluded:
                blocked[p].add('completed_backward_bridge_unimplemented')
            if normalize_status(schedule.activities[p].raw_status or schedule.activities[p].status)=='in_progress':
                if r.relationship_type.upper()=='SS' and r.lag_hours!=0:blocked[p].add('backward_progressed_ss_unimplemented')
                if r.relationship_type.upper()=='SF':blocked[p].add('backward_progressed_sf_unimplemented')
            if r.relationship_type.upper() not in {'FS','SS','FF','SF'}:blocked[p].add('unsupported_relationship_type')
        # Relation-specific forward validation errors are uncertainty in the reverse bound too.
        rel_by_id={r.relationship_id:r for r in schedule.relationships}
        for d in forward.diagnostics:
            if d.severity==CPMFindingSeverity.ERROR and d.relationship_id in rel_by_id:
                r=rel_by_id[d.relationship_id]
                if r.predecessor_activity_id in scope and r.successor_activity_id in scope:
                    blocked[r.predecessor_activity_id].add(d.code)
        def propagate():
            queue=deque(sorted({k for k,v in blocked.items() if v}|excluded));visited=set(queue)
            while queue:
                key=queue.popleft()
                for r in graph.predecessor_relationships.get(key,()):
                    p=r.predecessor_activity_id
                    if p not in scope or p in history or p in excluded:continue
                    blocked[p].add('blocked_backward_successor')
                    if p not in visited:visited.add(p);queue.append(p)
        propagate()
        backward=None;view=None;view_graph=None
        while True:
            valid={k for k in active_states if not blocked[k] and k not in excluded}
            if anchor.activity_id not in valid:
                # No imported proxy is used to bridge an invalid selected node.
                for key in valid:blocked[key].add('selected_backward_boundary_blocked')
                valid=set();break
            view=replace(schedule,activities={k:schedule.activities[k] for k in sorted(valid)},
                relationships=[r for r in schedule.relationships if r.predecessor_activity_id in valid and r.successor_activity_id in valid])
            view.rebuild_activity_indexes();view_graph=ScheduleGraph(view)
            try:
                backward=backward_pass(view,view_graph,config,{k:active_states[k] for k in valid},schedule.calendars,{},
                    CPMAnchor(anchor.selected_timestamp,anchor.timestamp_source,(anchor.activity_id,)))
                unresolved=valid-set(backward['late_starts'])
                if unresolved:
                    for key in unresolved:blocked[key].add('backward_cycle_or_unresolved_dependency')
                    propagate();continue
                failures=validate_pass_relationships(view,backward['late_starts'],backward['late_finishes'],'selected_backward')
                for key in valid:
                    a=schedule.activities[key];cal=schedule.calendars[a.calendar_id];dur=active_states[key][0]
                    ls,lf=backward['late_starts'][key],backward['late_finishes'][key]
                    good=ls==subtract_working_hours(cal,lf,dur)
                    if dur:good=good and is_working_time(cal,ls) and (is_working_time(cal,lf) or previous_working_time(cal,lf)==lf)
                    for kind,stamp in ((a.primary_constraint_type,a.primary_constraint_date),(a.secondary_constraint_type,a.secondary_constraint_date)):
                        if kind=='START_ON_OR_BEFORE':good=good and ls<=stamp
                        if kind=='FINISH_ON_OR_BEFORE':good=good and lf<=stamp
                    if not good:failures.append(CPMDiagnostic('selected_late_invariant_failed','Late calendar/duration/constraint invariant failed.',CPMFindingSeverity.ERROR,key))
                if failures:
                    diagnostics.extend(failures)
                    for d in failures:
                        key=d.activity_id or rel_by_id[d.relationship_id].predecessor_activity_id
                        blocked[key].add(d.code)
                    propagate();continue
            except (ValueError,OverflowError,TypeError,IndexError) as exc:
                for key in valid:blocked[key].add('selected_backward_arithmetic_error')
                issue('selected_backward_arithmetic_error',str(exc));valid=set();backward=None
            break
        original_outgoing=defaultdict(list)
        for r in schedule.relationships:original_outgoing[r.predecessor_activity_id].append(r)
        early_starts={k:r.calculated_early_start for k,r in prior.items()}
        early_finishes={k:r.calculated_early_finish for k,r in prior.items()}
        results=[];free_reasons={}
        options=schedule.scheduling_options
        for key in sorted(scope):
            raw=schedule.activities[key];base=prior.get(key)
            if key in excluded:continue
            if base is None and key not in valid:continue
            if base is None:
                state=active_states[key]
                base=CPMActivityResult(key,raw.activity_code,raw.activity_name,state[0],raw.calendar_id,
                    None,None,None,None,None,None,False,False,raw.early_start,raw.early_finish,raw.late_start,raw.late_finish,
                    raw.total_float_hours,raw.free_float_hours,effective_state=state[1],
                    imported_actual_start=raw.actual_start,imported_actual_finish=raw.actual_finish,
                    progress_state=CPMProgressState(raw.actual_start,raw.actual_finish,data_date,None,raw.remaining_start,raw.remaining_finish,raw.remaining_duration_hours),
                    early_date_status='EARLY_DATES_BLOCKED')
            ls=backward['late_starts'][key] if key in valid else None
            lf=backward['late_finishes'][key] if key in valid else None
            tf=tf_finish=ff=None;details=();controls=[];constraints=[]
            if key in valid:
                c=backward['controlling'][key]
                for r in view_graph.successor_relationships[key]:
                    if r.relationship_id in c['relationships']:
                        controls.append(CPMRelationshipControl(r.relationship_id,key,raw.activity_code,r.successor_activity_id,
                            schedule.activities[r.successor_activity_id].activity_code,r.relationship_type,r.lag_hours,config.lag_calendar_policy,raw.calendar_id,
                            'BACKWARD','LATE_FINISH',c['requirements'][r.relationship_id],len(c['relationships'])>1))
                constraints=[CPMConstraintControl(k,t,'BACKWARD',req,bool(c['relationships'])) for k,t,req in c['constraints']]
            if key in valid and key in prior and key not in history:
                tf,tf_finish=total_float(schedule.calendars[raw.calendar_id],base.calculated_early_start,ls,base.calculated_early_finish,lf)
                if tf is not None and tf_finish is not None and tf!=tf_finish:
                    issue('float_methods_disagree','Start-based primary and finish-based audit float differ.',key,start_float=tf,finish_float=tf_finish)
            # FF uses all original outgoing requirements, not a cropped anchor graph.
            if key in prior and key not in history:
                outgoing=original_outgoing.get(key,())
                reliable=all(r.relationship_id in relation_avail and relation_avail[r.relationship_id].forward_status=='FORWARD_USABLE' for r in outgoing)
                progressed=normalize_status(raw.raw_status or raw.status)=='in_progress'
                if progressed and any(r.relationship_type.upper() in {'SS','SF'} for r in outgoing):reliable=False
                if reliable:
                    try:
                        ff,details,reason=free_float_details(schedule,graph,schedule.calendars[raw.calendar_id],key,early_starts,early_finishes,config.lag_calendar_policy)
                        if reason:free_reasons[key]=reason
                    except (ValueError,TypeError,OverflowError) as exc:free_reasons[key]='free_float_arithmetic_unavailable';issue(free_reasons[key],str(exc),key)
                else:free_reasons[key]='free_float_unresolved_successor_requirement'
            critical,near=classify_criticality(tf,config.critical_float_threshold_hours,config.near_critical_float_threshold_hours)
            imported_critical=raw.total_float_hours<=config.critical_float_threshold_hours if raw.total_float_hours is not None else None
            results.append(replace(base,calculated_late_start=ls,calculated_late_finish=lf,calculated_total_float_hours=tf,
                calculated_start_float_hours=tf,calculated_finish_float_hours=tf_finish,calculated_free_float_hours=ff,
                relationship_free_float_hours=details,calculated_critical=critical,calculated_near_critical=near,
                imported_critical=imported_critical,critical_disagreement=critical!=imported_critical if tf is not None and imported_critical is not None else None,
                late_date_status='LATE_DATES_CALCULATED' if key in valid else 'HISTORICAL_ONLY' if key in history else 'LATE_DATES_BLOCKED',
                float_status='FLOAT_CALCULATED' if tf is not None else 'FLOAT_BLOCKED',
                controlling_successor_ids=tuple(backward['controlling'][key]['successors']) if key in valid else (),
                controlling_relationships=base.controlling_relationships+tuple(controls),controlling_constraints=base.controlling_constraints+tuple(constraints)))
        by_result={r.activity_id:r for r in results}
        dispositions=[]
        for key in sorted(scope):
            a=schedule.activities[key];r=by_result.get(key)
            reasons=set(blocked[key]);reason=free_reasons.get(key)
            if reason:reasons.add(reason)
            if key not in prior:
                reasons.update(activity_avail[key].reason_codes if key in activity_avail else ('early_result_unavailable',))
            availability='EXCLUDED' if key in excluded else 'HISTORICAL_ONLY' if key in history else 'BACKWARD_CALCULABLE' if key in valid else 'BLOCKED'
            def metric(value):return 'AVAILABLE' if value is not None else 'EXCLUDED' if key in excluded else 'NOT_APPLICABLE' if key in history else 'BLOCKED'
            dispositions.append(AnalysisActivityDisposition(key,a.activity_code,availability,tuple(sorted(reasons)),
                metric(r.calculated_early_start if r else None),metric(r.calculated_early_finish if r else None),
                'NOT_APPLICABLE' if key in history else metric(r.calculated_late_start if r else None),
                'NOT_APPLICABLE' if key in history else metric(r.calculated_late_finish if r else None),
                metric(r.calculated_total_float_hours if r else None),metric(r.calculated_free_float_hours if r else None)))
        relation_states=[];boundaries=[]
        for r in sorted(schedule.relationships,key=lambda r:r.relationship_id):
            p,q=r.predecessor_activity_id,r.successor_activity_id
            if p not in scope and q not in scope:continue
            reasons=[]
            if p not in schedule.activities or q not in schedule.activities:
                state='BLOCKED_BACKWARD';reasons=['missing_endpoint']
            elif p not in scope or q not in scope:
                state='OUTSIDE_ANALYSIS_SCOPE';reasons=['selected_scope_boundary_not_global_project_logic']
            elif p in excluded or q in excluded:
                state='EXCLUDED_ENDPOINT';reasons=['excluded_loe_or_wbs_endpoint']
            elif p in history or q in history:
                state='HISTORICAL_ONLY';reasons=['history_not_rescheduled']
            elif p in valid and q in valid:state='USABLE_BACKWARD'
            else:
                state='BLOCKED_BACKWARD';reasons=sorted(set(blocked[p])|set(blocked[q])) or ['unresolved_backward_endpoint']
            forward_state=relation_avail[r.relationship_id].forward_status if r.relationship_id in relation_avail else 'FORWARD_BLOCKED'
            original=relation_avail.get(r.relationship_id)
            relation_states.append(AnalysisRelationshipDisposition(r.relationship_id,p,q,forward_state,state,tuple(reasons),
                original.reason_codes if original else ('forward_relationship_unavailable',),tuple(reasons),
                original.forward_requirement_timestamp if original else None,original.expired_lag_hours if original else None,
                original.remaining_lag_hours if original else None))
            if state not in {'USABLE_BACKWARD','HISTORICAL_ONLY'}:boundaries.append(dict(relationship_id=r.relationship_id,predecessor_id=p,successor_id=q,disposition=state,reason_codes=tuple(reasons)))
        metrics,comparisons,critical_agreement=compare_selected(schedule,results,config)
        remaining_population=len(scope)-len(history)-len(excluded)
        for name,metric in metrics.items():
            suffix='_hours' if 'float' in name else ''
            available=sum(getattr(r,'calculated_'+name+suffix) is not None and r.date_basis!='PRESERVED_ACTUALS' for r in results)
            metric['missing_calculated']=remaining_population-available
        if critical_definition is not None:
            critical_agreement['source_definition']=critical_definition
            threshold=critical_definition.total_float_threshold_hours
            if threshold is not None:
                comparable=[r for r in results if r.calculated_total_float_hours is not None and r.imported_total_float_hours is not None]
                critical_agreement.update(p6_configured_threshold_hours=threshold,
                    definition_compatibility='EQUIVALENT_THRESHOLDS' if threshold==config.critical_float_threshold_hours else 'CONFIGURATION_DIFFERENCE',
                    configured_definition_comparable_count=len(comparable),
                    configured_definition_agreements=sum((r.imported_total_float_hours<=threshold)==r.calculated_critical for r in comparable),
                    configured_definition_application_only=sum(r.calculated_critical and r.imported_total_float_hours>threshold for r in comparable),
                    configured_definition_p6_only=sum(not r.calculated_critical and r.imported_total_float_hours<=threshold for r in comparable),
                    basis='P6_CONFIGURED_TOTAL_FLOAT_RECONSTRUCTION_NO_EXPORTED_CRITICAL_FLAG')
        cpm=replace(forward,activity_results=tuple(results),project_finish_anchor=None,calculated_completion=None,completion_anchor=None,
            critical_paths=(),near_critical_paths=(),path_statistics=(),comparisons=(),comparison_summary=None,
            calculation_config=config,reliability_scope='SELECTED_ANALYSIS_ANCHOR_RELATIVE',anchor_selection_status='EXPLICIT_ANALYSIS_ANCHOR',
            activity_calculability=tuple(CPMActivityCalculability(d.activity_id,'SELECTED_UPSTREAM',d.late_status,d.reason_codes,
                early_date_status='EARLY_DATES_CALCULATED' if d.es_availability=='AVAILABLE' else 'EARLY_DATES_BLOCKED',
                late_date_status='LATE_DATES_CALCULATED' if d.ls_availability=='AVAILABLE' else 'LATE_DATES_BLOCKED',
                float_status='FLOAT_CALCULATED' if d.total_float_availability=='AVAILABLE' else 'FLOAT_BLOCKED') for d in dispositions),
            eligible_activity_count=len(valid),blocked_activity_count=sum(d.late_status=='BLOCKED' for d in dispositions),excluded_activity_count=len(excluded),
            components=(),partially_calculated_activity_count=sum((d.es_availability=='AVAILABLE') != (d.ls_availability=='AVAILABLE') for d in dispositions if d.late_status!='HISTORICAL_ONLY'),
            relationship_calculability=tuple(CPMRelationshipCalculability(r.relationship_id,r.backward_status,tuple(sorted(set(r.forward_reason_codes+r.backward_reason_codes))),forward_status=r.forward_status,backward_status=r.backward_status,forward_requirement_timestamp=r.forward_requirement_timestamp,expired_lag_hours=r.expired_lag_hours,remaining_lag_hours=r.remaining_lag_hours) for r in relation_states),
            relationship_count=sum(r.predecessor_id in scope and r.successor_id in scope for r in relation_states),
            diagnostics=tuple(diagnostics),critical_activity_count=sum(r.calculated_critical for r in results),near_critical_activity_count=sum(r.calculated_near_critical for r in results))
        paths,statistics,path_diags,path_status=_trace_selected(cpm,graph,anchor)
        cpm=replace(cpm,critical_paths=paths,path_statistics=statistics,path_status=path_status,diagnostics=cpm.diagnostics+path_diags,
            truncation=dict(paths_truncated=any(s.truncated for s in statistics),nodes_inspected=sum(s.nodes_inspected for s in statistics)))
        raw_options=tuple((k,v) for k,v in (options.raw_fields if options else ()) if any(t in k for t in ('critical','float','longest')))
        summary=dict(selected_milestone=anchor.activity_code,anchor_kind='ANALYSIS_ANCHOR',mode=selection.mode,
            completion_authority_status=anchor.contractual_authority_status,imported_early_finish=anchor.imported_early_finish,
            imported_late_finish=anchor.imported_late_finish,selected_backward_timestamp=anchor.selected_timestamp,timestamp_source=anchor.timestamp_source,
            upstream_activity_count=len(scope),late_calculable=len(valid),total_float_valid=sum(r.calculated_total_float_hours is not None for r in results),
            free_float_valid=sum(r.calculated_free_float_hours is not None for r in results),excluded=len(excluded),historical_only=len(history),
            blocked=sum(d.late_status=='BLOCKED' for d in dispositions),early_calculable=sum(d.es_availability=='AVAILABLE' and d.late_status!='HISTORICAL_ONLY' for d in dispositions),
            relationship_dispositions=dict(Counter(r.backward_status for r in relation_states)),
            forward_usable_relationships=sum(r.forward_status=='FORWARD_USABLE' for r in relation_states),
            major_blockers=dict(Counter(reason for d in dispositions for reason in d.reason_codes)),
            late_blocker_reasons=dict(Counter(reason for d in dispositions if d.late_status=='BLOCKED' for reason in blocked[d.activity_id])),
            early_blocker_reasons=dict(Counter(reason for d in dispositions if d.es_availability=='BLOCKED' for reason in (activity_avail[d.activity_id].reason_codes if d.activity_id in activity_avail else ('early_result_unavailable',)))),
            free_float_blocker_reasons=dict(Counter(free_reasons.values())),metrics=metrics,critical_state=critical_agreement,
            controlling_path_count=len(paths),path_status=path_status,p6_option_evidence=raw_options,
            p6_equivalence_limitations=('ANCHOR_RELATIVE_NOT_GLOBAL_PROJECT_FLOAT','P6_CRITICAL_DEFINITION_NOT_CANONICALLY_IDENTIFIED','P6_LONGEST_PATH_EQUIVALENCE_NOT_ESTABLISHED'),
            dcma_critical_path_test='NOT_EVALUATED',cpli='NOT_EVALUATED')
        return SelectedAnchorAnalysis(anchor,selection.mode,tuple(sorted(scope)),tuple(dispositions),tuple(relation_states),cpm,summary,comparisons,path_status,tuple(boundaries),cpm.diagnostics)


def _trace_selected(cpm,original_graph,anchor):
    all_rows={r.activity_id:r for r in cpm.activity_results}
    ids={k for k,r in all_rows.items() if r.calculated_total_float_hours is not None}
    if anchor.activity_id not in ids:return (),(),(),'BLOCKED'
    view=replace(cpm.schedule,activities={k:cpm.schedule.activities[k] for k in sorted(ids)},
        relationships=[r for r in cpm.schedule.relationships if r.predecessor_activity_id in ids and r.successor_activity_id in ids])
    view.rebuild_activity_indexes();graph=ScheduleGraph(view)
    incoming={k:[r for r in all_rows[k].controlling_relationships if r.direction=='FORWARD' and r.predecessor_id in ids] for k in ids}
    # Eligibility ceiling affects traversal only, never published criticality/float/config.
    trace_config=replace(cpm.calculation_config,critical_float_threshold_hours=max(all_rows[k].calculated_total_float_hours for k in ids))
    result=replace(cpm,schedule=view,calculation_config=trace_config)
    path_anchor=CPMCompletionAnchor('ANALYSIS_ANCHOR',anchor.activity_id,anchor.activity_code,anchor.activity_name,required_finish=anchor.required_finish)
    config=cpm.calculation_config
    paths,stats,diags=_enumerate(result,graph,path_anchor,{k:all_rows[k] for k in ids},incoming,'CONTROLLING',
        config.maximum_critical_paths if config.maximum_critical_paths is not None else config.maximum_path_count,config.maximum_path_nodes_inspected,{})
    output=[]
    for path in paths:
        first=path.activity_ids[0]
        missing=any(r.direction=='FORWARD' and r.predecessor_id not in ids for r in all_rows[first].controlling_relationships)
        data_boundary=not incoming[first] and bool(original_graph.predecessor_relationships.get(first)) and not any(c.direction=='FORWARD' for c in all_rows[first].controlling_constraints)
        end_reason='BLOCKED_BOUNDARY' if missing else 'DATA_DATE_OR_NONCONTROLLING_BOUNDARY' if data_boundary else path.end_reason
        findings=path.diagnostics
        if missing or data_boundary:
            findings+=(CPMDiagnostic('analysis_path_boundary','Connected trace ends at an explicit historical, unavailable-float or noncontrolling boundary.',CPMFindingSeverity.INFORMATIONAL,first,metadata={'end_reason':end_reason}),)
        output.append(replace(path,path_id='AAP-'+str(path.rank).zfill(3),classification='APPLICATION_CALCULATED_CONTROLLING_PATH',
            qualification_reason='Connected calculated FORWARD controlling relationships to the explicitly selected Analysis Anchor; not P6 Longest Path.',
            trace_complete=False if missing or data_boundary else path.trace_complete,end_reason=end_reason,diagnostics=findings))
    return tuple(output),(replace(stats,classification='APPLICATION_CALCULATED_CONTROLLING_PATH'),),diags,'TRUNCATED' if stats.truncated else 'TRACED' if output else 'NO_CONTROLLING_PATHS'
