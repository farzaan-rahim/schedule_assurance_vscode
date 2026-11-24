from copy import deepcopy
from datetime import datetime

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule


def finish(task_id="F", code="FINISH"):
    a=activity(task_id,code,0)
    a.raw_activity_type="TT_FinMile"
    a.activity_type="finish_milestone"
    return a


def run(schedule,config=None):
    before=deepcopy(schedule)
    result=CPMService().calculate(schedule,ScheduleGraph(schedule),config)
    assert result.status == "CALCULATED",result.diagnostics
    assert schedule == before
    for path in result.critical_paths+result.near_critical_paths:
        assert path.activity_count == len(path.activity_ids)
        assert path.relationship_count == len(path.relationships) == len(path.activity_ids)-1
        assert path.activity_ids[-1] == result.completion_anchor.activity_id
        for index,rel in enumerate(path.relationships):
            assert (rel.predecessor_id,rel.successor_id) == path.activity_ids[index:index+2]
    return result


def diamond(short=4):
    return make_schedule([activity("A","A",1),activity("B","B",4),activity("C","C",short),finish()],
        [Relationship("AB","A","B","FS",0),Relationship("AC","A","C","FS",0),
         Relationship("BF","B","F","FS",0),Relationship("CF","C","F","FS",0)])


@pytest.mark.parametrize("milestone",[False,True])
def test_single_terminal_anchor(milestone):
    a=finish() if milestone else activity("F","FINISH",2)
    result=run(make_schedule([a],[]))
    assert result.anchor_selection_status == "SELECTED"
    assert result.completion_anchor.activity_id == "F"
    assert result.completion_anchor.activity_code == "FINISH"
    assert result.completion_anchor.source == "UNAMBIGUOUS_TERMINAL"
    assert len(result.critical_paths) == 1


def test_linear_connected_path():
    schedule=make_schedule([activity("A","A",2),activity("B","B",3),activity("C","C",1),finish()],
        [Relationship("AB","A","B","FS",0),Relationship("BC","B","C","FS",0),Relationship("CF","C","F","FS",0)])
    result=run(schedule)
    path,=result.critical_paths
    assert path.activity_codes == ("A","B","C","FINISH")
    assert path.sum_effective_activity_duration_hours == path.duration_hours == 6
    assert path.relationship_lag_contribution_hours == 0
    assert path.start_timestamp == datetime(2026,1,5,8)
    assert path.finish_timestamp == datetime(2026,1,5,14)
    assert not path.truncated and path.trace_complete


@pytest.mark.parametrize("connected",[False,True])
def test_multiple_terminals_require_selection(connected):
    schedule=make_schedule([activity("A","A",2),activity("B","B",3),finish()],
        [Relationship("AB","A","B","FS",0),Relationship("AF","A","F","FS",0)] if connected else [])
    result=run(schedule)
    assert result.anchor_selection_status == "AMBIGUOUS"
    assert result.completion_anchor is None
    assert len(result.completion_anchor_candidates) == (2 if connected else 3)
    assert result.critical_paths == result.near_critical_paths == ()
    assert any(d.code == "completion_anchor_ambiguous" for d in result.diagnostics)


@pytest.mark.parametrize("settings,source",[
    ({"completion_activity_id":"F"},"CONFIGURED_ACTIVITY"),
    ({"completion_activity_code":"FINISH"},"CONFIGURED_ACTIVITY"),
    ({"required_finish_activity_id":"F"},"CONFIGURED_REQUIRED_FINISH_ACTIVITY"),
    ({"required_finish_activity_code":"FINISH"},"CONFIGURED_REQUIRED_FINISH_ACTIVITY"),
    ({"completion_activity_id":"F","required_finish_activity_id":"B"},"CONFIGURED_ACTIVITY"),
])
def test_explicit_anchor_priority(settings,source):
    schedule=make_schedule([activity("B","B",2),finish()],[])
    result=run(schedule,CPMConfig(**settings))
    assert result.completion_anchor.activity_id == "F"
    assert result.completion_anchor.source == source
    assert result.completion_anchor.activity_name == "FINISH"


