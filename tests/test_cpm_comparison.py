from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.importers.schedule_mapper import ScheduleMapper
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule


def controlled_imports():
    schedule=make_schedule([activity("A","A",2),activity("B","B",2)], [Relationship("R","A","B","FS",0)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    for item in result.activity_results:
        a=schedule.activities_by_id[item.activity_id]
        for name in ("early_start","early_finish","late_start","late_finish"):
            setattr(a,name,getattr(item,"calculated_"+name))
        a.total_float_hours=item.calculated_total_float_hours
        a.free_float_hours=item.calculated_free_float_hours
    return schedule


def run(schedule,config=None):
    before=deepcopy(schedule)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),config)
    assert result.status == "CALCULATED",result.diagnostics
    assert schedule == before
    return result


def record(result,key="A"):
    return next(a for a in result.comparisons if a.activity_id == key)


def metric(comparison,name):
    return next(m for m in comparison.metrics if m.name == name)


def test_exact_comparison_and_aggregate_counts():
    result=run(controlled_imports())
    a=record(result)
    assert all(m.status == "MATCH" for m in a.metrics)
    assert a.imported_late_start == a.calculated_late_start == datetime(2026,1,5,8)
    assert a.early_start_variance_hours == a.late_start_variance_hours == 0
    summary=result.comparison_summary
    assert summary.activities_compared == summary.activity_records == 2
    assert summary.imported_dates_missing == 0
    assert summary.early_start_matches == summary.early_finish_matches == 2
    assert summary.late_start_matches == summary.late_finish_matches == 2
    assert summary.total_float_matches == 2 and summary.free_float_matches == 1
    assert summary.critical_state_agreements == 2 and summary.critical_state_disagreements == 0


@pytest.mark.parametrize("name,delta", [
    ("early_start",2),("early_finish",3),("late_start",-2),("late_finish",-3),
])
def test_date_differences_keep_exact_elapsed_hours(name,delta):
    schedule=controlled_imports()
    a=schedule.activities["A"]
    setattr(a,name,getattr(a,name)-timedelta(hours=delta))
    result=run(schedule)
    comparison=record(result)
    assert metric(comparison,name).status == "DIFFERENCE"
    assert getattr(comparison,name+"_variance_hours") == delta
    assert metric(comparison,name).variance_seconds == delta*3600
    assert getattr(result.comparison_summary,name+"_differences") == 1


@pytest.mark.parametrize("name,imported,expected", [("total_float",2.25,-2.25),("free_float",1.5,-1.5)])
def test_float_differences_remain_signed(name,imported,expected):
    schedule=controlled_imports()
    setattr(schedule.activities["A"],name+"_hours",imported)
    comparison=record(run(schedule))
    assert getattr(comparison,name+"_variance_hours") == expected
    assert metric(comparison,name).status == "DIFFERENCE"


def test_missing_imported_values_stay_none_even_with_planned_dates():
    a=activity("A","A",2,start=datetime(2025,12,1,8),finish=datetime(2025,12,1,10))
    a.total_float_hours=a.free_float_hours=None
    result=run(make_schedule([a],[]))
    comparison=record(result)
    assert comparison.imported_early_start is comparison.imported_early_finish is None
    assert comparison.early_start_variance_hours is comparison.total_float_variance_hours is None
    assert comparison.imported_critical is comparison.critical_disagreement is None
    assert result.activity_results[0].imported_early_start is None
    assert result.comparison_summary.imported_dates_missing == 4


def test_elapsed_variance_counts_weekend_not_only_work():
    schedule=controlled_imports()
    schedule.activities["A"].early_start=datetime(2026,1,2,16)
    # Friday 16 -> Monday 08 is 64 elapsed hours, only one working hour.
    assert record(run(schedule)).early_start_variance_hours == 64


def test_tolerances_only_classify_and_preserve_raw_values():
    schedule=controlled_imports()
    a=schedule.activities["A"]
    a.early_start-=timedelta(seconds=30)
    a.early_finish-=timedelta(seconds=61)
    a.total_float_hours=0.05
    a.free_float_hours=0.2
    result=run(schedule,CPMConfig(comparison_date_tolerance_seconds=60,comparison_float_tolerance_hours=0.1))
    comparison=record(result)
    assert metric(comparison,"early_start").status == "MATCH"
    assert comparison.early_start_variance_hours == 30/3600
    assert metric(comparison,"early_finish").status == "DIFFERENCE"
    assert comparison.early_finish_variance_hours == 61/3600
    assert metric(comparison,"total_float").status == "MATCH"
    assert comparison.total_float_variance_hours == -0.05
    assert metric(comparison,"free_float").status == "DIFFERENCE"
    assert comparison.free_float_variance_hours == -0.2
    assert result.activity_results[0].calculated_total_float_hours == 0


