from __future__ import annotations

from dataclasses import replace

from app.cpm.activity_state import activity_decision
from app.graph.schedule_graph import ScheduleGraph
from app.cpm.backward_pass import backward_pass
from app.cpm.config import CPMConfig
from app.cpm.criticality import classify_criticality
from app.cpm.float_calculation import free_float_details, total_float
from app.cpm.forward_pass import forward_pass
from app.cpm.models import CPMActivityResult, CPMAnchor, CPMDiagnostic, CPMFindingSeverity, CPMResult, CPMRelationshipControl, CPMConstraintControl
from app.cpm.validation import validate_date_invariants, validate_pass_relationships, validate_schedule


class CPMService:
    def calculate(self, schedule, graph, config: CPMConfig | None = None) -> CPMResult:
        config = config or CPMConfig()
        if config.component_calculation_policy == "DIRECTIONAL_FORWARD":
            from app.cpm.directional import calculate_forward_scope
            return calculate_forward_scope(schedule, graph, config)
        if config.component_calculation_policy == "VALID_COMPONENTS":
            from app.cpm.calculability import calculate_valid_components
            return calculate_valid_components(self, schedule, graph, config)
        diagnostics, fatal = validate_schedule(schedule, graph, config)

        input_schedule = schedule
        if fatal:
            return _failed_calculation(schedule, config, diagnostics)
        anchor = (schedule.project.data_date if schedule.project else None) or config.project_start_override
        effective_states = {}
        for activity in schedule.activities.values():
            state, _, disposition = activity_decision(activity, config, anchor)
            if disposition == "INCLUDE" and activity.calendar_id in schedule.calendars:
                effective_states[activity.activity_id] = state
        eligible_count = len(effective_states)
        excluded_count = len(schedule.activities) - eligible_count
        if excluded_count:
            incident = [r for r in schedule.relationships if r.predecessor_activity_id not in effective_states or r.successor_activity_id not in effective_states]
            if incident or not effective_states:
                diagnostics.append(CPMDiagnostic("excluded_relationship_endpoint" if incident else "no_eligible_activities", "Excluded activities cannot be silently bypassed in schedule logic.", CPMFindingSeverity.ERROR))
                return _failed_calculation(schedule, config, diagnostics, excluded_count)
            schedule = replace(schedule, activities={a.activity_id:a for a in schedule.activities.values() if a.activity_id in effective_states})
            schedule.rebuild_activity_indexes()
            graph = ScheduleGraph(schedule)

        # Both passes resolve by calendar_id, never by activity_id.
        try:
            forward = forward_pass(schedule, graph, config, effective_states, schedule.calendars)
        except (ValueError, OverflowError) as exc:
            diagnostics.append(CPMDiagnostic("calendar_arithmetic_error", str(exc), CPMFindingSeverity.ERROR))
            return _failed_calculation(input_schedule, config, diagnostics, excluded_count)

        boundary_findings = validate_pass_relationships(
            schedule, forward["early_starts"], forward["early_finishes"], "forward",
        )
        if boundary_findings:
            return _failed_calculation(input_schedule, config, diagnostics + boundary_findings, excluded_count)

        terminal_ids = tuple(activity.activity_id for activity in graph.get_finish_activities())
        if config.required_project_finish:
            finish_anchor = CPMAnchor(config.required_project_finish, "CONFIGURED_REQUIRED_PROJECT_FINISH", terminal_ids)
        else:
            latest_finish = max(forward["early_finishes"].values())
            finish_anchor = CPMAnchor(latest_finish, "LATEST_CALCULATED_EARLY_FINISH", terminal_ids)

        component_finishes = _component_finish_anchors(schedule, graph, forward, finish_anchor, config)
        try:
            backward = backward_pass(
                schedule, graph, config, effective_states,
                schedule.calendars,
                forward,
                finish_anchor,
                component_finishes,
            )
        except (ValueError, OverflowError) as exc:
            diagnostics.append(CPMDiagnostic("calendar_arithmetic_error", str(exc), CPMFindingSeverity.ERROR))
            return _failed_calculation(input_schedule, config, diagnostics, excluded_count)

        boundary_findings = validate_pass_relationships(
            schedule, backward["late_starts"], backward["late_finishes"], "backward",
        )
        if boundary_findings:
            return _failed_calculation(input_schedule, config, diagnostics + boundary_findings, excluded_count)

        invariant_findings = validate_date_invariants(schedule, effective_states, forward, backward)
        if invariant_findings:
            return _failed_calculation(input_schedule, config, diagnostics + invariant_findings, excluded_count)

        activity_results = []
        controlling_ids = []

        for activity in schedule.activities.values():
            activity_id = activity.activity_id
            calendar = schedule.calendars.get(activity.calendar_id)
            es = forward["early_starts"][activity_id]
            ef = forward["early_finishes"][activity_id]
            ls = backward["late_starts"][activity_id]
            lf = backward["late_finishes"][activity_id]

            if effective_states[activity_id][1] == "COMPLETE":
                tf, tf_finish, ff = None, None, None
                ff_details = ()
                diagnostics.append(CPMDiagnostic("completed_float_not_applicable", "Remaining-work float is not applicable to completed actuals.", CPMFindingSeverity.INFORMATIONAL, activity_id=activity_id))
            else:
                tf, tf_finish = total_float(calendar, es, ls, ef, lf)
                ff, ff_details, ff_reason = free_float_details(schedule, graph, calendar, activity_id, forward["early_starts"], forward["early_finishes"], config.lag_calendar_policy)
                if ff_reason:
                    diagnostics.append(CPMDiagnostic(ff_reason, "No reliable successor-based free float; value is None.", CPMFindingSeverity.INFORMATIONAL, activity_id=activity_id))
            critical, near = classify_criticality(tf, config.critical_float_threshold_hours, config.near_critical_float_threshold_hours)

            forward_control = forward["controlling"][activity_id]
            backward_control = backward["controlling"][activity_id]
            controlling_ids.extend(forward_control["relationships"])
            controlling_ids.extend(backward_control["relationships"])

            imported_critical = (activity.total_float_hours <= config.critical_float_threshold_hours) if activity.total_float_hours is not None else None
            disagreement = (critical != imported_critical) if tf is not None and imported_critical is not None else None
            if tf_finish is not None and tf is not None and tf_finish != tf:
                diagnostics.append(CPMDiagnostic(
                    "float_methods_disagree", "Start-based and finish-based float methods differ.",
                    CPMFindingSeverity.WARNING,
                    activity_id=activity_id,
                    metadata={"start_based_float": tf, "finish_based_float": tf_finish},
                ))

            applied = tuple(
                constraint for constraint in (
                    activity.primary_constraint_type,
                    activity.secondary_constraint_type,
                ) if constraint
            )

            result = CPMActivityResult(
                activity_id=activity_id,
                activity_code=activity.activity_code,
                activity_name=activity.activity_name,
                effective_duration_hours=effective_states[activity_id][0],
                effective_calendar_id=activity.calendar_id,
                calculated_early_start=es,
                calculated_early_finish=ef,
                calculated_late_start=ls,
                calculated_late_finish=lf,
                calculated_total_float_hours=tf,
                calculated_free_float_hours=ff,
                calculated_critical=critical,
                calculated_near_critical=near,
                imported_early_start=activity.early_start,
                imported_early_finish=activity.early_finish,
                imported_late_start=activity.late_start,
                imported_late_finish=activity.late_finish,
                imported_total_float_hours=activity.total_float_hours,
                imported_free_float_hours=activity.free_float_hours,
                controlling_predecessor_ids=tuple(forward_control["predecessors"]),
                controlling_successor_ids=tuple(backward_control["successors"]),
                controlling_relationship_ids=tuple(sorted(set(forward_control["relationships"] + backward_control["relationships"]))),
                controlling_constraint=forward_control["constraint"] or backward_control["constraint"],
                applied_constraints=applied,
                controlling_relationships=_relationship_controls(schedule, config, forward_control, backward_control),
                controlling_constraints=tuple(
                    CPMConstraintControl(kind, stamp, direction, requirement, bool(control["relationships"]))
                    for direction, control in (("FORWARD", forward_control), ("BACKWARD", backward_control))
                    for kind, stamp, requirement in control["constraints"]
                ),
                diagnostics=tuple(d for d in diagnostics if d.activity_id == activity_id),
                calculated_start_float_hours=tf,
                calculated_finish_float_hours=tf_finish,
                relationship_free_float_hours=ff_details,
                imported_critical=imported_critical,
                critical_disagreement=disagreement,
                effective_state=effective_states[activity_id][1],
                date_basis="PRESERVED_ACTUALS" if effective_states[activity_id][1] == "COMPLETE" else "REMAINING_WORK",
                effective_finish_anchor=component_finishes[activity_id],
                imported_actual_start=activity.actual_start,
                imported_actual_finish=activity.actual_finish,
            )
            activity_results.append(result)

        critical_count = sum(result.calculated_critical for result in activity_results)
        near_count = sum(result.calculated_near_critical for result in activity_results)

        start_anchor = CPMAnchor(
            forward["anchor"], forward["anchor_source"],
            tuple(activity.activity_id for activity in graph.get_start_activities()),
        )

        result = CPMResult(
            status="CALCULATED",
            calculation_config=config,
            config_version=config.version,
            schedule=input_schedule,
            eligible_activity_count=eligible_count,
            excluded_activity_count=excluded_count,
            relationship_count=len(schedule.relationships),
            external_relationship_count=sum(
                r.predecessor_activity_id not in schedule.activities_by_id
                or r.successor_activity_id not in schedule.activities_by_id
                for r in schedule.relationships
            ),
            project_start_anchor=start_anchor,
            project_finish_anchor=finish_anchor,
            calculated_completion=max(forward["early_finishes"].values()),
            critical_activity_count=critical_count,
            near_critical_activity_count=near_count,
            activity_results=tuple(activity_results),
            comparisons=(),
            controlling_relationship_ids=tuple(sorted(set(controlling_ids))),
            critical_paths=(),
            near_critical_paths=(),
            diagnostics=tuple(diagnostics),
            truncation={"activity_results_returned": len(activity_results), "activity_results_truncated": False},
        )
        from app.cpm.post_calculation import finalize_result
        return finalize_result(result, graph)



