from __future__ import annotations

from app.calendars.working_time import working_hours_between


def total_float(calendar, early_start, late_start, early_finish, late_finish):
    if calendar is None or early_start is None or late_start is None:
        return None, None

    start_method = working_hours_between(calendar, early_start, late_start)
    finish_method = (
        working_hours_between(calendar, early_finish, late_finish)
        if early_finish is not None and late_finish is not None
        else None
    )
    return start_method, finish_method


def free_float_details(schedule, graph, calendar, activity_id, early_starts, early_finishes, lag_calendar_policy="PREDECESSOR"):
    from app.calendars.working_time import inverse_lag_deadline
    successors = graph.successor_relationships.get(activity_id, [])
    if not successors:
        return None, (), "free_float_no_successor"
    if calendar is None or lag_calendar_policy != "PREDECESSOR":
        return None, (), "free_float_unsupported_methodology"
    candidates = []
    for relationship in successors:
        kind = relationship.relationship_type.upper()
        successor_id = relationship.successor_activity_id
        if kind not in {"FS", "SS", "FF", "SF"} or successor_id not in schedule.activities_by_id:
            return None, (), "free_float_missing_endpoint"
        source = early_starts.get(activity_id) if kind in {"SS", "SF"} else early_finishes.get(activity_id)
        target = early_starts.get(successor_id) if kind in {"FS", "SS"} else early_finishes.get(successor_id)
        if source is None or target is None:
            return None, (), "free_float_missing_dates"
        # FS: EF -> successor ES; SS: ES -> ES; FF: EF -> EF; SF: ES -> EF.
        # Invert the signed lag in the configured predecessor calendar, then
        # measure available endpoint displacement in this activity's hours.
        permitted = inverse_lag_deadline(calendar, target, float(relationship.lag_hours))
        candidates.append((relationship.relationship_id, working_hours_between(calendar, source, permitted)))
    return min(value for _, value in candidates), tuple(candidates), None


def free_float(schedule, graph, calendar, activity_id, early_starts, early_finishes, lag_calendar_policy="PREDECESSOR"):
    return free_float_details(schedule, graph, calendar, activity_id, early_starts, early_finishes, lag_calendar_policy)[0]
