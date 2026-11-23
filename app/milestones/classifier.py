from __future__ import annotations

from app.importers.p6_normalization import normalize_activity_type
from app.milestones.models import MilestoneClassification
from app.models.schedule import Activity


def classify_milestone(activity: Activity) -> MilestoneClassification:
    raw = activity.raw_activity_type
    canonical = normalize_activity_type(raw)

    if canonical == "start_milestone":
        return MilestoneClassification.START_MILESTONE
    if canonical == "finish_milestone":
        return MilestoneClassification.FINISH_MILESTONE
    if canonical in {"milestone", "generic_milestone"}:
        return MilestoneClassification.GENERIC_MILESTONE
    return MilestoneClassification.NON_MILESTONE
