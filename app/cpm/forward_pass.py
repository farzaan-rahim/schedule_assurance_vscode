from __future__ import annotations

from collections import deque

from app.calendars.working_time import add_working_hours, next_working_time
from app.cpm.constraint_math import forward_constraint_requirement
from app.cpm.relationship_math import forward_successor_requirement


def forward_pass(schedule, graph, config, effective_states, calendars, relationship_requirement=None) -> dict:
    indegree = {
        activity_id: len([r for r in graph.predecessor_relationships.get(activity_id, []) if r.predecessor_activity_id in schedule.activities_by_id])
        for activity_id in schedule.activities_by_id
    }
    queue = deque(activity_id for activity_id, degree in indegree.items() if degree == 0)

    anchor = max(t for t in (config.project_start_override, schedule.project.data_date if schedule.project else None) if t is not None)
    anchor_source = "CONFIGURED_PROJECT_START" if config.project_start_override else (
        "PROJECT_DATA_DATE" if schedule.project and schedule.project.data_date else "PROJECT_PLANNED_START"
    )

    early_starts: dict[str, object] = {}
    early_finishes: dict[str, object] = {}
    controlling: dict[str, dict] = {activity_id: {"predecessors": [], "relationships": [], "constraint": None, "requirements": {}, "constraints": []} for activity_id in schedule.activities_by_id}

    for activity_id in schedule.activities_by_id:
        activity = schedule.activities_by_id[activity_id]
        calendar = calendars.get(activity.calendar_id) if activity.calendar_id else None
        effective = effective_states[activity_id]

        if effective[1] == "COMPLETE":
            if activity.actual_start:
                early_starts[activity_id] = activity.actual_start
            else:
                early_starts[activity_id] = anchor
            if activity.actual_finish:
                early_finishes[activity_id] = activity.actual_finish
            else:
                early_finishes[activity_id] = early_starts[activity_id]
        else:
            early_starts[activity_id] = anchor

    while queue:
        activity_id = queue.popleft()
        activity = schedule.activities_by_id[activity_id]
        effective = effective_states[activity_id]
        calendar = calendars.get(activity.calendar_id) if activity.calendar_id else None

        candidate_starts = []
        predecessor_relationships = graph.predecessor_relationships.get(activity_id, [])
        for relationship in predecessor_relationships:
            predecessor_id = relationship.predecessor_activity_id
            if predecessor_id not in early_finishes:
                continue

            predecessor_calendar = calendars.get(schedule.activities_by_id[predecessor_id].calendar_id)
            predecessor = _PassActivity(
                calculated_early_start=early_starts[predecessor_id],
                calculated_early_finish=early_finishes[predecessor_id],
            )
            successor = _PassActivity(
                effective_duration_hours=effective[0],
            )

            required = (relationship_requirement or forward_successor_requirement)(
                relationship,
                predecessor,
                successor,
                predecessor_calendar,
                calendar,
                float(relationship.lag_hours),
            )
            if required is None:
                continue  # Explicit historical-only requirement in the opt-in progress scope.
            if effective[0] > 0:
                required = next_working_time(calendar, required)
            candidate_starts.append((required, predecessor_id, relationship))

        # Relationships are lower bounds; they cannot pull remaining work
        # before the project/Data Date anchor, even with a negative lag.
        latest = max([anchor] + [item[0] for item in candidate_starts])

        constraints = []
        for constraint_type, constraint_date in ((activity.primary_constraint_type, activity.primary_constraint_date), (activity.secondary_constraint_type, activity.secondary_constraint_date)):
            if effective[1] != "COMPLETE":
                requirement = forward_constraint_requirement(constraint_type, constraint_date, calendar, effective[0])
                if requirement is not None:
                    latest = max(latest, requirement)
                    constraints.append((constraint_type, constraint_date, requirement))
        if effective[0] > 0:
            latest = next_working_time(calendar, latest)
        if effective[1] != "COMPLETE":
            controlling[activity_id]["predecessors"] = [item[1] for item in candidate_starts if item[0] == latest]
            controlling[activity_id]["relationships"] = [item[2].relationship_id for item in candidate_starts if item[0] == latest]
            controlling[activity_id]["requirements"] = {item[2].relationship_id:item[0] for item in candidate_starts if item[0] == latest}
            controlling[activity_id]["constraints"] = [item for item in constraints if item[2] == latest]
            controlling[activity_id]["constraint"] = next((item[0] for item in constraints if item[2] == latest), None)

        if effective[1] == "COMPLETE":
            pass
        else:
            early_starts[activity_id] = latest
            if effective[0] == 0:
                early_finishes[activity_id] = latest
            else:
                early_finishes[activity_id] = add_working_hours(calendar, latest, effective[0])

        for relationship in graph.successor_relationships.get(activity_id, []):
            successor_id = relationship.successor_activity_id
            indegree[successor_id] -= 1
            if indegree[successor_id] == 0:
                queue.append(successor_id)

    return {
        "early_starts": early_starts,
        "early_finishes": early_finishes,
        "controlling": controlling,
        "anchor": anchor,
        "anchor_source": anchor_source,
    }


class _PassActivity:
    def __init__(self, calculated_early_start=None, calculated_early_finish=None, effective_duration_hours=0.0):
        self.calculated_early_start = calculated_early_start
        self.calculated_early_finish = calculated_early_finish
        self.effective_duration_hours = effective_duration_hours
