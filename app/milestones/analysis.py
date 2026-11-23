from __future__ import annotations

from datetime import datetime

from app.comparison.wbs import WBSHierarchyError, wbs_path
from app.importers.p6_normalization import normalize_status
from app.milestones.classifier import classify_milestone
from app.milestones.models import (
    MilestoneClassification,
    MilestoneFinding,
    MilestoneRecord,
    MilestoneSummary,
)
from app.models.schedule import Activity, Schedule


def preferred_planned_date(
    activity: Activity,
    classification: MilestoneClassification,
) -> datetime | None:
    if classification == MilestoneClassification.START_MILESTONE:
        return activity.planned_start
    return activity.planned_finish


def build_milestone_inventory(
    schedule: Schedule,
    critical_threshold_hours: float = 0.0,
) -> tuple[list[MilestoneRecord], list[MilestoneFinding]]:
    records: list[MilestoneRecord] = []
    findings: list[MilestoneFinding] = []
    data_date = schedule.project.data_date if schedule.project else None

    for activity in schedule.activities.values():
        classification = classify_milestone(activity)
        if classification == MilestoneClassification.NON_MILESTONE:
            continue

        try:
            stable_wbs_path = wbs_path(schedule, activity.wbs_id)
        except WBSHierarchyError:
            stable_wbs_path = None

        calendar_name = (
            schedule.calendars[activity.calendar_id].calendar_name
            if activity.calendar_id in schedule.calendars
            else None
        )

        status = normalize_status(activity.raw_status)
        completed = status == "complete"
        in_progress = status == "in_progress"
        not_started = status == "not_started"
        negative_float = activity.total_float_hours is not None and activity.total_float_hours < 0
        critical = activity.total_float_hours is not None and activity.total_float_hours <= critical_threshold_hours

        preferred_date = preferred_planned_date(activity, classification)
        missing_planned = preferred_date is None

        missing_actual = False
        if completed:
            missing_actual = activity.actual_finish is None
        elif in_progress:
            missing_actual = activity.actual_start is None

        overdue = bool(
            data_date is not None
            and preferred_date is not None
            and preferred_date < data_date
            and not completed
        )

        records.append(MilestoneRecord(
            activity_id=activity.activity_id,
            activity_code=activity.activity_code,
            activity_name=activity.activity_name,
            classification=classification,
            raw_activity_type=activity.raw_activity_type,
            status=activity.status,
            wbs_id=activity.wbs_id,
            wbs_path=stable_wbs_path,
            calendar_id=activity.calendar_id,
            calendar_name=calendar_name,
            planned_start=activity.planned_start,
            planned_finish=activity.planned_finish,
            actual_start=activity.actual_start,
            actual_finish=activity.actual_finish,
            total_float_hours=activity.total_float_hours,
            free_float_hours=activity.free_float_hours,
            percent_complete=activity.percent_complete,
            completed=completed,
            in_progress=in_progress,
            not_started=not_started,
            overdue=overdue,
            negative_float=negative_float,
            critical=critical,
            missing_planned_date=missing_planned,
            missing_required_actual_date=missing_actual,
        ))

        if overdue:
            findings.append(MilestoneFinding(
                "milestone_overdue", "Milestone is incomplete and planned before the data date.",
                "warning", activity.activity_code, activity.activity_id,
            ))
        if completed and activity.actual_finish is None:
            findings.append(MilestoneFinding(
                "completed_milestone_missing_actual_finish", "Completed milestone has no actual finish.",
                "critical", activity.activity_code, activity.activity_id,
            ))
        if not_started and (activity.actual_start is not None or activity.actual_finish is not None):
            findings.append(MilestoneFinding(
                "not_started_milestone_with_actual_date", "Not-started milestone has actual date values.",
                "critical", activity.activity_code, activity.activity_id,
            ))
        if negative_float:
            findings.append(MilestoneFinding(
                "milestone_negative_float", "Milestone has negative total float.",
                "critical", activity.activity_code, activity.activity_id,
                {"total_float_hours": activity.total_float_hours},
            ))
        if activity.total_float_hours is None:
            findings.append(MilestoneFinding(
                "milestone_missing_total_float", "Milestone has no total-float value.",
                "warning", activity.activity_code, activity.activity_id,
            ))
        if missing_planned:
            findings.append(MilestoneFinding(
                "milestone_missing_planned_date", "The preferred planned milestone date is missing.",
                "warning", activity.activity_code, activity.activity_id,
                {"preferred_field": "planned_start" if classification == MilestoneClassification.START_MILESTONE else "planned_finish"},
            ))

    return records, findings


def summarize_milestones(
    records: list[MilestoneRecord],
    comparisons: list | None = None,
) -> MilestoneSummary:
    comparisons = comparisons or []

    return MilestoneSummary(
        total_milestones=len(records),
        start_milestones=sum(r.classification == MilestoneClassification.START_MILESTONE for r in records),
        finish_milestones=sum(r.classification == MilestoneClassification.FINISH_MILESTONE for r in records),
        generic_milestones=sum(r.classification == MilestoneClassification.GENERIC_MILESTONE for r in records),
        completed_milestones=sum(r.completed for r in records),
        incomplete_milestones=sum(not r.completed for r in records),
        overdue_milestones=sum(r.overdue for r in records),
        critical_milestones=sum(r.critical for r in records),
        negative_float_milestones=sum(r.negative_float for r in records),
        milestones_missing_planned_dates=sum(r.missing_planned_date for r in records),
        milestones_missing_actual_dates=sum(r.missing_required_actual_date for r in records),
        delayed_matched_milestones=sum(c.movement.value == "DELAYED" for c in comparisons),
        improved_matched_milestones=sum(c.movement.value == "IMPROVED" for c in comparisons),
        unchanged_matched_milestones=sum(c.movement.value == "UNCHANGED" for c in comparisons),
        added_milestones=sum(c.movement.value == "ADDED" for c in comparisons),
        removed_milestones=sum(c.movement.value == "REMOVED" for c in comparisons),
        ambiguous_milestones=sum(c.movement.value == "AMBIGUOUS" for c in comparisons),
    )
