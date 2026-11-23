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
