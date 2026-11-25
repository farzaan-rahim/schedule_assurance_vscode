from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.schedule import Activity, Relationship, Schedule
from app.cpm.config import CPMConfig


class CPMFindingSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFORMATIONAL = "INFORMATIONAL"


@dataclass(frozen=True)
class CPMDiagnostic:
    code: str
    message: str
    severity: CPMFindingSeverity
    activity_id: str | None = None
    relationship_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CPMAnchor:
    timestamp: datetime
    source: str
    terminal_activity_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CPMRelationshipControl:
    relationship_id: str
    predecessor_id: str
    predecessor_code: str
    successor_id: str
    successor_code: str
    relationship_type: str
    lag_hours: float
    lag_calendar_policy: str
    lag_calendar_id: str
    direction: str
    requirement_kind: str
    required_timestamp: datetime
    tied: bool
    controlling: bool = True
    qualification_reason: str = "CONTROLLING_RELATIONSHIP"
    relationship_free_float_hours: float | None = None


@dataclass(frozen=True)
class CPMConstraintControl:
    constraint_type: str
    constraint_date: datetime
    direction: str
    required_timestamp: datetime
    tied_with_relationship: bool


@dataclass(frozen=True)
class CPMProgressState:
    actual_start: datetime | None
    actual_finish: datetime | None
    data_date: datetime | None
    observed_through: datetime | None
    imported_remaining_start: datetime | None
    imported_remaining_finish: datetime | None
    remaining_duration_hours: float | None


@dataclass(frozen=True)
class CPMActivityResult:
    activity_id: str
    activity_code: str
    activity_name: str

    effective_duration_hours: float
    effective_calendar_id: str | None

    calculated_early_start: datetime | None
    calculated_early_finish: datetime | None
    calculated_late_start: datetime | None
    calculated_late_finish: datetime | None
    calculated_total_float_hours: float | None
    calculated_free_float_hours: float | None
    calculated_critical: bool
    calculated_near_critical: bool

    imported_early_start: datetime | None
    imported_early_finish: datetime | None
    imported_late_start: datetime | None
    imported_late_finish: datetime | None
    imported_total_float_hours: float | None
    imported_free_float_hours: float | None

    controlling_predecessor_ids: tuple[str, ...] = ()
    controlling_successor_ids: tuple[str, ...] = ()
    controlling_relationship_ids: tuple[str, ...] = ()
    controlling_constraint: str | None = None
    applied_constraints: tuple[str, ...] = ()
    diagnostics: tuple[CPMDiagnostic, ...] = ()
    calculated_start_float_hours: float | None = None
    calculated_finish_float_hours: float | None = None
    total_float_method: str = "ACTIVITY_CALENDAR_START"
    relationship_free_float_hours: tuple[tuple[str, float], ...] = ()
    imported_critical: bool | None = None
    imported_critical_basis: str = "IMPORTED_TOTAL_FLOAT_THRESHOLD"
    critical_disagreement: bool | None = None
    effective_state: str | None = None
    date_basis: str = "REMAINING_WORK"
    effective_finish_anchor: datetime | None = None
    imported_actual_start: datetime | None = None
    imported_actual_finish: datetime | None = None
    progress_state: CPMProgressState | None = None
    early_date_status: str = "NOT_EVALUATED"
    late_date_status: str = "NOT_EVALUATED"
    float_status: str = "NOT_EVALUATED"
    controlling_relationships: tuple[CPMRelationshipControl, ...] = ()
    controlling_constraints: tuple[CPMConstraintControl, ...] = ()


@dataclass(frozen=True)
class CPMComparisonMetric:
    name: str
    imported: Any
    calculated: Any
    status: str
    variance_hours: float | None = None
    variance_seconds: float | None = None
    tolerance: float | None = None
    tolerance_unit: str | None = None


@dataclass(frozen=True)
class CPMCompletionAnchor:
    source: str
    activity_id: str | None = None
    activity_code: str | None = None
    activity_name: str | None = None
    calculated_early_finish: datetime | None = None
    calculated_late_finish: datetime | None = None
    imported_finish: datetime | None = None
    required_finish: datetime | None = None
    configured_completion_timestamp: datetime | None = None


@dataclass(frozen=True)
class CPMPathTraceStatistics:
    classification: str
    paths_returned: int
    completed_paths_found: int
    known_total_paths: int | None
    paths_lower_bound: int
    nodes_inspected: int
    truncated: bool
    limit_reasons: tuple[str, ...] = ()
    ranking_scope: str = "RETURNED_PATHS"


@dataclass(frozen=True)
class CPMPathConstraintCause:
    activity_id: str
    activity_code: str
    control: CPMConstraintControl


@dataclass(frozen=True)
class CPMComparisonSummary:
    activities_compared: int = 0
    activity_records: int = 0
    imported_dates_missing: int = 0
    activities_with_missing_imported_dates: int = 0
    early_start_matches: int = 0
    early_start_differences: int = 0
    early_finish_matches: int = 0
    early_finish_differences: int = 0
    late_start_matches: int = 0
    late_start_differences: int = 0
    late_finish_matches: int = 0
    late_finish_differences: int = 0
    total_float_matches: int = 0
    total_float_differences: int = 0
    free_float_matches: int = 0
    free_float_differences: int = 0
    critical_state_agreements: int = 0
    critical_state_disagreements: int = 0
    metric_counts: tuple[tuple[str, tuple[tuple[str, int], ...]], ...] = ()


