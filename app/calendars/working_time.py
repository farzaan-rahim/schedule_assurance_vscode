from __future__ import annotations

from datetime import datetime, timedelta

from app.calendars.models import CalendarException, WorkPeriod


SECONDS_PER_HOUR = 3600.0


def _day_pattern(calendar, day) -> tuple:
    if calendar.weekly_pattern is None:
        return ()
    work_day = calendar.weekly_pattern.days[day.weekday()]
    return work_day.periods if work_day.working else ()


def _periods_for_date(calendar, day) -> tuple[WorkPeriod, ...]:
    exception = next((item for item in getattr(calendar, "exceptions", ()) if item.exception_date == day), None)
    if exception is not None:
        return exception.periods if exception.working else ()
    return _day_pattern(calendar, day)


def _period_interval(day, period):
    start = datetime.combine(day, period.start)
    finish = datetime.combine(day, period.finish)
    if finish <= start:
        finish += timedelta(days=1)
    return start, finish


def _intervals_for_date(calendar, day):
    """Clip origin-day shifts (including overnight carry) and merge overlaps.

    Exceptions belong to the day a shift starts. Its overnight portion remains
    part of that shift on the following civil day.
    """
    lower = datetime.combine(day, datetime.min.time())
    upper = lower + timedelta(days=1)
    intervals = []
    for origin in (day - timedelta(days=1), day):
        for period in _periods_for_date(calendar, origin):
            start, finish = _period_interval(origin, period)
            start, finish = max(start, lower), min(finish, upper)
            if start < finish:
                intervals.append((start, finish))
    merged = []
    for start, finish in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(finish, merged[-1][1]))
        else:
            merged.append((start, finish))
    return merged


def _naive(timestamp):
    if timestamp.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")


def is_working_time(calendar, timestamp: datetime) -> bool:
    _naive(timestamp)
    return any(start <= timestamp < finish for start, finish in _intervals_for_date(calendar, timestamp.date()))


def next_working_time(calendar, timestamp: datetime) -> datetime:
    _naive(timestamp)
    day = timestamp.date()
    for _ in range(3660):
        for start, finish in _intervals_for_date(calendar, day):
            if timestamp < finish:
                return max(timestamp, start)
        day += timedelta(days=1)
        timestamp = datetime.combine(day, datetime.min.time())
    raise ValueError("Calendar has no reachable working time")


def previous_working_time(calendar, timestamp: datetime) -> datetime:
    _naive(timestamp)
    day = timestamp.date()
    for _ in range(3660):
        for start, finish in reversed(_intervals_for_date(calendar, day)):
            if start < timestamp:
                return min(timestamp, finish)
        timestamp = datetime.combine(day, datetime.min.time())
        day -= timedelta(days=1)
    raise ValueError("Calendar has no reachable previous working time")


def working_hours_between(calendar, start: datetime, finish: datetime) -> float:
    _naive(start)
    _naive(finish)
    sign = 1
    if finish < start:
        start, finish, sign = finish, start, -1
    total_seconds = 0.0
    day = start.date()
    while day <= finish.date():
        for left, right in _intervals_for_date(calendar, day):
            lower, upper = max(start, left), min(finish, right)
            if upper > lower:
                total_seconds += (upper - lower).total_seconds()
        day += timedelta(days=1)
    return sign * total_seconds / SECONDS_PER_HOUR


def _finite_hours(hours):
    from math import isfinite
    if not isfinite(hours):
        raise ValueError("Working duration must be finite")


def add_working_hours(calendar, start: datetime, hours: float) -> datetime:
    _naive(start)
    _finite_hours(hours)
    if hours == 0:
        return start
    if hours < 0:
        return subtract_working_hours(calendar, start, -hours)
    current = next_working_time(calendar, start)
    remaining = timedelta(hours=hours)
    day = current.date()
    for _ in range(3660 * 24):
        for lower, upper in _intervals_for_date(calendar, day):
            current = max(current, lower)
            if current < upper:
                available = upper - current
                if remaining <= available:
                    return current + remaining
                remaining -= available
        day += timedelta(days=1)
        current = datetime.combine(day, datetime.min.time())
    raise ValueError("Calendar has no reachable working time for the requested duration")


def subtract_working_hours(calendar, start: datetime, hours: float) -> datetime:
    _naive(start)
    _finite_hours(hours)
    if hours == 0:
        return start
    if hours < 0:
        return add_working_hours(calendar, start, -hours)
    current = start
    day = current.date()
    remaining = timedelta(hours=hours)
    for _ in range(3660 * 24):
        for lower, upper in reversed(_intervals_for_date(calendar, day)):
            current = min(current, upper)
            if current > lower:
                available = current - lower
                if remaining <= available:
                    return current - remaining
                remaining -= available
        current = datetime.combine(day, datetime.min.time())
        day -= timedelta(days=1)
    raise ValueError("Calendar has no reachable previous working time")


def working_boundaries_equivalent(calendar, first, second):
    """Exact zero-work equivalence, not elapsed-time tolerance."""
    return working_hours_between(calendar, first, second) == 0


def start_for_finish_not_before(calendar, finish, duration):
    """Earliest working start meeting a raw finish lower bound.

    Datetimes have a discrete one-microsecond resolution. If the lower bound
    lies in a non-working plateau, completing one tick after the next opening
    is the earliest achievable finish. No elapsed/working tolerance is used.
    """
    if duration == 0:
        return finish
    candidate = subtract_working_hours(calendar, finish, duration)
    if add_working_hours(calendar, candidate, duration) < finish:
        opening = next_working_time(calendar, finish)
        candidate = subtract_working_hours(calendar, opening + datetime.resolution, duration)
    return next_working_time(calendar, candidate)


def finish_for_start_not_after(calendar, start, duration):
    """Latest finish whose duration subtraction does not exceed start bound."""
    if duration == 0:
        return start
    candidate = add_working_hours(calendar, start, duration)
    if subtract_working_hours(calendar, candidate, duration) > start:
        candidate -= datetime.resolution
    return candidate


def inverse_lag_deadline(calendar, deadline, lag_hours):
    """Latest source endpoint whose signed lag lands no later than deadline."""
    if lag_hours >= 0:
        return subtract_working_hours(calendar, deadline, lag_hours)
    return finish_for_start_not_after(calendar, deadline, -lag_hours)
