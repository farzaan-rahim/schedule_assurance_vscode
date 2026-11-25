"""Independent, auditable forward availability around the existing pass.

Unknown predecessor early dates propagate downstream, never upstream. Excluded
source logic is retained in disposition records; it is not replaced with dates.
Late/float calculation is deliberately unavailable in this opt-in mode.
"""
from collections import defaultdict, deque
from dataclasses import replace

from app.calendars.working_time import add_working_hours, is_working_time, previous_working_time
from app.cpm.activity_state import activity_decision
from app.cpm.comparison import capability_diagnostics, compare_activities
from app.cpm.forward_pass import forward_pass
from app.cpm.models import (CPMActivityCalculability, CPMActivityResult, CPMAnchor,
    CPMConstraintControl, CPMDiagnostic, CPMFindingSeverity, CPMProgressState, CPMComponentCalculability,
    CPMRelationshipCalculability, CPMRelationshipControl, CPMResult)
from app.cpm.progress import retained_requirement
from app.cpm.validation import validate_schedule, validate_pass_relationships
from app.graph.schedule_graph import ScheduleGraph
from app.importers.p6_normalization import normalize_status


def calculate_forward_scope(schedule, graph, config):
    diagnostics, _ = validate_schedule(schedule, graph, config)
    from app.cpm.calculability import _components
    original_components, component_for = _components(schedule, graph)
    blocked, excluded, states = defaultdict(set), set(), {}
    blocking_predecessors = defaultdict(set)
    boundary_unknown = defaultdict(set)
    global_errors = []
    relationships = {r.relationship_id: r for r in schedule.relationships}
    anchor = max((t for t in (config.project_start_override, schedule.project.data_date if schedule.project else None) if t is not None), default=None)
    data_date = schedule.project.data_date if schedule.project and schedule.project.data_date else anchor
    options = schedule.scheduling_options

    def complete(key):
        a = schedule.activities[key]
        return normalize_status(a.raw_status or a.status) == 'complete'

    def issue(code, message, activity_id=None, relationship_id=None, severity=CPMFindingSeverity.ERROR, **metadata):
        diagnostics.append(CPMDiagnostic(code, message, severity, activity_id, relationship_id, metadata))

    for d in diagnostics:
        if d.severity != CPMFindingSeverity.ERROR or d.code == 'circular_logic':
            continue
        if d.activity_id in schedule.activities:
            blocked[d.activity_id].add(d.code)
        elif d.relationship_id in relationships:
            r = relationships[d.relationship_id]
            if r.successor_activity_id in schedule.activities and not complete(r.successor_activity_id):
                blocked[r.successor_activity_id].add(d.code)
        else:
            global_errors.append(d.code)
    if not global_errors:
        for a in schedule.activities.values():
            state, _, disposition = activity_decision(a, config, data_date)
            if disposition == 'EXCLUDE' or (a.calendar_id not in schedule.calendars and config.missing_calendar_policy == 'EXCLUDE'):
                excluded.add(a.activity_id)
            elif state:
                states[a.activity_id] = state
            if a.activity_id not in excluded and not complete(a.activity_id):
                if state and state[1] != 'MILESTONE' and (a.remaining_duration_hours is None or not config.remaining_duration_preference):
                    blocked[a.activity_id].add('unsupported_retained_duration_policy')
                    issue('unsupported_retained_duration_policy', 'Retained remaining work requires imported remaining duration, not original-duration preference/fallback.', a.activity_id)
                if a.expected_finish is not None and (options is None or options.use_expected_finish is not False):
                    blocked[a.activity_id].add('expected_finish_unimplemented')
                    issue('expected_finish_unimplemented', 'Enabled or unknown Expected Finish semantics are not substituted with imported EF or duration.', a.activity_id)
                if a.suspend_date or a.resume_date:
                    blocked[a.activity_id].add('suspended_work_unimplemented')
                    issue('suspended_work_unimplemented', 'Suspend/resume scheduling is not implemented.', a.activity_id)
        if (config.progress_scheduling_policy != 'P6_RETAINED_LOGIC' or options is None
                or options.project_id != (schedule.project.project_id if schedule.project else None)
                or options.retained_logic is not True or options.progress_override is not False):
            for key in states:
                if not complete(key):
                    blocked[key].add('unsupported_p6_progress_options')
            issue('unsupported_p6_progress_options', 'Explicit typed Retained Logic=Y / Progress Override=N and P6_RETAINED_LOGIC policy are required; no alternative mode is guessed.')
        for r in schedule.relationships:
            p = schedule.activities.get(r.predecessor_activity_id)
            q = schedule.activities.get(r.successor_activity_id)
            if not p or not q or complete(q.activity_id):
                continue
            pstatus = normalize_status(p.raw_status or p.status)
            reason = None
            if isinstance(r.lag_hours, (float, int)) and r.lag_hours != 0 and (options is None or options.lag_calendar_policy != config.lag_calendar_policy):
                reason = 'unsupported_p6_lag_calendar'
            if pstatus == 'in_progress':
                if r.relationship_type.upper() == 'SS' and (not isinstance(r.lag_hours, (float, int)) or r.lag_hours < 0 or options is None or options.ss_lag_from_early_start is not True):
                    reason = 'unsupported_progressed_ss_lag'
                if r.relationship_type.upper() == 'SF':
                    reason = 'unsupported_progressed_sf'
            if reason:
                blocked[q.activity_id].add(reason)
                issue(reason, 'Relationship progress option is outside the implemented subset.', q.activity_id, r.relationship_id)
    else:
        for key in schedule.activities:
            blocked[key].update(global_errors)

    # A completed actual span does not establish a retained future release
    # through an unfinished FS/FF endpoint. No imported proxy is substituted.
    for r in schedule.relationships:
        if (r.predecessor_activity_id in schedule.activities and r.successor_activity_id in schedule.activities
                and complete(r.successor_activity_id) and not complete(r.predecessor_activity_id)
                and r.successor_activity_id not in excluded and r.relationship_type.upper() in {'FS', 'FF'}):
            boundary_unknown[r.successor_activity_id].add('completed_retained_boundary_unimplemented')
            blocking_predecessors[r.successor_activity_id].add(r.predecessor_activity_id)

    def propagate():
        queue = deque(sorted(set(blocked) | excluded | set(boundary_unknown)))
        visited = set(queue)
        while queue:
            key = queue.popleft()
            for r in graph.successor_relationships.get(key, ()):
                target = r.successor_activity_id
                if target not in schedule.activities or target in excluded:
                    continue
                if complete(target):
                    boundary_unknown[target].add('completed_retained_boundary_unimplemented')
                else:
                    blocked[target].add('blocked_retained_boundary' if key in boundary_unknown else 'blocked_early_predecessor')
                blocking_predecessors[target].add(key)
                if target not in visited:
                    visited.add(target)
                    queue.append(target)

    propagate()

    def view():
        ids = {k for k in states if k not in blocked and k not in excluded}
        current = replace(schedule, activities={k: a for k, a in schedule.activities.items() if k in ids},
            relationships=[r for r in schedule.relationships if r.predecessor_activity_id in ids and r.successor_activity_id in ids and not complete(r.successor_activity_id)])
        current.rebuild_activity_indexes()
        return current, ScheduleGraph(current)

    current, current_graph = view()
    for a in current_graph.topological_sort().unresolved_activities:
        blocked[a.activity_id].add('forward_cycle')
        issue('forward_cycle', 'Cycle prevents remaining-work forward calculation.', a.activity_id)
    if any('forward_cycle' in v for v in blocked.values()):
        propagate()
        current, current_graph = view()
    decisions = {}

    def requirement(r, p, q, pcal, qcal, lag):
        d = retained_requirement(r, p, q, pcal, qcal, lag,
            source_predecessor=schedule.activities[r.predecessor_activity_id],
            source_successor=schedule.activities[r.successor_activity_id], data_date=data_date, options=options)
        decisions[r.relationship_id] = d
        return d.timestamp

    forward = None
    if current.activities:
        try:
            forward = forward_pass(current, current_graph, config,
                {k: states[k] for k in current.activities}, current.calendars,
                relationship_requirement=requirement)
        except (ValueError, OverflowError, IndexError, TypeError) as exc:
            issue('forward_calendar_arithmetic_error', str(exc))
            for key in current.activities:
                blocked[key].add('forward_calendar_arithmetic_error')
        if forward:
            # Retain the original raw endpoint audit for all unchanged requirements.
            unchanged = replace(current, relationships=[r for r in current.relationships if decisions[r.relationship_id].basis != 'P6_SS_EARLY_START_EXPIRED_LAG'])
            findings = validate_pass_relationships(unchanged, forward['early_starts'], forward['early_finishes'], 'forward')
            for r in current.relationships:
                if forward['early_starts'][r.successor_activity_id] < decisions[r.relationship_id].timestamp:
                    findings.append(CPMDiagnostic('progress_requirement_failed', 'Remaining-start requirement was violated.', CPMFindingSeverity.ERROR, relationship_id=r.relationship_id))
            findings.extend(_early_invariants(current, states, forward))
            diagnostics.extend(findings)
            for d in findings:
                key = d.activity_id or relationships[d.relationship_id].successor_activity_id
                blocked[key].add(d.code)
            propagate()
    valid = {k for k in current.activities if k not in blocked} if forward else set()
    for key in sorted(boundary_unknown):
        issue('completed_retained_boundary_unimplemented', 'Historical actuals remain available; prospective retained release through this completed chain is unimplemented.', key, severity=CPMFindingSeverity.WARNING, source_ids=tuple(sorted(blocking_predecessors[key])))
    by_activity_diagnostics = defaultdict(list)
    for d in diagnostics:
        if d.activity_id:
            by_activity_diagnostics[d.activity_id].append(d)
    results = []
    for key in sorted(valid):
        a, state = schedule.activities[key], states[key]
        controls = forward['controlling'][key]
        control_rows = tuple(CPMRelationshipControl(r.relationship_id, r.predecessor_activity_id,
            schedule.activities[r.predecessor_activity_id].activity_code, key, a.activity_code,
            r.relationship_type, r.lag_hours, config.lag_calendar_policy,
            schedule.activities[r.predecessor_activity_id].calendar_id, 'FORWARD', 'EARLY_START',
            controls['requirements'][r.relationship_id], len(controls['relationships']) > 1,
            qualification_reason=decisions[r.relationship_id].basis)
            for r in current_graph.predecessor_relationships[key] if r.relationship_id in controls['relationships'])
        results.append(CPMActivityResult(
            activity_id=key, activity_code=a.activity_code, activity_name=a.activity_name,
            effective_duration_hours=state[0], effective_calendar_id=a.calendar_id,
            calculated_early_start=forward['early_starts'][key], calculated_early_finish=forward['early_finishes'][key],
            calculated_late_start=None, calculated_late_finish=None, calculated_total_float_hours=None,
            calculated_free_float_hours=None, calculated_critical=False, calculated_near_critical=False,
            imported_early_start=a.early_start, imported_early_finish=a.early_finish,
            imported_late_start=a.late_start, imported_late_finish=a.late_finish,
            imported_total_float_hours=a.total_float_hours, imported_free_float_hours=a.free_float_hours,
            imported_actual_start=a.actual_start, imported_actual_finish=a.actual_finish,
            imported_critical=(a.total_float_hours <= config.critical_float_threshold_hours) if a.total_float_hours is not None else None,
            controlling_predecessor_ids=tuple(controls['predecessors']), controlling_relationship_ids=tuple(controls['relationships']),
            controlling_relationships=control_rows, controlling_constraint=controls['constraint'],
            controlling_constraints=tuple(CPMConstraintControl(kind, stamp, 'FORWARD', req, bool(controls['relationships'])) for kind, stamp, req in controls['constraints']),
            applied_constraints=tuple(k for k in (a.primary_constraint_type, a.secondary_constraint_type) if k in {'START_ON_OR_AFTER', 'FINISH_ON_OR_AFTER'} and state[1] != 'COMPLETE'),
            diagnostics=tuple(by_activity_diagnostics[key]), effective_state=state[1],
            date_basis='PRESERVED_ACTUALS' if state[1] == 'COMPLETE' else 'REMAINING_WORK',
            early_date_status='EARLY_DATES_CALCULATED', late_date_status='LATE_DATES_BLOCKED', float_status='FLOAT_BLOCKED',
            progress_state=CPMProgressState(a.actual_start, a.actual_finish, data_date,
                a.actual_finish if state[1] == 'COMPLETE' else (data_date if a.actual_start else None),
                a.remaining_start, a.remaining_finish, a.remaining_duration_hours),
        ))
    activity_states = tuple(CPMActivityCalculability(k, component_for[k],
        'EXCLUDED' if k in excluded else ('PARTIALLY_CALCULATED' if k in valid else 'BLOCKED'),
        tuple(sorted(set(blocked.get(k, ())) | set(boundary_unknown.get(k, ())))) if k not in excluded else tuple(d.code for d in by_activity_diagnostics[k]),
        early_date_status='EXCLUDED' if k in excluded else ('EARLY_DATES_CALCULATED' if k in valid else 'EARLY_DATES_BLOCKED'),
        late_date_status='LATE_DATES_BLOCKED', float_status='FLOAT_BLOCKED',
        blocking_predecessor_ids=tuple(sorted(blocking_predecessors[k])),
        forward_boundary_status='FORWARD_BOUNDARY_BLOCKED' if k in boundary_unknown or k not in valid else 'FORWARD_BOUNDARY_CALCULATED',
    ) for k in sorted(schedule.activities))
    relation_states = []
    for r in sorted(schedule.relationships, key=lambda r: r.relationship_id):
        if r.successor_activity_id in valid and complete(r.successor_activity_id):
            status = 'HISTORICAL_ONLY'
        elif r.successor_activity_id in excluded:
            status = 'FORWARD_EXCLUDED_TARGET'
        elif r.predecessor_activity_id in valid and r.successor_activity_id in valid:
            status = 'FORWARD_USABLE'
        else:
            status = 'FORWARD_BLOCKED'
        d = decisions.get(r.relationship_id)
        relation_states.append(CPMRelationshipCalculability(r.relationship_id, status,
            () if status == 'FORWARD_USABLE' else (status.lower(),),
            forward_status=status, backward_status='BACKWARD_BLOCKED',
            forward_requirement_timestamp=d.timestamp if d and status == 'FORWARD_USABLE' else None,
            expired_lag_hours=d.expired_lag_hours if d else None, remaining_lag_hours=d.remaining_lag_hours if d else None))
    component_relationships = defaultdict(int)
    for r in schedule.relationships:
        component = component_for.get(r.predecessor_activity_id, component_for.get(r.successor_activity_id))
        component_relationships[component] += 1
    component_states = tuple(CPMComponentCalculability(
        component, len(members), component_relationships[component],
        'PARTIALLY_CALCULATED' if any(k in valid for k in members) else ('BLOCKED' if any(k not in excluded for k in members) else 'EXCLUDED'),
        tuple(sorted({'late_and_float_not_evaluated'} | {reason for k in members for reason in set(blocked.get(k, ())) | set(boundary_unknown.get(k, ()))})),
        tuple(k for k in members if boundary_unknown.get(k) or (set(blocked.get(k, ())) - {'blocked_early_predecessor', 'blocked_retained_boundary'}) or (k in excluded and any(r.successor_activity_id in schedule.activities and not complete(r.successor_activity_id) for r in graph.successor_relationships[k]))),
    ) for component, members in original_components.items())
    # Compare only reliable remaining-work ES/EF, with exact raw variances.
    remaining = [a for a in results if a.date_basis == 'REMAINING_WORK']
    comparison_schedule = replace(schedule, activities={a.activity_id: schedule.activities[a.activity_id] for a in remaining})
    comparison_schedule.rebuild_activity_indexes()
    comparisons, _ = compare_activities(comparison_schedule, remaining, config)
    comparisons = tuple(replace(c, metrics=tuple(m for m in c.metrics if m.name in {'early_start', 'early_finish'})) for c in comparisons)
    issue('late_and_float_not_evaluated', 'Forward-only scope has no late/float/path or contractual completion result.', severity=CPMFindingSeverity.INFORMATIONAL)
    return CPMResult(status='PARTIALLY_CALCULATED' if results else ('BLOCKED' if blocked or global_errors else 'EXCLUDED'),
        config_version=config.version, schedule=schedule, eligible_activity_count=len(valid), excluded_activity_count=len(excluded),
        relationship_count=len(schedule.relationships), external_relationship_count=sum(r.predecessor_activity_id not in schedule.activities or r.successor_activity_id not in schedule.activities for r in schedule.relationships),
        project_start_anchor=CPMAnchor(anchor, 'DATA_DATE_FORWARD_ONLY', ()) if anchor else None,
        project_finish_anchor=None, calculated_completion=None, critical_activity_count=0, near_critical_activity_count=0,
        activity_results=tuple(results), comparisons=comparisons, controlling_relationship_ids=tuple(sorted({r for a in results for r in a.controlling_relationship_ids})),
        critical_paths=(), near_critical_paths=(), diagnostics=tuple(diagnostics),
        truncation={'activity_results_returned': len(results), 'activity_results_truncated': False},
        calculation_config=config, anchor_selection_status='NOT_EVALUATED_FORWARD_ONLY', path_status='NOT_EVALUATED',
        activity_calculability=activity_states, relationship_calculability=tuple(relation_states), components=component_states,
        blocked_activity_count=len(schedule.activities) - len(excluded) - len(valid), partially_calculated_activity_count=len(valid),
        reliability_scope='DIRECTIONAL_FORWARD', comparison_diagnostics=capability_diagnostics(schedule, config))


def _early_invariants(schedule, states, forward):
    findings = []
    for key, a in schedule.activities.items():
        es, ef = forward['early_starts'][key], forward['early_finishes'][key]
        duration, state = states[key]
        cal = schedule.calendars[a.calendar_id]
        if state == 'COMPLETE':
            valid = (es, ef) == (a.actual_start, a.actual_finish)
        else:
            valid = es >= forward['anchor'] and ef == add_working_hours(cal, es, duration)
            if duration:
                valid = valid and is_working_time(cal, es) and (is_working_time(cal, ef) or previous_working_time(cal, ef) == ef)
            for kind, stamp in ((a.primary_constraint_type, a.primary_constraint_date), (a.secondary_constraint_type, a.secondary_constraint_date)):
                if kind == 'START_ON_OR_AFTER':
                    valid = valid and es >= stamp
                if kind == 'FINISH_ON_OR_AFTER':
                    valid = valid and ef >= stamp
        if not valid:
            findings.append(CPMDiagnostic('early_date_invariant_failed', 'Early duration/calendar/history/constraint invariant failed.', CPMFindingSeverity.ERROR, activity_id=key))
    return findings
