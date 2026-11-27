from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock
import subprocess,sys
import pytest
from app.importers.preflight import preflight_xer
from app.services.schedule_import import ScheduleImportService
from app.persistence.exceptions import ImportRejected
from app.persistence.services.imports import PersistedScheduleImportService
from app.persistence.services.storage import LocalSourceStorage
from tests.test_analysis_anchors import controlled_xer
from tests.ui_helpers import memory_service


def multi_xer():
    return ("ERMHDR\t26.5\tSynthetic preflight fixture\n"
        "%T\tPROJECT\n%F\tproj_id\tproj_short_name\tproj_name\tlast_recalc_date\n"
        "%R\t10\tALPHA\tAlpha project\t2026-01-05 08:00\n%R\t20\tBETA\tBeta project\t2026-02-01 08:00\n"
        "%T\tPROJWBS\n%F\twbs_id\tproj_id\twbs_short_name\twbs_name\tparent_wbs_id\n"
        "%R\tWA\t10\tA\tAlpha WBS\t\n%R\tWB\t20\tB\tBeta WBS\t\n"
        "%T\tTASK\n%F\ttask_id\tproj_id\ttask_code\ttask_name\twbs_id\ttask_type\tstatus_code\ttarget_drtn_hr_cnt\n"
        "%R\t1\t10\tA1\tAlpha one\tWA\tTT_Task\tTK_NotStart\t4\n"
        "%R\t2\t10\tA2\tAlpha two\tWA\tTT_Task\tTK_NotStart\t4\n"
        "%R\t3\t20\tB1\tBeta one\tWB\tTT_Task\tTK_NotStart\t2\n"
        "%T\tTASKPRED\n%F\ttask_pred_id\tproj_id\ttask_id\tpred_task_id\tpred_type\tlag_hr_cnt\n"
        "%R\tR1\t10\t2\t1\tPR_FS\t0\n"
        "%E\n").encode()


def test_preflight_single_project_metadata_and_match():
    preview=preflight_xer(controlled_xer())
    p=preview.select(preview.default_project_id)
    assert (p.source_project_id,p.project_code,p.project_name)==('P1','P1','Synthetic selected analysis')
    assert p.data_date==datetime(2026,1,5,8)
    assert (p.activity_count,p.relationship_count,p.wbs_count)==(7,5,1)
    assert p.matches(SimpleNamespace(project_code='P1'))
    assert not p.matches(SimpleNamespace(project_code='TEST'))
    assert not p.matches(None)


def test_preflight_scans_all_projects_without_dominant_selection():
    preview=preflight_xer(multi_xer())
    assert preview.default_project_id is None
    assert [(p.project_code,p.activity_count,p.relationship_count,p.wbs_count) for p in preview.projects]==[('ALPHA',2,1,1),('BETA',1,0,1)]
    with pytest.raises(ValueError,match='Choose one unambiguous'):preview.select(None)
    with pytest.raises(ValueError,match='Choose one unambiguous'):preview.select('missing')


def test_explicit_non_dominant_project_is_imported(tmp_path):
    path=tmp_path/'multi.xer';path.write_bytes(multi_xer())
    result=ScheduleImportService().import_file(path,source_project_id='20')
    assert result.succeeded
    assert result.schedule.project.project_code=='BETA'
    assert list(result.schedule.activities)==['3']
    assert list(result.schedule.wbs_nodes)==['WB'] and not result.schedule.relationships
    assert path.read_bytes()==multi_xer()
    bad=ScheduleImportService().import_file(path,source_project_id='missing')
    assert not bad.succeeded and bad.diagnostics[0].code=='source_project_selection_invalid'


def test_preflight_rejects_ambiguous_project_identity():
    data=multi_xer().replace(b'%R\t20\tBETA',b'%R\t10\tBETA')
    with pytest.raises(ValueError,match='ambiguous'):preflight_xer(data)


def test_preflight_uses_project_root_wbs_name_when_project_name_absent():
    data=multi_xer().replace(b'proj_name',b'ignored_name')
    assert preflight_xer(data).select('10').project_name=='Alpha WBS'


