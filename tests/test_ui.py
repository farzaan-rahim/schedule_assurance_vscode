import json,subprocess,sys
from dataclasses import replace
from pathlib import Path
from datetime import datetime
import pytest
from app.ui.state import SessionState,TableQuery,NAVIGATION
from app.ui.presentation import page_rows,text,metric_evidence
from tests.ui_helpers import memory_service


def test_session_selection_and_navigation():
    s=SessionState();s.select_project('P');s.select_version('V');s.source_version_id='B';s.analysis_anchor_id='A'
    for name,_ in NAVIGATION:s.navigate(name);assert s.version_id=='V' and s.source_version_id=='B' and s.analysis_anchor_id=='A'
    s.select_version('V2');assert s.analysis_anchor_id is None
    s.select_project('P2');assert s.version_id is None and s.source_version_id is None
    with pytest.raises(ValueError):s.navigate('bad')

@pytest.mark.parametrize('limit',[0,201,-1])
def test_bounded_pages(limit):
    with pytest.raises(ValueError):TableQuery(limit=limit)


def test_large_rows_filter_sort_paginate_server_side():
    rows=[dict(activity_id=str(i),description='Activity '+str(i),wbs_path='ROOT > '+str(i%3),status='open',activity_type='task',classification='CHANGED',value=i) for i in range(25000)]
    out=page_rows(rows,TableQuery(wbs='ROOT > 1',status='open',activity_type='task',classification='CHANGED',sort='value',descending=True,offset=50,limit=100))
    assert out['total']==8333 and len(out['rows'])==100 and out['rows'][0]['value']>out['rows'][-1]['value']
    assert len(json.dumps(out))<50000 and out['has_more']


def test_missing_values_and_zero_distinct():
    assert text(None)=='Not available' and text(0)=='0'
    assert page_rows([],TableQuery())['rows']==[]


def test_report_sections_and_not_evaluated_contract():
    service=memory_service();b,c=service.catalog.versions
    report=service.report(b.id,c.id)
    assert len(report.sections)==29
    for section in report.sections:
        data=service.report_page(report,section.key,TableQuery(limit=50))
        assert data['section_key']==section.key and len(data['rows'])<=50
    assert service.report_page(report,'resources',TableQuery())['availability'].value=='NOT_EVALUATED'


def test_activity_detail_imported_calculated_and_availability():
    service=memory_service();v=service.catalog.versions[-1].id
    detail=service.activity_detail(v,'0')
    assert detail['identity']['activity_id']=='A' and detail['application_calculated'] is None
    assert detail['application_availability']=='NOT_EVALUATED' and detail['successors']
    selection=service.anchor_selection('5')
    analysis=service.anchor_analysis(v,selection)
    assert service.activity_detail(v,'0',analysis)['application_calculated']['activity_code']=='A'
    assert analysis.anchor.contractual_authority_status=='NOT_ESTABLISHED'


def test_cpt_cpli_bounded_audit_projection():
    service=memory_service();v=service.catalog.versions[-1].id
    result=service.dcma(v)
    for key in ('critical_path_test','cpli'):
        m=next(m for m in result.metric_results if m.metric_id==key)
        e=metric_evidence(m)
        assert m.status.value=='PASS'
        assert 'source_cpm_result' not in e and 'cpm_result' not in e
    s=service.catalog.schedules[v];s.calendars.clear();service.clear()
    for m in service.dcma(v).metric_results:
        if m.metric_id in ('critical_path_test','cpli'):assert metric_evidence(m)['diagnostics']


def test_export_delegates_existing_renderer_and_requires_pair():
    service=memory_service();b,c=service.catalog.versions
    assert service.export(b.id,c.id)[:2]==b'PK'
    with pytest.raises(ValueError):service.report(None,c.id)
    with pytest.raises(ValueError):service.anchor_selection(None)


