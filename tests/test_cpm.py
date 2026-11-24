from copy import deepcopy
from datetime import date, datetime, time, timedelta

import pytest

from app.calendars.models import CalendarException, WorkDay, WorkPeriod, WeeklyWorkPattern
from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Activity, Calendar, Project, Relationship, Schedule, WBS


def make_calendar(calendar_id="C1", periods=None, exceptions=()):
    periods = periods if periods is not None else (WorkPeriod(time(8), time(17)),)
    return Calendar(
        calendar_id, "Test Calendar", exceptions=exceptions, weekly_pattern=WeeklyWorkPattern(tuple(
            WorkDay(i, i not in {5, 6}, periods if i not in {5, 6} else ())
            for i in range(7)
        )),
    )


def activity(task_id, code, duration=40, status="TK_NotStart", calendar_id="C1", start=None, finish=None):
    return Activity(
        activity_id=task_id,
        activity_code=code,
        activity_name=code,
        project_id="P1",
        wbs_id="W1",
        calendar_id=calendar_id,
        raw_status=status,
        status=status,
        raw_activity_type="TT_Task",
        activity_type="task",
        planned_start=start,
        planned_finish=finish,
        original_duration_hours=duration,
        remaining_duration_hours=duration,
        total_float_hours=0,
    )


def make_schedule(activities, relationships):
    schedule = Schedule(
        project=Project("P1", "P1", "Project", datetime(2026, 1, 5, 8)),
        relationships=relationships,
        wbs_nodes={"W1": WBS("W1", "W1", "WBS")},
        calendars={"C1": make_calendar()},
    )
    schedule.activities = {a.activity_id: a for a in activities}
    schedule.rebuild_activity_indexes()
    return schedule


def test_simple_three_activity_fs_chain():
    schedule = make_schedule([
        activity("1", "A", 8),
        activity("2", "B", 8),
        activity("3", "C", 8),
    ], [
        Relationship("R1", "1", "2", "FS", 0),
        Relationship("R2", "2", "3", "FS", 0),
    ])

    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig())
    assert result.status == "CALCULATED"
    by_id = {item.activity_id: item for item in result.activity_results}

    assert by_id["1"].calculated_early_start == datetime(2026, 1, 5, 8)
    assert by_id["1"].calculated_early_finish == datetime(2026, 1, 5, 16)
    assert by_id["2"].calculated_early_start == datetime(2026, 1, 5, 16)
    # Nine-hour weekdays: B consumes Monday 16-17 plus Tuesday 08-15.
    # C consumes Tuesday 15-17 plus Wednesday 08-14.
    assert by_id["2"].calculated_early_finish == datetime(2026, 1, 6, 15)
    assert by_id["3"].calculated_early_start == datetime(2026, 1, 6, 15)
    assert by_id["3"].calculated_early_finish == datetime(2026, 1, 7, 14)


def test_fs_positive_lag():
    schedule = make_schedule([
        activity("1", "A", 8),
        activity("2", "B", 8),
    ], [Relationship("R1", "1", "2", "FS", 8)])

    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig())
    assert result.status == "CALCULATED"
    by_id = {item.activity_id: item for item in result.activity_results}
    # Lag consumes Monday 16-17 (1h) and Tuesday 08-15 (7h).
    assert by_id["2"].calculated_early_start == datetime(2026, 1, 6, 15)
    assert by_id["2"].calculated_early_finish == datetime(2026, 1, 7, 14)


def test_cycle_rejection():
    cyclic = make_schedule([
        activity("1", "A", 8),
        activity("2", "B", 8),
    ], [
        Relationship("R1", "1", "2", "FS", 0),
        Relationship("R2", "2", "1", "FS", 0),
    ])
    result = CPMService().calculate(cyclic, ScheduleGraph(cyclic), CPMConfig())
    assert result.status == "FAILED"
    assert any(d.code == "circular_logic" for d in result.diagnostics)


