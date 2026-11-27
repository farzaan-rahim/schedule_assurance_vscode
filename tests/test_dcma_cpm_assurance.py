from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.dcma.config import DCMAConfig
from app.dcma.service import DCMAAssessmentService
from app.cpm.config import CPMConfig
from app.cpm.simulation import CriticalPathTestConfig
from app.cpm.cpli import CPLIConfig
from app.graph.schedule_graph import ScheduleGraph
from tests.test_cpm_simulation import chain


def assess(schedule,config=None):
    return DCMAAssessmentService().analyze(schedule,ScheduleGraph(schedule),config)


def metric(result,key):return next(m for m in result.metric_results if m.metric_id==key)


def test_dcma_evaluates_only_after_immutable_and_required_finish_gates():
    s=chain();before=deepcopy(s)
    result=assess(s);cpt=metric(result,'critical_path_test');cpli=metric(result,'cpli')
    assert cpt.status.value=='PASS' and cpt.details['response_ratio']==1
    assert cpt.details['simulation']['source_completion_timestamp']==datetime(2026,1,5,16)
    assert cpli.status.value=='NOT_EVALUATED' and cpli.details['diagnostics']==('required_finish_missing',)
    config=DCMAConfig(cpm_config=CPMConfig(required_project_finish=datetime(2026,1,5,14)),critical_path_test_config=CriticalPathTestConfig(delay_hours=2))
    result=assess(s,config);cpt=metric(result,'critical_path_test');cpli=metric(result,'cpli')
    assert cpt.status.value=='PASS' and cpli.status.value=='FAIL'
    assert cpli.details['critical_path_length_hours']==8 and cpli.details['total_float_hours']==-2 and cpli.details['value']==.75
    assert cpli.details['numerator_hours']==6 and cpli.details['denominator_hours']==8
    assert any(c.metric_id=='cpli' and c.evaluated_weight>0 for c in result.overall_score.contributions)
    encoded=jsonable_encoder(result)
    assert encoded['metric_results'] and s==before
    assert 'schedule' not in cpt.details['simulation']['source_cpm_result']


def test_unusable_source_remains_not_evaluated_with_diagnostics():
    s=chain();s.calendars.clear();result=assess(s)
    for key in ('critical_path_test','cpli'):
        m=metric(result,key)
        assert m.status.value=='NOT_EVALUATED' and m.details['source_cpm_result']['status']=='FAILED'
        assert m.details['source_cpm_result']['diagnostics']
        contribution=next(c for c in result.overall_score.contributions if c.metric_id==key)
        assert contribution.evaluated_weight==0


def test_default_dcma_can_use_unambiguous_anchor_finish_deadline():
    s=chain();s.activities['F'].primary_constraint_type='FINISH_ON_OR_BEFORE';s.activities['F'].primary_constraint_date=datetime(2026,1,5,16)
    result=assess(s)
    assert metric(result,'critical_path_test').status.value=='PASS'
    assert metric(result,'cpli').status.value=='PASS'
    assert metric(result,'cpli').details['required_finish_source']=='SELECTED_ANCHOR_FINISH_ON_OR_BEFORE_CONSTRAINT'