def _failed_calculation(schedule, config, diagnostics, excluded_count=0):
    result = CPMResult(
        status="FAILED", calculation_config=config, config_version=config.version, schedule=schedule,
        eligible_activity_count=len(schedule.activities) - excluded_count, excluded_activity_count=excluded_count,
        relationship_count=len(schedule.relationships), external_relationship_count=0,
        project_start_anchor=None, project_finish_anchor=None, calculated_completion=None,
        critical_activity_count=0, near_critical_activity_count=0,
        activity_results=(), comparisons=(), controlling_relationship_ids=(),
        critical_paths=(), near_critical_paths=(), diagnostics=tuple(diagnostics),
        truncation={"activity_results_returned": 0, "activity_results_truncated": False},
    )

    from app.cpm.post_calculation import finalize_result
    return finalize_result(result, None)


def _component_finish_anchors(schedule, graph, forward, project_finish, config):
    if config.required_project_finish or config.disconnected_component_policy == "PROJECT_FINISH":
        return {key: project_finish.timestamp for key in schedule.activities_by_id}
    from collections import deque
    remaining = set(schedule.activities_by_id)
    anchors = {}
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        queue, component = deque([seed]), []
        while queue:
            current = queue.popleft()
            component.append(current)
            neighbors = [r.predecessor_activity_id for r in graph.predecessor_relationships[current]]
            neighbors += [r.successor_activity_id for r in graph.successor_relationships[current]]
            for neighbor in neighbors:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        finish = max(forward["early_finishes"][key] for key in component)
        anchors.update({key: finish for key in component})
    return anchors


def _relationship_controls(schedule, config, forward_control, backward_control):
    records = []
    by_id = {r.relationship_id:r for r in schedule.relationships}
    for direction, control, requirement_kind in (("FORWARD", forward_control, "EARLY_START"), ("BACKWARD", backward_control, "LATE_FINISH")):
        for relationship_id in control["relationships"]:
            r = by_id[relationship_id]
            pre, suc = schedule.activities_by_id[r.predecessor_activity_id], schedule.activities_by_id[r.successor_activity_id]
            records.append(CPMRelationshipControl(r.relationship_id, pre.activity_id, pre.activity_code,
                suc.activity_id, suc.activity_code, r.relationship_type.upper(), float(r.lag_hours),
                config.lag_calendar_policy, pre.calendar_id, direction, requirement_kind,
                control["requirements"][relationship_id], len(control["relationships"]) > 1))
    return tuple(records)
