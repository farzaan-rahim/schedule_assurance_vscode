from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DCMAStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class DCMADiagnostic:
    code: str
    message: str
    severity: str = "warning"
    metric_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DCMAFinding:
    finding_type: str
    message: str
    activity_id: str | None = None
    activity_code: str | None = None
    activity_name: str | None = None
    wbs_path: str | None = None
    relationship_id: str | None = None
    predecessor_activity_id: str | None = None
    successor_activity_id: str | None = None
    relationship_type: str | None = None
    lag_hours: float | None = None
    observed_value: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DCMAMetricResult:
    metric_id: str
    metric_name: str
    description: str
    status: DCMAStatus
    eligible_count: int
    finding_count: int
    finding_percentage: float | None
    threshold: Any
    threshold_interpretation: str
    pass_fail_warning: str
    findings: tuple[DCMAFinding, ...]
    excluded_count: int
    exclusion_reasons: dict[str, int]
    calculation_notes: tuple[str, ...]
    source_fields: tuple[str, ...]
    limitations: tuple[str, ...]
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DCMAMetricContribution:
    metric_id: str
    weight: float
    evaluated_weight: float
    score: float | None
    contribution: float | None


@dataclass(frozen=True)
class DCMAOverallScore:
    enabled: bool
    score: float | None
    rating: str | None
    evaluated_weight: float
    excluded_weight: float
    contributions: tuple[DCMAMetricContribution, ...]


@dataclass(frozen=True)
class DCMAAssessmentResult:
    project_id: str | None
    project_code: str | None
    project_name: str | None
    data_date: datetime | None
    source_filename: str | None
    configuration_version: str
    metrics_evaluated: int
    metrics_not_evaluated: int
    total_activity_population: int
    metric_results: tuple[DCMAMetricResult, ...]
    overall_score: DCMAOverallScore
    diagnostics: tuple[DCMADiagnostic, ...]
    truncation: dict[str, Any]
