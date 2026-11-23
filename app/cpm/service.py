from __future__ import annotations

from app.cpm.activity_state import effective_duration
from app.cpm.backward_pass import backward_pass
from app.cpm.config import CPMConfig
from app.cpm.criticality import classify_criticality
from app.cpm.float_calculation import free_float, total_float
from app.cpm.forward_pass import forward_pass
from app.cpm.models import CPMActivityComparison, CPMActivityResult, CPMAnchor, CPMDiagnostic, CPMFindingSeverity, CPMResult
from app.cpm.validation import validate_schedule
from app.calendars.working_time import working_hours_between


class CPMService:
    def calculate(self, schedule, graph, config: CPMConfig | None = None) -> CPMResult:
        config = config or CPMConfig()
        diagnostics, fatal = validate_schedule(schedule, graph, config)

        if fatal:
            return CPMResult(
                status="FAILED",
                config_version=config.version,
                schedule=schedule,
                eligible_activity_count=len(schedule.activities),
                excluded_activity_count=0,
                relationship_count=len(schedule.relationships),
                external_relationship_count=sum(
                    r.predecessor_activity_id not in schedule.activities_by_id
                    or r.successor_activity_id not in schedule.activities_by_id
                    for r in schedule.relationships
                ),
                project_start_anchor=None,
                project_finish_anchor=None,
                calculated_completion=None,
                critical_activity_count=0,
                near_critical_activity_count=0,
                activity_results=(),
                comparisons=(),
                controlling_relationship_ids=(),
                critical_paths=(),
                near_critical_paths=(),
                diagnostics=tuple(diagnostics),
                truncation={"activity_results_returned": 0, "activity_results_truncated": False},
            )

        effective_states: dict[str, tuple[float, str]] = {}
        calendars = {}
        eligible_count = 0
        for activity in schedule.activities.values():
            try:
                duration, state = effective_duration(activity, config)
            except ValueError as exc:
                diagnostics.append(CPMDiagnostic(
                    "unsupported_activity_state", str(exc), CPMFindingSeverity.WARNING,
                    activity_id=activity.activity_id,
                ))
                continue

            calendar = schedule.calendars.get(activity.calendar_id) if activity.calendar_id else None
            if calendar is None:
                diagnostics.append(CPMDiagnostic(
                    "missing_activity_calendar", "No calendar was available for CPM arithmetic.",
                    CPMFindingSeverity.ERROR,
                    activity_id=activity.activity_id,
                ))
                continue

            effective_states[activity.activity_id] = (duration, state)
            calendars[activity.activity_id] = calendar
            eligible_count += 1

        if len(effective_states) != len(schedule.activities):
            return CPMResult(
                status="FAILED", config_version=config.version, schedule=schedule,
                eligible_activity_count=eligible_count,
                excluded_activity_count=len(schedule.activities) - eligible_count,
                relationship_count=len(schedule.relationships),
                external_relationship_count=0,
                project_start_anchor=None, project_finish_anchor=None,
                calculated_completion=None, critical_activity_count=0,
                near_critical_activity_count=0, activity_results=(), comparisons=(),
                controlling_relationship_ids=(), critical_paths=(), near_critical_paths=(),
                diagnostics=tuple(diagnostics), truncation={"activity_results_returned": 0, "activity_results_truncated": False},
            )

        forward = forward_pass(schedule, graph, config, effective_states, schedule.calendars)

        terminal_ids = tuple(activity.activity_id for activity in graph.get_finish_activities())
        if config.required_project_finish:
            finish_anchor = CPMAnchor(config.required_project_finish, "CONFIGURED_REQUIRED_PROJECT_FINISH", terminal_ids)
        else:
            latest_finish = max(forward["early_finishes"].values())
            finish_anchor = CPMAnchor(latest_finish, "LATEST_CALCULATED_EARLY_FINISH", terminal_ids)

        backward = backward_pass(
            schedule, graph, config, effective_states,
            schedule.calendars,
            forward,
            finish_anchor,
        )

        activity_results = []
        comparisons = []
        controlling_ids = []

        for activity in schedule.activities.values():
            activity_id = activity.activity_id
            calendar = schedule.calendars.get(activity.calendar_id)
            es = forward["early_starts"][activity_id]
            ef = forward["early_finishes"][activity_id]
            ls = backward["late_starts"][activity_id]
            lf = backward["late_finishes"][activity_id]

            tf, tf_finish = total_float(calendar, es, ls, ef, lf)
            ff = free_float(schedule, graph, calendar, activity_id, forward["early_starts"], forward["early_finishes"])
            critical, near = classify_criticality(tf, config.critical_float_threshold_hours, config.near_critical_float_threshold_hours)

            forward_control = forward["controlling"][activity_id]
            backward_control = backward["controlling"][activity_id]
            controlling_ids.extend(forward_control["relationships"])
            controlling_ids.extend(backward_control["relationships"])

            if tf_finish is not None and tf is not None and abs(tf_finish - tf) > 1e-7:
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
                imported_early_start=activity.planned_start,
                imported_early_finish=activity.planned_finish,
                imported_late_start=None,
                imported_late_finish=None,
                imported_total_float_hours=activity.total_float_hours,
                imported_free_float_hours=activity.free_float_hours,
                controlling_predecessor_ids=tuple(forward_control["predecessors"]),
                controlling_successor_ids=tuple(backward_control["successors"]),
                controlling_relationship_ids=tuple(set(forward_control["relationships"] + backward_control["relationships"])),
                controlling_constraint=forward_control["constraint"] or backward_control["constraint"],
                applied_constraints=applied,
            )
            activity_results.append(result)

            def elapsed(current, imported):
                if current is None or imported is None:
                    return None
                return working_hours_between(calendar, imported, current) if calendar else None

            comparisons.append(CPMActivityComparison(
                activity_id=activity_id,
                activity_code=activity.activity_code,
                early_start_variance_hours=elapsed(es, activity.planned_start),
                early_finish_variance_hours=elapsed(ef, activity.planned_finish),
                late_start_variance_hours=None,
                late_finish_variance_hours=None,
                total_float_variance_hours=(tf - activity.total_float_hours) if tf is not None and activity.total_float_hours is not None else None,
                free_float_variance_hours=(ff - activity.free_float_hours) if ff is not None and activity.free_float_hours is not None else None,
                critical_disagreement=(critical != (activity.total_float_hours is not None and activity.total_float_hours <= config.critical_float_threshold_hours)),
            ))

        critical_count = sum(result.calculated_critical for result in activity_results)
        near_count = sum(result.calculated_near_critical for result in activity_results)

        start_anchor = CPMAnchor(
            forward["anchor"], forward["anchor_source"],
            tuple(activity.activity_id for activity in graph.get_start_activities()),
        )

        return CPMResult(
            status="CALCULATED",
            config_version=config.version,
            schedule=schedule,
            eligible_activity_count=eligible_count,
            excluded_activity_count=len(schedule.activities) - eligible_count,
            relationship_count=len(schedule.relationships),
            external_relationship_count=sum(
                r.predecessor_activity_id not in schedule.activities_by_id
                or r.successor_activity_id not in schedule.activities_by_id
                for r in schedule.relationships
            ),
            project_start_anchor=start_anchor,
            project_finish_anchor=finish_anchor,
            calculated_completion=finish_anchor.timestamp,
            critical_activity_count=critical_count,
            near_critical_activity_count=near_count,
            activity_results=tuple(activity_results),
            comparisons=tuple(comparisons),
            controlling_relationship_ids=tuple(sorted(set(controlling_ids))),
            critical_paths=(),
            near_critical_paths=(),
            diagnostics=tuple(diagnostics),
            truncation={"activity_results_returned": len(activity_results), "activity_results_truncated": False},
        )
