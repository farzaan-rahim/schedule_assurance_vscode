from __future__ import annotations

from collections import Counter

from app.importers.p6_normalization import normalize_activity_type, normalize_status
from app.models.schedule import Activity


def base_activity_exclusions(activity: Activity) -> dict[str, bool]:
    canonical_type = normalize_activity_type(activity.raw_activity_type)
    status = normalize_status(activity.raw_status)
    return {
        "LOE": canonical_type == "level_of_effort",
        "MILESTONE": canonical_type in {
            "start_milestone", "finish_milestone", "milestone", "generic_milestone"
        },
        "COMPLETED": status == "complete",
    }


def eligible_activities(
    activities: list[Activity],
    exclude_completed: bool = False,
    exclude_milestones: bool = False,
    exclude_loe: bool = True,
) -> tuple[list[Activity], dict[str, int]]:
    eligible: list[Activity] = []
    reasons: Counter[str] = Counter()

    for activity in activities:
        exclusions = base_activity_exclusions(activity)
        reason = None
        if exclude_loe and exclusions["LOE"]:
            reason = "LOE activity"
        elif exclude_milestones and exclusions["MILESTONE"]:
            reason = "Milestone"
        elif exclude_completed and exclusions["COMPLETED"]:
            reason = "Completed activity"

        if reason:
            reasons[reason] += 1
        else:
            eligible.append(activity)

    return eligible, dict(reasons)