def test_missing_configured_anchor_never_falls_back():
    result=run(make_schedule([finish()],[]),CPMConfig(completion_activity_code="MISSING"))
    assert result.anchor_selection_status == "INVALID"
    assert result.completion_anchor is None and not result.critical_paths
    assert any(d.code == "configured_completion_anchor_not_found" for d in result.diagnostics)


def test_duplicate_activity_code_requires_internal_id():
    schedule=make_schedule([activity("A","DUP",1),activity("B","DUP",2)],[])
    result=run(schedule,CPMConfig(completion_activity_code="DUP"))
    assert result.anchor_selection_status == "AMBIGUOUS"
    assert not result.critical_paths
    assert len(result.completion_anchor_candidates) == 2


def test_project_timestamp_anchor_does_not_invent_relationships():
    result=run(make_schedule([activity("A","A",1),activity("B","B",2)],[]),
        CPMConfig(project_completion_timestamp=datetime(2026,1,5,17)))
    assert result.completion_anchor.source == "CONFIGURED_PROJECT_TIMESTAMP"
    assert result.completion_anchor.activity_id is None
    assert result.critical_paths == result.near_critical_paths == ()
    assert result.path_status == "NO_ACTIVITY_ANCHOR"


def test_timestamp_can_bind_one_exact_terminal():
    result=run(make_schedule([activity("A","A",1),activity("B","B",2)],[]),
        CPMConfig(project_completion_timestamp=datetime(2026,1,5,10)))
    assert result.completion_anchor.activity_id == "B"
    assert result.critical_paths[0].activity_ids == ("B",)


def test_diamond_preserves_tied_controlling_paths():
    result=run(diamond())
    assert [p.activity_ids for p in result.critical_paths] == [("A","B","F"),("A","C","F")]
    assert [p.rank for p in result.critical_paths] == [1,2]
    assert all("F" in p.controlling_tie_activity_ids for p in result.critical_paths)
    assert not result.near_critical_paths


def test_shorter_parallel_chain_is_near_critical():
    result=run(diamond(2),CPMConfig(near_critical_float_threshold_hours=2))
    assert [p.activity_ids for p in result.critical_paths] == [("A","B","F")]
    path,=result.near_critical_paths
    assert path.activity_ids == ("A","C","F")
    assert (path.minimum_total_float_hours,path.maximum_total_float_hours) == (0,2)
    assert path.relationships[-1].direction == "NEAR_QUALIFYING"
    assert not run(diamond(2),CPMConfig(near_critical_float_threshold_hours=1)).near_critical_paths


def test_constraint_ends_relationship_trace_cleanly():
    a,b=activity("A","A",2),activity("B","B",2)
    b.primary_constraint_type="START_ON_OR_AFTER"
    b.primary_constraint_date=datetime(2026,1,5,13)
    result=run(make_schedule([a,b,finish()], [Relationship("AB","A","B","FS",0),Relationship("BF","B","F","FS",0)]))
    path,=result.critical_paths
    assert path.activity_ids == ("B","F")
    assert path.end_reason == "CONSTRAINT"
    assert path.constraint_causes[0].activity_id == "B"
    assert path.relationship_ids == ("BF",)


def test_negative_float_path_and_explicit_finish_milestone():
    result=run(make_schedule([activity("A","A",1),activity("B","B",4),finish()],
        [Relationship("AB","A","B","FS",0),Relationship("BF","B","F","FS",0)]),
        CPMConfig(completion_activity_id="F",required_project_finish=datetime(2026,1,5,12)))
    path,=result.critical_paths
    assert path.activity_ids == ("A","B","F")
    assert path.minimum_total_float_hours == path.maximum_total_float_hours == -1
    assert result.completion_anchor.required_finish == datetime(2026,1,5,12)
    assert result.completion_anchor.calculated_early_finish == datetime(2026,1,5,13)


