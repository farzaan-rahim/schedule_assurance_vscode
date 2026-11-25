"""Proprietary-free reductions of defects observed during genuine-XER validation."""
from datetime import date, datetime, time

import pytest

from app.calendars.models import WorkPeriod
from app.calendars.parser import parse_calendar_data
from app.calendars.working_time import add_working_hours
from app.models.schedule import Calendar


def period(start,finish,start_first):
    return f"s|{start}|f|{finish}" if start_first else f"f|{finish}|s|{start}"


@pytest.mark.parametrize("start_first",[False,True])
def test_calendar_weekly_period_keys_are_order_independent(start_first):
    morning=period("08:00","12:00",start_first)
    afternoon=period("13:00","17:00",start_first)
    raw=f"(0||CalendarData()((0||DaysOfWeek()((0||1()())(0||2()((0||0({morning})())(0||1({afternoon})())))(0||7()())))))"
    calendar=parse_calendar_data(Calendar("C","Synthetic calendar",raw_clndr_data=raw))
    assert calendar.weekly_pattern.days[0].periods == (WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17)))
    assert add_working_hours(calendar,datetime(2026,1,5,8),8) == datetime(2026,1,5,17)


@pytest.mark.parametrize("start_first",[False,True])
def test_calendar_working_exception_keys_are_order_independent(start_first):
    serial=(date(2026,1,6)-date(1899,12,30)).days
    work=period("09:00","11:00",start_first)
    raw=f"(0||CalendarData()((0||DaysOfWeek()((0||1()())(0||2()())))(0||Exceptions()((0||0(d|{serial})((0||0({work})())))))))"
    calendar=parse_calendar_data(Calendar("C","Synthetic calendar",raw_clndr_data=raw))
    assert calendar.exceptions[0].periods == (WorkPeriod(time(9),time(11)),)
    assert add_working_hours(calendar,datetime(2026,1,6,9),2) == datetime(2026,1,6,11)



@pytest.mark.parametrize("raw,expected",[
    ("CS_MSOA","START_ON_OR_AFTER"),
    ("CS_MEOB","FINISH_ON_OR_BEFORE"),
    ("CS_MEOA","FINISH_ON_OR_AFTER"),
    ("CS_MSOB","START_ON_OR_BEFORE"),
])
def test_observed_p6_constraint_codes_have_the_correct_identity(raw,expected):
    from app.importers.p6_normalization import normalize_constraint_type
    assert normalize_constraint_type(raw) == expected


def test_observed_p6_loe_code_uses_existing_exclusion_policy():
    from app.importers.p6_normalization import normalize_activity_type
    from app.cpm.activity_state import activity_decision
    from app.cpm.config import CPMConfig
    from tests.test_cpm import activity
    a=activity("A","A",2)
    a.raw_activity_type="TT_LOE"
    assert normalize_activity_type(a.raw_activity_type) == "level_of_effort"
    state,findings,disposition=activity_decision(a,CPMConfig(),datetime(2026,1,5,8))
    assert state is None and disposition == "EXCLUDE"
    assert findings[0].code == "loe_not_supported"


@pytest.mark.parametrize("raw,expected_field,expected_date",[
    ("CS_MSOA","calculated_early_start",datetime(2026,1,6,10)),
    ("CS_MEOB","calculated_late_finish",datetime(2026,1,6,10)),
])
def test_observed_alias_uses_existing_constraint_math(raw,expected_field,expected_date):
    from app.importers.p6_normalization import normalize_constraint_type
    from app.cpm.config import CPMConfig
    from app.cpm.service import CPMService
    from app.graph.schedule_graph import ScheduleGraph
    from tests.test_cpm import activity,make_schedule
    a=activity("A","A",2)
    a.primary_constraint_type=normalize_constraint_type(raw)
    a.primary_constraint_date=expected_date
    schedule=make_schedule([a],[])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,6,17)))
    assert result.status == "CALCULATED"
    assert getattr(result.activity_results[0],expected_field) == expected_date
