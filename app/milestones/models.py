from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.comparison.models import ActivityVariance, MatchMethod
from app.models.schedule import Activity, Schedule


class MilestoneClassification(str, Enum):
    START_MILESTONE = "START_MILESTONE"
    FINISH_MILESTONE = "FINISH_MILESTONE"
    GENERIC_MILESTONE = "GENERIC_MILESTONE"
    NON_MILESTONE = "NON_MILESTONE"


class MilestoneMovement(str, Enum):
    UNCHANGED = "UNCHANGED"
    DELAYED = "DELAYED"
    IMPROVED = "IMPROVED"
    COMPLETED = "COMPLETED"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class MilestoneRecord:
    activity_id: str
    activity_code: str
    activity_name: str
    classification: MilestoneClassification
    raw_activity_type: str | None
    status: str | None
    wbs_id: str | None
    wbs_path: str | None
    calendar_id: str | None
    calendar_name: str | None
    planned_start: datetime | None
    planned_finish: datetime | None
    actual_start: datetime | None
    actual_finish: datetime | None
    total_float_hours: float | None
    free_float_hours: float | None
    percent_complete: float | None
    completed: bool
    in_progress: bool
    not_started: bool
    overdue: bool
    negative_float: bool
    critical: bool
    missing_planned_date: bool
    missing_required_actual_date: bool


@dataclass(frozen=True)
class MilestoneComparison:
    activity_code: str
    classification: MilestoneClassification
    movement: MilestoneMovement
    match_method: MatchMethod | None
    baseline_activity: Activity | None
    current_activity: Activity | None
    baseline_wbs_path: str | None
    current_wbs_path: str | None
    baseline_planned_date: datetime | None
    current_planned_date: datetime | None
    planned_date_variance_hours: float | None
    planned_date_variance_calendar_days: float | None
    baseline_actual_date: datetime | None
    current_actual_date: datetime | None
    baseline_total_float: float | None
    current_total_float: float | None
    float_variance_hours: float | None
    float_deteriorated: bool
    became_negative_float: bool
    became_critical: bool
    baseline_status: str | None
    current_status: str | None


@dataclass(frozen=True)
class MilestoneFinding:
    code: str
    message: str
    severity: str
    activity_code: str
    activity_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateDriver:
    activity_id: str
    activity_code: str
    activity_name: str
    relationship_type: str
    lag_hours: float
    status: str | None
    planned_finish: datetime | None
    total_float_hours: float | None
    negative_float: bool
    incomplete: bool
    rank_score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MilestoneSummary:
    total_milestones: int
    start_milestones: int
    finish_milestones: int
    generic_milestones: int
    completed_milestones: int
    incomplete_milestones: int
    overdue_milestones: int
    critical_milestones: int
    negative_float_milestones: int
    milestones_missing_planned_dates: int
    milestones_missing_actual_dates: int
    delayed_matched_milestones: int
    improved_matched_milestones: int
    unchanged_matched_milestones: int
    added_milestones: int
    removed_milestones: int
    ambiguous_milestones: int


@dataclass(frozen=True)
class MilestoneAnalysisResult:
    schedule: Schedule
    summary: MilestoneSummary
    milestones: tuple[MilestoneRecord, ...]
    findings: tuple[MilestoneFinding, ...]
    comparisons: tuple[MilestoneComparison, ...] = ()
    candidate_drivers: dict[str, tuple[CandidateDriver, ...]] = field(default_factory=dict)
    truncation: dict[str, Any] = field(default_factory=dict)
