from copy import deepcopy
from dataclasses import replace
from datetime import datetime,date,time
import pytest
from app.cpm.config import CPMConfig
from app.cpm.simulation import simulate_duration_change, CriticalPathTestService, CriticalPathTestConfig
from app.cpm.cpli import CPLIService,CPLIConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity,make_schedule,make_calendar

D=datetime(2026,1,5,8)
def chain():
    f=activity('F','FINISH',0);f.activity_type='finish_milestone';f.raw_activity_type='TT_FinMile'
    return make_schedule([activity('A','A',4),activity('B','B',4),f],[Relationship('AB','A','B','FS',0),Relationship('BF','B','F','FS',0)])

def calculate(s,config=None):return CPMService().calculate(s,ScheduleGraph(s),config)

def test_initial_immutable_full_recalculation():
    s=chain();snapshot=deepcopy(s);before=calculate(s)
    out=simulate_duration_change(s,'A',2,CPMConfig())
    assert out.status=='CALCULATED' and out.original_effective_duration_hours==4 and out.simulated_effective_duration_hours==6
    assert out.source_completion_timestamp==datetime(2026,1,5,16)
    assert out.simulated_completion_timestamp==datetime(2026,1,6,9)
    assert out.completion_movement_working_hours==2 and out.completion_movement_elapsed_hours==17
    assert s==snapshot and calculate(s)==before
    assert out.source_cpm_result.schedule is not s and out.simulated_cpm_result.schedule is not s
    assert out.source_completion_anchor.activity_id==out.simulated_completion_anchor.activity_id=='F'

@pytest.mark.parametrize('finish,cpl,tf,value,status',[(datetime(2026,1,5,16),8,0,1,'PASS'),(datetime(2026,1,6,9),8,2,1.25,'PASS'),(datetime(2026,1,5,14),8,-2,.75,'FAIL')])
def test_manually_derived_cpli(finish,cpl,tf,value,status):
    out=CPLIService().calculate(chain(),CPMConfig(),CPLIConfig(required_finish=finish))
    assert out.status==status and out.critical_path_length_hours==cpl and out.total_float_hours==tf
    assert out.numerator_hours==cpl+tf and out.denominator_hours==cpl and out.value==value
    assert out.formula_version=='APPLICATION-CPLI-V1'


def test_initial_critical_path_response():
    out=CriticalPathTestService().evaluate(chain(),CPMConfig(),CriticalPathTestConfig(delay_hours=2))
    assert out.status=='PASS' and out.response_ratio==1 and out.selected_activity_id=='A'
    assert out.simulation.completion_movement_working_hours==2



def diamond(tied=False):
    s=chain();s.activities['C']=activity('C','C',8 if tied else 2)
    s.relationships.append(Relationship('CF','C','F','FS',0));s.rebuild_activity_indexes()
    return s

@pytest.mark.parametrize('tied',[False,True])
def test_parallel_and_tied_critical_paths(tied):
    out=CriticalPathTestService().evaluate(diamond(tied),config=CriticalPathTestConfig(delay_hours=2))
    assert out.status=='PASS' and out.response_ratio==1
    assert len(out.simulation.source_cpm_result.critical_paths)==(2 if tied else 1)
    assert len(out.simulation.simulated_cpm_result.critical_paths)==1


def test_general_reduction_can_switch_path_and_lose_criticality():
    s=diamond();s.activities['C'].remaining_duration_hours=7;s.activities['C'].original_duration_hours=7
    out=simulate_duration_change(s,'A',-3)
    assert out.status=='CALCULATED'
    rows={a.activity_id:a for a in out.simulated_cpm_result.activity_results}
    assert not rows['A'].calculated_critical and rows['C'].calculated_critical
    assert out.completion_movement_working_hours==-1
    assert next(r for r in out.total_float_changes if r['activity_id']=='A')['variance_hours']==2

@pytest.mark.parametrize('which',['A','B'])
def test_explicit_selection_including_immediately_before_finish(which):
    out=CriticalPathTestService().evaluate(chain(),config=CriticalPathTestConfig(test_activity_id=which,delay_hours=1.5))
    assert out.status=='PASS' and out.selected_activity_id==which and out.selection_reason=='EXPLICIT_ELIGIBLE_CRITICAL_ACTIVITY'


