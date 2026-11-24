from __future__ import annotations

from collections import deque
from types import SimpleNamespace

from app.calendars.working_time import previous_working_time, subtract_working_hours
from app.cpm.constraint_math import backward_constraint
from app.cpm.relationship_math import reverse_predecessor_requirement


def backward_pass(schedule, graph, config, effective_states, calendars, forward, finish_anchor, component_finishes=None):
    late_starts: dict[str, object] = {}
    late_finishes: dict[str, object] = {}
    controlling: dict[str, dict] = {activity_id: {"successors": [], "relationships": [], "constraint": None, "requirements": {}, "constraints": []} for activity_id in schedule.activities_by_id}

    outdegree = {
        activity_id: len(graph.successor_relationships.get(activity_id, []))
        for activity_id in schedule.activities_by_id
    }
    queue = deque(activity_id for activity_id, degree in outdegree.items() if degree == 0)

    while queue:
        activity_id = queue.popleft()
        activity = schedule.activities_by_id[activity_id]
        calendar = calendars.get(activity.calendar_id) if activity.calendar_id else None

        candidate_finishes = []
        for relationship in graph.successor_relationships.get(activity_id, []):
            successor_id = relationship.successor_activity_id
            if successor_id not in late_starts or effective_states[activity_id][1] == "COMPLETE":
                continue

            successor = schedule.activities_by_id[successor_id]
            successor_calendar = calendars.get(successor.calendar_id)
            permitted_finish = reverse_predecessor_requirement(
                relationship,
                SimpleNamespace(effective_duration_hours=effective_states[activity_id][0]),
                SimpleNamespace(calculated_late_start=late_starts[successor_id],
                                calculated_late_finish=late_finishes[successor_id]),
                calendar, successor_calendar, float(relationship.lag_hours),
            )
            if effective_states[activity_id][0] > 0:
                permitted_finish = previous_working_time(calendar, permitted_finish)

            candidate_finishes.append((permitted_finish, successor_id, relationship))

        # The project finish bounds all activity finishes, including those
        # whose SS/SF relationships would otherwise allow a later completion.
        earliest = min([(component_finishes or {}).get(activity_id, finish_anchor.timestamp)] + [item[0] for item in candidate_finishes])

        constraints = []
        for constraint_type, constraint_date in ((activity.primary_constraint_type, activity.primary_constraint_date), (activity.secondary_constraint_type, activity.secondary_constraint_date)):
            earliest = backward_constraint(earliest, constraint_type, constraint_date)
            if constraint_type == "FINISH_ON_OR_BEFORE":
                requirement = previous_working_time(calendar, constraint_date) if effective_states[activity_id][0] > 0 else constraint_date
                constraints.append((constraint_type, constraint_date, requirement))
        if effective_states[activity_id][0] > 0:
            earliest = previous_working_time(calendar, earliest)
        if effective_states[activity_id][1] != "COMPLETE":
            controlling[activity_id]["successors"] = [item[1] for item in candidate_finishes if item[0] == earliest]
            controlling[activity_id]["relationships"] = [item[2].relationship_id for item in candidate_finishes if item[0] == earliest]
            controlling[activity_id]["requirements"] = {item[2].relationship_id:item[0] for item in candidate_finishes if item[0] == earliest}
            controlling[activity_id]["constraints"] = [item for item in constraints if item[2] == earliest]
            controlling[activity_id]["constraint"] = next((item[0] for item in constraints if item[2] == earliest), None)

        if effective_states[activity_id][1] == "COMPLETE":
            late_starts[activity_id] = activity.actual_start
            late_finishes[activity_id] = activity.actual_finish
        else:
            late_finishes[activity_id] = earliest
            late_starts[activity_id] = subtract_working_hours(calendar, earliest, effective_states[activity_id][0])

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