# The predecessor runs Monday 08-17 and Tuesday 08-17 (18h).
# The successor requires 4h. Each expected pair follows the same nine-hour day.
@pytest.mark.parametrize("kind,lag,start,finish", [
    ("FS", -6, (6, 11), (6, 15)),
    ("FS", 0, (7, 8), (7, 12)),
    ("FS", 6, (7, 14), (8, 9)),
    ("SS", -6, (5, 8), (5, 12)),
    ("SS", 0, (5, 8), (5, 12)),
    ("SS", 6, (5, 14), (6, 9)),
    ("FF", -6, (5, 16), (6, 11)),
    ("FF", 0, (6, 13), (6, 17)),
    ("FF", 6, (7, 10), (7, 14)),
    ("SF", -6, (5, 8), (5, 12)),
    ("SF", 0, (5, 8), (5, 12)),
    ("SF", 6, (5, 10), (5, 14)),
])
def test_relationship_early_dates(kind, lag, start, finish):
    schedule = make_schedule([
        activity("1", "A", 18), activity("2", "B", 4),
    ], [Relationship("R1", "1", "2", kind, lag)])
    result = CPMService().calculate(schedule, ScheduleGraph(schedule))
    assert result.status == "CALCULATED"
    successor = result.activity_results[1]
    assert successor.calculated_early_start == datetime(2026, 1, *start)
    assert successor.calculated_early_finish == datetime(2026, 1, *finish)


@pytest.mark.parametrize("policy", ["SUCCESSOR", "PROJECT", "ELAPSED", "INVALID"])
def test_unsupported_lag_calendar_policy_is_diagnosed(policy):
    schedule = make_schedule([activity("1", "A", 8)], [])
    result = CPMService().calculate(
        schedule, ScheduleGraph(schedule), CPMConfig(lag_calendar_policy=policy),
    )
    assert result.status == "FAILED"
    assert result.activity_results == ()
    assert any(d.code == "unsupported_lag_calendar_policy" for d in result.diagnostics)


def test_calculation_preserves_imported_schedule():
    schedule = make_schedule([
        activity("1", "A", 8, start=datetime(2025, 12, 1, 8), finish=datetime(2025, 12, 1, 16)),
        activity("2", "B", 8, start=datetime(2025, 12, 2, 8), finish=datetime(2025, 12, 2, 16)),
    ], [Relationship("R1", "1", "2", "FS", 0)])
    schedule.activities["1"].total_float_hours = 123
    schedule.activities["1"].free_float_hours = 45
    before = deepcopy(schedule)
    result = CPMService().calculate(schedule, ScheduleGraph(schedule))
    assert result.status == "CALCULATED"
    assert schedule == before
    assert result.activity_results[0].calculated_early_start == datetime(2026, 1, 5, 8)
    assert result.activity_results[0].imported_total_float_hours == 123
    assert result.activity_results[0].imported_free_float_hours == 45


# Predecessor: 08-12 / 13-17, 8h/day. Its 14h run ends Tuesday Jan 6, 15:00.
# Successor: 10-16, 6h/day, 2h duration. Lag always uses PREDECESSOR calendar.
@pytest.mark.parametrize("kind,lag,start,finish", [
    ("FS", 0, (6, 15), (7, 11)),    # Tue 15-16 + Wed 10-11.
    ("FS", 5, (7, 11), (7, 13)),    # Lag Tue 15-17 + Wed 08-11.
    ("FS", -3, (6, 11), (6, 13)),   # Lag back Tue 15-13 + 12-11.
    ("SS", 0, (5, 10), (5, 12)),    # Mon 08 lower bound snaps to 10.
    ("SS", 5, (5, 14), (5, 16)),    # Lag Mon 08-12 + 13-14.
    ("SS", -3, (5, 10), (5, 12)),   # Friday bound is superseded by Data Date.
    ("FF", 0, (6, 13), (6, 15)),    # Two successor hours back from Tue 15.
    ("FF", 5, (6, 15), (7, 11)),    # Required Wed 11; Tue 15-16 + Wed 10-11.
    ("FF", -3, (5, 15), (6, 11)),   # Required Tue 11; Mon 15-16 + Tue 10-11.
    ("SF", 0, (5, 10), (5, 12)),    # Finish bound Mon 08; Data Date controls.
    ("SF", 5, (5, 12), (5, 14)),    # Start Mon 08 + 5 predecessor hours = 14.
    ("SF", -3, (5, 10), (5, 12)),   # Friday bound is superseded by Data Date.
])
def test_different_calendar_early_dates(kind, lag, start, finish):
    schedule=make_schedule([
        activity("1", "A", 14), activity("2", "B", 2, calendar_id="C2"),
    ], [Relationship("R1", "1", "2", kind, lag)])
    schedule.calendars = {
        "C1": make_calendar(periods=(WorkPeriod(time(8),time(12)), WorkPeriod(time(13),time(17)))),
        "C2": make_calendar("C2", periods=(WorkPeriod(time(10),time(16)),)),
    }
    before=deepcopy(schedule)
    config=CPMConfig()
    assert config.lag_calendar_policy == "PREDECESSOR"
    result=CPMService().calculate(schedule, ScheduleGraph(schedule), config)
    assert result.status == "CALCULATED"
    by_id={a.activity_id:a for a in result.activity_results}
    assert by_id["1"].calculated_early_finish == datetime(2026,1,6,15)
    assert by_id["2"].calculated_early_start == datetime(2026,1,*start)
    assert by_id["2"].calculated_early_finish == datetime(2026,1,*finish)
    assert schedule == before