def test_fixed_anchor_ignores_later_unrelated_terminal():
    s=chain();s.activities['X']=activity('X','X',30);s.rebuild_activity_indexes()
    config=CPMConfig(completion_activity_code='FINISH')
    out=simulate_duration_change(s,'A',2,config)
    assert out.status=='CALCULATED' and out.source_completion_anchor.activity_id==out.simulated_completion_anchor.activity_id=='F'
    assert out.simulated_completion_timestamp==datetime(2026,1,6,9)
    assert out.simulated_cpm_result.calculated_completion>out.simulated_completion_timestamp
    for policy in ('FIXED_ACTIVITY','RESELECT_TERMINAL'):
        r=simulate_duration_change(chain(),'A',1,anchor_policy=policy)
        assert r.status=='CALCULATED' and r.anchor_policy==policy


def test_ambiguous_and_invalid_anchors_are_not_evaluated():
    s=chain();s.activities['X']=activity('X','X',1);s.rebuild_activity_indexes()
    assert CriticalPathTestService().evaluate(s).status=='NOT_EVALUATED'
    assert simulate_duration_change(s,'A',1).diagnostics==('completion_anchor_unresolved',)
    assert simulate_duration_change(chain(),'A',1,CPMConfig(completion_activity_code='absent')).status=='NOT_EVALUATED'
    assert simulate_duration_change(chain(),'A',1,anchor_policy='arbitrary').status=='NOT_EVALUATED'


def test_negative_float_retains_traceable_response():
    cfg=CPMConfig(required_project_finish=datetime(2026,1,5,14))
    out=CriticalPathTestService().evaluate(chain(),cfg,CriticalPathTestConfig(delay_hours=2))
    assert out.status=='PASS' and out.response_ratio==1
    assert all(r.calculated_total_float_hours==-2 for r in out.simulation.source_cpm_result.activity_results)
    assert all(r.calculated_total_float_hours==-4 for r in out.simulation.simulated_cpm_result.activity_results)


def test_constraint_control_absorbs_delay_without_fabricating_movement():
    s=chain();s.activities['F'].primary_constraint_type='FINISH_ON_OR_AFTER';s.activities['F'].primary_constraint_date=datetime(2026,1,6,16)
    result=simulate_duration_change(s,'A',1)
    assert result.status=='CALCULATED' and result.completion_movement_working_hours==0
    assert CriticalPathTestService().evaluate(s).status=='NOT_EVALUATED' # no positive work on the constraint-only trace

@pytest.mark.parametrize('kind,lag,finish',[('FS',2,datetime(2026,1,6,9)),('SS',0,datetime(2026,1,5,12)),('FF',0,datetime(2026,1,5,12)),('SF',0,datetime(2026,1,5,12))])
def test_full_relationship_network_recalculation(kind,lag,finish):
    s=chain();s.relationships[0]=Relationship('AB','A','B',kind,lag)
    out=simulate_duration_change(s,'A',2)
    assert out.status=='CALCULATED' and out.source_completion_timestamp==finish
    expected={'FS':2,'SS':0,'FF':2,'SF':0}[kind]
    assert out.completion_movement_working_hours==expected

@pytest.mark.parametrize('calendar_case',['split','holiday','exception'])
def test_calendar_driven_delay_and_immutability(calendar_case):
    from app.calendars.models import WorkPeriod,CalendarException
    s=chain()
    if calendar_case=='split':s.calendars['C1']=make_calendar(periods=(WorkPeriod(time(8),time(12)),WorkPeriod(time(13),time(17))))
    if calendar_case=='holiday':s.calendars['C1']=make_calendar(exceptions=(CalendarException(date(2026,1,6),False,()),))
    if calendar_case=='exception':s.calendars['C1']=make_calendar(exceptions=(CalendarException(date(2026,1,6),True,(WorkPeriod(time(10),time(12)),)),))
    snapshot=deepcopy(s);before=calculate(s)
    out=CriticalPathTestService().evaluate(s,config=CriticalPathTestConfig(delay_hours=3))
    assert out.status=='PASS' and out.simulation.completion_movement_working_hours==3
    assert s==snapshot and calculate(s)==before
    if calendar_case=='holiday':assert out.simulation.simulated_completion_timestamp==datetime(2026,1,7,10)


