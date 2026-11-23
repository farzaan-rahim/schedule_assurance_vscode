from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.schedule import Activity, Schedule


class ScheduleVersionType(str, Enum):
    BASELINE = "BASELINE"
    UPDATE = "UPDATE"
    CURRENT = "CURRENT"


@dataclass(frozen=True)
class ScheduleVersion:
    version_id: str
    version_label: str
    version_type: ScheduleVersionType
    source_filename: str
    data_date: datetime | None
    imported_at: datetime
    schedule: Schedule


class MatchClassification(str, Enum):
    MATCHED = "MATCHED"
    BASELINE_ONLY = "BASELINE_ONLY"
    CURRENT_ONLY = "CURRENT_ONLY"
    AMBIGUOUS = "AMBIGUOUS"


class MatchMethod(str, Enum):
    ACTIVITY_CODE = "ACTIVITY_CODE"
    ACTIVITY_CODE_WBS = "ACTIVITY_CODE_WBS"
    MANUAL_RESERVED_FOR_FUTURE = "MANUAL_RESERVED_FOR_FUTURE"


@dataclass(frozen=True)
class ActivityMatch:
    classification: MatchClassification
    baseline_activity: Activity | None
    current_activity: Activity | None
    match_method: MatchMethod | None = None
    baseline_wbs_path: str | None = None
    current_wbs_path: str | None = None


@dataclass(frozen=True)
class ComparisonDiagnostic:
    code: str
    message: str
    severity: str = "warning"
    activity_code: str | None = None
    baseline_activity_id: str | None = None
    current_activity_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivityVariance:
    activity_code: str
    classification: MatchClassification
    baseline_activity: Activity | None
    current_activity: Activity | None
    match_method: MatchMethod | None = None
    baseline_wbs_path: str | None = None
    current_wbs_path: str | None = None

    name_changed: bool = False
    wbs_changed: bool = False
    calendar_changed: bool = False
    activity_type_changed: bool = False
    status_changed: bool = False
    percent_complete_changed: bool = False

    start_changed: bool = False
    start_variance_hours: float | None = None
    start_variance_calendar_days: float | None = None
    finish_changed: bool = False
    finish_variance_hours: float | None = None
    finish_variance_calendar_days: float | None = None
    actual_start_changed: bool = False
    actual_finish_changed: bool = False

    original_duration_variance_hours: float | None = None
    remaining_duration_variance_hours: float | None = None
    total_float_variance_hours: float | None = None
    free_float_variance_hours: float | None = None

    became_negative_float: bool = False
    recovered_from_negative_float: bool = False
    became_critical: bool = False
    left_critical_status: bool = False

    float_deteriorated: bool = False
    float_improved: bool = False


class RelationshipChangeType(str, Enum):
    UNCHANGED = "UNCHANGED"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    TYPE_CHANGED = "TYPE_CHANGED"
    LAG_CHANGED = "LAG_CHANGED"


@dataclass(frozen=True)
class RelationshipVariance:
    change_type: RelationshipChangeType
    predecessor_activity_code: str | None
    successor_activity_code: str | None
    baseline_relationship: Any | None = None
    current_relationship: Any | None = None
    baseline_predecessor_activity: Activity | None = None
    baseline_successor_activity: Activity | None = None
    current_predecessor_activity: Activity | None = None
    current_successor_activity: Activity | None = None
    baseline_relationship_type: str | None = None
    current_relationship_type: str | None = None
    baseline_lag_hours: float | None = None
    current_lag_hours: float | None = None


@dataclass(frozen=True)
class ComparisonSummary:
    matched_activity_count: int
    baseline_only_count: int
    current_only_count: int
    ambiguous_count: int

    names_changed: int
    wbs_changes: int
    calendar_changes: int
    activity_type_changes: int
    status_changes: int

    starts_changed: int
    starts_later: int
    starts_earlier: int
    finishes_changed: int
    finishes_later: int
    finishes_earlier: int

    original_duration_changes: int
    remaining_duration_changes: int
    total_float_changes: int
    float_deteriorated: int
    float_improved: int
    became_negative_float: int
    recovered_from_negative_float: int

    relationships_added: int
    relationships_removed: int
    relationship_types_changed: int
    relationship_lags_changed: int


@dataclass(frozen=True)
class ComparisonResult:
    baseline_version: ScheduleVersion
    current_version: ScheduleVersion
    summary: ComparisonSummary
    activity_variances: tuple[ActivityVariance, ...]
    relationship_variances: tuple[RelationshipVariance, ...]
    diagnostics: tuple[ComparisonDiagnostic, ...]
