from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CPMConfig:
    version: str = "APPLICATION-CPM-PHASE6-V1"

    critical_float_threshold_hours: float = 0.0
    near_critical_float_threshold_hours: float = 40.0

    project_start_override: datetime | None = None
    required_project_finish: datetime | None = None

    missing_calendar_policy: str = "ERROR"
    missing_duration_policy: str = "ERROR"
    lag_calendar_policy: str = "PREDECESSOR"
    constraint_handling_policy: str = "SUPPORTED_ONLY"
    completed_activity_treatment: str = "PRESERVE_ACTUALS"
    in_progress_activity_treatment: str = "REMAINING_FROM_DATA_DATE"
    disconnected_component_policy: str = "INDEPENDENT_ANCHOR"

    maximum_path_count: int = 20
    maximum_path_depth: int = 500
    calculation_safety_bounds: int = 10000

    remaining_duration_preference: bool = True
    duration_fallback_policy: str = "ORIGINAL_WITH_WARNING"
    invalid_activity_policy: str = "ERROR"
    loe_policy: str = "EXCLUDE"
    completed_remaining_duration_policy: str = "ZERO_WITH_WARNING"
    milestone_duration_policy: str = "ZERO_WITH_WARNING"
    zero_duration_task_policy: str = "ALLOW"

    completion_activity_id: str | None = None
    completion_activity_code: str | None = None
    required_finish_activity_id: str | None = None
    required_finish_activity_code: str | None = None
    project_completion_timestamp: datetime | None = None
    maximum_critical_paths: int | None = None
    maximum_near_critical_paths: int | None = None
    maximum_path_nodes_inspected: int = 10000
    comparison_date_tolerance_seconds: float = 0.0
    comparison_float_tolerance_hours: float = 0.0
