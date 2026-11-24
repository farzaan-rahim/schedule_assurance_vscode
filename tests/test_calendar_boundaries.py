from datetime import date, datetime, time, timedelta

import pytest

from app.calendars.models import CalendarException, WorkPeriod
from app.calendars.working_time import (
    add_working_hours, subtract_working_hours, working_hours_between,
    next_working_time, previous_working_time, is_working_time,
)
from tests.test_calendars import calendar


@pytest.mark.parametrize("stamp", [
    datetime(2026, 1, 5, 8), datetime(2026, 1, 5, 12),
    datetime(2026, 1, 5, 12, 30), datetime(2026, 1, 5, 13),
    datetime(2026, 1, 5, 17), datetime(2026, 1, 10),
    datetime(2026, 1, 12, 8), datetime(2026, 1, 10, 10),
])
@pytest.mark.parametrize("hours", [0.25, 1, 5.5])
def test_bidirectional_boundary_inverses(stamp, hours):
    cal = calendar(exceptions=(
        CalendarException(date(2026, 1, 12), False),
        CalendarException(date(2026, 1, 10), True, (WorkPeriod(time(9), time(11)),)),
    ))
    end = add_working_hours(cal, stamp, hours)
    recovered = subtract_working_hours(cal, end, hours)
    assert working_hours_between(cal, recovered, next_working_time(cal, stamp)) == 0
    assert working_hours_between(cal, recovered, end) == hours
    start = subtract_working_hours(cal, stamp, hours)
    recovered = add_working_hours(cal, start, hours)
    assert working_hours_between(cal, recovered, previous_working_time(cal, stamp)) == 0
    assert working_hours_between(cal, start, recovered) == hours


def test_adjacent_periods_have_no_gap():
    cal = calendar(periods=(WorkPeriod(time(8), time(12)), WorkPeriod(time(12), time(17))))
    assert add_working_hours(cal, datetime(2026, 1, 5, 11), 2) == datetime(2026, 1, 5, 13)
    assert subtract_working_hours(cal, datetime(2026, 1, 5, 13), 2) == datetime(2026, 1, 5, 11)


@pytest.mark.parametrize("finish", [time(0), time(4)])
def test_overnight_and_midnight_intervals(finish):
    cal = calendar(periods=(WorkPeriod(time(20), finish),))
    begin = datetime(2026, 1, 5, 22)
    end = datetime(2026, 1, 6, 0 if finish == time(0) else 2)
    hours = 2 if finish == time(0) else 4
    assert working_hours_between(cal, begin, end) == hours
    assert add_working_hours(cal, begin, hours) == end
    assert subtract_working_hours(cal, end, hours) == begin
    if finish != time(0):
        assert is_working_time(cal, datetime(2026, 1, 6, 1))
        assert next_working_time(cal, datetime(2026, 1, 6, 1)) == datetime(2026, 1, 6, 1)
        assert previous_working_time(cal, datetime(2026, 1, 6, 1)) == datetime(2026, 1, 6, 1)


@pytest.mark.parametrize("hours", [0.0, -0.0])
def test_zero_is_identity_and_signed_operations_agree(hours):
    cal = calendar()
    gap = datetime(2026, 1, 5, 12, 30)
    assert add_working_hours(cal, gap, hours) == gap
    assert subtract_working_hours(cal, gap, hours) == gap
    assert add_working_hours(cal, gap, -0.5) == subtract_working_hours(cal, gap, 0.5)
    assert subtract_working_hours(cal, gap, -0.5) == add_working_hours(cal, gap, 0.5)


@pytest.mark.parametrize("lag", [-2, -0.25, 0, 0.25, 2])
def test_inverse_lag_deadline_is_exact_and_maximal(lag):
    from app.calendars.working_time import inverse_lag_deadline
    cal = calendar()
    bound = datetime(2026, 1, 7, 7)
    result = inverse_lag_deadline(cal, bound, lag)
    assert add_working_hours(cal, result, lag) <= bound
    assert add_working_hours(cal, result + datetime.resolution, lag) > bound


def test_finish_lower_bound_inverse_is_exact_and_minimal():
    from app.calendars.working_time import start_for_finish_not_before
    cal = calendar(periods=(WorkPeriod(time(10), time(12)),))
    bound = datetime(2026, 1, 5, 14)
    result = start_for_finish_not_before(cal, bound, 1)
    assert add_working_hours(cal, result, 1) >= bound
    assert add_working_hours(cal, result - datetime.resolution, 1) < bound


def test_working_exception_overnight_belongs_to_origin_day():
    cal=calendar(exceptions=(CalendarException(date(2026,1,10),True,(WorkPeriod(time(22),time(2)),)),))
    begin,end=datetime(2026,1,10,23),datetime(2026,1,11,1)
    assert add_working_hours(cal,begin,2) == end
    assert subtract_working_hours(cal,end,2) == begin
    assert working_hours_between(cal,begin,end) == 2


def test_parser_preserves_overnight_shift():
    from app.calendars.parser import parse_calendar_data
    from app.models.schedule import Calendar
    raw="(0||CalendarData()((0||DaysOfWeek()((0||2()((0||0(f|04:00|s|20:00)())))))))"
    cal=parse_calendar_data(Calendar("N","Night",raw_clndr_data=raw))
    assert cal.weekly_pattern.days[0].working
    assert working_hours_between(cal,datetime(2026,1,5,22),datetime(2026,1,6,2)) == 4