def test_preflight_does_not_map_store_or_write_database(monkeypatch,tmp_path):
    from app.importers.schedule_mapper import ScheduleMapper
    service=memory_service();before=(len(service.catalog.projects),len(service.catalog.versions))
    monkeypatch.setattr(ScheduleMapper,'map',Mock(side_effect=AssertionError('No full mapping in preflight')))
    monkeypatch.setattr(LocalSourceStorage,'store',Mock(side_effect=AssertionError('No file persistence in preflight')))
    service.catalog.create_project=Mock(side_effect=AssertionError('No project creation'))
    service.services.importer.import_bytes=Mock(side_effect=AssertionError('No persisted import'))
    assert service.preflight_xer(controlled_xer(),'schedule.xer').projects
    assert (len(service.catalog.projects),len(service.catalog.versions))==before
    assert not list(tmp_path.iterdir())


def test_create_from_xer_preserves_code_and_editable_name_and_reuses_existing():
    service=memory_service();p=preflight_xer(multi_xer()).select('20')
    created=service.create_project_from_xer(p,'Planner chosen name')
    assert created.project_code=='BETA' and created.project_name=='Planner chosen name'
    assert service.matching_project(p)==created
    again=service.create_project_from_xer(p,'Must not overwrite existing name')
    assert again==created and len(service.catalog.projects)==2


def test_existing_matching_project_is_reused_without_creation():
    service=memory_service();p=preflight_xer(controlled_xer()).projects[0]
    service.catalog.create_project=Mock(side_effect=AssertionError('Do not create a duplicate'))
    assert service.matching_project(p)==service.catalog.project
    assert service.create_project_from_xer(p,'Any name')==service.catalog.project


def test_backend_mismatch_guard_survives_frontend_bypass(tmp_path):
    # Execute the real persistence import method up to its unchanged safety guard.
    # No database/SQLite substitute is used to claim constraint validation.
    selected=SimpleNamespace(project_code='TEST',id=uuid4())
    session=Mock();session.__enter__=Mock(return_value=session);session.__exit__=Mock(return_value=False)
    session.get.return_value=selected
    storage=LocalSourceStorage(tmp_path/'sources')
    service=PersistedScheduleImportService(lambda:session,storage)
    with pytest.raises(ImportRejected,match='Source project code does not match the selected project'):
        service.import_bytes(controlled_xer(),'bypass.xer',label='Bypass',project_id=selected.id,source_project_id='P1')
    session.rollback.assert_called_once();session.commit.assert_not_called()
    assert not list((tmp_path/'sources').rglob('*.xer'))


@pytest.mark.parametrize('filename,content',[('bad.txt',b'XER'),('empty.xer',b'')])
def test_preflight_reuses_upload_validation(filename,content):
    with pytest.raises(ImportRejected):memory_service().preflight_xer(content,filename)


def test_preflight_ui_workflow():
    result=subprocess.run([sys.executable,'-m','tests.ui_preflight_scenario'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'PREFLIGHT_UI_PASSED' in result.stdout
    assert 'Traceback (most recent call last)' not in result.stderr,result.stderr


def test_import_api_passes_explicit_source_project_selection():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.persistence import router,get_persistence_services
    calls=[]
    def import_bytes(content,filename,**kwargs):
        calls.append((content,filename,kwargs));return {'source_project_id':kwargs['source_project_id']}
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_persistence_services]=lambda:SimpleNamespace(maximum_upload_bytes=104857600,importer=SimpleNamespace(import_bytes=import_bytes))
    project_id=uuid4()
    with TestClient(app) as client:
        result=client.post(f'/api/projects/{project_id}/schedule-versions',files={'file':('multi.xer',multi_xer(),'application/octet-stream')},
            data={'label':'Selected Beta','version_type':'UPDATE','source_project_id':'20'})
    assert result.status_code==201 and result.json()['source_project_id']=='20'
    assert calls[0][0]==multi_xer() and calls[0][2]['project_id']==project_id


def test_project_node_name_takes_precedence_over_eps_root_name():
    data=multi_xer().replace(b'parent_wbs_id\n',b'parent_wbs_id\tproj_node_flag\n',1)
    data=data.replace(b'%R\tWA\t10\tA\tAlpha WBS\t\n',b'%R\tEPS\t10\tEPS\tEPS name\t\tN\n%R\tWA\t10\tA\tAlpha WBS\tEPS\tY\n')
    assert preflight_xer(data.replace(b'proj_name',b'ignored_name')).select('10').project_name=='Alpha WBS'
