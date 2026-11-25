import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from uuid import UUID,uuid4
import pytest
from alembic import command
from sqlalchemy import select,func,text,insert,inspect
from sqlalchemy.exc import DBAPIError,IntegrityError
from tests.conftest_postgres import pg
from tests.persistence_helpers import rich_xer
from app.persistence.models import schema as orm
from app.persistence.exceptions import DuplicateScheduleVersion,ImportRejected,PersistenceError,CommitOutcomeUnknown
from app.persistence.services.imports import PersistedScheduleImportService
from app.persistence.repositories.schedule_data import ScheduleDataRepository
from app.services.schedule_import import ScheduleImportService

pytestmark=pytest.mark.postgres


def test_project_multiple_versions_and_multiple_baselines(pg):
    project=pg.catalog.create_project('P1','Project','Description')
    assert isinstance(project.id,UUID) and project.active
    assert pg.catalog.get_project(project.id)==project
    assert len(pg.catalog.list_projects())==1
    a=pg.importer.import_bytes(rich_xer(),'same-name.xer',label='Baseline 1',version_type='BASELINE',project_id=project.id)
    b=pg.importer.import_bytes(rich_xer()+b'\n','same-name.xer',label='Baseline 2',version_type='BASELINE',project_id=project.id)
    c=pg.importer.import_bytes(rich_xer()+b'\n\n','same-name.xer',label='Snapshot',version_type='SNAPSHOT',project_id=project.id)
    assert len({a.id,b.id,c.id})==3 and a.source_sha256!=b.source_sha256
    assert [v.version_type for v in pg.catalog.list_versions(project.id)]==['BASELINE','BASELINE','SNAPSHOT']
    with pytest.raises(ImportRejected):pg.catalog.create_project('P1','Duplicate')


def test_native_uuid_jsonb_fk_unique_and_index(pg):
    version=pg.importer.import_bytes(rich_xer(),'a.xer',label='A')
    with pg.sessions() as s:
        row=s.scalar(select(orm.ActivityRecord).where(orm.ActivityRecord.source_task_id=='0'))
        assert isinstance(row.id,UUID) and isinstance(row.schedule_version_id,UUID)
        assert s.scalar(text("SELECT pg_typeof(id)::text FROM activities LIMIT 1"))=='uuid'
        assert s.scalar(text("SELECT pg_typeof(working_pattern)::text FROM calendars LIMIT 1"))=='jsonb'
        assert s.scalar(text("SELECT working_pattern->0->>'weekday' FROM calendars LIMIT 1"))=='0'
        indexes=inspect(s.connection()).get_indexes('activities')
        assert any(i['name']=='ix_activities_version_code' and i['column_names']==['schedule_version_id','activity_code'] for i in indexes)
        assert s.scalar(select(func.count()).select_from(orm.SourceFileRecord))==1
        source=s.scalar(select(orm.SourceFileRecord));assert not Path(source.relative_path).is_absolute()
        assert source.storage_filename!=source.original_filename and pg.storage.resolve(source.relative_path).exists()