def mixed():
    from app.calendars.models import WorkPeriod
    s=chain();s.calendars['C2']=make_calendar('C2',periods=(WorkPeriod(time(8),time(12)),))
    s.activities['F'].calendar_id='C2'
    return s


def test_mixed_calendar_requires_explicit_measurement_basis():
    s=mixed();out=CriticalPathTestService().evaluate(s,config=CriticalPathTestConfig(delay_hours=2))
    assert out.status=='NOT_EVALUATED' and out.simulation.completion_movement_elapsed_hours==17
    cfg=CriticalPathTestConfig(delay_hours=2,completion_calendar_id='C1')
    assert CriticalPathTestService().evaluate(s,config=cfg).response_ratio==1
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=datetime(2026,1,6,10)))
    assert out.status=='NOT_EVALUATED'
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=datetime(2026,1,6,10),common_calendar_id='C1',path_length_method='COMMON_CALENDAR_WORKING_SPAN'))
    assert out.status=='PASS' and out.critical_path_length_hours==8 and out.total_float_hours==3 and out.value==1.375

@pytest.mark.parametrize('delta',[float('nan'),float('inf'),-20,'bad'])
def test_invalid_delta_is_not_evaluated(delta):
    assert simulate_duration_change(chain(),'A',delta).status=='NOT_EVALUATED'

@pytest.mark.parametrize('cfg',[CriticalPathTestConfig(delay_hours=0),CriticalPathTestConfig(delay_hours=-1),CriticalPathTestConfig(response_tolerance=-1),CriticalPathTestConfig(warning_response_tolerance=0),CriticalPathTestConfig(required_response_ratio=float('nan'))])
def test_invalid_cpt_configuration(cfg):assert CriticalPathTestService().evaluate(chain(),config=cfg).status=='NOT_EVALUATED'

@pytest.mark.parametrize('activity_id',['missing','F'])
def test_invalid_explicit_activity(activity_id):
    assert simulate_duration_change(chain(),activity_id,2).status=='NOT_EVALUATED'
    assert CriticalPathTestService().evaluate(chain(),config=CriticalPathTestConfig(test_activity_id=activity_id)).status=='NOT_EVALUATED'


def test_no_positive_work_and_unsupported_loe():
    s=chain()
    for a in s.activities.values():a.original_duration_hours=0;a.remaining_duration_hours=0
    assert CriticalPathTestService().evaluate(s).status=='NOT_EVALUATED'
    s=chain();s.activities['A'].raw_activity_type='TT_LOE';s.activities['A'].activity_type='level_of_effort'
    assert simulate_duration_change(s,'B',1).status=='NOT_EVALUATED'


def test_simulation_failure_not_assessed_as_fail(monkeypatch):
    from app.cpm import simulation
    def fail(*args):raise RuntimeError('synthetic recalculation failure')
    monkeypatch.setattr(simulation,'run_cpm',fail)
    assert simulate_duration_change(chain(),'A',1).status=='NOT_EVALUATED'
    assert CriticalPathTestService().evaluate(chain()).status=='NOT_EVALUATED'


def test_duration_fallback_and_preference_overlay_exact_field():
    s=chain();s.activities['A'].remaining_duration_hours=None
    out=simulate_duration_change(s,'A',2)
    assert out.simulated_cpm_result.schedule.activities['A'].original_duration_hours==6
    assert out.simulated_cpm_result.schedule.activities['A'].remaining_duration_hours is None
    s=chain();s.activities['A'].remaining_duration_hours=1
    out=simulate_duration_change(s,'A',2,CPMConfig(remaining_duration_preference=False))
    assert out.original_effective_duration_hours==4 and out.simulated_effective_duration_hours==6
    assert out.simulated_cpm_result.schedule.activities['A'].remaining_duration_hours==1

