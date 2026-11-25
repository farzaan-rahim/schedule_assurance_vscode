"""Identified P6 scheduling settings; raw fields are audit evidence only."""
from dataclasses import dataclass


@dataclass(frozen=True)
class P6SchedulingOptions:
    project_id: str
    retained_logic: bool | None = None
    progress_override: bool | None = None
    ss_lag_from_early_start: bool | None = None
    use_expected_finish: bool | None = None
    lag_calendar_policy: str | None = None
    external_relationship_policy: str | None = None
    set_planned_to_forecast: bool | None = None
    raw_fields: tuple[tuple[str, str], ...] = ()
