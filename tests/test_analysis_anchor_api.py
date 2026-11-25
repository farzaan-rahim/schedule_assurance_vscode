from dataclasses import replace
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.cpm.analysis_io import CriticalDefinitionEvidence
from tests.test_analysis_anchors import fixture


@pytest.fixture
def source(monkeypatch):
    from app.cpm import analysis_io
    from app.graph.schedule_graph import ScheduleGraph
    from types import SimpleNamespace
    def imported(path):
        s=fixture()
        return SimpleNamespace(schedule=s,graph=ScheduleGraph(s)),CriticalDefinitionEvidence('P1','CT_TotFloat','0')
    monkeypatch.setattr(analysis_io,'import_analysis_file',imported)


def test_selector_api_contract_and_pagination(source):
    with TestClient(app) as client:
        r=client.post('/api/schedules/cpm/analysis-anchors?limit=1',files={'file':('test.xer',b'controlled domain import')})
    assert r.status_code==200,r.text
    p=r.json();assert p['count']==3 and len(p['candidates'])==1 and p['has_more']
    assert p['selected_analysis_anchor'] is None and p['completion_authority_status']=='NOT_ESTABLISHED'
    assert p['p6_critical_definition_evidence']['raw_path_type']=='CT_TotFloat'


def test_selected_api_calibration_and_independent_success(source):
    with TestClient(app) as client:
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('test.xer',b'domain import')},data={'activity_code':'F3','selected_by':'Caller'})
        assert r.status_code==200,r.text
        p=r.json();assert p['analysis_anchor']['timestamp_source']=='CALIBRATION_IMPORTED_LATE_FINISH'
        assert p['analysis_anchor']['selected_by']=='Caller'
        assert p['summary']['late_calculable']==6 and p['summary']['total_float_valid']==6
        assert p['completion_authority_status']=='NOT_ESTABLISHED'
        assert p['controlling_paths'][0]['classification']=='APPLICATION_CALCULATED_CONTROLLING_PATH'
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('test.xer',b'domain import')},
            data={'internal_id':'5','mode':'INDEPENDENT','required_finish':'2026-01-05T12:00:00'})
        assert r.status_code==200,r.text
        assert r.json()['analysis_anchor']['timestamp_source']=='CALLER_REQUIRED_FINISH'
        assert r.json()['completion_authority_status']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('data,code',[({'activity_code':'none'},'analysis_anchor_not_found'),({},'analysis_anchor_required'),
    ({'activity_code':'F3','mode':'INDEPENDENT'},'analysis_required_finish_missing'),
    ({'activity_code':'F3','internal_id':'1'},'analysis_anchor_selector_conflict')])
def test_selected_api_controlled_errors(source,data,code):
    with TestClient(app) as client:
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('test.xer',b'domain import')},data=data)
    assert r.status_code==422 and r.json()['detail']['code']==code


def test_selected_api_extension_and_malformed_import():
    with TestClient(app) as client:
        assert client.post('/api/schedules/cpm/analysis-anchors',files={'file':('bad.xlsx',b'bad')}).status_code==415
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('bad.xer',b'not xer')},data={'activity_code':'F3'})
        assert r.status_code==422 and r.json()['detail']['code']=='analysis_import_failed'
        assert client.post('/api/schedules/cpm/analysis-anchors?limit=0',files={'file':('test.xer',b'bad')}).status_code==422


def test_selected_api_ambiguity_has_no_fallback(source,monkeypatch):
    from app.cpm import analysis_io
    from app.graph.schedule_graph import ScheduleGraph
    from types import SimpleNamespace
    def imported(path):
        s=fixture();s.activities['DUP']=replace(s.activities['5'],activity_id='DUP');s.rebuild_activity_indexes()
        return SimpleNamespace(schedule=s,graph=ScheduleGraph(s)),None
    monkeypatch.setattr(analysis_io,'import_analysis_file',imported)
    with TestClient(app) as client:
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('test.xer',b'domain import')},data={'activity_code':'F3'})
    assert r.status_code==422 and r.json()['detail']['code']=='analysis_anchor_ambiguous'


def test_actual_xer_upload_to_selected_analysis_and_report_export():
    from io import BytesIO
    from openpyxl import load_workbook
    from tests.test_analysis_anchors import controlled_xer
    data=controlled_xer()
    with TestClient(app) as client:
        r=client.post('/api/schedules/cpm/analyze-anchor',files={'file':('synthetic.xer',data)},data={'activity_code':'F2'})
        assert r.status_code==200,r.text
        assert r.json()['summary']['late_calculable']==4
        files={'baseline':('source.xer',data),'current':('current.xer',data)}
        params={'analysis_anchor_activity_code':'F3','analysis_mode':'CALIBRATION'}
        r=client.post('/api/reports/forensic-change/preview',files=files,data=params)
        assert r.status_code==200,r.text
        assert r.json()['metadata']['selected_analysis_anchor']['activity_code']=='F3'
        r=client.post('/api/reports/forensic-change/excel',files=files,data=params)
        assert r.status_code==200,r.text
        wb=load_workbook(BytesIO(r.content))
        ws=wb['App Controlling Paths']
        assert ws['A7'].value=='F3' and ws['A8'].value=='F3'
        r=client.post('/api/reports/forensic-change/preview',files=files,data={'analysis_anchor_activity_code':'missing'})
        assert r.status_code==422 and r.json()['detail']['code']=='analysis_anchor_not_found'