def test_deep_path_is_iterative():
    schedule=make_schedule([activity(str(i),f"A{i:04d}",1) for i in range(1101)],
        [Relationship(str(i),str(i),str(i+1),"FS",0) for i in range(1100)])
    config=CPMConfig(maximum_path_depth=1200,maximum_path_nodes_inspected=3000)
    result=run(schedule,config)
    path,=result.critical_paths
    assert len(path.activity_ids) == 1101 and not path.truncated
    assert result == run(schedule,config)


def branching(levels=8):
    activities=[activity("START","START",1),finish()]
    relationships=[]
    previous=["START"]
    for level in range(levels):
        current=[f"L{level}A",f"L{level}B"]
        activities.extend(activity(key,key,1) for key in current)
        relationships.extend(Relationship(f"{a}_{b}",a,b,"FS",0) for a in previous for b in current)
        previous=current
    relationships.extend(Relationship(f"{a}_F",a,"F","FS",0) for a in previous)
    return make_schedule(activities,relationships)


@pytest.mark.parametrize("config,reason",[
    (CPMConfig(maximum_critical_paths=3),"MAXIMUM_CRITICAL_PATHS"),
    (CPMConfig(maximum_path_depth=3),"MAXIMUM_PATH_DEPTH"),
    (CPMConfig(maximum_path_nodes_inspected=3),"MAXIMUM_PATH_NODES_INSPECTED"),
])
def test_branching_limits_are_explicit_and_deterministic(config,reason):
    schedule=branching()
    result=run(schedule,config)
    stats=result.path_statistics[0]
    assert stats.truncated and reason in stats.limit_reasons
    assert stats.known_total_paths is None
    assert stats.nodes_inspected <= config.maximum_path_nodes_inspected
    assert any(d.code == "path_trace_truncated" for d in result.diagnostics)
    assert result == run(schedule,config)


@pytest.mark.parametrize("kind,lag",[("SS",2),("FF",2),("SF",6)])
def test_non_fs_duration_is_not_invented(kind,lag):
    result=run(make_schedule([activity("A","A",4),activity("B","B",2)], [Relationship("R","A","B",kind,lag)]))
    path,=result.critical_paths
    assert path.sum_effective_activity_duration_hours == 6
    assert path.relationship_lag_contribution_hours == lag
    assert path.duration_hours is None



def near_branches(count=5):
    activities=[activity("A","A",1),activity("LONG","LONG",8),finish()]
    relationships=[Relationship("AL","A","LONG","FS",0),Relationship("LF","LONG","F","FS",0)]
    for i in range(count):
        key=f"SHORT{i}"
        activities.append(activity(key,key,1))
        relationships.extend([Relationship("A"+key,"A",key,"FS",0),Relationship(key+"F",key,"F","FS",0)])
    return make_schedule(activities,relationships)


def test_near_critical_collection_has_its_own_count_limit():
    result=run(near_branches(),CPMConfig(near_critical_float_threshold_hours=7,maximum_near_critical_paths=2))
    assert len(result.critical_paths) == 1 and len(result.near_critical_paths) == 2
    stats=result.path_statistics[1]
    assert stats.truncated and "MAXIMUM_NEAR_CRITICAL_PATHS" in stats.limit_reasons
    assert stats.paths_lower_bound >= 3 and stats.known_total_paths is None
    assert all(p.maximum_total_float_hours == 7 for p in result.near_critical_paths)
    assert all("above the critical threshold" in p.qualification_reason for p in result.near_critical_paths)
    assert all(p.relationships[-1].relationship_free_float_hours == 7 for p in result.near_critical_paths)


