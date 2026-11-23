from __future__ import annotations

from datetime import datetime

from app.importers.p6_normalization import normalize_status
from app.milestones.models import CandidateDriver
from app.models.schedule import Activity, Schedule


def candidate_drivers(
    schedule: Schedule,
    graph,
    milestone: Activity,
    milestone_date: datetime | None,
    limit: int = 20,
    upstream_limit: int = 200,
) -> tuple[list[CandidateDriver], dict[str, int]]:
    direct_ids = {
        activity.activity_id
        for activity in graph.get_direct_predecessors(milestone.activity_code)
    }

    upstream = graph.get_all_predecessors(milestone.activity_code)
    upstream_ids = {activity.activity_id for activity in upstream}

    upstream = sorted(upstream, key=lambda item: (item.activity_code, item.activity_id))
    upstream_total = len(upstream)
    upstream = upstream[:upstream_limit]

    candidates: list[CandidateDriver] = []

    relationships_by_predecessor: dict[str, list] = {}
    for relationship in schedule.relationships:
        if relationship.successor_activity_id == milestone.activity_id:
            relationships_by_predecessor.setdefault(
                relationship.predecessor_activity_id, []
            ).append(relationship)

    for activity in upstream:
        direct = activity.activity_id in direct_ids
        status = normalize_status(activity.raw_status)
        incomplete = status != "complete"
        negative_float = activity.total_float_hours is not None and activity.total_float_hours < 0

        score = 0
        reasons: list[str] = []

        if direct:
            score += 400
            reasons.append("Direct predecessor of the milestone")
        if incomplete:
            score += 300
            reasons.append("Incomplete upstream activity")
        if negative_float:
            score += 250
            reasons.append("Negative total float")
        if activity.total_float_hours is not None:
            score += max(0, 100 - int(activity.total_float_hours))
            reasons.append(f"Low total float: {activity.total_float_hours:g} hours")

        if milestone_date is not None and activity.planned_finish is not None:
            distance_hours = abs((milestone_date - activity.planned_finish).total_seconds() / 3600.0)
            if distance_hours <= 24 * 30:
                score += 50
                reasons.append("Planned finish is within 30 calendar days of milestone date")

        direct_relationships = relationships_by_predecessor.get(activity.activity_id, [])
        relationship = direct_relationships[0] if direct_relationships else None

        candidates.append(CandidateDriver(
            activity_id=activity.activity_id,
            activity_code=activity.activity_code,
            activity_name=activity.activity_name,
            relationship_type=relationship.relationship_type if relationship else "",
            lag_hours=relationship.lag_hours if relationship else 0.0,
            status=activity.status,
            planned_finish=activity.planned_finish,
            total_float_hours=activity.total_float_hours,
            negative_float=negative_float,
            incomplete=incomplete,
            rank_score=score,
            reasons=tuple(reasons),
        ))

    candidates.sort(key=lambda item: (
        -item.rank_score,
        item.total_float_hours if item.total_float_hours is not None else float("inf"),
        item.activity_code,
        item.activity_id,
    ))

    stats = {
        "direct_predecessors": len(direct_ids),
        "upstream_activities": len(upstream),
        "upstream_activities_total": upstream_total,
    }

    return candidates[:limit], stats
