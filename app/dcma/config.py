from __future__ import annotations

from dataclasses import dataclass, field
from app.cpm.config import CPMConfig
from app.cpm.simulation import CriticalPathTestConfig
from app.cpm.cpli import CPLIConfig


@dataclass(frozen=True)
class DCMAConfig:
    version: str = "DCMA-STYLE-PHASE8-V1"

    missing_logic_warning_pct: float = 5.0
    missing_logic_fail_pct: float = 10.0
    lead_warning_pct: float = 0.0
    lead_fail_pct: float = 5.0
    lag_warning_pct: float = 5.0
    lag_fail_pct: float = 10.0
    excessive_lag_hours: float = 80.0
    non_fs_warning_pct: float = 10.0
    non_fs_fail_pct: float = 20.0

    high_float_threshold_hours: float = 1320.0
    high_float_warning_pct: float = 5.0
    high_float_fail_pct: float = 10.0
    negative_float_warning_pct: float = 1.0
    negative_float_fail_pct: float = 5.0

    high_duration_threshold_hours: float = 352.0
    high_duration_warning_pct: float = 5.0
    high_duration_fail_pct: float = 10.0

    invalid_date_warning_pct: float = 5.0
    invalid_date_fail_pct: float = 10.0

    hard_constraint_types: frozenset[str] = field(default_factory=lambda: frozenset({
        "MANDATORY_START", "MANDATORY_FINISH", "MUST_START_ON", "MUST_FINISH_ON"
    }))
    hard_constraint_warning_pct: float = 5.0
    hard_constraint_fail_pct: float = 10.0

    bei_warning: float = 0.90
    bei_fail: float = 0.80

    overall_score_enabled: bool = True
    pass_score: float = 100.0
    warning_score: float = 70.0
    fail_score: float = 0.0

    detail_limit: int = 100

    resource_exclude_completed: bool = True
    resource_exclude_milestones: bool = True
    resource_exclude_loe: bool = True
    resource_warning_pct: float = 5.0
    resource_fail_pct: float = 10.0

    weights: dict[str, float] = field(default_factory=lambda: {
        "missing_logic": 1.0,
        "leads": 1.0,
        "lags": 1.0,
        "relationship_types": 1.0,
        "hard_constraints": 1.0,
        "high_float": 1.0,
        "negative_float": 1.0,
        "high_duration": 1.0,
        "invalid_dates": 1.0,
        "resources": 1.0,
        "missed_activities": 1.0,
        "critical_path_test": 1.0,
        "cpli": 1.0,
        "bei": 1.0,
    })

    # Application methodology inputs; no database/host-specific policy.
    cpm_config: CPMConfig = field(default_factory=CPMConfig)
    critical_path_test_config: CriticalPathTestConfig = field(default_factory=CriticalPathTestConfig)
    cpli_config: CPLIConfig = field(default_factory=CPLIConfig)
