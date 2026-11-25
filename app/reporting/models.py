from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_EVALUATED = "NOT_EVALUATED"
    BLOCKED = "BLOCKED"
    EXCLUDED = "EXCLUDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Provenance(str, Enum):
    IMPORTED_P6 = "IMPORTED_P6"
    APPLICATION_CALCULATED = "APPLICATION_CALCULATED"
    BASELINE_COMPARISON = "BASELINE_COMPARISON"
    CURRENT_SCHEDULE = "CURRENT_SCHEDULE"
    DCMA_ANALYSIS = "DCMA_ANALYSIS"
    HEALTH_ANALYSIS = "HEALTH_ANALYSIS"
    MILESTONE_ANALYSIS = "MILESTONE_ANALYSIS"


class ChangeClassification(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"
    DELAYED = "DELAYED"
    IMPROVED = "IMPROVED"
    DETERIORATED = "DETERIORATED"
    RECOVERED = "RECOVERED"
    BECAME_NEGATIVE = "BECAME_NEGATIVE"
    WBS_MOVED = "WBS_MOVED"
    TYPE_CHANGED = "TYPE_CHANGED"
    LAG_CHANGED = "LAG_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class ChangeValue:
    baseline: Any = None
    current: Any = None
    absolute_variance: float | None = None
    percentage_variance: float | None = None
    unit: str | None = None
    classification: ChangeClassification = ChangeClassification.NOT_COMPARABLE
    availability: Availability = Availability.NOT_EVALUATED
    provenance: tuple[Provenance, ...] = (Provenance.IMPORTED_P6, Provenance.BASELINE_COMPARISON)
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActivityRowContext:
    sequence: int
    internal_task_id: str
    activity_id: str
    description: str
    activity_type: str | None
    status: str | None
    remaining_duration_hours: float | None
    wbs_code: str | None
    wbs_name: str | None
    wbs_path: str | None
    baseline_internal_task_id: str | None
    current_internal_task_id: str | None
    baseline_wbs: str | None
    current_wbs: str | None
    baseline_calendar: str | None
    current_calendar: str | None


@dataclass(frozen=True)
class ReportRow:
    cells: dict[str, Any]
    change_values: dict[str, ChangeValue] = field(default_factory=dict)
    context: ActivityRowContext | None = None
    classification: str = "UNCHANGED"
    availability: Availability = Availability.AVAILABLE
    provenance: tuple[Provenance, ...] = (Provenance.IMPORTED_P6, Provenance.BASELINE_COMPARISON)
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReportColumn:
    key: str
    title: str
    data_type: str = "text"
    width: float = 22


@dataclass(frozen=True)
class ReportFilter:
    column_key: str
    operators: tuple[str, ...]


@dataclass(frozen=True)
class ReportSection:
    key: str
    title: str
    sheet_name: str
    columns: tuple[ReportColumn, ...]
    rows: tuple[ReportRow, ...]
    count: int
    availability: Availability = Availability.AVAILABLE
    diagnostics: tuple[str, ...] = ()
    message: str | None = None
    filters: tuple[ReportFilter, ...] = ()
    sort_metadata: tuple[str, ...] = ()
    pagination: dict[str, int] = field(default_factory=dict)
    truncated: bool = False


@dataclass(frozen=True)
class ScheduleReference:
    version_id: str
    label: str
    filename: str
    data_date: datetime | None
    project_id: str | None
    project_code: str | None
    project_name: str | None


@dataclass(frozen=True)
class ReportMetadata:
    report_identifier: str
    report_title: str
    generated_at: datetime
    generated_by: str | None
    project_id: str | None
    project_code: str | None
    project_name: str | None
    baseline: ScheduleReference
    current: ScheduleReference
    comparison_configuration: dict[str, Any]
    completion_authority_status: str = "NOT_ESTABLISHED"
    selected_analysis_anchor: Any | None = None
    analysis_anchor_selection_method: str | None = None
    analysis_anchor_timestamp: datetime | None = None
    analysis_anchor_timestamp_source: str | None = None
    analysis_mode: str | None = None


@dataclass(frozen=True)
class ForensicChangeReport:
    metadata: ReportMetadata
    sections: tuple[ReportSection, ...]
    schema_version: str = "1.0"

    def section(self, key: str) -> ReportSection:
        return next(section for section in self.sections if section.key == key)
