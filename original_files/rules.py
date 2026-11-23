from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable

from app.health.models import HealthIssue
from app.health.models import ScheduleHealthContext
from app.health.models import Severity
from app.health.models import normalize_value
from app.models.schedule import Activity
from app.models.schedule import Relationship


RuleEvaluator = Callable[[ScheduleHealthContext], list[HealthIssue]]


@dataclass(frozen=True)
class HealthRule:
    rule_id: str
    name: str
    description: str
    default_severity: Severity
    evaluator: RuleEvaluator

    def evaluate(
        self,
        context: ScheduleHealthContext,
    ) -> list[HealthIssue]:
        return self.evaluator(context)


def _activity_issue(
    rule_id: str,
    rule_name: str,
    severity: Severity,
    message: str,
    activity: Activity,
    observed_value=None,
    expected_value=None,
    metadata: dict | None = None,
) -> HealthIssue:
    return HealthIssue(
        rule_id=rule_id,
        rule_name=rule_name,
        severity=severity,
        message=message,
        activity_code=activity.activity_code,
        activity_name=activity.activity_name,
        observed_value=observed_value,
        expected_value=expected_value,
        metadata=metadata or {},
    )


def _relationship_issue(
    rule_id: str,
    rule_name: str,
    severity: Severity,
    message: str,
    relationship: Relationship,
    observed_value=None,
    expected_value=None,
    metadata: dict | None = None,
) -> HealthIssue:
    return HealthIssue(
        rule_id=rule_id,
        rule_name=rule_name,
        severity=severity,
        message=message,
        relationship_id=relationship.relationship_id,
        predecessor_activity_id=(
            relationship.predecessor_activity_id
        ),
        successor_activity_id=relationship.successor_activity_id,
        observed_value=observed_value,
        expected_value=expected_value,
        metadata=metadata or {},
    )


def circular_logic(context: ScheduleHealthContext) -> list[HealthIssue]:
    issues = []
    for cycle in context.graph.detect_cycles():
        activities = [
            {
                "activity_code": activity.activity_code,
                "activity_name": activity.activity_name,
            }
            for activity in cycle
        ]
        first = cycle[0] if cycle else None
        issues.append(
            HealthIssue(
                rule_id="circular_logic",
                rule_name="Circular Logic",
                severity=Severity.CRITICAL,
                message="A circular activity-logic path was detected.",
                activity_code=(first.activity_code if first else None),
                activity_name=(first.activity_name if first else None),
                metadata={"activities": activities},
            )
        )
    return issues


def open_starts(context: ScheduleHealthContext) -> list[HealthIssue]:
    return [
        _activity_issue(
            "open_starts",
            "Open Starts",
            Severity.WARNING,
            "Activity has no valid predecessor and requires review.",
            activity,
        )
        for activity in context.graph.get_start_activities()
        if normalize_value(activity.activity_type)
        not in context.start_milestone_types
    ]


def open_finishes(context: ScheduleHealthContext) -> list[HealthIssue]:
    return [
        _activity_issue(
            "open_finishes",
            "Open Finishes",
            Severity.WARNING,
            "Activity has no valid successor and requires review.",
            activity,
        )
        for activity in context.graph.get_finish_activities()
        if normalize_value(activity.activity_type)
        not in context.finish_milestone_types
    ]


def negative_total_float(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    activities = sorted(
        (
            activity
            for activity in context.activities_by_code.values()
            if activity.total_float_hours is not None
            and activity.total_float_hours < 0
        ),
        key=lambda activity: activity.total_float_hours,
    )
    return [
        _activity_issue(
            "negative_total_float",
            "Negative Total Float",
            Severity.CRITICAL,
            "Activity has negative total float.",
            activity,
            observed_value=activity.total_float_hours,
            expected_value=">= 0 hours",
        )
        for activity in activities
    ]


def missing_total_float(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "missing_total_float",
            "Missing Total Float",
            Severity.WARNING,
            "Incomplete activity has no total-float value.",
            activity,
            observed_value=None,
            expected_value="A numeric total-float value",
        )
        for activity in context.activities_by_code.values()
        if activity.total_float_hours is None
        and normalize_value(activity.status)
        not in context.completed_statuses
    ]


def long_duration(context: ScheduleHealthContext) -> list[HealthIssue]:
    threshold = context.config.long_duration_threshold_hours
    return [
        _activity_issue(
            "long_duration",
            "Long Duration",
            Severity.WARNING,
            "Original duration exceeds the configured hours threshold.",
            activity,
            observed_value=activity.original_duration_hours,
            expected_value=f"<= {threshold} hours",
        )
        for activity in context.activities_by_code.values()
        if activity.original_duration_hours is not None
        and activity.original_duration_hours > threshold
    ]


