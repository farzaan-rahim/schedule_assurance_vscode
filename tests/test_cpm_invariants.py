from copy import deepcopy
from datetime import datetime, time, timedelta

import pytest

from app.calendars.working_time import add_working_hours, subtract_working_hours, working_hours_between
from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule


def assert_date_invariants(result):
    assert result.status == "CALCULATED", result.diagnostics
    for item in result.activity_results:
        a=result.schedule.activities_by_id[item.activity_id]
        cal=result.schedule.calendars[item.effective_calendar_id]
        if item.effective_state == "COMPLETE":
            assert (item.calculated_early_start,item.calculated_early_finish) == (a.actual_start,a.actual_finish)
            assert (item.calculated_late_start,item.calculated_late_finish) == (a.actual_start,a.actual_finish)
        else:
            assert item.calculated_early_finish == add_working_hours(cal,item.calculated_early_start,item.effective_duration_hours)
            assert item.calculated_late_start == subtract_working_hours(cal,item.calculated_late_finish,item.effective_duration_hours)


def test_thousand_activity_chain_is_iterative_and_deterministic():
    schedule=make_schedule([activity(str(i),f"A{i}",1) for i in range(1000)],
        [Relationship(f"R{i}",str(i),str(i+1),"FS",0) for i in range(999)])
    before=deepcopy(schedule)
    graph=ScheduleGraph(schedule)
    first=CPMService().calculate(schedule,graph)
    second=CPMService().calculate(schedule,graph)
    assert first == second
    assert schedule == before
    assert len(first.activity_results) == 1000
    assert_date_invariants(first)
    assert all(a.calculated_total_float_hours == 0 for a in first.activity_results)
    assert working_hours_between(schedule.calendars["C1"],first.activity_results[0].calculated_early_start,first.activity_results[-1].calculated_early_finish) == 1000
    assert len(first.critical_paths) == 1
    assert first.critical_paths[0].activity_ids[-1] == "999"
    assert first.critical_paths[0].truncated  # Default depth remains the visible 500-node bound.
    assert first.path_statistics[0].truncated
    assert first.near_critical_paths == ()


def test_broad_fan_in_fan_out_and_tied_provenance():
    sources=[activity(f"S{i}",f"SRC{i}",i%8+1) for i in range(200)]
    sinks=[activity(f"T{i}",f"DST{i}",3) for i in range(200)]
    rels=[Relationship(f"IN{i}",a.activity_id,"JOIN","FS",0) for i,a in enumerate(sources)]
    rels += [Relationship(f"OUT{i}","JOIN",a.activity_id,"FS",0) for i,a in enumerate(sinks)]
    schedule=make_schedule(sources+[activity("JOIN","JOIN",1)]+sinks,rels)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert_date_invariants(result)
    join=next(a for a in result.activity_results if a.activity_id == "JOIN")
    assert join.calculated_early_start == datetime(2026,1,5,16)
    assert join.calculated_early_finish == datetime(2026,1,5,17)
    assert len(join.controlling_predecessor_ids) == 25
    assert len(join.controlling_successor_ids) == 200
    assert all(c.tied for c in join.controlling_relationships)
    for c in join.controlling_relationships:
        assert c.relationship_type == "FS" and c.lag_hours == 0
        assert c.lag_calendar_policy == "PREDECESSOR" and c.lag_calendar_id == "C1"
        assert c.predecessor_code == schedule.activities_by_id[c.predecessor_id].activity_code
        assert c.successor_code == schedule.activities_by_id[c.successor_id].activity_code
        assert c.required_timestamp == (join.calculated_early_start if c.direction == "FORWARD" else join.calculated_late_finish)


def test_relationship_and_constraint_are_separate_tied_causes():
    a,b=activity("1","A",4),activity("2","B",2)
    b.primary_constraint_type="START_ON_OR_AFTER"
    b.primary_constraint_date=datetime(2026,1,5,12)
    schedule=make_schedule([a,b],[Relationship("R","1","2","FS",0)])
    item=CPMService().calculate(schedule,ScheduleGraph(schedule)).activity_results[1]
    assert len(item.controlling_relationships) == len(item.controlling_constraints) == 1
    assert item.controlling_constraints[0].tied_with_relationship
    assert item.controlling_constraints[0].constraint_date == datetime(2026,1,5,12)
    assert item.controlling_relationships[0].required_timestamp == datetime(2026,1,5,12)


def test_both_constraint_slots_are_applied():
    a=activity("1","A",2)
    a.primary_constraint_type="START_ON_OR_AFTER"
    a.primary_constraint_date=datetime(2026,1,5,10)
    a.secondary_constraint_type="FINISH_ON_OR_BEFORE"
    a.secondary_constraint_date=datetime(2026,1,5,15)
    schedule=make_schedule([a],[])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(required_project_finish=datetime(2026,1,5,17)))
    assert_date_invariants(result)
    item=result.activity_results[0]
    assert item.calculated_early_start == datetime(2026,1,5,10)
    assert item.calculated_late_finish == datetime(2026,1,5,15)
    assert {c.constraint_type for c in item.controlling_constraints} == {"START_ON_OR_AFTER","FINISH_ON_OR_BEFORE"}


@pytest.mark.parametrize("direction", ["forward", "backward"])
def test_protective_relationship_audit_remains_active(monkeypatch,direction):
    import app.cpm.service as module
    name=direction+"_pass"
    original=getattr(module,name)
    def broken(*args,**kwargs):
        result=original(*args,**kwargs)
        result["early_finishes" if direction == "forward" else "late_finishes"]["1"]+=timedelta(hours=1)
        return result
    monkeypatch.setattr(module,name,broken)
    schedule=make_schedule([activity("1","A",2),activity("2","B",2)],[Relationship("R","1","2","FS",0)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert result.status == "FAILED" and result.activity_results == ()
    assert any(d.code == "unsupported_calendar_relationship_boundary" and d.metadata["pass"] == direction for d in result.diagnostics)


def test_cpm_overnight_dates_and_float_obey_invariants():
    from app.calendars.models import WorkPeriod
    from tests.test_cpm import make_calendar
    schedule=make_schedule([activity("1","NIGHT",4)],[])
    schedule.calendars["C1"]=make_calendar(periods=(WorkPeriod(time(20),time(4)),))
    schedule.project.data_date=datetime(2026,1,5,22)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert_date_invariants(result)
    item=result.activity_results[0]
    assert item.calculated_early_finish == datetime(2026,1,6,2)
    assert item.calculated_total_float_hours == 0
