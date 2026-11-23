from __future__ import annotations

from app.comparison.models import ActivityVariance, ComparisonResult, MatchClassification
from app.importers.p6_normalization import normalize_status
from app.milestones.analysis import preferred_planned_date
from app.milestones.classifier import classify_milestone
from app.milestones.models import (
    MilestoneClassification,
    MilestoneComparison,
    MilestoneFinding,
    MilestoneMovement,
)


def compare_milestones(comparison: ComparisonResult) -> tuple[list[MilestoneComparison], list[MilestoneFinding]]:
    comparisons: list[MilestoneComparison] = []
    findings: list[MilestoneFinding] = []

    for variance in comparison.activity_variances:
        baseline = variance.baseline_activity
        current = variance.current_activity

        baseline_classification = classify_milestone(baseline) if baseline else MilestoneClassification.NON_MILESTONE
        current_classification = classify_milestone(current) if current else MilestoneClassification.NON_MILESTONE

        if baseline_classification == MilestoneClassification.NON_MILESTONE and current_classification == MilestoneClassification.NON_MILESTONE:
            continue

        if variance.classification == MatchClassification.BASELINE_ONLY:
            classification = baseline_classification
            comparisons.append(MilestoneComparison(
                variance.activity_code, classification, MilestoneMovement.REMOVED,
                variance.match_method, baseline, None,
                variance.baseline_wbs_path, None,
                preferred_planned_date(baseline, classification) if baseline else None,
                None, None, None, None, None,
                baseline.total_float_hours if baseline else None, None, None,
                False, False, False,
                baseline.status if baseline else None, None,
            ))
            continue

        if variance.classification == MatchClassification.CURRENT_ONLY:
            classification = current_classification
            comparisons.append(MilestoneComparison(
                variance.activity_code, classification, MilestoneMovement.ADDED,
                variance.match_method, None, current,
                None, variance.current_wbs_path,
                None,
                preferred_planned_date(current, classification) if current else None,
                None, None, None, None,
                None, current.total_float_hours if current else None, None,
                False, False, False,
                None, current.status if current else None,
            ))
            continue

        if variance.classification == MatchClassification.AMBIGUOUS:
            classification = current_classification if current_classification != MilestoneClassification.NON_MILESTONE else baseline_classification
            comparisons.append(MilestoneComparison(
                variance.activity_code, classification, MilestoneMovement.AMBIGUOUS,
                variance.match_method, baseline, current,
                variance.baseline_wbs_path, variance.current_wbs_path,
                preferred_planned_date(baseline, classification) if baseline else None,
                preferred_planned_date(current, classification) if current else None,
                None, None, None, None,
                baseline.total_float_hours if baseline else None,
                current.total_float_hours if current else None,
                None, False, False, False,
                baseline.status if baseline else None,
                current.status if current else None,
            ))
            continue

        if baseline is None or current is None:
            continue

        classification = current_classification
        baseline_date = preferred_planned_date(baseline, classification)
        current_date = preferred_planned_date(current, classification)

        if baseline_date is None or current_date is None:
            movement = MilestoneMovement.NOT_COMPARABLE
            variance_hours = None
            variance_days = None
        else:
            variance_hours = (current_date - baseline_date).total_seconds() / 3600.0
            variance_days = variance_hours / 24.0

            baseline_status = normalize_status(baseline.raw_status)
            current_status = normalize_status(current.raw_status)

            if baseline_status != "complete" and current_status == "complete":
                movement = MilestoneMovement.COMPLETED
            elif variance_hours > 0:
                movement = MilestoneMovement.DELAYED
            elif variance_hours < 0:
                movement = MilestoneMovement.IMPROVED
            else:
                movement = MilestoneMovement.UNCHANGED

            if movement == MilestoneMovement.DELAYED:
                findings.append(MilestoneFinding(
                    "milestone_delayed", "Milestone planned date moved later than baseline.",
                    "warning", current.activity_code, current.activity_id,
                    {"variance_hours": variance_hours, "variance_calendar_days": variance_days},
                ))

        float_variance = None
        if baseline.total_float_hours is not None and current.total_float_hours is not None:
            float_variance = current.total_float_hours - baseline.total_float_hours

        baseline_negative = baseline.total_float_hours is not None and baseline.total_float_hours < 0
        current_negative = current.total_float_hours is not None and current.total_float_hours < 0
        became_negative = not baseline_negative and current_negative

        baseline_actual = current.actual_start if False else (
            baseline.actual_start if classification == MilestoneClassification.START_MILESTONE else baseline.actual_finish
        )
        current_actual = (
            current.actual_start if classification == MilestoneClassification.START_MILESTONE else current.actual_finish
        )

        became_critical = bool(
            variance.became_critical
        )

        record = MilestoneComparison(
            activity_code=current.activity_code,
            classification=classification,
            movement=movement,
            match_method=variance.match_method,
            baseline_activity=baseline,
            current_activity=current,
            baseline_wbs_path=variance.baseline_wbs_path,
            current_wbs_path=variance.current_wbs_path,
            baseline_planned_date=baseline_date,
            current_planned_date=current_date,
            planned_date_variance_hours=variance_hours,
            planned_date_variance_calendar_days=variance_days,
            baseline_actual_date=baseline_actual,
            current_actual_date=current_actual,
            baseline_total_float=baseline.total_float_hours,
            current_total_float=current.total_float_hours,
            float_variance_hours=float_variance,
            float_deteriorated=bool(float_variance is not None and float_variance < 0),
            became_negative_float=became_negative,
            became_critical=became_critical,
            baseline_status=baseline.status,
            current_status=current.status,
        )
        comparisons.append(record)

        if became_negative:
            findings.append(MilestoneFinding(
                "milestone_newly_negative_float", "Milestone became negative float since baseline.",
                "critical", current.activity_code, current.activity_id,
                {"float_variance_hours": float_variance},
            ))
        if variance.wbs_changed:
            findings.append(MilestoneFinding(
                "milestone_moved_wbs", "Milestone moved between WBS paths.",
                "warning", current.activity_code, current.activity_id,
                {"baseline_wbs_path": variance.baseline_wbs_path, "current_wbs_path": variance.current_wbs_path},
            ))

    return comparisons, findings