def test_complete_canonical_roundtrip_and_all_existing_analyses(pg,tmp_path):
    data=rich_xer();p=tmp_path/'original.xer';p.write_bytes(data)
    imported=ScheduleImportService().import_file(p);original=imported.schedule
    version=pg.importer.import_bytes(data,'rich.xer',label='Rich',version_type='CURRENT')
    info,loaded=pg.catalog.load_version(version.id)
    assert loaded==original
    assert pg.catalog.diagnostics(version.id)==tuple(imported.diagnostics)
    assert loaded.activities['0'].early_start==original.activities['0'].early_start
    assert loaded.resources['R1'].parent_resource_id=='R0'
    assert loaded.get_resource_assignments('0')[0].planned_cost==original.get_resource_assignments('0')[0].planned_cost
    assert loaded.activity_code_values['V1'].parent_activity_code_id=='V0'
    assert len(loaded.udf_values)==5 and any(v.subject_table=='PROJECT' for v in loaded.udf_values)
    assert all(v.subject_table=='TASK' for v in loaded.get_activity_udf_values('0'))
    from app.graph.schedule_graph import ScheduleGraph
    from app.services.schedule_health import ScheduleHealthService
    from app.dcma.service import DCMAAssessmentService
    from app.milestones.service import MilestoneAnalysisService
    from app.cpm.service import CPMService
    from app.cpm.selected_analysis import SelectedAnchorService
    from app.cpm.analysis_anchors import AnalysisAnchorConfig
    from app.comparison.engine import ScheduleComparisonEngine
    from app.comparison.models import ScheduleVersion,ScheduleVersionType
    from app.reporting.builder import ForensicReportBuilder
    from app.reporting.serialization import report_json
    graphs=[ScheduleGraph(s) for s in (original,loaded)]
    assert graphs[0].topological_sort()==graphs[1].topological_sort()
    for service in (ScheduleHealthService(),DCMAAssessmentService(),MilestoneAnalysisService(),CPMService()):
        first=service.analyze(original,graphs[0]) if hasattr(service,'analyze') else service.calculate(original,graphs[0])
        second=service.analyze(loaded,graphs[1]) if hasattr(service,'analyze') else service.calculate(loaded,graphs[1])
        assert first==second
    chosen=[SelectedAnchorService().analyze(s,g,AnalysisAnchorConfig(analysis_anchor_activity_code='F3')) for s,g in zip((original,loaded),graphs)]
    assert chosen[0]==chosen[1]
    now=datetime(2026,1,5,tzinfo=timezone.utc)
    def compare(schedule):
        b=ScheduleVersion('b','Baseline',ScheduleVersionType.BASELINE,'rich.xer',schedule.project.data_date,now,schedule)
        c=replace(b,version_id='c',version_label='Current',version_type=ScheduleVersionType.CURRENT)
        return ScheduleComparisonEngine().compare(b,c)
    a,b=compare(original),compare(loaded);assert a==b
    assert report_json(ForensicReportBuilder().build(a,generated_at=now,report_identifier='same'))==report_json(ForensicReportBuilder().build(b,generated_at=now,report_identifier='same'))
    protected=[m for m in DCMAAssessmentService().analyze(loaded,graphs[1]).metric_results if m.metric_id in {'critical_path_test','cpli'}]
    assert len(protected)==2 and all(m.status.value=='NOT_EVALUATED' for m in protected)


def test_duplicate_hash_is_controlled_and_does_not_leave_files(pg):
    first=pg.importer.import_bytes(rich_xer(),'one.xer',label='Original')
    with pytest.raises(DuplicateScheduleVersion) as exc:pg.importer.import_bytes(rich_xer(),'renamed.xer',label='Different label',version_type='BASELINE')
    assert exc.value.version_id==first.id
    assert len(pg.catalog.list_versions(first.project_id))==1
    assert len(list(pg.storage.root.rglob('*.xer')))==1


def test_concurrent_duplicate_imports_have_one_winner(pg):
    def run(label):
        try:return pg.importer.import_bytes(rich_xer(),'same.xer',label=label)
        except DuplicateScheduleVersion:return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,['one','two']))
    assert sum(r=='duplicate' for r in results)==1
    assert len(list(pg.storage.root.rglob('*.xer')))==1
    with pg.sessions() as s:assert s.scalar(select(func.count()).select_from(orm.ScheduleVersionRecord))==1


def test_rollback_removes_all_rows_and_orphan_file(pg,monkeypatch):
    original=ScheduleDataRepository.persist
    def fail(self,*args):original(self,*args);raise RuntimeError('Synthetic write failure after inserting data')
    monkeypatch.setattr(ScheduleDataRepository,'persist',fail)
    with pytest.raises(RuntimeError):pg.importer.import_bytes(rich_xer(),'failing.xer',label='Failure')
    with pg.sessions() as s:
        for table in (orm.ProjectRecord,orm.ScheduleVersionRecord,orm.ActivityRecord,orm.SourceFileRecord):assert s.scalar(select(func.count()).select_from(table))==0
    assert not list(pg.storage.root.rglob('*.xer'))


def test_bad_source_and_wrong_project_do_not_leave_partial_versions(pg):
    with pytest.raises(ImportRejected):pg.importer.import_bytes(b'not an XER','bad.xer',label='Bad')
    project=pg.catalog.create_project('OTHER','Other')
    with pytest.raises(ImportRejected):pg.importer.import_bytes(rich_xer(),'wrong.xer',label='Wrong',project_id=project.id)
    assert pg.catalog.list_versions(project.id)==()
    assert not list(pg.storage.root.rglob('*.xer'))


def test_duplicate_activity_codes_are_preserved(pg):
    data=rich_xer().replace(b'0\tA\tA\tP1',b'0\tF1\tA\tP1')
    version=pg.importer.import_bytes(data,'duplicates.xer',label='Duplicates')
    _,loaded=pg.catalog.load_version(version.id)
    assert len(loaded.get_activities_by_code('F1'))==2
    assert len({a.activity_id for a in loaded.get_activities_by_code('F1')})==2


