from __future__ import annotations

from collections import deque

from app.calendars.working_time import subtract_working_hours
from app.cpm.constraint_math import backward_constraint


def backward_pass(schedule, graph, config, effective_states, calendars, forward, finish_anchor):
    late_starts: dict[str, object] = {}
    late_finishes: dict[str, object] = {}
    controlling: dict[str, dict] = {activity_id: {"successors": [], "relationships": [], "constraint": None} for activity_id in schedule.activities_by_id}

    outdegree = {
        activity_id: len(graph.successor_relationships.get(activity_id, []))
        for activity_id in schedule.activities_by_id
    }
    queue = deque(activity_id for activity_id, degree in outdegree.items() if degree == 0)

    for activity_id in schedule.activities_by_id:
        if outdegree[activity_id] == 0:
            late_finishes[activity_id] = finish_anchor.timestamp
            late_starts[activity_id] = subtract_working_hours(
                calendars.get(schedule.activities_by_id[activity_id].calendar_id),
                finish_anchor.timestamp,
                effective_states[activity_id][0],
            )

    while queue:
        activity_id = queue.popleft()
        activity = schedule.activities_by_id[activity_id]
        calendar = calendars.get(activity.calendar_id) if activity.calendar_id else None

        candidate_finishes = []
        for relationship in graph.successor_relationships.get(activity_id, []):
            successor_id = relationship.successor_activity_id
            if successor_id not in late_starts:
                continue

            successor = schedule.activities_by_id[successor_id]
            successor_calendar = calendars.get(successor.calendar_id)
            relationship_type = relationship.relationship_type.upper()

            lag_hours = float(relationship.lag_hours)
            successor_late_start = late_starts[successor_id]

            if relationship_type == "FS":
                permitted_finish = subtract_working_hours(successor_calendar, successor_late_start, lag_hours)
            elif relationship_type == "SS":
                permitted_finish = subtract_working_hours(successor_calendar, late_starts[successor_id], lag_hours)
            elif relationship_type == "FF":
                permitted_finish = subtract_working_hours(successor_calendar, late_finishes[successor_id], lag_hours)
            elif relationship_type == "SF":
                permitted_finish = subtract_working_hours(successor_calendar, successor.calculated_late_finish if hasattr(successor, "calculated_late_finish") else late_finishes[successor_id], lag_hours)
            else:
                continue

            candidate_finishes.append((permitted_finish, successor_id, relationship))

        if candidate_finishes:
            earliest = min(item[0] for item in candidate_finishes)
            controlling[activity_id]["successors"] = [item[1] for item in candidate_finishes if item[0] == earliest]
            controlling[activity_id]["relationships"] = [item[2].relationship_id for item in candidate_finishes if item[0] == earliest]
        else:
            earliest = finish_anchor.timestamp

        constraint_type = activity.primary_constraint_type or activity.secondary_constraint_type
        constraint_date = activity.primary_constraint_date or activity.secondary_constraint_date
        earliest = backward_constraint(earliest, constraint_type, constraint_date)
        if constraint_type:
            controlling[activity_id]["constraint"] = constraint_type

        late_finishes[activity_id] = earliest
        late_starts[activity_id] = subtract_working_hours(
            calendar,
            earliest,
            effective_states[activity_id][0],
        )

        for relationship in graph.predecessor_relationships.get(activity_id, []):
            predecessor_id = relationship.predecessor_activity_id
            outdegree[predecessor_id] -= 1
            if outdegree[predecessor_id] == 0:
                queue.append(predecessor_id)

    return {
        "late_starts": late_starts,
        "late_finishes": late_finishes,
        "controlling": controlling,
    }
