from datetime import date, datetime, time, timedelta

import pytest

from app.calendars.models import CalendarException, WorkDay, WorkPeriod, WeeklyWorkPattern
from app.calendars.parser import parse_calendar_data
from app.calendars.resolver import resolve_calendar_inheritance
from app.calendars.working_time import (
    add_working_hours,
    is_working_time,
    next_working_time,
    previous_working_time,
    subtract_working_hours,
    working_hours_between,
)
from app.models.schedule import Calendar, Schedule


def calendar(calendar_id="C1", periods=None, exceptions=(), base_id=None):
    periods = periods if periods is not None else (
        WorkPeriod(time(8), time(12)),
        WorkPeriod(time(13), time(17)),
    )
    days = tuple(
        WorkDay(i, i not in {5, 6}, periods if i not in {5, 6} else ())
        for i in range(7)
    )
    return Calendar(
        calendar_id=calendar_id,
        calendar_name="Test",
        base_calendar_id=base_id,
        weekly_pattern=WeeklyWorkPattern(days),
        exceptions=tuple(exceptions),
        raw_clndr_data="test",
    )


def test_split_shift_boundaries_lunch_and_weekend():
    cal = calendar()
    assert is_working_time(cal, datetime(2026, 11, 20, 8, 0)) is True
    assert is_working_time(cal, datetime(2026, 11, 20, 12, 0)) is False
    assert is_working_time(cal, datetime(2026, 11, 20, 13, 0)) is True
    assert is_working_time(cal, datetime(2026, 11, 20, 17, 0)) is False
    assert is_working_time(cal, datetime(2026, 11, 21, 9, 0)) is False


def test_holiday_and_working_exception():
    holiday = CalendarException(date(2026, 11, 20), False)
    work_day = CalendarException(date(2026, 11, 21), True, (
        WorkPeriod(time(9), time(11)),
    ))
    cal = calendar(exceptions=(holiday, work_day))
    assert is_working_time(cal, datetime(2026, 11, 20, 9)) is False
    assert is_working_time(cal, datetime(2026, 11, 21, 9)) is True


def test_next_and_previous_working_time():
    cal = calendar()
    friday = datetime(2026, 11, 20, 12)
    assert next_working_time(cal, friday) == datetime(2026, 11, 20, 13)
    assert next_working_time(cal, datetime(2026, 11, 21, 9)) == datetime(2026, 11, 23, 8)
    assert previous_working_time(cal, datetime(2026, 11, 23, 7)) == datetime(2026, 11, 20, 17)


def test_working_duration_across_lunch_and_weekend():
    cal = calendar()
    assert working_hours_between(cal, datetime(2026, 11, 20, 11), datetime(2026, 11, 20, 14)) == 2
    assert working_hours_between(cal, datetime(2026, 11, 20, 16), datetime(2026, 11, 23, 9)) == 2
    assert working_hours_between(cal, datetime(2026, 11, 20, 14), datetime(2026, 11, 20, 11)) == -2


def test_add_and_subtract_working_hours():
    cal = calendar()
    assert add_working_hours(cal, datetime(2026, 11, 20, 11), 2) == datetime(2026, 11, 20, 14)
    assert add_working_hours(cal, datetime(2026, 11, 20, 17), 8) == datetime(2026, 11, 23, 17)
    assert add_working_hours(cal, datetime(2026, 11, 20, 9), 0) == datetime(2026, 11, 20, 9)
    # 14-13 (1h), skip lunch, then 12-11 (1h).
    assert subtract_working_hours(cal, datetime(2026, 11, 20, 14), 2) == datetime(2026, 11, 20, 11)


def test_calendar_inheritance_missing_and_cycle():
    base = calendar("BASE")
    child = calendar("CHILD", base_id="BASE")
    child = Calendar(
        calendar_id="CHILD", calendar_name="Child", base_calendar_id="BASE",
        weekly_pattern=None, exceptions=(), raw_clndr_data="(0||()())",
    )
    calendars = {"BASE": base, "CHILD": child}
    resolved, diagnostics = resolve_calendar_inheritance(calendars)
    assert resolved["CHILD"].weekly_pattern is not None

    missing, missing_diagnostics = resolve_calendar_inheritance({"CHILD": child})
    assert any(d.code == "missing_base_calendar" for d in missing_diagnostics)

    cycle_a = calendar("A", base_id="B")
    cycle_a = Calendar("A", "A", base_calendar_id="B")
    cycle_b = Calendar("B", "B", base_calendar_id="A")
    _, cycle_diagnostics = resolve_calendar_inheritance({"A": cycle_a, "B": cycle_b})
    assert any(d.code == "circular_calendar_inheritance" for d in cycle_diagnostics)


