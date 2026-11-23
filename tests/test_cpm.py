from datetime import datetime, time

from app.calendars.models import WorkDay, WorkPeriod, WeeklyWorkPattern
from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Activity, Calendar, Project, Relationship, Schedule, WBS


def test_calendar():
    periods = (WorkPeriod(time(8), time(17)),)
    return Calendar(
        "C1", "Test Calendar", weekly_pattern=WeeklyWorkPattern(tuple(
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
        calendars={"C1": test_calendar()},
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
    assert by_id["3"].calculated_early_finish == datetime(2026, 1, 6, 16)


def test_positive_lag_and_cycle_rejection():
    schedule = make_schedule([
        activity("1", "A", 8),
        activity("2", "B", 8),
    ], [Relationship("R1", "1", "2", "FS", 8)])

    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig())
    assert result.status == "CALCULATED"
    by_id = {item.activity_id: item for item in result.activity_results}
    assert by_id["2"].calculated_early_start == datetime(2026, 1, 6, 0)

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
