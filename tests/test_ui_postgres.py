import pytest
from tests.conftest_postgres import pg
from tests.persistence_helpers import rich_xer
from app.persistence.repositories.navigation import NavigationRepository
from app.api.persistence import PersistenceServices
from app.persistence.services.analyses import StoredAnalysisService
from app.persistence.exceptions import DuplicateScheduleVersion
from app.ui.service import PlannerService
from app.ui.state import TableQuery
from app.ui.presentation import selected_analysis_rows

pytestmark=pytest.mark.postgres


def test_bounded_navigation_uses_real_postgresql(pg):
    pg.catalog.create_project('P%2','Literal wildcard')
    first=pg.importer.import_bytes(rich_xer(),'base.xer',label='Baseline',version_type='BASELINE')
    last=pg.importer.import_bytes(rich_xer()+b'\n','current.xer',label='Current',version_type='CURRENT')
    repo=NavigationRepository(pg.sessions)
    rows,total=repo.projects(limit=1,search='%')
    assert total==1 and rows[0].project_code=='P%2'
    rows,total=repo.versions(first.project_id,limit=1)
    assert total==2 and len(rows)==1 and rows[0].id==last.id
    rows,total=repo.versions(first.project_id,offset=1,limit=1)
    assert rows[0].id==first.id
    rows,total=repo.versions(first.project_id,limit=1,sort='label')
    assert rows[0].id==first.id


def test_ui_orchestration_with_persisted_versions(pg):
    services=PersistenceServices(pg.catalog,pg.importer,StoredAnalysisService(pg.catalog),104857600)
    service=PlannerService(services)
    a=pg.importer.import_bytes(rich_xer(),'base.xer',label='Baseline',version_type='BASELINE')
    b=service.import_xer(a.project_id,rich_xer()+b'\n','current.xer','Current','CURRENT')
    assert service.overview(b.id)['health_score']==services.analyses.health(b.id).score
    report=service.report(a.id,b.id)
    assert len(report.sections)==29 and service.export(a.id,b.id)[:2]==b'PK'
    assert service.anchors(b.id)['selected_analysis_anchor'] is None
    selected=service.anchor_analysis(b.id,service.anchor_selection(None,activity_code='F3'))
    rows=selected_analysis_rows(selected)
    assert len(rows)==6 and all(r['availability']=='BACKWARD_CALCULABLE' for r in rows)
    assert service.activity_detail(b.id,'0',selected)['application_calculated']['activity_code']=='A'
    assert any(r['category']=='IMPORT' for r in service.diagnostics(b.id,selected))
    with pytest.raises(DuplicateScheduleVersion):service.import_xer(a.project_id,rich_xer(),'renamed.xer','Duplicate','UPDATE')