def test_inspection_budget_is_shared_by_both_path_classes():
    result=run(near_branches(),CPMConfig(near_critical_float_threshold_hours=7,maximum_path_nodes_inspected=4))
    assert sum(s.nodes_inspected for s in result.path_statistics) == 4
    assert result.path_statistics[1].truncated


def test_exact_path_count_limit_does_not_falsely_truncate():
    result=run(diamond(),CPMConfig(maximum_critical_paths=2))
    assert len(result.critical_paths) == 2
    assert not result.path_statistics[0].truncated
    assert result.path_statistics[0].known_total_paths == 2


def test_zero_path_limit_reports_omitted_paths():
    result=run(diamond(),CPMConfig(maximum_critical_paths=0))
    assert not result.critical_paths
    assert result.path_statistics[0].truncated
    assert result.path_statistics[0].paths_lower_bound >= 1


def test_conflicting_selector_does_not_use_lower_priority_fallback():
    result=run(make_schedule([activity("A","A",1),finish()],[]),
        CPMConfig(completion_activity_id="A",completion_activity_code="FINISH",required_finish_activity_id="F"))
    assert result.anchor_selection_status == "INVALID" and result.completion_anchor is None


def test_configured_activity_precedes_timestamp_selection():
    result=run(make_schedule([activity("A","A",1),finish()],[]),
        CPMConfig(completion_activity_id="F",project_completion_timestamp=datetime(2026,1,5,9)))
    assert result.completion_anchor.activity_id == "F"


def test_ranking_uses_duration_before_lexical_code():
    f=finish()
    f.primary_constraint_type="FINISH_ON_OR_BEFORE"
    f.primary_constraint_date=datetime(2026,1,5,8)
    schedule=make_schedule([activity("LONG","ZZZ",8),activity("SHORT","AAA",4),f],
        [Relationship("L","LONG","F","SS",0),Relationship("S","SHORT","F","SS",0)])
    result=run(schedule,CPMConfig(required_project_finish=datetime(2026,1,5,16)))
    assert [p.activity_codes[0] for p in result.critical_paths] == ["ZZZ","AAA"]
    assert [p.minimum_total_float_hours for p in result.critical_paths] == [0,0]


@pytest.mark.parametrize("lag,span",[(2,8),(-2,4)])
def test_path_duration_preserves_signed_lag_separately(lag,span):
    result=run(make_schedule([activity("A","A",4),activity("B","B",2)], [Relationship("R","A","B","FS",lag)]))
    path,=result.critical_paths
    assert path.sum_effective_activity_duration_hours == 6
    assert path.relationship_lag_contribution_hours == lag
    assert path.duration_hours == span


def test_mixed_calendars_have_no_invented_combined_duration():
    from datetime import time
    from app.calendars.models import WorkPeriod
    from tests.test_cpm import make_calendar
    schedule=make_schedule([activity("A","A",2),activity("B","B",2,calendar_id="C2")],[Relationship("R","A","B","FS",0)])
    schedule.calendars["C2"]=make_calendar("C2",periods=(WorkPeriod(time(10),time(16)),))
    path,=run(schedule).critical_paths
    assert path.duration_hours is None
    assert path.sum_effective_activity_duration_hours == 4



def test_fractional_duration_uses_calendar_resolution_for_combined_span():
    result=run(make_schedule([activity("A","A",0.1),activity("B","B",0.2)], [Relationship("R","A","B","FS",0)]))
    path,=result.critical_paths
    # Six plus twelve working minutes is exactly eighteen minutes (0.3h).
    assert path.duration_hours == 0.3
    assert path.sum_effective_activity_duration_hours == sum((0.1,0.2))


def test_anchor_reports_imported_finish_without_calibration():
    f=finish()
    f.early_finish=datetime(2026,1,5,9)
    result=run(make_schedule([f],[]),CPMConfig(completion_activity_code="FINISH"))
    assert result.completion_anchor.imported_finish == datetime(2026,1,5,9)
    assert result.completion_anchor.calculated_early_finish == datetime(2026,1,5,8)
