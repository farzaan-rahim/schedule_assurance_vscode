from __future__ import annotations

from app.graph.schedule_graph import ScheduleGraph
from app.health.models import (
    HealthCheckConfig,
    HealthIssue,
    HealthRuleResult,
    ScheduleHealthContext,
    ScheduleHealthResult,
    normalize_value,
)
from app.health.rules import REGISTERED_RULES
from app.health.scoring import calculate_health_score
from app.models.schedule import Schedule


class ScheduleHealthService:
    def analyze(
        self,
        schedule: Schedule,
        graph: ScheduleGraph,
        config: HealthCheckConfig | None = None,
        schedule_version_id: int | None = None,
    ) -> ScheduleHealthResult:
        config = config or HealthCheckConfig()

        def canonical_set(values: frozenset[str]) -> frozenset[str]:
            return frozenset(normalize_value(value) for value in values)

        context = ScheduleHealthContext(
            schedule=schedule,
            graph=graph,
            activities_by_code={
                activity.activity_id: activity
                for activity in schedule.activities.values()
            },
            activities_by_id=dict(schedule.activities_by_id),
            config=config,
            completed_statuses=canonical_set(config.completed_status_values),
            in_progress_statuses=canonical_set(config.in_progress_status_values),
            not_started_statuses=canonical_set(config.not_started_status_values),
            start_milestone_types=canonical_set(config.start_milestone_activity_types),
            finish_milestone_types=canonical_set(config.finish_milestone_activity_types),
        )

        rule_results: list[HealthRuleResult] = []
        all_issues: list[HealthIssue] = []

        for rule in REGISTERED_RULES:
            issues = rule.evaluate(context)
            all_issues.extend(issues)
            if config.include_details:
                detailed = issues[: config.detail_limit_per_rule]
            else:
                detailed = []

            rule_results.append(HealthRuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.default_severity,
                issue_count=len(issues),
                returned_count=len(detailed),
                issues=detailed,
            ))

        score, rating = calculate_health_score(rule_results)
        critical = sum(issue.severity.value == "critical" for issue in all_issues)
        warning = sum(issue.severity.value == "warning" for issue in all_issues)
        info = sum(issue.severity.value == "info" for issue in all_issues)

        thresholds = {
            "long_duration_threshold_hours": config.long_duration_threshold_hours,
            "excessive_lag_threshold_hours": config.excessive_lag_threshold_hours,
        }

        return ScheduleHealthResult(
            schedule_version_id=schedule_version_id,
            project_name=schedule.project.project_name if schedule.project else None,
            project_code=schedule.project.project_code if schedule.project else None,
            score=score,
            rating=rating,
            total_issues=len(all_issues),
            critical_issues=critical,
            warning_issues=warning,
            info_issues=info,
            rules_evaluated=len(rule_results),
            rule_results=rule_results,
            thresholds=thresholds,
        )
