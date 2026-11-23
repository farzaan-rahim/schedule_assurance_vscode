from __future__ import annotations

from datetime import datetime

from app.calendars.working_time import add_working_hours, subtract_working_hours, working_hours_between


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
    lag_calendar = predecessor_calendar if lag_hours >= 0 else predecessor_calendar
    lagged = lag_datetime(lag_calendar, predecessor.calculated_early_start if relationship.relationship_type == "SS"
                      else predecessor.calculated_early_finish,
                      lag_hours)

    relationship_type = relationship.relationship_type.upper()
    if relationship_type == "FS":
        return lagged
    if relationship_type == "SS":
        return lagged
    if relationship_type == "FF":
        required_finish = lagged
        return subtract_working_hours(successor_calendar, required_finish, successor.effective_duration_hours)
    if relationship_type == "SF":
        required_finish = lagged
        return subtract_working_hours(successor_calendar, required_finish, successor.effective_duration_hours)
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

    if relationship_type == "FS":
        return subtract_working_hours(successor_calendar, successor.calculated_late_start, lag_hours)
    if relationship_type == "SS":
        return subtract_working_hours(successor_calendar, successor.calculated_late_start, lag_hours)
    if relationship_type == "FF":
        return subtract_working_hours(successor_calendar, successor.calculated_late_finish, lag_hours)
    if relationship_type == "SF":
        base_finish = successor.calculated_late_finish
        return subtract_working_hours(successor_calendar, base_finish, successor.effective_duration_hours)
    raise ValueError(f"Unsupported relationship type: {relationship_type}")
