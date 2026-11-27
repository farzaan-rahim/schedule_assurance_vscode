from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import persistence as api
from app.persistence.services.analyses import StoredAnalysisService
from app.services.schedule_import import ScheduleImportService
from app.dcma.service import DCMAAssessmentService
from app.graph.schedule_graph import ScheduleGraph
from tests.conftest_postgres import pg
from tests.persistence_helpers import rich_xer

pytestmark=pytest.mark.postgres


def phase8_xer():
    # New controlled fixture: one terminal milestone with an explicit deadline.
    lines=[];table=None
    for line in rich_xer().decode().splitlines():
        if line.startswith('%T\t'):table=line.split('\t')[1]
        if table=='TASK' and line.startswith('%F\t'):line+='\tcstr_type\tcstr_date'
        if table=='TASK' and line.startswith('%R\t'):
            task_id=line.split('\t')[1]
            if task_id=='X':continue
            line+='\t'+('CS_FNLT\t2026-01-05 14:00' if task_id=='5' else '\t')
        lines.append(line)
    return ('\n'.join(lines)+'\n').encode()


def test_phase8_in_memory_reloaded_and_stored_endpoint_parity(pg,tmp_path):
    data=phase8_xer();path=tmp_path/'phase8.xer';path.write_bytes(data)
    original=ScheduleImportService().import_file(path);assert original.succeeded
    assert original.schedule.activities['5'].primary_constraint_type=='FINISH_ON_OR_BEFORE'
    before=DCMAAssessmentService().analyze(original.schedule,ScheduleGraph(original.schedule),source_filename='phase8.xer')
    v=pg.importer.import_bytes(data,'phase8.xer',label='Phase 8 parity')
    info,loaded=pg.catalog.load_version(v.id)
    after=DCMAAssessmentService().analyze(loaded,ScheduleGraph(loaded),source_filename='phase8.xer')
    assert before==after
    for key in ('critical_path_test','cpli'):
        metric=next(m for m in after.metric_results if m.metric_id==key)
        assert metric.status.value=='PASS'
    stored=StoredAnalysisService(pg.catalog)
    assert stored.dcma(v.id)==after
    services=api.PersistenceServices(pg.catalog,pg.importer,stored,100*1024*1024)
    app.dependency_overrides[api.get_persistence_services]=lambda:services
    try:
        with TestClient(app) as client:
            result=client.get(f'/api/schedule-versions/{v.id}/dcma')
            assert result.status_code==200,result.text
            metrics={m['metric_id']:m for m in result.json()['dcma']['metric_results']}
            assert metrics['critical_path_test']['details']['response_ratio']==1
            assert metrics['cpli']['details']['value']==1
            assert metrics['cpli']['details']['critical_path_length_hours']==6
    finally:app.dependency_overrides.pop(api.get_persistence_services,None)