@pytest.mark.parametrize('ratio,status',[(1,'PASS'),(.97,'WARNING'),(.9,'FAIL'),(1.1,'FAIL')])
def test_visible_cpt_response_thresholds(ratio,status):
    # SS allows shortening B's response: A duration is not its start requirement.
    s=chain();s.relationships[0]=Relationship('AB','A','B','SS',0)
    out=CriticalPathTestService().evaluate(s,config=CriticalPathTestConfig(test_activity_id='B',delay_hours=1,required_response_ratio=ratio,response_tolerance=1e-9,warning_response_tolerance=.05))
    assert out.response_ratio==1 and out.status==status


def test_cpli_missing_finish_zero_length_and_completed_history():
    assert CPLIService().calculate(chain()).diagnostics==('required_finish_missing',)
    s=chain()
    for a in s.activities.values():a.original_duration_hours=0;a.remaining_duration_hours=0
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=D))
    assert out.status=='NOT_EVALUATED' and out.denominator_hours==0 and out.value is None


def test_cpli_finish_constraint_provenance_and_conflicts():
    s=chain();s.activities['F'].primary_constraint_type='FINISH_ON_OR_BEFORE';s.activities['F'].primary_constraint_date=datetime(2026,1,5,14)
    out=CPLIService().calculate(s)
    assert out.required_finish_source=='SELECTED_ANCHOR_FINISH_ON_OR_BEFORE_CONSTRAINT' and out.value==.75
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=datetime(2026,1,6,10)))
    assert out.status=='NOT_EVALUATED' and out.diagnostics==('required_finish_not_effective_anchor_deadline',)
    s.activities['F'].secondary_constraint_type='FINISH_ON_OR_BEFORE';s.activities['F'].secondary_constraint_date=datetime(2026,1,5,15)
    assert CPLIService().calculate(s).diagnostics==('ambiguous_required_finish_constraints',)


def test_cpli_constraint_release_path_duration_and_non_fs_policy():
    s=chain();s.activities['A'].primary_constraint_type='START_ON_OR_AFTER';s.activities['A'].primary_constraint_date=datetime(2026,1,6,8)
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=datetime(2026,1,6,16)))
    assert out.value==1 and out.selected_path.end_reason=='CONSTRAINT' and out.critical_path_length_hours==8
    s=chain();s.relationships[0]=Relationship('AB','A','B','SS',0)
    assert CPLIService().calculate(s,config=CPLIConfig(required_finish=datetime(2026,1,5,12))).status=='NOT_EVALUATED'
    cfg=CPLIConfig(required_finish=datetime(2026,1,5,12),common_calendar_id='C1',path_length_method='COMMON_CALENDAR_WORKING_SPAN')
    assert CPLIService().calculate(s,config=cfg).value==1

@pytest.mark.parametrize('finish,value,status',[(datetime(2026,1,5,15,36),.95,'WARNING'),(datetime(2026,1,5,15,48),.975,'WARNING')])
def test_cpli_warning_threshold_exact_and_between(finish,value,status):
    out=CPLIService().calculate(chain(),config=CPLIConfig(required_finish=finish))
    assert out.value==pytest.approx(value) and out.status==status


def test_cpli_ties_and_trace_limits():
    out=CPLIService().calculate(diamond(True),config=CPLIConfig(required_finish=datetime(2026,1,5,16)))
    assert len(out.paths)==2 and out.value==1
    cfg=CPMConfig(maximum_path_depth=1)
    assert CPLIService().calculate(chain(),cfg,CPLIConfig(required_finish=datetime(2026,1,5,16))).status=='NOT_EVALUATED'
    assert CriticalPathTestService().evaluate(chain(),cfg).status=='NOT_EVALUATED'


def test_cpli_required_config_and_immutability():
    s=chain();before=deepcopy(s)
    cfg=CPMConfig(required_project_finish=datetime(2026,1,5,16))
    out=CPLIService().calculate(s,cfg)
    assert out.value==1 and out.required_finish_source=='CONFIGURED_CPM_REQUIRED_FINISH'
    assert s==before
    assert CPLIService().calculate(s,cfg,CPLIConfig(required_finish=datetime(2026,1,5,17))).status=='NOT_EVALUATED'


