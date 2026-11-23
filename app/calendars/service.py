from __future__ import annotations

from app.calendars.resolver import resolve_calendar_inheritance
from app.calendars.working_time import (
    add_working_hours,
    is_working_time,
    next_working_time,
    previous_working_time,
    subtract_working_hours,
    working_hours_between,
)


class CalendarService:
    def resolve_schedule_calendars(self, schedule) -> dict[str, object]:
        calendars, diagnostics = resolve_calendar_inheritance(schedule.calendars)
        for diagnostic in diagnostics:
            existing = getattr(calendars.get(diagnostic.calendar_id), "diagnostics", ())
            calendar = calendars.get(diagnostic.calendar_id)
            if calendar is not None:
                calendar.diagnostics = tuple(existing) + (diagnostic,)
        return calendars

    def get_calendar(self, schedule, calendar_id: str):
        return schedule.calendars.get(calendar_id)

    def get_activity_calendar(self, schedule, activity):
        if activity.calendar_id is None:
            return None
        return schedule.calendars.get(activity.calendar_id)

    def is_working_time(self, calendar, timestamp):
        return is_working_time(calendar, timestamp)

    def next_working_time(self, calendar, timestamp):
        return next_working_time(calendar, timestamp)

    def previous_working_time(self, calendar, timestamp):
        return previous_working_time(calendar, timestamp)

    def working_hours_between(self, calendar, start, finish):
        return working_hours_between(calendar, start, finish)

    def add_working_hours(self, calendar, start, hours):
        return add_working_hours(calendar, start, hours)

    def subtract_working_hours(self, calendar, start, hours):
        return subtract_working_hours(calendar, start, hours)

    def calendar_variance_hours(self, calendar, baseline, current):
        return working_hours_between(calendar, baseline, current)
