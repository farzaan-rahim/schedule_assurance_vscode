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


def free_float(schedule, graph, calendar, activity_id, early_starts, early_finishes):
    successors = graph.successor_relationships.get(activity_id, [])
    if not successors:
        return None

    candidates = []
    for relationship in successors:
        successor = schedule.activities_by_id.get(relationship.successor_activity_id)
        if successor is None:
            continue
        successor_calendar = schedule.calendars.get(successor.calendar_id)
        if successor_calendar is None:
            continue

        successor_es = early_starts.get(successor.activity_id)
        if successor_es is None:
            continue

        lag = float(relationship.lag_hours)
        relationship_type = relationship.relationship_type.upper()
        if relationship_type == "FS":
            allowed = successor_es
        elif relationship_type == "SS":
            allowed = successor_es
        elif relationship_type == "FF":
            allowed = successor_es
        elif relationship_type == "SF":
            allowed = successor_es
        else:
            continue

        candidates.append(working_hours_between(calendar, early_finishes[activity_id], allowed))

    return min(candidates) if candidates else None
