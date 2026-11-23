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


def is_working_time(calendar, timestamp: datetime) -> bool:
    if timestamp.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported by P6 naive calendar arithmetic")

    for period in _periods_for_date(calendar, timestamp.date()):
        start, finish = _period_interval(timestamp.date(), period)
        if start <= timestamp < finish:
            return True
    previous_day = timestamp.date() - timedelta(days=1)
    for period in _periods_for_date(calendar, previous_day):
        start, finish = _period_interval(previous_day, period)
        if start <= timestamp < finish:
            return True
    return False


def next_working_time(calendar, timestamp: datetime) -> datetime:
    if timestamp.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")

    day = timestamp.date()
    for _ in range(3660):
        periods = _periods_for_date(calendar, day)
        for period in periods:
            start, finish = _period_interval(day, period)
            if timestamp < finish and timestamp < start:
                return start
            if start <= timestamp < finish:
                return timestamp
        day += timedelta(days=1)
        timestamp = datetime.combine(day, datetime.min.time())
    raise ValueError("Calendar has no reachable working time")


def previous_working_time(calendar, timestamp: datetime) -> datetime:
    if timestamp.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")

    day = timestamp.date()
    for _ in range(3660):
        periods = _periods_for_date(calendar, day)
        for period in reversed(periods):
            start, finish = _period_interval(day, period)
            if timestamp > finish:
                return finish
            if start < timestamp <= finish:
                return timestamp
        day -= timedelta(days=1)
        timestamp = datetime.combine(day, datetime.max.time().replace(microsecond=0))
    raise ValueError("Calendar has no reachable previous working time")


def working_hours_between(calendar, start: datetime, finish: datetime) -> float:
    if start.tzinfo is not None or finish.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")

    if finish < start:
        return -working_hours_between(calendar, finish, start)

    total_seconds = 0.0
    day = start.date()
    while day <= finish.date():
        for period in _periods_for_date(calendar, day):
            period_start = datetime.combine(day, period.start)
            period_finish = datetime.combine(day, period.finish)
            overlap_start = max(start, period_start)
            overlap_finish = min(finish, period_finish)
            if overlap_finish > overlap_start:
                total_seconds += (overlap_finish - overlap_start).total_seconds()
        day += timedelta(days=1)
    return total_seconds / SECONDS_PER_HOUR


def add_working_hours(calendar, start: datetime, hours: float) -> datetime:
    if start.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")
    if hours == 0:
        return start
    if hours < 0:
        return subtract_working_hours(calendar, start, -hours)

    current = next_working_time(calendar, start)
    remaining_seconds = hours * SECONDS_PER_HOUR

    for _ in range(3660 * 24):
        periods = _periods_for_date(calendar, current.date())
        progressed = False
        for period in periods:
            period_start, period_finish = _period_interval(current.date(), period)
            if current < period_start:
                current = period_start
            if period_start <= current < period_finish:
                available = (period_finish - current).total_seconds()
                if remaining_seconds <= available:
                    return current + timedelta(seconds=remaining_seconds)
                remaining_seconds -= available
                current = period_finish
                progressed = True

        if remaining_seconds <= 0:
            return current

        next_day = current.date() + timedelta(days=1)
        current = datetime.combine(next_day, datetime.min.time())
        current = next_working_time(calendar, current)

    raise ValueError("Calendar has no reachable working time for the requested duration")


def subtract_working_hours(calendar, start: datetime, hours: float) -> datetime:
    if start.tzinfo is not None:
        raise ValueError("Timezone-aware datetimes are not supported")
    if hours == 0:
        return start
    if hours < 0:
        return add_working_hours(calendar, start, -hours)

    current = previous_working_time(calendar, start)
    remaining = hours * SECONDS_PER_HOUR

    for _ in range(3660 * 24):
        periods = _periods_for_date(calendar, current.date())
        for index, period in enumerate(periods):
            period_start, period_finish = _period_interval(current.date(), period)
            if period_start <= current <= period_finish:
                if index > 0:
                    previous_finish = datetime.combine(current.date(), periods[index - 1].finish)
                else:
                    previous_finish = None

                available = (current - period_start).total_seconds()
                if remaining <= available:
                    return current - timedelta(seconds=remaining)

                remaining -= available
                if index > 0:
                    morning_start, morning_finish = _period_interval(current.date(), periods[index - 1])
                    morning_available = (morning_finish - morning_start).total_seconds()
                    if remaining <= morning_available:
                        return morning_finish - timedelta(seconds=max(0.0, remaining - SECONDS_PER_HOUR))
                    remaining -= morning_available
                    current = morning_start
                else:
                    current = period_start
                break

        if remaining <= 0:
            return current

        previous_day = current.date() - timedelta(days=1)
        current = datetime.combine(previous_day, datetime.max.time().replace(microsecond=0))
        current = previous_working_time(calendar, current)

    raise ValueError("Calendar has no reachable previous working time")


def _period_interval(day, period):
    start = datetime.combine(day, period.start)
    finish = datetime.combine(day, period.finish)
    if period.finish.hour == 0 and period.finish <= period.start:
        finish = datetime.combine(day + timedelta(days=1), period.finish)
    return start, finish