def test_in_progress_actual_segment_is_not_changed():
    s=chain();a=s.activities['A'];a.status=a.raw_status='TK_Active';a.actual_start=datetime(2026,1,2,8)
    before=deepcopy(s);out=simulate_duration_change(s,'A',2)
    assert out.status=='CALCULATED' and s==before
    assert out.simulated_cpm_result.schedule.activities['A'].actual_start==before.activities['A'].actual_start



def test_response_warning_boundary_is_inclusive():
    cfg=CriticalPathTestConfig(delay_hours=1,required_response_ratio=1.05,warning_response_tolerance=.05)
    out=CriticalPathTestService().evaluate(chain(),config=cfg)
    assert out.response_ratio==1 and out.status=='WARNING'



def test_anchor_identity_changes_only_by_explicit_policy():
    s=chain();s.activities.pop('B');s.activities['F'].activity_code='F1';f2=deepcopy(s.activities['F']);f2.activity_id='F2';f2.activity_code='F2';s.activities['F2']=f2
    s.activities['A'].remaining_duration_hours=s.activities['A'].original_duration_hours=2
    s.relationships=[Relationship('AF1','A','F','FS',2),Relationship('AF2','A','F2','FS',0)];s.rebuild_activity_indexes()
    config=CPMConfig(project_completion_timestamp=datetime(2026,1,5,12))
    locked=simulate_duration_change(s,'A',2,config)
    reselected=simulate_duration_change(s,'A',2,config,anchor_policy='RESELECT_TERMINAL',completion_calendar_id='C1')
    assert locked.source_completion_anchor.activity_id==locked.simulated_completion_anchor.activity_id=='F'
    assert locked.completion_movement_working_hours==2
    assert reselected.source_completion_anchor.activity_id=='F' and reselected.simulated_completion_anchor.activity_id=='F2'
    assert reselected.completion_movement_working_hours==0
    assert simulate_duration_change(s,'A',2,config,anchor_policy='RESELECT_TERMINAL').status=='NOT_EVALUATED'


def test_original_imported_dates_float_constraints_and_calendars_preserved():
    s=chain();a=s.activities['A']
    a.early_start=D;a.early_finish=datetime(2026,1,5,12);a.late_start=D;a.late_finish=datetime(2026,1,5,12)
    a.planned_start=datetime(2026,1,2,8);a.planned_finish=datetime(2026,1,2,12)
    a.total_float_hours=-7;a.free_float_hours=-3
    a.primary_constraint_type='START_ON_OR_AFTER';a.primary_constraint_date=D
    a.secondary_constraint_type='FINISH_ON_OR_BEFORE';a.secondary_constraint_date=datetime(2026,1,5,17)
    before=deepcopy(s);original=calculate(s)
    out=simulate_duration_change(s,'A',1)
    assert out.status=='CALCULATED' and s==before and calculate(s)==original
    for field in ('early_start','early_finish','late_start','late_finish','planned_start','planned_finish','total_float_hours','free_float_hours','primary_constraint_date','secondary_constraint_date'):
        assert getattr(out.simulated_cpm_result.schedule.activities['A'],field)==getattr(a,field)
    assert out.source_cpm_result.schedule.calendars['C1'] is not s.calendars['C1']
    assert out.simulated_cpm_result.schedule.calendars['C1'] is not out.source_cpm_result.schedule.calendars['C1']


def test_completed_actuals_remain_history():
    s=chain();h=activity('H','H',4,status='TK_Complete');h.actual_start=datetime(2026,1,2,8);h.actual_finish=datetime(2026,1,2,12)
    s.activities['H']=h;s.relationships.insert(0,Relationship('HA','H','A','FS',0));s.rebuild_activity_indexes()
    before=deepcopy(s);out=simulate_duration_change(s,'B',2)
    assert out.status=='CALCULATED' and s==before
    row=next(r for r in out.simulated_cpm_result.activity_results if r.activity_id=='H')
    assert row.calculated_early_start==h.actual_start and row.calculated_early_finish==h.actual_finish
    assert simulate_duration_change(s,'H',2).status=='NOT_EVALUATED'