@pytest.mark.parametrize("holiday,expected_day", [(False,12), (True,13)])
def test_forward_split_shift_weekend_and_holiday(holiday, expected_day):
    schedule=make_schedule([activity("1","A",7),activity("2","B",2)],
                           [Relationship("R1","1","2","FS",0)])
    schedule.project.data_date=datetime(2026,1,9,8)  # Friday.
    exceptions=(CalendarException(date(2026,1,12),False),) if holiday else ()
    schedule.calendars["C1"]=make_calendar(periods=(WorkPeriod(time(8),time(12)), WorkPeriod(time(13),time(17))), exceptions=exceptions)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    first,second=result.activity_results
    # A works Friday 08-12 + 13-16. B works Fri 16-17 plus next workday 08-09.
    assert first.calculated_early_finish == datetime(2026,1,9,16)
    assert second.calculated_early_start == datetime(2026,1,9,16)
    assert second.calculated_early_finish == datetime(2026,1,expected_day,9)


def test_forward_milestone_and_start_on_or_after():
    milestone=activity("2","M",0)
    milestone.raw_activity_type="TT_FinMile"
    milestone.activity_type="finish_milestone"
    milestone.primary_constraint_type="START_ON_OR_AFTER"
    milestone.primary_constraint_date=datetime(2026,1,6,10)
    schedule=make_schedule([activity("1","A",8),milestone], [Relationship("R1","1","2","FS",0)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    # Predecessor finishes Monday 16; constraint holds the milestone to Tuesday 10.
    item=result.activity_results[1]
    assert item.calculated_early_start == item.calculated_early_finish == datetime(2026,1,6,10)
    assert item.controlling_predecessor_ids == ()
    assert item.controlling_constraint == "START_ON_OR_AFTER"


def test_forward_start_constraint_in_lunch():
    a=activity("1","A",2)
    a.primary_constraint_type="START_ON_OR_AFTER"
    a.primary_constraint_date=datetime(2026,1,5,12,30)
    schedule=make_schedule([a],[])
    schedule.calendars["C1"]=make_calendar(periods=(WorkPeriod(time(8),time(12)), WorkPeriod(time(13),time(17))))
    item=CPMService().calculate(schedule,ScheduleGraph(schedule)).activity_results[0]
    # Constraint lies in lunch; two hours run from 13 to 15.
    assert item.calculated_early_start == datetime(2026,1,5,13)
    assert item.calculated_early_finish == datetime(2026,1,5,15)


@pytest.mark.parametrize("durations,expected_ids,expected_relationships", [
    ((2,8),("2",),("R2",)), ((8,8),("1","2"),("R1","R2")),
])
def test_forward_latest_and_tied_controlling_predecessors(durations,expected_ids,expected_relationships):
    schedule=make_schedule([activity("1","A",durations[0]),activity("2","B",durations[1]),activity("3","C",1)],
        [Relationship("R1","1","3","FS",0),Relationship("R2","2","3","FS",0)])
    item=CPMService().calculate(schedule,ScheduleGraph(schedule)).activity_results[2]
    # The longest incoming run finishes Mon 16; C works 16-17. Ties retain both.
    assert item.calculated_early_start == datetime(2026,1,5,16)
    assert item.calculated_early_finish == datetime(2026,1,5,17)
    assert item.controlling_predecessor_ids == expected_ids
    assert set(item.controlling_relationship_ids) == set(expected_relationships)


def test_forward_not_started_respects_data_date_and_working_time():
    a=activity("1","A",2,start=datetime(2025,12,1,8))
    schedule=make_schedule([a],[])
    schedule.project.data_date=datetime(2026,1,10,9)  # Saturday; imported planned start is historical.
    item=CPMService().calculate(schedule,ScheduleGraph(schedule)).activity_results[0]
    assert item.calculated_early_start == datetime(2026,1,12,8)
    assert item.calculated_early_finish == datetime(2026,1,12,10)


# Required completion Wed Jan 7 17:00; A=4h, B=6h, nine-hour weekdays.
# Ordinary B: LS Wed 11 / LF Wed 17. SF case additionally caps B at Wed 11,
# giving B LS Tue 14, so SF start bounds are visible before project completion.
@pytest.mark.parametrize("kind,lag,start,finish", [
    ("FS", 0, (6,16), (7,11)),    # A finish <= B start Wed 11; 3h Wed + 1h Tue.
    ("FS", 2, (6,14), (7,9)),     # Remove 2h lag from Wed 11 -> Wed 09.
    ("FS", -2, (7,9), (7,13)),    # Negative lag permits A finish 2h after B start.
    ("SS", 0, (7,11), (7,15)),    # A start <= B start Wed 11.
    ("SS", 2, (7,9), (7,13)),     # A start <= Wed 09; add its own 4h duration.
    ("SS", -2, (7,13), (7,17)),   # A start <= Wed 13.
    ("FF", 0, (7,13), (7,17)),    # A finish <= B finish Wed 17.
    ("FF", 2, (7,11), (7,15)),    # A finish <= Wed 15.
    ("FF", -2, (7,13), (7,17)),   # Link allows Thu 09, but required finish caps at Wed 17.
    ("SF", 0, (7,11), (7,15)),    # A start <= B finish Wed 11.
    ("SF", 2, (7,9), (7,13)),     # A start <= B finish minus 2h = Wed 09.
    ("SF", -2, (7,13), (7,17)),   # A start <= B finish plus 2h = Wed 13.
])
def test_backward_relationship_dates(kind,lag,start,finish):
    a,b=activity("1","A",4),activity("2","B",6)
    if kind == "SF":
        b.primary_constraint_type="FINISH_ON_OR_BEFORE"
        b.primary_constraint_date=datetime(2026,1,7,11)
    schedule=make_schedule([a,b],[Relationship("R1","1","2",kind,lag)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,7,17)))
    assert result.status == "CALCULATED"
    first,second=result.activity_results
    assert first.calculated_late_start == datetime(2026,1,*start)
    assert first.calculated_late_finish == datetime(2026,1,*finish)
    assert second.calculated_late_start == (datetime(2026,1,6,14) if kind == "SF" else datetime(2026,1,7,11))
    assert second.calculated_late_finish == datetime(2026,1,7,11 if kind == "SF" else 17)


@pytest.mark.parametrize("durations,expected_ids", [((2,6),("3",)),((6,6),("2","3"))])
def test_backward_multiple_and_tied_successors(durations,expected_ids):
    schedule=make_schedule([activity("1","A",2),activity("2","B",durations[0]),activity("3","C",durations[1])],
        [Relationship("R1","1","2","FS",0),Relationship("R2","1","3","FS",0)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,7,17)))
    first=result.activity_results[0]
    # Longest successor starts Wed 11; A works Wed 09-11.
    assert first.calculated_late_start == datetime(2026,1,7,9)
    assert first.calculated_late_finish == datetime(2026,1,7,11)
    assert first.controlling_successor_ids == expected_ids
    expected_relationships = {"R1" if activity_id == "2" else "R2" for activity_id in expected_ids}
    assert set(first.controlling_relationship_ids) == expected_relationships