@dataclass(frozen=True)
class CPMActivityComparison:
    activity_id: str
    activity_code: str
    early_start_variance_hours: float | None
    early_finish_variance_hours: float | None
    late_start_variance_hours: float | None
    late_finish_variance_hours: float | None
    total_float_variance_hours: float | None
    free_float_variance_hours: float | None
    critical_disagreement: bool | None
    imported_early_start: datetime | None = None
    calculated_early_start: datetime | None = None
    imported_early_finish: datetime | None = None
    calculated_early_finish: datetime | None = None
    imported_late_start: datetime | None = None
    calculated_late_start: datetime | None = None
    imported_late_finish: datetime | None = None
    calculated_late_finish: datetime | None = None
    imported_total_float_hours: float | None = None
    calculated_total_float_hours: float | None = None
    imported_free_float_hours: float | None = None
    calculated_free_float_hours: float | None = None
    imported_critical: bool | None = None
    calculated_critical: bool | None = None
    metrics: tuple[CPMComparisonMetric, ...] = ()


@dataclass(frozen=True)
class CPMPath:
    path_id: str
    terminal_activity_id: str
    activity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    minimum_total_float_hours: float | None
    maximum_total_float_hours: float | None
    duration_hours: float | None
    rank: int
    ranking_reason: str
    anchor: CPMCompletionAnchor | None = None
    classification: str = "CRITICAL"
    qualification_reason: str = ""
    activity_codes: tuple[str, ...] = ()
    relationships: tuple[CPMRelationshipControl, ...] = ()
    activity_count: int = 0
    relationship_count: int = 0
    sum_effective_activity_duration_hours: float = 0.0
    relationship_lag_contribution_hours: float = 0.0
    duration_method: str = "SEPARATE_ACTIVITY_AND_LAG_HOURS"
    start_timestamp: datetime | None = None
    finish_timestamp: datetime | None = None
    controlling_tie_activity_ids: tuple[str, ...] = ()
    constraint_causes: tuple[CPMPathConstraintCause, ...] = ()
    end_reason: str = "NETWORK_START"
    trace_complete: bool = True
    truncated: bool = False
    diagnostics: tuple[CPMDiagnostic, ...] = ()


@dataclass(frozen=True)
class CPMActivityCalculability:
    activity_id: str
    component_id: str
    status: str
    reason_codes: tuple[str, ...] = ()
    early_date_status: str = "NOT_EVALUATED"
    late_date_status: str = "NOT_EVALUATED"
    float_status: str = "NOT_EVALUATED"
    blocking_predecessor_ids: tuple[str, ...] = ()
    forward_boundary_status: str = "NOT_EVALUATED"


@dataclass(frozen=True)
class CPMRelationshipCalculability:
    relationship_id: str
    status: str
    reason_codes: tuple[str, ...] = ()
    forward_status: str = "NOT_EVALUATED"
    backward_status: str = "NOT_EVALUATED"
    forward_requirement_timestamp: datetime | None = None
    expired_lag_hours: float | None = None
    remaining_lag_hours: float | None = None


@dataclass(frozen=True)
class CPMComponentCalculability:
    component_id: str
    activity_count: int
    relationship_count: int
    status: str
    reason_codes: tuple[str, ...]
    blocking_activity_ids: tuple[str, ...]
    calculated_finish: datetime | None = None


@dataclass(frozen=True)
class CPMResult:
    status: str
    config_version: str
    schedule: Schedule
    eligible_activity_count: int
    excluded_activity_count: int
    relationship_count: int
    external_relationship_count: int
    project_start_anchor: CPMAnchor | None
    project_finish_anchor: CPMAnchor | None
    calculated_completion: datetime | None
    critical_activity_count: int
    near_critical_activity_count: int
    activity_results: tuple[CPMActivityResult, ...]
    comparisons: tuple[CPMActivityComparison, ...]
    controlling_relationship_ids: tuple[str, ...]
    critical_paths: tuple[CPMPath, ...]
    near_critical_paths: tuple[CPMPath, ...]
    diagnostics: tuple[CPMDiagnostic, ...]
    truncation: dict[str, Any]
    calculation_config: CPMConfig | None = None
    completion_anchor: CPMCompletionAnchor | None = None
    completion_anchor_candidates: tuple[CPMCompletionAnchor, ...] = ()
    anchor_selection_status: str = "NOT_EVALUATED"
    path_status: str = "NOT_EVALUATED"
    path_statistics: tuple[CPMPathTraceStatistics, ...] = ()
    comparison_summary: CPMComparisonSummary | None = None
    comparison_diagnostics: tuple[CPMDiagnostic, ...] = ()
    activity_calculability: tuple[CPMActivityCalculability, ...] = ()
    relationship_calculability: tuple[CPMRelationshipCalculability, ...] = ()
    components: tuple[CPMComponentCalculability, ...] = ()
    blocked_activity_count: int = 0
    partially_calculated_activity_count: int = 0
    reliability_scope: str = "COMPLETE_SCHEDULE"