def test_nicegui_event_scenario():
    result=subprocess.run([sys.executable,'-m','tests.ui_scenario'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'UI_SCENARIO_PASSED' in result.stdout
    assert 'Traceback (most recent call last)' not in result.stderr,result.stderr



def test_code_anchor_selection_and_required_finish_modes():
    service=memory_service();v=service.catalog.versions[-1].id
    selection=service.anchor_selection(None,activity_code='F3')
    assert service.anchor_analysis(v,selection).anchor.activity_code=='F3'
    independent=service.anchor_selection('5','INDEPENDENT','2026-01-05 14:00')
    assert service.anchor_analysis(v,independent).anchor.timestamp_source=='CALLER_REQUIRED_FINISH'
    from app.cpm.analysis_anchors import AnchorSelectionError
    with pytest.raises(AnchorSelectionError):service.anchor_analysis(v,service.anchor_selection('5','INDEPENDENT'))


def test_directional_rows_join_existing_variances():
    from app.ui.presentation import selected_analysis_rows
    service=memory_service();v=service.catalog.versions[-1].id
    analysis=service.anchor_analysis(v,service.anchor_selection('5'))
    rows=selected_analysis_rows(analysis)
    assert len(rows)==len(analysis.activity_dispositions)
    assert rows[0]['late_start_variance_hours']==next(c['variance_hours'] for c in analysis.comparisons if c['activity_id']==rows[0]['activity_id'] and c['metric']=='late_start')
    assert rows[0]['es_availability']=='AVAILABLE'


def test_report_rows_keep_source_and_target_identity():
    service=memory_service();b,c=service.catalog.versions
    data=service.report_page(service.report(b.id,c.id),'activities',TableQuery())
    assert all(row['_version_id']==str(c.id) for row in data['rows'])


def test_diagnostic_category_and_severity_filters():
    rows=[dict(category='IMPORT',severity='ERROR',message='bad'),dict(category='CPM',severity='WARNING',message='blocked')]
    assert page_rows(rows,TableQuery(category='CPM',severity='WARNING'))['total']==1


def test_finding_projection_exposes_relationship_context():
    service=memory_service();v=service.catalog.versions[-1].id
    metric=next(m for m in service.dcma(v).metric_results if m.metric_id=='missing_logic')
    rows=service.dcma_finding_rows(v,metric)
    assert rows and 'predecessor_count' in rows[0] and 'successor_count' in rows[0]


def test_activity_code_ambiguity_does_not_choose_arbitrary_task():
    service=memory_service();v=service.catalog.versions[-1].id
    s=service.catalog.schedules[v];s.activities['2'].activity_code='A';s.rebuild_activity_indexes()
    from app.persistence.exceptions import RecordNotFound
    with pytest.raises(RecordNotFound):service.activity_detail(v,'A',by_code=True)


def test_workspace_mount_and_existing_api():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        assert client.get('/',follow_redirects=False).headers['location']=='/ui/'
        response=client.get('/ui/')
        assert response.status_code==200 and 'Schedule Assurance' in response.text
        assert client.get('/api/health').status_code==200



def test_controlled_fixture_changes_remain_visible_in_report_pages():
    from app.services.schedule_import import ScheduleImportService
    root=Path(__file__).resolve().parents[1];service=memory_service();b,c=service.catalog.versions
    for info,kind in ((b,'baseline'),(c,'current')):
        service.catalog.schedules[info.id]=ScheduleImportService().import_file(root/f'sample_data/sample_{kind}.xer').schedule
    report=service.report(b.id,c.id)
    rows=service.report_page(report,'activities',TableQuery())['rows']
    assert next(r for r in rows if r['activity_id']=='A1500')['classification']=='REMOVED'
    assert next(r for r in rows if r['activity_id']=='A1700')['classification']=='ADDED'
    assert next(r for r in rows if r['activity_id']=='A1500')['_version_id']==str(b.id)
    delayed=service.report_page(report,'planned_finish',TableQuery(search='A1200'))['rows']
    assert delayed and delayed[0]['classification']=='DELAYED'



def test_early_variances_are_existing_comparison_results():
    from copy import deepcopy
    service=memory_service();v=service.catalog.versions[-1].id
    analysis=service.anchor_analysis(v,service.anchor_selection('5'));before=deepcopy(analysis.cpm_result.schedule)
    rows=service.analysis_rows(analysis)
    assert rows[0]['early_start_variance_hours']==0 and rows[0]['early_finish_variance_hours']==0
    assert analysis.cpm_result.schedule==before



def test_milestone_date_projection_uses_existing_milestone_policy():
    service=memory_service();v=service.catalog.versions[-1].id
    a=service.catalog.schedules[v].activities['5'];a.activity_type='start_milestone';a.raw_activity_type='TT_StartMile'
    a.planned_start=datetime(2026,1,5,14);a.planned_finish=None
    rows=service.milestone_rows(v,service.milestones(v))
    assert next(r for r in rows if r['activity_id']=='5')['planned_date']==a.planned_start



def test_classification_filter_does_not_match_unchanged_substring():
    rows=[dict(activity_id='A',classification='CHANGED'),dict(activity_id='B',classification='UNCHANGED')]
    assert page_rows(rows,TableQuery(classification='CHANGED'))['total']==1