def test_unresolved_relationships_are_separate_and_roundtrip(pg,tmp_path):
    data=rich_xer().replace(b'%T\tSCHEDOPTIONS',b'%R\tEXT\tMISSING\t0\tPR_FS\t2\n%T\tSCHEDOPTIONS')
    p=tmp_path/'external.xer';p.write_bytes(data);original=ScheduleImportService().import_file(p)
    version=pg.importer.import_bytes(data,'external.xer',label='External')
    _,loaded=pg.catalog.load_version(version.id)
    assert loaded==original.schedule
    assert loaded.relationships[-1].predecessor_activity_id=='MISSING'
    with pg.sessions() as s:
        assert s.scalar(select(func.count()).select_from(orm.UnresolvedRelationshipRecord))==1
        assert s.scalar(select(func.count()).select_from(orm.RelationshipRecord))==5


@pytest.mark.parametrize('model',[orm.ScheduleVersionRecord,orm.SourceFileRecord,orm.ActivityRecord,orm.WBSRecord,orm.CalendarRecord,
    orm.RelationshipRecord,orm.ResourceRecord,orm.ResourceAssignmentRecord,orm.ActivityCodeTypeRecord,orm.ActivityCodeValueRecord,
    orm.ActivityCodeAssignmentRecord,orm.UDFDefinitionRecord,orm.UDFValueRecord,orm.SchedulingOptionsRecord,orm.DiagnosticRecord])
def test_successful_version_and_all_imported_records_are_immutable(pg,model):
    pg.importer.import_bytes(rich_xer(),'sealed.xer',label='Sealed')
    with pytest.raises(DBAPIError) as exc:
        with pg.sessions.begin() as s:
            row=s.scalar(select(model));assert row is not None
            if model is orm.ScheduleVersionRecord:row.label='changed'
            elif model is orm.SourceFileRecord:row.original_filename='changed.xer'
            else:row.source_order=row.source_order+100
            s.flush()
    assert exc.value.orig.sqlstate=='55000'


def test_successful_delete_insert_and_truncate_are_rejected(pg):
    v=pg.importer.import_bytes(rich_xer(),'sealed.xer',label='Sealed')
    for statement in ('DELETE FROM activities','TRUNCATE activities CASCADE','DELETE FROM schedule_versions'):
        with pytest.raises(DBAPIError) as exc:
            with pg.engine.begin() as c:c.execute(text(statement))
        assert exc.value.orig.sqlstate=='55000'
    with pytest.raises(DBAPIError):
        with pg.sessions.begin() as s:
            s.add(orm.ActivityRecord(id=uuid4(),schedule_version_id=v.id,source_order=100,source_task_id='NEW'))


def draft(pg,session):
    from app.persistence.repositories.versions import ScheduleVersionRepository
    from app.persistence.repositories.projects import ProjectRepository
    from tests.test_analysis_anchors import fixture
    from types import SimpleNamespace
    schedule=fixture();project=ProjectRepository(session).resolve_source(schedule.project)
    return ScheduleVersionRepository(session).create_importing(uuid4(),project.id,schedule,SimpleNamespace(original_filename='draft.xer',sha256=uuid4().hex*2),'Draft','UPDATE')


def test_native_unique_source_task_and_cross_version_fk(pg):
    with pytest.raises(IntegrityError) as e:
        with pg.sessions.begin() as s:
            v=draft(pg,s)
            s.add_all([orm.ActivityRecord(id=uuid4(),schedule_version_id=v.id,source_order=i,source_task_id='SAME',activity_code='duplicate-code') for i in (0,1)])
            s.flush()
    assert e.value.orig.sqlstate=='23505'
    v=pg.importer.import_bytes(rich_xer(),'base.xer',label='Base')
    with pytest.raises(IntegrityError) as e:
        with pg.sessions.begin() as s:
            other=draft(pg,s);w=s.scalar(select(orm.WBSRecord).where(orm.WBSRecord.schedule_version_id==v.id))
            s.add(orm.ActivityRecord(id=uuid4(),schedule_version_id=other.id,source_order=0,source_task_id='BAD',wbs_db_id=w.id))
    assert e.value.orig.sqlstate=='23503'


def test_non_task_udf_never_links_to_activity_and_jsonb_raw_survives(pg):
    v=pg.importer.import_bytes(rich_xer(),'rich.xer',label='Rich')
    with pg.sessions() as s:
        value=s.scalar(select(orm.UDFValueRecord).where(orm.UDFValueRecord.subject_table=='PROJECT'))
        assert value.foreign_object_id=='0' and value.activity_db_id is None
        assert isinstance(value.raw,dict) and value.raw['udf_text']=='Project only'
        option=s.scalar(select(orm.SchedulingOptionsRecord));assert option.retained_logic is True and option.progress_override is False
        assert ['sched_retained_logic','Y'] in option.raw_fields
        diagnostic=s.scalar(select(orm.DiagnosticRecord));assert diagnostic.details['row_number'] is not None


