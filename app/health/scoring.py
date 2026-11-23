from __future__ import annotations

from dataclasses import dataclass

from app.health.models import HealthRuleResult
from app.health.models import Severity


@dataclass(frozen=True)
class ScoringConfig:
    critical_points_per_issue: float = 5
    warning_points_per_issue: float = 1
    info_points_per_issue: float = 0.25
    maximum_critical_deduction_per_rule: float = 25
    maximum_warning_deduction_per_rule: float = 10
    maximum_info_deduction_per_rule: float = 5


def calculate_health_score(
    rule_results: list[HealthRuleResult],
    config: ScoringConfig | None = None,
) -> tuple[float, str]:
    scoring = config or ScoringConfig()
    points = {
        Severity.CRITICAL: scoring.critical_points_per_issue,
        Severity.WARNING: scoring.warning_points_per_issue,
        Severity.INFO: scoring.info_points_per_issue,
    }
    caps = {
        Severity.CRITICAL: (
            scoring.maximum_critical_deduction_per_rule
        ),
        Severity.WARNING: (
            scoring.maximum_warning_deduction_per_rule
        ),
        Severity.INFO: scoring.maximum_info_deduction_per_rule,
    }

    deduction = sum(
        min(
            result.issue_count * points[result.severity],
            caps[result.severity],
        )
        for result in rule_results
    )
    score = round(max(0.0, min(100.0, 100.0 - deduction)), 2)
    return score, health_rating(score)


def health_rating(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs Attention"
    return "Poor"
