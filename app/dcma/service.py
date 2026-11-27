from __future__ import annotations

from app.comparison.models import ComparisonResult
from app.dcma.config import DCMAConfig
from app.dcma.metrics import (
    baseline_metrics,
    duration_metric,
    hard_constraints,
    float_metrics,
    invalid_dates,
    missing_logic,
    relationship_lags,
    resource_metric,
)
from app.dcma.models import DCMAAssessmentResult, DCMADiagnostic
from app.dcma.scoring import calculate_dcma_score
from app.dcma.cpm_metrics import critical_path_test, cpli_metric


class DCMAAssessmentService:
    def analyze(
        self,
        schedule,
        graph,
        config: DCMAConfig | None = None,
        source_filename: str | None = None,
        comparison: ComparisonResult | None = None,
    ) -> DCMAAssessmentResult:
        config = config or DCMAConfig()

        leads, lags, relationship_types = relationship_lags(schedule, config)
        high_float, negative_float = float_metrics(schedule, config)
        missed, bei = baseline_metrics(comparison, config)

        metric_results = (
            missing_logic(schedule, graph, config),
            leads,
            lags,
            relationship_types,
            hard_constraints(schedule, config),
            high_float,
            negative_float,
            duration_metric(schedule, config),
            invalid_dates(schedule, config),
            resource_metric(schedule, config),
            missed,
            critical_path_test(schedule, config.cpm_config, config.critical_path_test_config),
            cpli_metric(schedule, config.cpm_config, config.cpli_config),
            bei,
        )

        overall = calculate_dcma_score(metric_results, config)
        project = schedule.project

        diagnostics = []
        if comparison is None:
            diagnostics.append(DCMADiagnostic(
                "baseline_context_missing",
                "Missed Activities and BEI require a baseline/current comparison.",
                "info",
                "missed_activities",
            ))

        metrics_not_evaluated = sum(
            result.status.value in {"NOT_EVALUATED", "NOT_APPLICABLE"}
            for result in metric_results
        )

        findings_total = sum(result.finding_count for result in metric_results)
        truncated_results = sum(
            result.finding_count > len(result.findings)
            for result in metric_results
        )

        truncation = {
            "detail_limit": config.detail_limit,
            "findings_total": findings_total,
            "metrics_with_truncated_findings": truncated_results,
        }

        return DCMAAssessmentResult(
            project_id=project.project_id if project else None,
            project_code=project.project_code if project else None,
            project_name=project.project_name if project else None,
            data_date=project.data_date if project else None,
            source_filename=source_filename,
            configuration_version=config.version,
            metrics_evaluated=len(metric_results) - metrics_not_evaluated,
            metrics_not_evaluated=metrics_not_evaluated,
            total_activity_population=len(schedule.activities),
            metric_results=metric_results,
            overall_score=overall,
            diagnostics=tuple(diagnostics),
            truncation=truncation,
        )