def test_criticality_disagreement_is_separate():
    schedule=controlled_imports()
    schedule.activities["A"].total_float_hours=100
    comparison=record(run(schedule))
    assert comparison.imported_critical is False and comparison.calculated_critical is True
    assert comparison.critical_disagreement is True


def test_importer_preserves_early_late_and_planned_dates_separately():
    row={"task_id":"A","task_code":"A","proj_id":"P","task_type":"TT_Task","status_code":"TK_NotStart",
         "target_start_date":"2025-12-01 08:00","target_end_date":"2025-12-02 08:00",
         "early_start_date":"2026-01-05 08:00","early_end_date":"2026-01-05 10:00",
         "late_start_date":"2026-01-05 09:00","late_end_date":"2026-01-05 11:00",
         "expect_end_date":"2026-01-06 12:00"}
    schedule=ScheduleMapper().map({"PROJECT":[{"proj_id":"P"}],"TASK":[row]})
    a=schedule.activities_by_id["A"]
    assert a.planned_start == datetime(2025,12,1,8)
    assert a.early_start == datetime(2026,1,5,8) and a.early_finish == datetime(2026,1,5,10)
    assert a.late_start == datetime(2026,1,5,9) and a.late_finish == datetime(2026,1,5,11)
    assert a.expected_finish == datetime(2026,1,6,12)


def test_expected_finish_capability_is_evidence_based_not_applied():
    schedule=controlled_imports()
    schedule.activities["A"].expected_finish=datetime(2026,1,9,17)
    result=run(schedule)
    diagnostic=next(d for d in result.comparison_diagnostics if d.code == "expected_finish_capability")
    assert diagnostic.metadata["support"] == "UNSUPPORTED"
    assert diagnostic.metadata["cause_established"] is False
    assert result.activity_results[0].calculated_early_finish == datetime(2026,1,5,10)


def test_progress_and_observed_out_of_sequence_are_diagnostics_only():
    a,b=activity("A","A",2,status="TK_Complete"),activity("B","B",2,status="TK_Active")
    a.actual_start,a.actual_finish=datetime(2026,1,1,8),datetime(2026,1,2,10)
    a.remaining_duration_hours=0
    b.actual_start=datetime(2026,1,2,8)
    result=run(make_schedule([a,b],[Relationship("R","A","B","FS",0)]))
    codes={d.code for d in result.comparison_diagnostics}
    assert {"progress_policy_capability","observed_out_of_sequence_progress"} <= codes
    assert all(d.metadata["cause_established"] is False for d in result.comparison_diagnostics)


@pytest.mark.parametrize("settings",[
    {"comparison_date_tolerance_seconds":-1}, {"comparison_float_tolerance_hours":float("nan")},
    {"maximum_path_depth":0}, {"maximum_critical_paths":-1}, {"maximum_path_nodes_inspected":-1},
])
def test_invalid_comparison_and_path_configuration_is_rejected(settings):
    schedule=controlled_imports()
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),CPMConfig(**settings))
    assert result.status == "FAILED"



def test_capability_hints_do_not_invent_relevant_features():
    result=run(controlled_imports())
    codes={d.code for d in result.comparison_diagnostics}
    assert "expected_finish_capability" not in codes and "progress_policy_capability" not in codes
    assert "lag_calendar_capability" not in codes
    assert all(d.metadata["cause_established"] is False for d in result.comparison_diagnostics)
    assert all(d.metadata["support"] in {"SUPPORTED","PARTIALLY_SUPPORTED","UNSUPPORTED","INFORMATIONAL_ONLY"} for d in result.comparison_diagnostics)


def test_imported_aware_date_is_rejected_before_comparison():
    from datetime import timezone
    schedule=controlled_imports()
    schedule.activities["A"].late_finish=datetime(2026,1,5,10,tzinfo=timezone.utc)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert result.status == "FAILED"
    assert any(d.code == "timezone_mixing" for d in result.diagnostics)



@pytest.mark.parametrize("kind,lag,start",[("SS",0,datetime(2026,1,1,9)),("FS",-2,datetime(2026,1,2,9))])
def test_legitimate_actual_overlap_is_not_called_out_of_sequence(kind,lag,start):
    a,b=activity("A","A",2,status="TK_Complete"),activity("B","B",2,status="TK_Active")
    a.actual_start,a.actual_finish=datetime(2026,1,1,8),datetime(2026,1,2,10)
    a.remaining_duration_hours=0
    b.actual_start=start
    result=run(make_schedule([a,b],[Relationship("R","A","B",kind,lag)]))
    assert not any(d.code == "observed_out_of_sequence_progress" for d in result.comparison_diagnostics)
