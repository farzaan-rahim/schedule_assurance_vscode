from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Activity
from app.models.schedule import Schedule


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class HealthCheckConfig:
    long_duration_threshold_hours: float = 320
    excessive_lag_threshold_hours: float = 80
    detail_limit_per_rule: int = 100
    include_details: bool = True
    completed_status_values: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"TK_Complete", "Complete", "Completed"}
        )
    )
    in_progress_status_values: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"TK_Active", "Active", "In Progress", "InProgress"}
        )
    )
    not_started_status_values: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"TK_NotStart", "Not Started", "NotStart"}
        )
    )
    start_milestone_activity_types: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"TT_StartMile", "Start Milestone", "StartMilestone"}
        )
    )
    finish_milestone_activity_types: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"TT_FinMile", "Finish Milestone", "FinishMilestone"}
        )
    )

    def __post_init__(self) -> None:
        if self.long_duration_threshold_hours < 0:
            raise ValueError(
                "The long-duration threshold must be non-negative."
            )
        if self.excessive_lag_threshold_hours < 0:
            raise ValueError(
                "The excessive-lag threshold must be non-negative."
            )
        if not 1 <= self.detail_limit_per_rule <= 1000:
            raise ValueError(
                "The detail limit per rule must be between 1 and 1000."
            )


@dataclass(frozen=True)
class ScheduleHealthContext:
    schedule: Schedule
    graph: ScheduleGraph
    activities_by_code: dict[str, Activity]
    activities_by_id: dict[str, Activity]
    config: HealthCheckConfig
    completed_statuses: frozenset[str]
    in_progress_statuses: frozenset[str]
    not_started_statuses: frozenset[str]
    start_milestone_types: frozenset[str]
    finish_milestone_types: frozenset[str]


@dataclass(frozen=True)
class HealthIssue:
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    activity_code: str | None = None
    activity_name: str | None = None
    relationship_id: str | None = None
    predecessor_activity_id: str | None = None
    successor_activity_id: str | None = None
    observed_value: Any | None = None
    expected_value: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthRuleResult:
    rule_id: str
    rule_name: str
    severity: Severity
    issue_count: int
    returned_count: int
    issues: list[HealthIssue]


@dataclass(frozen=True)
class ScheduleHealthResult:
    schedule_version_id: int | None
    project_name: str | None
    project_code: str | None
    score: float
    rating: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    rules_evaluated: int
    rule_results: list[HealthRuleResult]
    thresholds: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(
            json.dumps(
                asdict(self),
                default=str,
                ensure_ascii=False,
            )
        )


def normalize_value(value: str | None) -> str:
    return value.strip().casefold() if value else ""
