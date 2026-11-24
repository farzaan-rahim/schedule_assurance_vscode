from datetime import datetime, time

import pytest

from app.calendars.models import WorkPeriod
from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.cpm.float_calculation import total_float, free_float
from app.cpm.criticality import classify_criticality
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule, make_calendar


def run(schedule, config=None):
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),config)
    assert result.status == "CALCULATED", result.diagnostics
    return result


def test_simple_critical_chain_float():
    schedule=make_schedule([activity(str(i),str(i),8) for i in range(3)],
        [Relationship("R1","0","1","FS",0),Relationship("R2","1","2","FS",0)])
    result=run(schedule)
    for item in result.activity_results:
        assert item.calculated_total_float_hours == 0
        assert item.calculated_start_float_hours == item.calculated_finish_float_hours == 0
    assert [a.calculated_free_float_hours for a in result.activity_results] == [0,0,None]
    assert len(result.critical_paths) == 1
    assert result.critical_paths[0].activity_ids == ("0", "1", "2")


def test_shorter_parallel_path_float():
    schedule=make_schedule([activity("1","A",4),activity("2","B",8),activity("3","C",1)],
        [Relationship("R1","1","3","FS",0),Relationship("R2","2","3","FS",0)])
    result=run(schedule)
    # C starts Mon 16. A has Mon 12-16 = 4 working hours to spare.
    assert [a.calculated_total_float_hours for a in result.activity_results] == [4,0,0]
    assert [a.calculated_free_float_hours for a in result.activity_results] == [4,0,None]


@pytest.mark.parametrize("duration,required,expected", [(4,17,5),(8,15,-1),(2.5,10,-0.5)])
def test_required_finish_signed_fractional_float(duration,required,expected):
    result=run(make_schedule([activity("1","A",duration)],[]),CPMConfig(required_project_finish=datetime(2026,1,5,required)))
    item=result.activity_results[0]
    assert item.calculated_total_float_hours == expected
    assert item.calculated_start_float_hours == item.calculated_finish_float_hours == expected


@pytest.mark.parametrize("kind,lag,tf_b,ff_a", [
    ("FS",2,0,0),("FS",-2,0,0),
    ("SS",2,0,0),("SS",-2,2,2),
    ("FF",2,0,0),("FF",-2,2,0),
    ("SF",6,0,0),("SF",-2,2,4),
])
def test_relationship_float_formulas(kind,lag,tf_b,ff_a):
    # A works Mon 08-12 (4h); B takes 2h. Anchor is latest activity finish.
    # FS +/-2: B 14-16 / 10-12. SS +/-2: B 10-12 / 08-10.
    # FF +/-2: B 12-14 / 08-10. SF +6/-2: B 12-14 / 08-10.
    # Negative SS/SF leave start-endpoint slack even while A's TF is zero.
    schedule=make_schedule([activity("1","A",4),activity("2","B",2)],
        [Relationship("R1","1","2",kind,lag)])
    a,b=run(schedule).activity_results
    assert a.calculated_total_float_hours == 0
    assert b.calculated_total_float_hours == tf_b
    assert a.calculated_free_float_hours == ff_a


def test_split_shift_float_uses_four_hours_not_five_elapsed_hours():
    schedule=make_schedule([activity("1","A",4)],[])
    schedule.calendars["C1"]=make_calendar(periods=(WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17))))
    item=run(schedule,CPMConfig(required_project_finish=datetime(2026,1,5,17))).activity_results[0]
    assert item.calculated_total_float_hours == 4


def test_different_calendar_float_and_lag():
    schedule=make_schedule([activity("1","A",14),activity("2","B",2,calendar_id="C2")],
        [Relationship("R1","1","2","FS",5)])
    schedule.calendars={"C1":make_calendar(periods=(WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17)))),
                        "C2":make_calendar("C2",periods=(WorkPeriod(time(10),time(16)),))}
    result=run(schedule)
    # A ends Tue 15, lag consumes Tue 15-17 and Wed 08-11; B ends Wed 13.
    assert [a.calculated_total_float_hours for a in result.activity_results] == [0,0]
    assert result.activity_results[0].calculated_free_float_hours == 0


