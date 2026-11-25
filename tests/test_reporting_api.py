from io import BytesIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from app.main import app
from app.reporting.limits import ReportLimits
from app.reporting.service import ForensicReportingService

ROOT=Path(__file__).resolve().parents[1]


def uploads():
    return {name:(f'{name}.xer',(ROOT/f'sample_data/sample_{name}.xer').read_bytes(),'application/octet-stream') for name in ('baseline','current')}


def test_reporting_preview_contract_and_pagination():
    with TestClient(app) as client:
        response=client.post('/api/reports/forensic-change/preview?limit=2',files=uploads(),data={'generated_by':'Synthetic reviewer'})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['schema_version']=='1.0' and len(data['sections'])==29
    assert data['metadata']['generated_by']=='Synthetic reviewer'
    assert data['metadata']['completion_authority_status']=='NOT_ESTABLISHED'
    assert data['metadata']['selected_analysis_anchor'] is None
    activities=next(s for s in data['sections'] if s['key']=='activities')
    assert activities['count']==8 and len(activities['rows'])==2
    assert activities['has_more'] and not activities['truncated']
    tf=next(s for s in data['sections'] if s['key']=='total_float')
    assert tf['rows'][0]['cells']['application_calculated'] is None


def test_reporting_excel_attachment():
    with TestClient(app) as client:
        response=client.post('/api/reports/forensic-change/excel',files=uploads())
    assert response.status_code==200,response.text
    assert response.headers['content-type']=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'Schedule Assurance Forensic Change Report.xlsx' in response.headers['content-disposition']
    wb=load_workbook(BytesIO(response.content),read_only=True)
    assert len(wb.sheetnames)==29 and wb.sheetnames[0]=='Report Summary'
    assert wb['Activities']['A7'].value==1


@pytest.mark.parametrize('endpoint',['preview','excel'])
def test_reporting_bad_extension_and_missing_upload(endpoint):
    with TestClient(app) as client:
        files=uploads();files['baseline']=('bad.xlsx',b'bad','application/octet-stream')
        assert client.post('/api/reports/forensic-change/'+endpoint,files=files).status_code==415
        assert client.post('/api/reports/forensic-change/'+endpoint,files={}).status_code==422


def test_reporting_malformed_and_cross_project_sources():
    with TestClient(app) as client:
        files=uploads();files['baseline']=('bad.xer',b'not an XER','application/octet-stream')
        assert client.post('/api/reports/forensic-change/preview',files=files).status_code==422
        files=uploads();files['current']=('current.xer',files['current'][1].replace(b'SYNTHETIC',b'OTHERPROJECT'),'application/octet-stream')
        assert client.post('/api/reports/forensic-change/preview',files=files).status_code==422
        assert client.post('/api/reports/forensic-change/preview?limit=0',files=uploads()).status_code==422


def test_reporting_upload_limit_is_enforced(monkeypatch):
    from app.api import reports
    monkeypatch.setattr(reports,'ForensicReportingService',lambda:ForensicReportingService(ReportLimits(maximum_upload_bytes=10)))
    with TestClient(app) as client:
        assert client.post('/api/reports/forensic-change/preview',files=uploads()).status_code==413