def excessive_positive_lag(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    threshold = context.config.excessive_lag_threshold_hours
    return [
        _relationship_issue(
            "excessive_positive_lag",
            "Excessive Positive Lag",
            Severity.WARNING,
            "Relationship lag exceeds the configured hours threshold.",
            relationship,
            observed_value=relationship.lag_hours,
            expected_value=f"<= {threshold} hours",
        )
        for relationship in context.schedule.relationships
        if relationship.lag_hours > threshold
    ]


def negative_lag(context: ScheduleHealthContext) -> list[HealthIssue]:
    return [
        _relationship_issue(
            "negative_lag",
            "Negative Lag",
            Severity.WARNING,
            "Relationship has negative lag and requires review.",
            relationship,
            observed_value=relationship.lag_hours,
            expected_value=">= 0 hours",
        )
        for relationship in context.schedule.relationships
        if relationship.lag_hours < 0
    ]


def invalid_planned_dates(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "invalid_planned_dates",
            "Invalid Planned Dates",
            Severity.CRITICAL,
            "Planned finish is earlier than planned start.",
            activity,
            observed_value={
                "planned_start": activity.planned_start.isoformat(),
                "planned_finish": activity.planned_finish.isoformat(),
            },
            expected_value="planned_finish >= planned_start",
        )
        for activity in context.activities_by_code.values()
        if activity.planned_start is not None
        and activity.planned_finish is not None
        and activity.planned_finish < activity.planned_start
    ]


def invalid_actual_dates(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "invalid_actual_dates",
            "Invalid Actual Dates",
            Severity.CRITICAL,
            "Actual finish is earlier than actual start.",
            activity,
            observed_value={
                "actual_start": activity.actual_start.isoformat(),
                "actual_finish": activity.actual_finish.isoformat(),
            },
            expected_value="actual_finish >= actual_start",
        )
        for activity in context.activities_by_code.values()
        if activity.actual_start is not None
        and activity.actual_finish is not None
        and activity.actual_finish < activity.actual_start
    ]


def completed_missing_actual_finish(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return _status_missing_date_issues(
        context,
        rule_id="completed_missing_actual_finish",
        rule_name="Completed Activity Missing Actual Finish",
        date_field="actual_finish",
    )


def completed_missing_actual_start(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return _status_missing_date_issues(
        context,
        rule_id="completed_missing_actual_start",
        rule_name="Completed Activity Missing Actual Start",
        date_field="actual_start",
    )


def _status_missing_date_issues(
    context: ScheduleHealthContext,
    rule_id: str,
    rule_name: str,
    date_field: str,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            rule_id,
            rule_name,
            Severity.CRITICAL,
            f"Completed activity has no {date_field.replace('_', ' ')}.",
            activity,
            expected_value=f"A populated {date_field}",
        )
        for activity in context.activities_by_code.values()
        if normalize_value(activity.status) in context.completed_statuses
        and getattr(activity, date_field) is None
    ]


def not_started_with_actual_dates(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "not_started_with_actual_dates",
            "Not-Started Activity With Actual Dates",
            Severity.CRITICAL,
            "Not-started activity contains actual date values.",
            activity,
            observed_value={
                "actual_start": (
                    activity.actual_start.isoformat()
                    if activity.actual_start else None
                ),
                "actual_finish": (
                    activity.actual_finish.isoformat()
                    if activity.actual_finish else None
                ),
            },
            expected_value="No actual dates",
        )
        for activity in context.activities_by_code.values()
        if normalize_value(activity.status) in context.not_started_statuses
        and (
            activity.actual_start is not None
            or activity.actual_finish is not None
        )
    ]


def in_progress_missing_actual_start(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "in_progress_missing_actual_start",
            "In-Progress Activity Missing Actual Start",
            Severity.CRITICAL,
            "In-progress activity has no actual start.",
            activity,
            expected_value="A populated actual_start",
        )
        for activity in context.activities_by_code.values()
        if normalize_value(activity.status) in context.in_progress_statuses
        and activity.actual_start is None
    ]


def percent_complete_out_of_range(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "percent_complete_out_of_range",
            "Percent Complete Outside Valid Range",
            Severity.CRITICAL,
            "Percent complete is outside the 0 to 100 range.",
            activity,
            observed_value=activity.percent_complete,
            expected_value="0 <= percent_complete <= 100",
        )
        for activity in context.activities_by_code.values()
        if activity.percent_complete is not None
        and (
            activity.percent_complete < 0
            or activity.percent_complete > 100
        )
    ]


def completed_below_100_percent(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "completed_below_100_percent",
            "Completed Activity Below 100 Percent",
            Severity.WARNING,
            "Completed activity is below 100 percent complete.",
            activity,
            observed_value=activity.percent_complete,
            expected_value=100,
        )
        for activity in context.activities_by_code.values()
        if normalize_value(activity.status) in context.completed_statuses
        and activity.percent_complete is not None
        and activity.percent_complete < 100
    ]


def not_started_above_0_percent(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _activity_issue(
            "not_started_above_0_percent",
            "Not-Started Activity Above 0 Percent",
            Severity.WARNING,
            "Not-started activity is above zero percent complete.",
            activity,
            observed_value=activity.percent_complete,
            expected_value=0,
        )
        for activity in context.activities_by_code.values()
        if normalize_value(activity.status) in context.not_started_statuses
        and activity.percent_complete is not None
        and activity.percent_complete > 0
    ]


