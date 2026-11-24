from __future__ import annotations

from app.importers.p6_normalization import normalize_activity_type, normalize_status


def activity_decision(activity, config, data_date):
    """Central policy: (effective duration/state or None, findings, disposition).

    Exclusions never reconnect logic across an excluded activity. The service
    rejects incident relationships rather than silently bypassing them.
    """
    from math import isfinite
    from app.cpm.models import CPMDiagnostic, CPMFindingSeverity

    findings = []
    def issue(code, message, disposition="ERROR", severity=None):
        level = severity or ("ERROR" if disposition == "ERROR" else "WARNING")
        findings.append(CPMDiagnostic(code, message, CPMFindingSeverity(level),
            activity_id=activity.activity_id, metadata={"disposition": disposition}))
    def reject(code, message, policy=None):
        disposition = policy or config.invalid_activity_policy
        issue(code, message, disposition)
        return None, findings, disposition

    status = normalize_status(activity.raw_status if activity.raw_status is not None else activity.status)
    kind = normalize_activity_type(activity.raw_activity_type if activity.raw_activity_type is not None else activity.activity_type)
    if status not in {"not_started", "in_progress", "complete"}:
        return reject("unsupported_activity_status", "Unknown or missing activity status.")
    if kind == "level_of_effort":
        return reject("loe_not_supported", "LOE scheduling is unsupported.", config.loe_policy)
    milestones = {"start_milestone", "finish_milestone", "milestone", "generic_milestone"}
    if kind not in milestones | {"task"}:
        return reject("unsupported_activity_type", "Unknown or missing activity type.")
    for value in (activity.original_duration_hours, activity.remaining_duration_hours):
        if value is not None:
            if not isinstance(value, (int, float)) or not isfinite(value):
                return reject("invalid_duration", "Duration must be a finite number.", "ERROR")
            if value < 0:
                return reject("negative_duration", "Negative imported duration is invalid.", "ERROR")
    actual_start, actual_finish = activity.actual_start, activity.actual_finish
    if actual_start and actual_finish and actual_finish < actual_start:
        return reject("actual_finish_before_start", "Actual Finish precedes Actual Start.")
    if data_date and any(value and value > data_date for value in (actual_start, actual_finish)):
        return reject("actual_after_data_date", "Actual dates cannot exceed Data Date.")
    if status == "not_started" and (actual_start or actual_finish):
        return reject("not_started_actual_dates", "Not-started activity contains actual dates.")
    if status == "in_progress":
        if actual_start is None:
            return reject("in_progress_missing_actual_start", "In-progress activity requires Actual Start.")
        if actual_finish is not None:
            return reject("in_progress_actual_finish", "In-progress activity cannot have Actual Finish.")
    if status == "complete":
        if actual_start is None:
            return reject("complete_missing_actual_start", "Completed activity requires Actual Start.")
        if actual_finish is None:
            return reject("complete_missing_actual_finish", "Completed activity requires Actual Finish.")
        if activity.remaining_duration_hours:
            if config.completed_remaining_duration_policy == "ERROR":
                return reject("complete_remaining_duration", "Completed activity has remaining duration.", "ERROR")
            issue("complete_remaining_duration_ignored", "Remaining duration is zeroed in results; actual dates are preserved.", "FALLBACK")
        return (0.0, "COMPLETE"), findings, "INCLUDE"
    if kind in milestones:
        if activity.original_duration_hours or activity.remaining_duration_hours:
            if config.milestone_duration_policy == "ERROR":
                return reject("milestone_nonzero_duration", "Milestone has non-zero imported duration.", "ERROR")
            issue("milestone_duration_ignored", "Milestone effective duration is zero.", "FALLBACK")
        return (0.0, "MILESTONE"), findings, "INCLUDE"
    if activity.planned_start and data_date and activity.planned_start < data_date:
        issue("planned_start_before_data_date", "Historical planned/forecast start is retained; remaining work starts no earlier than Data Date.", "INFORMATIONAL", "INFORMATIONAL")
    duration = activity.remaining_duration_hours if config.remaining_duration_preference else activity.original_duration_hours
    if duration is None:
        if activity.original_duration_hours is not None and config.duration_fallback_policy == "ORIGINAL_WITH_WARNING":
            duration = activity.original_duration_hours
            issue("original_duration_fallback", "Missing remaining duration: original hours used by configured fallback.", "FALLBACK")
        else:
            return reject("missing_duration", "No usable duration under the configured preference/fallback.", config.missing_duration_policy)
    if duration == 0 and config.zero_duration_task_policy == "ERROR":
        return reject("zero_duration_task", "Ordinary zero-duration tasks are disabled.", "ERROR")
    prefix = "IN_PROGRESS" if status == "in_progress" else "NOT_STARTED"
    return (float(duration), prefix + "_REMAINING_WORK"), findings, "INCLUDE"


def effective_duration(activity, config):
    state, findings, disposition = activity_decision(activity, config, None)
    if state is None:
        raise ValueError(findings[-1].message)
    return state
