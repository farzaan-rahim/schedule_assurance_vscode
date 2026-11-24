from __future__ import annotations

from datetime import datetime

from app.cpm.config import CPMConfig
from app.cpm.models import CPMDiagnostic, CPMFindingSeverity
from app.importers.p6_normalization import normalize_status


def validate_schedule(schedule, graph, config: CPMConfig):
    from math import isfinite
    from app.cpm.activity_state import activity_decision
    from app.calendars.working_time import next_working_time
    diagnostics = []
    def error(code, message, **kwargs):
        diagnostics.append(CPMDiagnostic(code, message, CPMFindingSeverity.ERROR, **kwargs))
    options = {
        "lag_calendar_policy": {"PREDECESSOR"},
        "missing_calendar_policy": {"ERROR", "EXCLUDE"},
        "missing_duration_policy": {"ERROR", "EXCLUDE"},
        "invalid_activity_policy": {"ERROR", "EXCLUDE"},
        "loe_policy": {"ERROR", "EXCLUDE"},
        "duration_fallback_policy": {"ORIGINAL_WITH_WARNING", "ERROR"},
        "completed_remaining_duration_policy": {"ZERO_WITH_WARNING", "ERROR"},
        "milestone_duration_policy": {"ZERO_WITH_WARNING", "ERROR"},
        "zero_duration_task_policy": {"ALLOW", "ERROR"},
        "completed_activity_treatment": {"PRESERVE_ACTUALS"},
        "in_progress_activity_treatment": {"REMAINING_FROM_DATA_DATE"},
        "disconnected_component_policy": {"INDEPENDENT_ANCHOR", "PROJECT_FINISH"},
        "constraint_handling_policy": {"SUPPORTED_ONLY"},
    }
    for name, values in options.items():
        if getattr(config, name) not in values:
            error("unsupported_" + name, "Unsupported configuration: " + name)
    if not all(isinstance(v, (int, float)) and isfinite(v) for v in (config.critical_float_threshold_hours, config.near_critical_float_threshold_hours)) or config.near_critical_float_threshold_hours < config.critical_float_threshold_hours:
        error("invalid_critical_thresholds", "Critical thresholds must be finite and ordered.")
    for name in ("maximum_path_count", "maximum_path_nodes_inspected", "maximum_path_depth", "maximum_critical_paths", "maximum_near_critical_paths"):
        value = getattr(config, name)
        optional = name in {"maximum_critical_paths", "maximum_near_critical_paths"}
        if value is None and optional:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < (1 if name == "maximum_path_depth" else 0):
            error("invalid_path_limit", "Path limits must be non-negative integers; depth must be at least one.")
    for name in ("comparison_date_tolerance_seconds", "comparison_float_tolerance_hours"):
        value = getattr(config, name)
        if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            error("invalid_comparison_tolerance", "Comparison tolerances must be finite and non-negative.")
    for name in ("completion_activity_id", "completion_activity_code", "required_finish_activity_id", "required_finish_activity_code"):
        value = getattr(config, name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            error("invalid_completion_selector", "Completion selectors must be non-empty strings.")
    timestamps = [config.project_start_override, config.required_project_finish, config.project_completion_timestamp]
    if schedule.project:
        timestamps += [schedule.project.data_date, schedule.project.planned_start]
    for a in schedule.activities.values():
        timestamps += [getattr(a, name) for name in ("planned_start", "planned_finish", "actual_start", "actual_finish", "primary_constraint_date", "secondary_constraint_date", "early_start", "early_finish", "late_start", "late_finish", "expected_finish")]
    if any(t is not None and (not isinstance(t, datetime) or t.tzinfo is not None) for t in timestamps):
        error("timezone_mixing", "CPM requires naive project-local datetime values.")
    if diagnostics:
        return diagnostics, True
    data_date = (schedule.project.data_date if schedule.project else None) or config.project_start_override
    anchor = max((t for t in (config.project_start_override, data_date) if t is not None), default=None)
    if anchor is None:
        error("missing_data_date", "Data Date or explicit start override is required.")
        return diagnostics, True
    if not graph.topological_sort().is_valid:
        error("circular_logic", "Circular logic prevents CPM calculation.")
    valid_ids = set(schedule.activities_by_id)
    for r in schedule.relationships:
        for side, activity_id in (("predecessor", r.predecessor_activity_id), ("successor", r.successor_activity_id)):
            if activity_id not in valid_ids:
                error("external_or_missing_" + side, "Relationship endpoint is unavailable.", relationship_id=r.relationship_id)
        if r.relationship_type.upper() not in {"FS", "SS", "FF", "SF"}:
            error("unsupported_relationship_type", "Unsupported relationship type.", relationship_id=r.relationship_id)
        if not isinstance(r.lag_hours, (int, float)) or not isfinite(r.lag_hours):
            error("invalid_lag", "Lag must be finite.", relationship_id=r.relationship_id)
    for a in schedule.activities.values():
        state, findings, disposition = activity_decision(a, config, data_date)
        diagnostics.extend(findings)
        calendar = schedule.calendars.get(a.calendar_id)
        if calendar is None:
            policy = config.missing_calendar_policy
            diagnostics.append(CPMDiagnostic("missing_activity_calendar", "Activity calendar is unavailable.", CPMFindingSeverity.ERROR if policy == "ERROR" else CPMFindingSeverity.WARNING, activity_id=a.activity_id, metadata={"disposition": policy}))
        elif disposition == "INCLUDE":
            try:
                if any(getattr(d.severity, "value", d.severity) == "error" for d in calendar.diagnostics):
                    raise ValueError("Imported calendar contains parsing errors")
                if calendar.weekly_pattern is not None and len(calendar.weekly_pattern.days) != 7:
                    raise ValueError("Weekly pattern must have seven days")
                next_working_time(calendar, anchor)
            except (ValueError, IndexError, TypeError) as exc:
                error("unusable_activity_calendar", str(exc), activity_id=a.activity_id)
        for kind, stamp in ((a.primary_constraint_type, a.primary_constraint_date), (a.secondary_constraint_type, a.secondary_constraint_date)):
            if kind is None and stamp is None:
                continue
            if kind not in {"START_ON_OR_AFTER", "FINISH_ON_OR_BEFORE"}:
                error("unsupported_constraint", "Constraint is not implemented by this CPM increment.", activity_id=a.activity_id)
            elif stamp is None:
                error("malformed_constraint", "Constraint requires a datetime.", activity_id=a.activity_id)
    if not schedule.activities:
        error("no_eligible_activities", "Schedule has no activities.")
    return diagnostics, any(d.severity == CPMFindingSeverity.ERROR for d in diagnostics)


def validate_pass_relationships(schedule, starts, finishes, pass_name):
    """Check endpoint inequalities after calendar arithmetic, before float.

    Working-time addition/subtraction is not globally invertible across gaps.
    Reject unsupported boundary inversions instead of publishing infeasible dates.
    """
    from app.cpm.relationship_math import lag_datetime

    diagnostics = []
    for relationship in schedule.relationships:
        kind = relationship.relationship_type.upper()
        predecessor_id = relationship.predecessor_activity_id
        successor_id = relationship.successor_activity_id
        calendar = schedule.calendars[schedule.activities_by_id[predecessor_id].calendar_id]
        base = starts[predecessor_id] if kind in {"SS", "SF"} else finishes[predecessor_id]
        available = starts[successor_id] if kind in {"FS", "SS"} else finishes[successor_id]
        required = lag_datetime(calendar, base, float(relationship.lag_hours))
        if required > available:
            diagnostics.append(CPMDiagnostic(
                "unsupported_calendar_relationship_boundary",
                "Calendar-boundary conversion produced an infeasible relationship; calculation was rejected.",
                CPMFindingSeverity.ERROR,
                relationship_id=relationship.relationship_id,
                metadata={"pass": pass_name, "relationship_type": kind,
                          "required": required.isoformat(), "available": available.isoformat(),
                          "lag_calendar_policy": "PREDECESSOR"},
            ))
    return diagnostics


def validate_date_invariants(schedule, states, forward, backward):
    from app.calendars.working_time import add_working_hours, subtract_working_hours, is_working_time, previous_working_time
    diagnostics = []
    for activity_id, (duration, state) in states.items():
        a = schedule.activities_by_id[activity_id]
        cal = schedule.calendars[a.calendar_id]
        es, ef = forward["early_starts"][activity_id], forward["early_finishes"][activity_id]
        ls, lf = backward["late_starts"][activity_id], backward["late_finishes"][activity_id]
        if state == "COMPLETE":
            valid = (es, ef, ls, lf) == (a.actual_start, a.actual_finish, a.actual_start, a.actual_finish)
        else:
            valid = ef == add_working_hours(cal, es, duration) and ls == subtract_working_hours(cal, lf, duration)
            if duration:
                valid = valid and is_working_time(cal, es) and is_working_time(cal, ls)
                valid = valid and all(is_working_time(cal, t) or previous_working_time(cal, t) == t for t in (ef, lf))
        if not valid:
            diagnostics.append(CPMDiagnostic("date_invariant_failed", "Date/duration or calendar-boundary invariant failed; float withheld.", CPMFindingSeverity.ERROR, activity_id=activity_id))
    return diagnostics