def test_large_immutable_simulation_is_iterative():
    n=1001
    s=make_schedule([activity(str(i),str(i),.25) for i in range(n)],
        [Relationship(str(i),str(i),str(i+1),'FS',0) for i in range(n-1)])
    cfg=CPMConfig(maximum_path_depth=1100,maximum_path_nodes_inspected=20000)
    before=deepcopy(s)
    out=CriticalPathTestService().evaluate(s,cfg,CriticalPathTestConfig(delay_hours=1))
    assert out.status=='PASS' and out.response_ratio==1 and s==before
    assert len(out.simulation.source_cpm_result.critical_paths[0].activity_ids)==n

@pytest.mark.parametrize('cfg',[CPLIConfig(pass_threshold=float('nan')),CPLIConfig(warning_threshold=2),CPLIConfig(path_length_method='guess'),CPLIConfig(common_calendar_id='C1')])
def test_cpli_invalid_methods_and_thresholds(cfg):assert CPLIService().calculate(chain(),config=cfg).status=='NOT_EVALUATED'


@pytest.mark.parametrize('lag,length,finish',[(2,10,datetime(2026,1,6,9)),(-1,7,datetime(2026,1,5,15))])
def test_cpli_signed_lag_contribution(lag,length,finish):
    s=chain();s.relationships[0]=Relationship('AB','A','B','FS',lag)
    out=CPLIService().calculate(s,config=CPLIConfig(required_finish=finish))
    assert out.value==1 and out.critical_path_length_hours==length
    assert out.sum_effective_activity_duration_hours==8 and out.relationship_lag_contribution_hours==lag
    assert out.numerator_hours==out.denominator_hours==length


def test_start_control_does_not_guarantee_duration_response():
    s=chain();s.relationships[0]=Relationship('AB','A','B','SS',0)
    out=CriticalPathTestService().evaluate(s,config=CriticalPathTestConfig(delay_hours=1))
    assert out.selected_activity_id=='A' and out.status=='FAIL' and out.response_ratio==0
    assert out.simulation.status=='CALCULATED'


def test_simulated_recalculation_failure_preserves_original_result(monkeypatch):
    from app.cpm import simulation
    s=chain();before=deepcopy(s);real=simulation.run_cpm;calls=[]
    def injected(*args):
        calls.append(1)
        if len(calls)==2:raise RuntimeError('synthetic second network calculation failure')
        return real(*args)
    monkeypatch.setattr(simulation,'run_cpm',injected)
    out=simulate_duration_change(s,'A',1)
    assert out.status=='NOT_EVALUATED' and out.source_cpm_result.status=='CALCULATED'
    assert len(calls)==2 and s==before


def test_cpli_does_not_infer_deadline_from_imported_or_planned_finish():
    s=chain();a=s.activities['F'];a.early_finish=a.late_finish=a.planned_finish=datetime(2026,1,5,16)
    s.project.planned_finished=datetime(2026,1,5,16)
    assert CPLIService().calculate(s).diagnostics==('required_finish_missing',)


def test_cpli_independent_threshold_configuration_is_visible():
    out=CPLIService().calculate(chain(),config=CPLIConfig(required_finish=datetime(2026,1,5,14),pass_threshold=.7,warning_threshold=.5))
    assert out.value==.75 and out.status=='PASS'


def test_unsupported_expected_finish_and_partial_scope_not_evaluated():
    from tests.test_cpm_progress import options
    s=chain();s.scheduling_options=options();s.activities['A'].expected_finish=datetime(2026,1,5,12)
    for policy in ('STRICT','DIRECTIONAL_FORWARD','VALID_COMPONENTS'):
        cfg=CPMConfig(component_calculation_policy=policy,progress_scheduling_policy='P6_RETAINED_LOGIC')
        assert simulate_duration_change(s,'B',1,cfg).status=='NOT_EVALUATED'
        assert CPLIService().calculate(s,cfg,CPLIConfig(required_finish=datetime(2026,1,5,16))).status=='NOT_EVALUATED'
