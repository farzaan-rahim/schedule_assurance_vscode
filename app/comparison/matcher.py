from __future__ import annotations

from collections import defaultdict

from app.comparison.models import (
    ActivityMatch,
    ComparisonDiagnostic,
    MatchClassification,
    MatchMethod,
)
from app.comparison.wbs import WBSHierarchyError, wbs_path
from app.models.schedule import Activity, Schedule


class ActivityMatcher:
    def match(
        self,
        baseline: Schedule,
        current: Schedule,
    ) -> tuple[list[ActivityMatch], tuple[ComparisonDiagnostic, ...]]:
        baseline_codes = self._index_by_code(baseline)
        current_codes = self._index_by_code(current)
        diagnostics: list[ComparisonDiagnostic] = []
        matches: list[ActivityMatch] = []

        all_codes = sorted(set(baseline_codes) | set(current_codes))

        for code in all_codes:
            baseline_items = baseline_codes.get(code, [])
            current_items = current_codes.get(code, [])

            if not baseline_items:
                for activity in current_items:
                    matches.append(ActivityMatch(
                        MatchClassification.CURRENT_ONLY,
                        None,
                        activity,
                        None,
                        None,
                        self._safe_wbs_path(current, activity),
                    ))
                continue

            if not current_items:
                for activity in baseline_items:
                    matches.append(ActivityMatch(
                        MatchClassification.BASELINE_ONLY,
                        activity,
                        None,
                        None,
                        self._safe_wbs_path(baseline, activity),
                        None,
                    ))
                continue

            if len(baseline_items) == 1 and len(current_items) == 1:
                baseline_activity = baseline_items[0]
                current_activity = current_items[0]
                matches.append(ActivityMatch(
                    MatchClassification.MATCHED,
                    baseline_activity,
                    current_activity,
                    MatchMethod.ACTIVITY_CODE,
                    self._safe_wbs_path(baseline, baseline_activity),
                    self._safe_wbs_path(current, current_activity),
                ))
                continue

            diagnostics.append(ComparisonDiagnostic(
                code="duplicate_activity_code",
                message="Duplicate activity code requires WBS discrimination.",
                activity_code=code,
                metadata={
                    "baseline_count": len(baseline_items),
                    "current_count": len(current_items),
                },
            ))

            used_baseline: set[str] = set()
            used_current: set[str] = set()

            baseline_by_path = self._index_activities_by_wbs_path(baseline, baseline_items)
            current_by_path = self._index_activities_by_wbs_path(current, current_items)

            for path in sorted(set(baseline_by_path) & set(current_by_path)):
                baseline_candidates = baseline_by_path[path]
                current_candidates = current_by_path[path]
                if len(baseline_candidates) == 1 and len(current_candidates) == 1:
                    baseline_activity = baseline_candidates[0]
                    current_activity = current_candidates[0]
                    used_baseline.add(baseline_activity.activity_id)
                    used_current.add(current_activity.activity_id)
                    matches.append(ActivityMatch(
                        MatchClassification.MATCHED,
                        baseline_activity,
                        current_activity,
                        MatchMethod.ACTIVITY_CODE_WBS,
                        path,
                        path,
                    ))

            for activity in baseline_items:
                if activity.activity_id not in used_baseline:
                    matches.append(ActivityMatch(
                        MatchClassification.AMBIGUOUS,
                        activity,
                        None,
                        None,
                        self._safe_wbs_path(baseline, activity),
                        None,
                    ))

            for activity in current_items:
                if activity.activity_id not in used_current:
                    already_reported = any(
                        match.current_activity is not None
                        and match.current_activity.activity_id == activity.activity_id
                        for match in matches
                    )
                    if not already_reported:
                        matches.append(ActivityMatch(
                            MatchClassification.AMBIGUOUS,
                            None,
                            activity,
                            None,
                            None,
                            self._safe_wbs_path(current, activity),
                        ))

        return matches, tuple(diagnostics)

    @staticmethod
    def _index_by_code(schedule: Schedule) -> dict[str, list[Activity]]:
        return {
            code: list(items)
            for code, items in schedule.activities_by_code.items()
        }

    @staticmethod
    def _safe_wbs_path(schedule: Schedule, activity: Activity) -> str | None:
        try:
            return wbs_path(schedule, activity.wbs_id)
        except WBSHierarchyError:
            return None

    @staticmethod
    def _index_activities_by_wbs_path(
        schedule: Schedule,
        activities: list[Activity],
    ) -> dict[str, list[Activity]]:
        indexed: dict[str, list[Activity]] = defaultdict(list)
        for activity in activities:
            try:
                path = wbs_path(schedule, activity.wbs_id)
                if path:
                    indexed[path].append(activity)
            except WBSHierarchyError:
                continue
        return indexed
