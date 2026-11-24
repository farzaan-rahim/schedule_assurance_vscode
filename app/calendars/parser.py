from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, time

from app.calendars.models import (
    CalendarDiagnostic,
    CalendarDiagnosticSeverity,
    CalendarException,
    P6Calendar,
    WorkDay,
    WorkPeriod,
    WeeklyWorkPattern,
)


P6_EPOCH = date(1899, 12, 30)


def _parse_time(value: str) -> time | None:
    value = value.strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value)
    if not match:
        return None
    hour, minute, second = int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)
    try:
        return time(hour, minute, second)
    except ValueError:
        return None


def _parse_p6_date_serial(value: str) -> date | None:
    try:
        serial = int(value)
        return P6_EPOCH + __import__("datetime").timedelta(days=serial)
    except (ValueError, OverflowError):
        return None


def parse_calendar_data(calendar) -> object:
    raw = calendar.raw_clndr_data or ""
    diagnostics: list[CalendarDiagnostic] = list(calendar.diagnostics)

    if not raw:
        return calendar

    if raw.strip() == "(0||()())":
        diagnostics.append(CalendarDiagnostic(
            code="empty_calendar_data", message="P6 calendar has no weekday or exception structure.",
            severity=CalendarDiagnosticSeverity.WARNING, calendar_id=calendar.calendar_id,
            raw_value=raw,
        ))
        return replace(calendar, diagnostics=tuple(diagnostics))

    if "DaysOfWeek" not in raw:
        days = tuple(WorkDay(weekday=i, working=False) for i in range(7))
        diagnostics.append(CalendarDiagnostic(
            code="calendar_weekdata_unrecognized",
            message="The observed P6 weekday structure could not be parsed.",
            severity=CalendarDiagnosticSeverity.WARNING,
            calendar_id=calendar.calendar_id,
            raw_value=raw,
        ))
    else:
        days = _parse_weekdays(raw, calendar.calendar_id, diagnostics)

    exceptions = _parse_exceptions(raw, calendar.calendar_id, diagnostics)

    return replace(
        calendar,
        weekly_pattern=WeeklyWorkPattern(days=days),
        exceptions=tuple(exceptions),
        diagnostics=tuple(diagnostics),
    )


def _parse_weekdays(content: str, calendar_id: str, diagnostics: list[CalendarDiagnostic]) -> tuple[WorkDay, ...]:
    days: dict[int, WorkDay] = {}
    markers = list(re.finditer(r"\(0\|\|(\d+)\(\)", content))

    for index, marker in enumerate(markers):
        p6_day = int(marker.group(1))
        if p6_day < 1 or p6_day > 7:
            continue
        end = markers[index + 1].start() if index + 1 < len(markers) else len(content)
        exception_start = content.find("Exceptions")
        if exception_start >= 0:
            end = min(end, exception_start)
        body = content[marker.end():end]
        periods: list[WorkPeriod] = []

        for period_match in re.finditer(r"f\|([^|)]+)\|s\|([^|)]+)", body):
            finish = _parse_time(period_match.group(1))
            start_time = _parse_time(period_match.group(2))
            if start_time is None or finish is None:
                diagnostics.append(CalendarDiagnostic(
                    code="malformed_work_period", message="Calendar contains an invalid work period time.",
                    severity=CalendarDiagnosticSeverity.ERROR, calendar_id=calendar_id,
                    raw_value=period_match.group(0),
                ))
                continue
            # A finish at/before start denotes an overnight/full-day shift.
            periods.append(WorkPeriod(start=start_time, finish=finish))

        periods.sort(key=lambda period: period.start)
        for left, right in zip(periods, periods[1:]):
            if left.finish > right.start and left.finish != time(0, 0):
                diagnostics.append(CalendarDiagnostic(
                    code="overlapping_work_periods", message="Calendar contains overlapping work periods.",
                    severity=CalendarDiagnosticSeverity.WARNING, calendar_id=calendar_id,
                    raw_value=(left, right),
                ))

        python_weekday = (p6_day - 2) % 7
        days[python_weekday] = WorkDay(weekday=python_weekday, working=bool(periods), periods=tuple(periods))

    return tuple(days.get(i, WorkDay(weekday=i, working=False)) for i in range(7))


def _parse_exceptions(raw: str, calendar_id: str, diagnostics: list[CalendarDiagnostic]) -> list[CalendarException]:
    matches = list(re.finditer(r"\(0\|\|\d+\(d\|(-?\d+)\)", raw))
    exceptions: list[CalendarException] = []

    for index, match in enumerate(matches):
        exception_date = _parse_p6_date_serial(match.group(1))
        if exception_date is None:
            diagnostics.append(CalendarDiagnostic(
                code="exception_invalid_date", message="Calendar exception has an invalid P6 date serial.",
                severity=CalendarDiagnosticSeverity.ERROR, calendar_id=calendar_id,
                raw_value=match.group(1),
            ))
            continue

        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        body = raw[match.end():end]
        periods: list[WorkPeriod] = []

        for period_match in re.finditer(r"f\|([^|)]+)\|s\|([^|)]+)", body):
            finish = _parse_time(period_match.group(1))
            start = _parse_time(period_match.group(2))
            if start is None or finish is None:
                diagnostics.append(CalendarDiagnostic(
                    code="malformed_work_period", message="Calendar exception contains an invalid work period time.",
                    severity=CalendarDiagnosticSeverity.ERROR, calendar_id=calendar_id,
                    raw_value=period_match.group(0),
                ))
                continue
            # A finish at/before start denotes an overnight/full-day shift.
            periods.append(WorkPeriod(start=start, finish=finish))

        periods.sort(key=lambda period: period.start)
        exceptions.append(CalendarException(exception_date, bool(periods), tuple(periods)))

    return exceptions