def test_backward_different_calendars_and_split_shifts():
    schedule=make_schedule([activity("1","A",2),activity("2","B",2,calendar_id="C2")],
        [Relationship("R1","1","2","FS",3)])
    schedule.calendars={
        "C1":make_calendar(periods=(WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17)))),
        "C2":make_calendar("C2",periods=(WorkPeriod(time(10),time(16)),)),
    }
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,7,16)))
    a,b=result.activity_results
    # B Wed 14-16. Remove 3 predecessor-calendar hours: 14-13 (1), 12-10 (2).
    # A then works Wed 08-10. Successor-calendar lag would incorrectly allow 11.
    assert b.calculated_late_start == datetime(2026,1,7,14)
    assert b.calculated_late_finish == datetime(2026,1,7,16)
    assert a.calculated_late_start == datetime(2026,1,7,8)
    assert a.calculated_late_finish == datetime(2026,1,7,10)


@pytest.mark.parametrize("kind,lag,start,finish", [
    ("FS",0,(7,11),(7,14)),   # B starts Wed 14; A works 11-12 + 13-14.
    ("FS",3,(7,8),(7,10)),    # Remove 14-13 + 12-10 lag; A works 08-10.
    ("FS",-3,(7,14),(7,16)),  # Link allows Wed 17; project cap is Wed 16.
    ("SS",0,(7,14),(7,16)),   # Start <= B start Wed 14; duration 2h.
    ("SS",3,(7,10),(7,12)),   # Start <= Wed 10; duration 2h.
    ("SS",-3,(7,14),(7,16)),  # Link allows start 17; project cap controls.
    ("FF",0,(7,14),(7,16)),   # Finish <= B finish Wed 16.
    ("FF",3,(7,10),(7,12)),   # Finish bound 13; previous work closes at 12.
    ("FF",-3,(7,14),(7,16)),  # Link allows Thu 10; project cap controls.
    ("SF",0,(7,14),(7,16)),   # Start bound 16; project cap controls.
    ("SF",3,(7,13),(7,15)),   # Start <= Wed 13; two work hours to 15.
    ("SF",-3,(7,14),(7,16)),  # Link allows Thu 10; project cap controls.
])
def test_backward_cross_calendar_relationship_dates(kind,lag,start,finish):
    schedule=make_schedule([activity("1","A",2),activity("2","B",2,calendar_id="C2")],
        [Relationship("R1","1","2",kind,lag)])
    schedule.calendars={
        "C1":make_calendar(periods=(WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17)))),
        "C2":make_calendar("C2",periods=(WorkPeriod(time(10),time(16)),)),
    }
    before=deepcopy(schedule)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,7,16)))
    assert result.status == "CALCULATED"
    a,b=result.activity_results
    assert a.calculated_late_start == datetime(2026,1,*start)
    assert a.calculated_late_finish == datetime(2026,1,*finish)
    assert b.calculated_late_start == datetime(2026,1,7,14)
    assert b.calculated_late_finish == datetime(2026,1,7,16)
    assert schedule == before