@pytest.mark.parametrize("policy,expected", [("INDEPENDENT_ANCHOR",0),("PROJECT_FINISH",6)])
def test_disconnected_component_policy(policy,expected):
    schedule=make_schedule([activity("1","A",2),activity("2","B",8)],[])
    a,b=run(schedule,CPMConfig(disconnected_component_policy=policy)).activity_results
    assert a.calculated_total_float_hours == expected
    assert b.calculated_total_float_hours == 0


def test_milestone_float_and_missing_imported_critical():
    a=activity("1","M",0)
    a.raw_activity_type="TT_Mile"
    a.total_float_hours=None
    item=run(make_schedule([a],[]),CPMConfig(required_project_finish=datetime(2026,1,5,10))).activity_results[0]
    assert item.calculated_total_float_hours == 2
    assert item.imported_critical is None
    assert item.critical_disagreement is None


def test_float_none_and_both_methods_remain_distinct():
    cal=make_calendar()
    assert total_float(None,None,None,None,None) == (None,None)
    assert total_float(cal,datetime(2026,1,5,8),datetime(2026,1,5,10),datetime(2026,1,5,12),datetime(2026,1,5,15)) == (2,3)


def test_negative_free_float_and_multiple_successors():
    schedule=make_schedule([activity("1","A",4),activity("2","B",1),activity("3","C",1)],
        [Relationship("R1","1","2","FS",2),Relationship("R2","1","3","FS",0)])
    # Explicit feasibility-check input: A finishes 12; B starts 13 with 2h lag,
    # so its signed slack is -1. C starts 16, providing +4; minimum is -1.
    starts={"1":datetime(2026,1,5,8),"2":datetime(2026,1,5,13),"3":datetime(2026,1,5,16)}
    finishes={"1":datetime(2026,1,5,12),"2":datetime(2026,1,5,14),"3":datetime(2026,1,5,17)}
    assert free_float(schedule,ScheduleGraph(schedule),schedule.calendars["C1"],"1",starts,finishes) == -1


@pytest.mark.parametrize("value,expected", [(-1,(True,False)),(2,(True,False)),(3,(False,True)),(5,(False,True)),(6,(False,False)),(None,(False,False))])
def test_visible_critical_thresholds(value,expected):
    assert classify_criticality(value,2,5) == expected


def test_method_disagreement_retains_both_and_warns(monkeypatch):
    # Test the reporting contract independently of the two calendar integrals.
    monkeypatch.setattr("app.cpm.service.total_float",lambda *args:(2,3))
    result=run(make_schedule([activity("1","A",2)],[]))
    item=result.activity_results[0]
    assert item.calculated_total_float_hours == item.calculated_start_float_hours == 2
    assert item.calculated_finish_float_hours == 3
    assert any(d.code == "float_methods_disagree" for d in result.diagnostics)


@pytest.mark.parametrize("value,critical,near", [(-1,True,False),(2,True,False),(3,False,True),(5,False,True),(6,False,False)])
def test_classification_and_imported_disagreement_in_results(value,critical,near):
    a=activity("1","A",1)
    a.total_float_hours=100
    item=run(make_schedule([a],[]),CPMConfig(required_project_finish=datetime(2026,1,5,9+value),critical_float_threshold_hours=2,near_critical_float_threshold_hours=5)).activity_results[0]
    assert item.calculated_total_float_hours == value
    assert (item.calculated_critical,item.calculated_near_critical) == (critical,near)
    assert item.imported_critical is False
    assert item.critical_disagreement == critical


def test_free_float_unknown_methodology_returns_none_with_reason():
    from app.cpm.float_calculation import free_float_details
    schedule=make_schedule([activity("1","A",1),activity("2","B",1)], [Relationship("R","1","2","FS",0)])
    value,details,reason=free_float_details(schedule,ScheduleGraph(schedule),None,"1",{}, {})
    assert value is None and details == () and reason == "free_float_unsupported_methodology"
