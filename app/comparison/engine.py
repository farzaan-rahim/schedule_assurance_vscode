from __future__ import annotations

from app.comparison.activity_diff import compare_activity
from app.comparison.matcher import ActivityMatcher
from app.comparison.models import (
    ComparisonDiagnostic,
    ComparisonResult,
    ComparisonSummary,
    MatchClassification,
    RelationshipChangeType,
    ScheduleVersion,
)
from app.comparison.relationship_diff import compare_relationships
from app.comparison.wbs import WBSHierarchyError, wbs_path


class ScheduleComparisonEngine:
    def compare(
        self,
        baseline_version: ScheduleVersion,
        current_version: ScheduleVersion,
        critical_threshold_hours: float = 0.0,
    ) -> ComparisonResult:
        baseline = baseline_version.schedule
        current = current_version.schedule

        matches, matching_diagnostics = ActivityMatcher().match(baseline, current)

        diagnostics = list(matching_diagnostics)
        for schedule_label, schedule in (
            ("baseline", baseline),
            ("current", current),
        ):
            for activity in schedule.activities.values():
                if activity.wbs_id:
                    try:
                        wbs_path(schedule, activity.wbs_id)
                    except WBSHierarchyError as exc:
                        diagnostics.append(ComparisonDiagnostic(
                            code="malformed_wbs_ancestry",
                            message=str(exc),
                            activity_code=activity.activity_code,
                            metadata={"schedule": schedule_label},
                        ))

        baseline_calendars = {
            calendar_id: calendar.calendar_name
            for calendar_id, calendar in baseline.calendars.items()
        }
        current_calendars = {
            calendar_id: calendar.calendar_name
            for calendar_id, calendar in current.calendars.items()
        }

        activity_variances = tuple(
            compare_activity(
                match,
                critical_threshold_hours,
                baseline_calendars,
                current_calendars,
            )
            for match in matches
        )

        relationship_variances, relationship_diagnostics = compare_relationships(
            baseline,
            current,
            matches,
        )
        diagnostics.extend(relationship_diagnostics)

        matched = [v for v in activity_variances if v.classification == MatchClassification.MATCHED]
        baseline_only = [v for v in activity_variances if v.classification == MatchClassification.BASELINE_ONLY]
        current_only = [v for v in activity_variances if v.classification == MatchClassification.CURRENT_ONLY]
        ambiguous = [v for v in activity_variances if v.classification == MatchClassification.AMBIGUOUS]

        starts_changed = [v for v in matched if v.start_changed]
        finishes_changed = [v for v in matched if v.finish_changed]

        original_duration_changes = [
            v for v in matched
            if v.original_duration_variance_hours is not None
            and v.original_duration_variance_hours != 0
        ]
        remaining_duration_changes = [
            v for v in matched
            if v.remaining_duration_variance_hours is not None
            and v.remaining_duration_variance_hours != 0
        ]

        summary = ComparisonSummary(
            matched_activity_count=len(matched),
            baseline_only_count=len(baseline_only),
            current_only_count=len(current_only),
            ambiguous_count=len(ambiguous),
            names_changed=sum(v.name_changed for v in matched),
            wbs_changes=sum(v.wbs_changed for v in matched),
            calendar_changes=sum(v.calendar_changed for v in matched),
            activity_type_changes=sum(v.activity_type_changed for v in matched),
            status_changes=sum(v.status_changed for v in matched),
            starts_changed=len(starts_changed),
            starts_later=sum(
                v.start_variance_hours is not None and v.start_variance_hours > 0
                for v in starts_changed
            ),
            starts_earlier=sum(
                v.start_variance_hours is not None and v.start_variance_hours < 0
                for v in starts_changed
            ),
            finishes_changed=len(finishes_changed),
            finishes_later=sum(
                v.finish_variance_hours is not None and v.finish_variance_hours > 0
                for v in finishes_changed
            ),
            finishes_earlier=sum(
                v.finish_variance_hours is not None and v.finish_variance_hours < 0
                for v in finishes_changed
            ),
            original_duration_changes=len(original_duration_changes),
            remaining_duration_changes=len(remaining_duration_changes),
            total_float_changes=sum(
                v.total_float_variance_hours is not None
                and v.total_float_variance_hours != 0
                for v in matched
            ),
            float_deteriorated=sum(
                v.total_float_variance_hours is not None
                and v.total_float_variance_hours < 0
                for v in matched
            ),
            float_improved=sum(
                v.total_float_variance_hours is not None
                and v.total_float_variance_hours > 0
                for v in matched
            ),
            became_negative_float=sum(v.became_negative_float for v in matched),
            recovered_from_negative_float=sum(v.recovered_from_negative_float for v in matched),
            relationships_added=sum(
                r.change_type == RelationshipChangeType.ADDED
                for r in relationship_variances
            ),
            relationships_removed=sum(
                r.change_type == RelationshipChangeType.REMOVED
                for r in relationship_variances
            ),
            relationship_types_changed=sum(
                r.change_type == RelationshipChangeType.TYPE_CHANGED
                for r in relationship_variances
            ),
            relationship_lags_changed=sum(
                r.change_type == RelationshipChangeType.LAG_CHANGED
                for r in relationship_variances
            ),
        )

        return ComparisonResult(
            baseline_version=baseline_version,
            current_version=current_version,
            summary=summary,
            activity_variances=activity_variances,
            relationship_variances=tuple(relationship_variances),
            diagnostics=tuple(diagnostics),
        )