def test_p6_calendar_data_parser_split_shift_and_holiday():
    raw = "(0||CalendarData()((0||DaysOfWeek()((0||1()())(0||2()((0||0(f|12:00|s|08:00)())(0||1(f|17:00|s|13:00)())))(0||7()())))(0||Exceptions()((0||0(d|46000)())(0||1(d|46001)((0||0(f|11:00|s|09:00)()))))))"
    cal = Calendar("C1", "Test", raw_clndr_data=raw)
    parsed = parse_calendar_data(cal)

    assert parsed.weekly_pattern is not None
    monday = parsed.weekly_pattern.days[0]
    assert monday.working is True
    assert len(monday.periods) == 2
    assert len(parsed.exceptions) == 2


@pytest.mark.external_xer
def test_real_xer_calendars_and_activity_coverage():
    from app.services.schedule_import import ScheduleImportService

    result = ScheduleImportService().import_file("sample_data/NRG00800.xer")
    assert result.succeeded
    schedule = result.schedule
    assert schedule is not None

    assert len(schedule.calendars) == 5
    missing = [a.activity_id for a in schedule.activities.values() if a.calendar_id not in schedule.calendars]
    assert missing == []

    from app.calendars.service import CalendarService
    service = CalendarService()
    calendar_5829 = schedule.calendars["5829"]
    assert is_working_time(calendar_5829, datetime(2011, 8, 1, 9)) is True
    assert next_working_time(calendar_5829, datetime(2011, 7, 30, 17)) == datetime(2011, 8, 1, 8)


@pytest.mark.parametrize("hours,expected", [
    (1, datetime(2026, 11, 20, 13)),
    (2, datetime(2026, 11, 20, 11)),
    (3, datetime(2026, 11, 20, 10)),
    (4, datetime(2026, 11, 20, 9)),
    # 14-13 = 1h; 12-08 = 4h. Five hours ends at 08:00.
    (5, datetime(2026, 11, 20, 8)),
    (6, datetime(2026, 11, 19, 16)),
])
def test_subtract_across_lunch(hours, expected):
    cal = calendar()
    end = datetime(2026, 11, 20, 14)
    result = subtract_working_hours(cal, end, hours)
    assert result == expected
    assert working_hours_between(cal, result, end) == hours


@pytest.mark.parametrize("hour,minute", [(13, 0), (12, 0), (12, 30)])
def test_subtract_period_boundary_and_gap(hour, minute):
    # Positive subtraction from the afternoon opening or lunch resumes at
    # the morning closing (12:00), then consumes one hour to 11:00.
    cal = calendar()
    end = datetime(2026, 11, 20, hour, minute)
    assert subtract_working_hours(cal, end, 1) == datetime(2026, 11, 20, 11)
    # Zero hours preserves the supplied instant, including non-working time.
    assert subtract_working_hours(cal, end, 0) == end


def test_subtract_weekend_and_holiday():
    cal = calendar(exceptions=(CalendarException(date(2026, 11, 20), False),))
    # Monday 09-08 = 1h; Friday holiday and weekend skipped; Thursday 17-16 = 1h.
    end = datetime(2026, 11, 23, 9)
    result = subtract_working_hours(cal, end, 2)
    assert result == datetime(2026, 11, 19, 16)
    assert working_hours_between(cal, result, end) == 2
    assert subtract_working_hours(calendar(), end, 2) == datetime(2026, 11, 20, 16)


@pytest.mark.parametrize("start", [
    datetime(2026, 11, 19, 8), datetime(2026, 11, 19, 11),
    datetime(2026, 11, 19, 12, 30), datetime(2026, 11, 19, 13),
    datetime(2026, 11, 19, 17), datetime(2026, 11, 21, 10),
])
@pytest.mark.parametrize("hours", [0.5, 2, 5, 17.25])
def test_working_time_add_subtract_inverse(start, hours):
    cal = calendar(exceptions=(CalendarException(date(2026, 11, 20), False),))
    finish = add_working_hours(cal, start, hours)
    recovered = subtract_working_hours(cal, finish, hours)
    # Forward positive work normalizes starts in gaps to the next working time.
    assert recovered == next_working_time(cal, start)
    assert working_hours_between(cal, recovered, finish) == hours


def test_subtract_three_periods_without_assuming_gap_length():
    cal = calendar(periods=(
        WorkPeriod(time(6), time(8)), WorkPeriod(time(10), time(12)),
        WorkPeriod(time(15), time(18)),
    ))
    # 18-15 (3h) + 12-10 (2h) + 08-07 (1h); gaps consume no work.
    end = datetime(2026, 11, 20, 18)
    assert subtract_working_hours(cal, end, 6) == datetime(2026, 11, 20, 7)