def invalid_relationship_references(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    for relationship in context.schedule.relationships:
        if (
            relationship.predecessor_activity_id
            not in context.activities_by_id
        ):
            issues.append(
                _relationship_issue(
                    "invalid_relationship_references",
                    "Invalid Relationship References",
                    Severity.CRITICAL,
                    "Relationship predecessor is not in the schedule.",
                    relationship,
                    observed_value=(
                        relationship.predecessor_activity_id
                    ),
                    expected_value="A valid predecessor activity ID",
                    metadata={"missing_reference": "predecessor"},
                )
            )
        if (
            relationship.successor_activity_id
            not in context.activities_by_id
        ):
            issues.append(
                _relationship_issue(
                    "invalid_relationship_references",
                    "Invalid Relationship References",
                    Severity.CRITICAL,
                    "Relationship successor is not in the schedule.",
                    relationship,
                    observed_value=relationship.successor_activity_id,
                    expected_value="A valid successor activity ID",
                    metadata={"missing_reference": "successor"},
                )
            )
    return issues


def self_referencing_relationships(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    return [
        _relationship_issue(
            "self_referencing_relationships",
            "Self-Referencing Relationships",
            Severity.CRITICAL,
            "Relationship points from an activity to itself.",
            relationship,
            observed_value=relationship.predecessor_activity_id,
            expected_value="Different predecessor and successor IDs",
        )
        for relationship in context.schedule.relationships
        if relationship.predecessor_activity_id
        == relationship.successor_activity_id
    ]


def duplicate_activity_codes(
    context: ScheduleHealthContext,
) -> list[HealthIssue]:
    activities = list(context.schedule.activities.values())
    counts = Counter(activity.activity_code for activity in activities)
    duplicates = {code for code, count in counts.items() if count > 1}
    return [
        _activity_issue(
            "duplicate_activity_codes",
            "Duplicate Activity Codes",
            Severity.CRITICAL,
            "Activity code appears more than once in the schedule.",
            activity,
            observed_value=activity.activity_code,
            expected_value="A unique activity code",
        )
        for activity in activities
        if activity.activity_code in duplicates
    ]


REGISTERED_RULES = [
    HealthRule("circular_logic", "Circular Logic", "Detect cycles.", Severity.CRITICAL, circular_logic),
    HealthRule("open_starts", "Open Starts", "Detect open starts.", Severity.WARNING, open_starts),
    HealthRule("open_finishes", "Open Finishes", "Detect open finishes.", Severity.WARNING, open_finishes),
    HealthRule("negative_total_float", "Negative Total Float", "Detect negative float.", Severity.CRITICAL, negative_total_float),
    HealthRule("missing_total_float", "Missing Total Float", "Detect missing float.", Severity.WARNING, missing_total_float),
    HealthRule("long_duration", "Long Duration", "Detect long durations.", Severity.WARNING, long_duration),
    HealthRule("excessive_positive_lag", "Excessive Positive Lag", "Detect high lag.", Severity.WARNING, excessive_positive_lag),
    HealthRule("negative_lag", "Negative Lag", "Detect negative lag.", Severity.WARNING, negative_lag),
    HealthRule("invalid_planned_dates", "Invalid Planned Dates", "Detect invalid planned dates.", Severity.CRITICAL, invalid_planned_dates),
    HealthRule("invalid_actual_dates", "Invalid Actual Dates", "Detect invalid actual dates.", Severity.CRITICAL, invalid_actual_dates),
    HealthRule("completed_missing_actual_finish", "Completed Activity Missing Actual Finish", "Detect missing actual finishes.", Severity.CRITICAL, completed_missing_actual_finish),
    HealthRule("completed_missing_actual_start", "Completed Activity Missing Actual Start", "Detect missing actual starts.", Severity.CRITICAL, completed_missing_actual_start),
    HealthRule("not_started_with_actual_dates", "Not-Started Activity With Actual Dates", "Detect inconsistent actual dates.", Severity.CRITICAL, not_started_with_actual_dates),
    HealthRule("in_progress_missing_actual_start", "In-Progress Activity Missing Actual Start", "Detect missing starts.", Severity.CRITICAL, in_progress_missing_actual_start),
    HealthRule("percent_complete_out_of_range", "Percent Complete Outside Valid Range", "Detect invalid progress values.", Severity.CRITICAL, percent_complete_out_of_range),
    HealthRule("completed_below_100_percent", "Completed Activity Below 100 Percent", "Detect incomplete completion values.", Severity.WARNING, completed_below_100_percent),
    HealthRule("not_started_above_0_percent", "Not-Started Activity Above 0 Percent", "Detect premature progress.", Severity.WARNING, not_started_above_0_percent),
    HealthRule("invalid_relationship_references", "Invalid Relationship References", "Detect missing endpoints.", Severity.CRITICAL, invalid_relationship_references),
    HealthRule("self_referencing_relationships", "Self-Referencing Relationships", "Detect self references.", Severity.CRITICAL, self_referencing_relationships),
    HealthRule("duplicate_activity_codes", "Duplicate Activity Codes", "Detect duplicate activity codes.", Severity.CRITICAL, duplicate_activity_codes),
]
