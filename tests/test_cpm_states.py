from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from tests.test_cpm import activity, make_schedule


def calculate(a, config=None):
    schedule = make_schedule([a], [])
    before = deepcopy(schedule)
    result = CPMService().calculate(schedule, ScheduleGraph(schedule), config)
    assert schedule == before
    return result


@pytest.mark.parametrize("status,changes,code", [
    ("TK_NotStart", {"remaining_duration_hours": -1}, "negative_duration"),
    ("TK_NotStart", {"remaining_duration_hours": None, "original_duration_hours": None}, "missing_duration"),
    ("TK_NotStart", {"actual_start": datetime(2026,1,4,8)}, "not_started_actual_dates"),
    ("TK_Active", {}, "in_progress_missing_actual_start"),
    ("TK_Active", {"actual_start": datetime(2026,1,6,8)}, "actual_after_data_date"),
    ("TK_Active", {"actual_start": datetime(2026,1,2,8), "actual_finish": datetime(2026,1,2,9)}, "in_progress_actual_finish"),
    ("TK_Active", {"actual_start": datetime(2026,1,2,8), "remaining_duration_hours": -1}, "negative_duration"),
    ("TK_Complete", {}, "complete_missing_actual_start"),
    ("TK_Complete", {"actual_start": datetime(2026,1,2,8)}, "complete_missing_actual_finish"),
    ("TK_Complete", {"actual_start": datetime(2026,1,2,10), "actual_finish": datetime(2026,1,2,9)}, "actual_finish_before_start"),
    ("unknown", {}, "unsupported_activity_status"),
    (None, {}, "unsupported_activity_status"),
    ("TK_NotStart", {"raw_activity_type": "mystery"}, "unsupported_activity_type"),
    ("TK_NotStart", {"remaining_duration_hours": float("nan")}, "invalid_duration"),
])
def test_invalid_state_is_fatal(status, changes, code):
    a = activity("1", "A", 4, status=status)
    for name,value in changes.items():
        setattr(a,name,value)
    result = calculate(a)
    assert result.status == "FAILED"
    assert result.activity_results == ()
    assert any(d.code == code and d.severity.value == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("status", ["TK_NotStart", "TK_Active"])
@pytest.mark.parametrize("duration", [0, 2.5])
def test_remaining_duration_policy(status, duration):
    a = activity("1", "A", 16, status=status)
    a.remaining_duration_hours = duration
    if status == "TK_Active":
        a.actual_start = datetime(2026,1,2,8)
    result = calculate(a)
    assert result.status == "CALCULATED"
    item = result.activity_results[0]
    assert item.effective_duration_hours == duration
    assert item.calculated_early_start == datetime(2026,1,5,8)
    assert item.calculated_early_finish == datetime(2026,1,5,8) + timedelta(hours=duration)


@pytest.mark.parametrize("status", ["TK_NotStart", "TK_Active"])
def test_original_duration_fallback_is_visible(status):
    a = activity("1", "A", 3, status=status)
    a.remaining_duration_hours = None
    if status == "TK_Active":
        a.actual_start = datetime(2026,1,2,8)
    result = calculate(a)
    assert result.status == "CALCULATED"
    assert result.activity_results[0].effective_duration_hours == 3
    assert any(d.code == "original_duration_fallback" for d in result.diagnostics)
    assert calculate(a, CPMConfig(duration_fallback_policy="ERROR")).status == "FAILED"


def test_complete_preserves_actuals_and_has_no_remaining_float():
    a = activity("1", "A", 8, status="TK_Complete")
    a.actual_start, a.actual_finish = datetime(2026,1,2,8), datetime(2026,1,2,16)
    result = calculate(a)
    assert result.status == "CALCULATED"
    item = result.activity_results[0]
    assert item.effective_duration_hours == 0
    assert item.calculated_early_start == item.calculated_late_start == a.actual_start
    assert item.calculated_early_finish == item.calculated_late_finish == a.actual_finish
    assert item.calculated_total_float_hours is None
    assert any(d.code == "complete_remaining_duration_ignored" for d in result.diagnostics)
    assert calculate(a,CPMConfig(completed_remaining_duration_policy="ERROR")).status == "FAILED"


@pytest.mark.parametrize("kind", ["TT_StartMile", "TT_FinMile", "TT_Mile"])
def test_milestone_duration_is_zero_with_diagnostic(kind):
    a = activity("1", "M", 8)
    a.raw_activity_type = kind
    result = calculate(a)
    assert result.status == "CALCULATED"
    item=result.activity_results[0]
    assert item.effective_duration_hours == 0
    assert item.calculated_early_start == item.calculated_early_finish
    assert any(d.code == "milestone_duration_ignored" for d in result.diagnostics)


def test_isolated_loe_exclusion_is_explicit():
    a,b = activity("1","A",4),activity("2","LOE",4)
    b.raw_activity_type = "TT_LOEP"
    schedule = make_schedule([a,b],[])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert result.status == "CALCULATED"
    assert result.excluded_activity_count == 1
    assert [a.activity_id for a in result.activity_results] == ["1"]
    assert any(d.code == "loe_not_supported" and d.metadata["disposition"] == "EXCLUDE" for d in result.diagnostics)


@pytest.mark.parametrize("policy", ["invalid_activity_policy", "missing_duration_policy", "missing_calendar_policy"])
def test_isolated_exclusion_policies(policy):
    from dataclasses import replace
    a,b=activity("1","A",2),activity("2","B",2)
    if policy == "invalid_activity_policy": b.raw_status="unknown"
    if policy == "missing_duration_policy": b.remaining_duration_hours=b.original_duration_hours=None
    if policy == "missing_calendar_policy": b.calendar_id="MISSING"
    schedule=make_schedule([a,b],[])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),replace(CPMConfig(),**{policy:"EXCLUDE"}))
    assert result.status == "CALCULATED"
    assert result.excluded_activity_count == 1
    assert len(result.activity_results) == 1


