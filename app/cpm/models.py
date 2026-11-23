from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.schedule import Activity, Relationship, Schedule


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
    critical_disagreement: bool


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
