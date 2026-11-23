from __future__ import annotations

from app.importers.p6_normalization import normalize_activity_type, normalize_status


def effective_duration(activity, config) -> tuple[float, str]:
    status = normalize_status(activity.raw_status)
    activity_type = normalize_activity_type(activity.raw_activity_type)

    if activity_type in {"start_milestone", "finish_milestone", "milestone", "generic_milestone"}:
        return 0.0, "MILESTONE"
    if status == "complete":
        return 0.0, "COMPLETE"
    if status == "in_progress":
        if activity.remaining_duration_hours is not None:
            return float(activity.remaining_duration_hours), "IN_PROGRESS_REMAINING_DURATION"
        if config.remaining_duration_preference and activity.original_duration_hours is not None:
            return float(activity.original_duration_hours), "IN_PROGRESS_FALLBACK_ORIGINAL_DURATION"
        raise ValueError("In-progress activity has no remaining or original duration")
    if status == "not_started" or status is None:
        if config.remaining_duration_preference and activity.remaining_duration_hours is not None:
            return float(activity.remaining_duration_hours), "NOT_STARTED_REMAINING_DURATION"
        if activity.original_duration_hours is not None:
            return float(activity.original_duration_hours), "NOT_STARTED_ORIGINAL_DURATION"
        raise ValueError("Not-started activity has no remaining or original duration")
    if activity_type == "level_of_effort":
        raise ValueError("Level-of-effort effective duration is unsupported")

    raise ValueError("Unsupported activity state")
