from __future__ import annotations

from datetime import datetime

from app.calendars.working_time import (
    add_working_hours, subtract_working_hours, start_for_finish_not_before,
    finish_for_start_not_after, inverse_lag_deadline,
)


def lag_datetime(calendar, base: datetime, lag_hours: float) -> datetime:
    if lag_hours >= 0:
        return add_working_hours(calendar, base, lag_hours)
    return subtract_working_hours(calendar, base, -lag_hours)


def forward_successor_requirement(
    relationship,
    predecessor,
    successor,
    predecessor_calendar,
    successor_calendar,
    lag_hours: float,
) -> datetime:
    # Phase 6 currently supports predecessor-calendar working-hour lag.
    # SF and SS reference predecessor start; FS and FF reference finish.
    relationship_type = relationship.relationship_type.upper()
    base = (predecessor.calculated_early_start if relationship_type in {"SS", "SF"}
            else predecessor.calculated_early_finish)
    lagged = lag_datetime(predecessor_calendar, base, lag_hours)
    if relationship_type == "FS":
        return lagged
    if relationship_type == "SS":
        return lagged
    if relationship_type == "FF":
        required_finish = lagged
        return start_for_finish_not_before(successor_calendar, required_finish, successor.effective_duration_hours)
    if relationship_type == "SF":
        required_finish = lagged
        return start_for_finish_not_before(successor_calendar, required_finish, successor.effective_duration_hours)
    raise ValueError(f"Unsupported relationship type: {relationship_type}")


def reverse_predecessor_requirement(
    relationship,
    predecessor,
    successor,
    predecessor_calendar,
    successor_calendar,
    lag_hours: float,
) -> datetime:
    relationship_type = relationship.relationship_type.upper()
    if relationship_type not in {"FS", "SS", "FF", "SF"}:
        raise ValueError(f"Unsupported relationship type: {relationship_type}")
    # Invert the same predecessor-calendar lag used by the forward pass.
    base = (successor.calculated_late_start if relationship_type in {"FS", "SS"}
            else successor.calculated_late_finish)
    permitted = inverse_lag_deadline(predecessor_calendar, base, lag_hours)
    if relationship_type in {"SS", "SF"}:
        # These bound predecessor START, so convert to its finish using its
        # own duration/calendar before comparing with finish-based bounds.
        return finish_for_start_not_after(predecessor_calendar, permitted, predecessor.effective_duration_hours)
    return permitted