def test_forward_finish_bound_in_successor_nonworking_gap_is_inverted():
    schedule=make_schedule([activity("1","A",6),activity("2","B",1,calendar_id="C2")],
        [Relationship("R1","1","2","FF",0)])
    schedule.calendars["C2"]=make_calendar("C2",periods=(WorkPeriod(time(10),time(12)),))
    # One tick after Mon 11 is the earliest start whose one working hour
    # finishes after Mon 14: Tue 10 + one microsecond. The previous tick
    # finishes Mon 12, which is too early. Keep the raw FF inequality.
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert result.status == "CALCULATED"
    item = result.activity_results[1]
    assert item.calculated_early_start == datetime(2026,1,5,11) + datetime.resolution
    assert item.calculated_early_finish == datetime(2026,1,6,10) + datetime.resolution


def test_reverse_negative_lag_at_calendar_opening_is_inverted():
    schedule=make_schedule([activity("1","A",2),activity("2","B",4,calendar_id="C2")],
        [Relationship("R1","1","2","FS",-2)])
    schedule.calendars["C2"]=make_calendar("C2",periods=(WorkPeriod(time(7),time(11)),))
    # B late start is Wed 07. Latest A finish is one tick before Wed 10;
    # its negative lag lands Tue 17 minus one tick, safely before B's start.
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,7,11)))
    assert result.status == "CALCULATED"
    item = result.activity_results[0]
    assert item.calculated_late_finish == datetime(2026,1,7,10) - datetime.resolution
    assert item.calculated_late_start == datetime(2026,1,6,17) - datetime.resolution
