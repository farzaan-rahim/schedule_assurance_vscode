from __future__ import annotations

from app.dcma.config import DCMAConfig
from app.dcma.models import DCMAMetricContribution, DCMAMetricResult, DCMAOverallScore, DCMAStatus


def calculate_dcma_score(
    metric_results: tuple[DCMAMetricResult, ...],
    config: DCMAConfig,
) -> DCMAOverallScore:
    if not config.overall_score_enabled:
        return DCMAOverallScore(False, None, None, 0.0, 0.0, ())

    contributions: list[DCMAMetricContribution] = []
    evaluated_weight = 0.0
    excluded_weight = 0.0

    for result in metric_results:
        weight = float(config.weights.get(result.metric_id, 1.0))
        if result.status in {DCMAStatus.NOT_EVALUATED, DCMAStatus.NOT_APPLICABLE}:
            excluded_weight += weight
            contributions.append(DCMAMetricContribution(result.metric_id, weight, 0.0, None, None))
            continue

        evaluated_weight += weight
        if result.status == DCMAStatus.PASS:
            score = config.pass_score
        elif result.status == DCMAStatus.WARNING:
            score = config.warning_score
        else:
            score = config.fail_score
        contribution = weight * score
        contributions.append(DCMAMetricContribution(result.metric_id, weight, weight, score, contribution))

    score = round(
        sum(c.contribution or 0.0 for c in contributions) / evaluated_weight,
        2,
    ) if evaluated_weight else None

    if score is None:
        rating = "NOT_EVALUATED"
    elif score >= 90:
        rating = "Excellent"
    elif score >= 75:
        rating = "Good"
    elif score >= 60:
        rating = "Needs Attention"
    else:
        rating = "Poor"

    return DCMAOverallScore(True, score, rating, evaluated_weight, excluded_weight, tuple(contributions))
