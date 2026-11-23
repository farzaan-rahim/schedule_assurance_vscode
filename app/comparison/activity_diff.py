from __future__ import annotations

from datetime import datetime

from app.comparison.models import ActivityMatch, ActivityVariance, MatchClassification
from app.models.schedule import Activity


def elapsed_hours(baseline: datetime | None, current: datetime | None) -> float | None:
    if baseline is None or current is None:
        return None
    return (current - baseline).total_seconds() / 3600.0


def numeric_variance(baseline: float | None, current: float | None) -> float | None:
    if baseline is None or current is None:
        return None
    return current - baseline


def compare_activity(
    match: ActivityMatch,
    critical_threshold_hours: float = 0.0,
    baseline_calendars: dict[str, str] | None = None,
    current_calendars: dict[str, str] | None = None,
) -> ActivityVariance:
    baseline = match.baseline_activity
    current = match.current_activity

    if match.classification == MatchClassification.AMBIGUOUS:
        selected = baseline or current
        assert selected is not None
        return ActivityVariance(
            activity_code=selected.activity_code,
            classification=MatchClassification.AMBIGUOUS,
            baseline_activity=baseline,
            current_activity=current,
            match_method=match.match_method,
            baseline_wbs_path=match.baseline_wbs_path,
            current_wbs_path=match.current_wbs_path,
        )

    if baseline is None:
        assert current is not None
        return ActivityVariance(
            activity_code=current.activity_code,
            classification=MatchClassification.CURRENT_ONLY,
            baseline_activity=None,
            current_activity=current,
            baseline_wbs_path=match.baseline_wbs_path,
            current_wbs_path=match.current_wbs_path,
        )

    if current is None:
        return ActivityVariance(
            activity_code=baseline.activity_code,
            classification=MatchClassification.BASELINE_ONLY,
            baseline_activity=baseline,
            current_activity=None,
            baseline_wbs_path=match.baseline_wbs_path,
            current_wbs_path=match.current_wbs_path,
        )

    start_variance = elapsed_hours(baseline.planned_start, current.planned_start)
    finish_variance = elapsed_hours(baseline.planned_finish, current.planned_finish)

    start_changed = baseline.planned_start != current.planned_start
    finish_changed = baseline.planned_finish != current.planned_finish

    total_float_variance = numeric_variance(
        baseline.total_float_hours,
        current.total_float_hours,
    )

    baseline_negative = (
        baseline.total_float_hours is not None
        and baseline.total_float_hours < 0
    )
    current_negative = (
        current.total_float_hours is not None
        and current.total_float_hours < 0
    )

    baseline_critical = (
        baseline.total_float_hours is not None
        and baseline.total_float_hours <= critical_threshold_hours
    )
    current_critical = (
        current.total_float_hours is not None
        and current.total_float_hours <= critical_threshold_hours
    )

    if baseline_calendars is not None and current_calendars is not None:
        baseline_calendar = baseline_calendars.get(baseline.calendar_id or "", baseline.calendar_id)
        current_calendar = current_calendars.get(current.calendar_id or "", current.calendar_id)
    else:
        baseline_calendar = baseline.calendar_id
        current_calendar = current.calendar_id

    return ActivityVariance(
        activity_code=current.activity_code,
        classification=MatchClassification.MATCHED,
        baseline_activity=baseline,
        current_activity=current,
        match_method=match.match_method,
        baseline_wbs_path=match.baseline_wbs_path,
        current_wbs_path=match.current_wbs_path,
        name_changed=baseline.activity_name != current.activity_name,
        wbs_changed=match.baseline_wbs_path != match.current_wbs_path,
        calendar_changed=baseline_calendar != current_calendar,
        activity_type_changed=baseline.activity_type != current.activity_type,
        status_changed=baseline.status != current.status,
        percent_complete_changed=baseline.percent_complete != current.percent_complete,
        start_changed=start_changed,
        start_variance_hours=start_variance,
        start_variance_calendar_days=start_variance / 24.0 if start_variance is not None else None,
        finish_changed=finish_changed,
        finish_variance_hours=finish_variance,
        finish_variance_calendar_days=finish_variance / 24.0 if finish_variance is not None else None,
        actual_start_changed=baseline.actual_start != current.actual_start,
        actual_finish_changed=baseline.actual_finish != current.actual_finish,
        original_duration_variance_hours=numeric_variance(
            baseline.original_duration_hours,
            current.original_duration_hours,
        ),
        remaining_duration_variance_hours=numeric_variance(
            baseline.remaining_duration_hours,
            current.remaining_duration_hours,
        ),
        total_float_variance_hours=total_float_variance,
        free_float_variance_hours=numeric_variance(
            baseline.free_float_hours,
            current.free_float_hours,
        ),
        float_deteriorated=total_float_variance is not None and total_float_variance < 0,
        float_improved=total_float_variance is not None and total_float_variance > 0,
        became_negative_float=not baseline_negative and current_negative,
        recovered_from_negative_float=baseline_negative and not current_negative,
        became_critical=not baseline_critical and current_critical,
        left_critical_status=baseline_critical and not current_critical,
    )
