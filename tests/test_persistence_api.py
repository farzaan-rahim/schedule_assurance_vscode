from io import BytesIO
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import select,func
from app.main import app
from app.api import persistence as api
from app.persistence.models import schema as orm
from app.persistence.settings import PersistenceSettings
from app.persistence.services.analyses import StoredAnalysisService
from tests.conftest_postgres import pg
from tests.persistence_helpers import rich_xer


def test_optional_persistence_does_not_disable_existing_application(monkeypatch):
    monkeypatch.setattr(api,'PersistenceSettings',lambda:PersistenceSettings(database_url=None,_env_file=None))
    with TestClient(app) as client:
        response=client.get('/api/projects')
        assert response.status_code==503 and 'not configured' in response.json()['detail']
        assert client.get('/api/health').status_code==200


@pytest.mark.postgres
def test_stored_schedule_api_workflow_and_analyses(pg):
    services=api.PersistenceServices(pg.catalog,pg.importer,StoredAnalysisService(pg.catalog),100*1024*1024)
    app.dependency_overrides[api.get_persistence_services]=lambda:services
    try:
        with TestClient(app) as client:
            response=client.post('/api/projects',json={'project_code':'P1','project_name':'API Project'})
            assert response.status_code==201,response.text
            project=response.json();pid=project['id']
            assert client.get('/api/projects').json()==[project]
            assert client.get('/api/projects/'+pid).json()==project
            assert client.get('/api/projects/'+str(uuid4())).status_code==404
            versions=[]
            for i,kind in enumerate(('BASELINE','CURRENT')):
                r=client.post(f'/api/projects/{pid}/schedule-versions',data={'label':kind,'version_type':kind},files={'file':('same.xer',rich_xer()+b'\n'*i,'application/octet-stream')})
                assert r.status_code==201,r.text
                versions.append(r.json()['id'])
                assert r.json()['import_status']=='SUCCEEDED'
            b,c=versions;pair={'baseline_version_id':b,'current_version_id':c}
            assert len(client.get(f'/api/projects/{pid}/schedule-versions').json())==2
            assert client.get('/api/schedule-versions/'+b).json()['version_type']=='BASELINE'
            duplicate=client.post(f'/api/projects/{pid}/schedule-versions',data={'label':'Duplicate'},files={'file':('renamed.xer',rich_xer())})
            assert duplicate.status_code==409,duplicate.text
            assert duplicate.json()['detail']['existing_version_id']==b
            assert client.get(f'/api/schedule-versions/{c}/health').status_code==200
            result=client.get(f'/api/schedule-versions/{c}/dcma');assert result.status_code==200,result.text
            for route in ('compare','compare-milestones'):
                result=client.post('/api/schedule-versions/'+route,json=pair)
                assert result.status_code==200,result.text
            result=client.post(f'/api/schedule-versions/{c}/analyze-anchor',json={'activity_code':'F3'})
            assert result.status_code==200,result.text
            result=client.post(f'/api/schedule-versions/{c}/analyze-anchor',json={'activity_code':'missing'})
            assert result.status_code==422,result.text
            body={**pair,'analysis_anchor':{'activity_code':'F3'},'generated_by':'Synthetic API test'}
            result=client.post('/api/reports/forensic-change/stored/preview',json=body)
            assert result.status_code==200,result.text
            assert len(result.json()['sections'])==29
            result=client.post('/api/reports/forensic-change/stored/excel',json=body)
            assert result.status_code==200,result.text
            workbook=load_workbook(BytesIO(result.content),read_only=True)
            assert len(workbook.sheetnames)==29;workbook.close()
            assert client.post('/api/schedule-versions/compare',json={'baseline_version_id':'bad','current_version_id':c}).status_code==422
            for filename,content,status in [('bad.txt',b'bad',415),('bad.xer',b'bad',422),('../bad.xer',rich_xer(),422)]:
                result=client.post(f'/api/projects/{pid}/schedule-versions',data={'label':'Bad'},files={'file':(filename,content)})
                assert result.status_code==status,result.text
            services.maximum_upload_bytes=1
            assert client.post(f'/api/projects/{pid}/schedule-versions',data={'label':'Large'},files={'file':('large.xer',rich_xer())}).status_code==413
            with pg.sessions() as s:assert s.scalar(select(func.count()).select_from(orm.ScheduleVersionRecord))==2
            assert len(list(pg.storage.root.rglob('*.xer')))==2
    finally:app.dependency_overrides.pop(api.get_persistence_services,None)