def test_sealing_incomplete_version_fails(pg):
    with pytest.raises(IntegrityError) as e:
        with pg.sessions.begin() as s:v=draft(pg,s);v.import_status='SUCCEEDED';s.flush()
    assert e.value.orig.sqlstate=='23514'


def test_migration_downgrade_and_upgrade_from_empty(pg):
    pg.importer.import_bytes(rich_xer(),'data.xer',label='Data')
    pg.migration('downgrade','base')
    with pg.engine.connect() as c:assert set(inspect(c).get_table_names())<={'alembic_version'}
    pg.migration('upgrade','head')
    with pg.engine.connect() as c:assert 'activities' in inspect(c).get_table_names()


@pytest.mark.parametrize('committed',[False,True])
def test_commit_acknowledgement_failure_preserves_only_referenced_file(pg,committed):
    from sqlalchemy.orm import Session,sessionmaker
    class LostAcknowledgement(Session):
        def commit(self):
            if committed:super().commit()
            raise RuntimeError('Synthetic acknowledgement failure')
    factory=sessionmaker(pg.engine,class_=LostAcknowledgement,expire_on_commit=False)
    importer=PersistedScheduleImportService(factory,pg.storage)
    if committed:
        with pytest.raises(CommitOutcomeUnknown) as exc:importer.import_bytes(rich_xer(),'ack.xer',label='Acknowledgement')
        _,schedule=pg.catalog.load_version(exc.value.version_id)
        assert len(schedule.activities)==7
    else:
        with pytest.raises(RuntimeError):importer.import_bytes(rich_xer(),'ack.xer',label='Acknowledgement')
    with pg.sessions() as s:assert s.scalar(select(func.count()).select_from(orm.ScheduleVersionRecord))==int(committed)
    assert len(list(pg.storage.root.rglob('*.xer')))==int(committed)


def test_project_rename_does_not_change_imported_snapshot(pg):
    v=pg.importer.import_bytes(rich_xer(),'snapshot.xer',label='Snapshot')
    _,before=pg.catalog.load_version(v.id)
    with pg.sessions.begin() as s:s.get(orm.ProjectRecord,v.project_id).project_name='Renamed catalogue project'
    _,after=pg.catalog.load_version(v.id)
    assert before==after and after.project.project_name!='Renamed catalogue project'


def test_migration_has_no_metadata_drift(pg):
    from alembic.config import Config
    from tests.conftest_postgres import ROOT
    config=Config(str(ROOT/'alembic.ini'))
    with pg.engine.begin() as connection:
        config.attributes['connection']=connection
        command.check(config)



def test_populated_optional_activity_dates_constraints_and_wbs_hierarchy(pg,tmp_path):
    from tests.persistence_helpers import detailed_xer
    data=detailed_xer();path=tmp_path/'detailed.xer';path.write_bytes(data)
    imported=ScheduleImportService().import_file(path);assert imported.succeeded
    version=pg.importer.import_bytes(data,'detailed.xer',label='All imported fields')
    _,loaded=pg.catalog.load_version(version.id)
    assert loaded==imported.schedule
    a=loaded.activities['0']
    for field in ('planned_start','planned_finish','actual_start','actual_finish','expected_finish','remaining_start','remaining_finish',
        'duration_type','suspend_date','resume_date','primary_constraint_type','primary_constraint_date','secondary_constraint_type','secondary_constraint_date'):
        assert getattr(a,field) is not None,field
    assert a.percent_complete==37.5
    with pg.sessions() as s:
        child=s.scalar(select(orm.WBSRecord).where(orm.WBSRecord.source_wbs_id=='W2'))
        parent=s.get(orm.WBSRecord,child.parent_db_id)
        assert parent.source_wbs_id=='W1' and child.stable_path=='W1 > CHILD'


def test_controlled_baseline_current_comparison_and_reporting_after_reload(pg):
    from tests.conftest_postgres import ROOT
    from app.persistence.services.analyses import StoredAnalysisService
    from tests.test_reporting import activity_row
    versions=[pg.importer.import_bytes((ROOT/f'sample_data/sample_{kind}.xer').read_bytes(),f'{kind}.xer',label=kind,version_type=kind.upper()) for kind in ('baseline','current')]
    service=StoredAnalysisService(pg.catalog)
    report=service.forensic(*(v.id for v in versions))
    assert activity_row(report,'activities','A1500').classification=='REMOVED'
    assert activity_row(report,'activities','A1700').classification=='ADDED'
    assert activity_row(report,'description','A1200').cells['current_value']=='Revised build'
    assert report.metadata.completion_authority_status=='NOT_ESTABLISHED'
    assert report.metadata.selected_analysis_anchor is None