def test_excluded_loe_cannot_be_bypassed():
    from app.models.schedule import Relationship
    a,b=activity("1","A",2),activity("2","LOE",2)
    b.raw_activity_type="TT_LOEP"
    schedule=make_schedule([a,b],[Relationship("R","1","2","FS",0)])
    result=CPMService().calculate(schedule,ScheduleGraph(schedule))
    assert result.status == "FAILED"
    assert any(d.code == "excluded_relationship_endpoint" for d in result.diagnostics)


@pytest.mark.parametrize("changes,config,code", [
    ({"original_duration_hours":-1},CPMConfig(),"negative_duration"),
    ({"remaining_duration_hours":0},CPMConfig(zero_duration_task_policy="ERROR"),"zero_duration_task"),
    ({"raw_activity_type":"TT_Mile"},CPMConfig(milestone_duration_policy="ERROR"),"milestone_nonzero_duration"),
    ({"calendar_id":None},CPMConfig(),"missing_activity_calendar"),
    ({"raw_status":"TK_Complete","actual_finish":datetime(2026,1,2,16)},CPMConfig(),"complete_missing_actual_start"),
])
def test_additional_fatal_policy_cases(changes,config,code):
    a=activity("1","A",2)
    for name,value in changes.items(): setattr(a,name,value)
    result=calculate(a,config)
    assert result.status == "FAILED"
    assert any(d.code == code for d in result.diagnostics)


def test_original_preference_and_historical_plan_are_explicit():
    a=activity("1","A",3,start=datetime(2025,12,1,8))
    a.remaining_duration_hours=1
    result=calculate(a,CPMConfig(remaining_duration_preference=False))
    assert result.activity_results[0].effective_duration_hours == 3
    assert any(d.code == "planned_start_before_data_date" for d in result.diagnostics)


def test_invariant_failure_prevents_float(monkeypatch):
    import app.cpm.service as module
    real=module.backward_pass
    def broken(*args,**kwargs):
        result=real(*args,**kwargs)
        result["late_starts"]["1"]+=timedelta(hours=1)
        return result
    monkeypatch.setattr(module,"backward_pass",broken)
    def forbidden(*args): raise AssertionError("Float was reached before invariant check")
    monkeypatch.setattr(module,"total_float",forbidden)
    result=calculate(activity("1","A",2))
    assert result.status == "FAILED"
    assert any(d.code == "date_invariant_failed" for d in result.diagnostics)


def test_start_override_never_moves_remaining_work_before_data_date():
    item=calculate(activity("1","A",1),CPMConfig(project_start_override=datetime(2025,12,1,8))).activity_results[0]
    assert item.calculated_early_start == datetime(2026,1,5,8)


def test_future_override_does_not_authorize_future_actual_dates():
    a=activity("1","A",1,status="TK_Active")
    a.actual_start=datetime(2026,1,6,8)
    assert calculate(a,CPMConfig(project_start_override=datetime(2026,1,7,8))).status == "FAILED"


@pytest.mark.parametrize("critical,near", [(5,2),(float("nan"),40),(None,40)])
def test_invalid_threshold_configuration_is_diagnosed(critical,near):
    result=calculate(activity("1","A",1),CPMConfig(critical_float_threshold_hours=critical,near_critical_float_threshold_hours=near))
    assert result.status == "FAILED"
    assert any(d.code == "invalid_critical_thresholds" for d in result.diagnostics)
