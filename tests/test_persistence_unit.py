from copy import deepcopy
from dataclasses import fields,replace
from datetime import date,datetime,time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from pydantic import ValidationError
from app.persistence.base import Base
from app.persistence.models import schema as orm
from app.persistence.mappers.codec import encode_raw,decode_raw,calendar_values,calendar_from_record
from app.persistence.mappers.schedule import dump_schedule,load_schedule
from app.persistence.services.storage import LocalSourceStorage
from app.persistence.settings import PersistenceSettings
from app.persistence.exceptions import ImportRejected,UnsafeStoragePath,PersistenceError
from app.services.schedule_import import ScheduleImportService
from app.calendars.models import CalendarException,WorkPeriod
from tests.persistence_helpers import rich_xer


def test_full_mapper_round_trip_without_orm_leaking_into_domain(tmp_path):
    p=tmp_path/'rich.xer';p.write_bytes(rich_xer());original=ScheduleImportService().import_file(p).schedule
    snapshot=deepcopy(original);rows=dump_schedule(original,uuid4())
    records={model:[model(**row) for row in data] for model,data in rows.items()}
    project=original.project
    version=SimpleNamespace(source_project_id=project.project_id,source_project_code=project.project_code,source_project_name=project.project_name,
        data_date=project.data_date,source_planned_start=project.planned_start,source_planned_finished=project.planned_finished)
    loaded=load_schedule(version,records)
    assert loaded==original==snapshot
    assert type(loaded.activities['0']).__module__=='app.models.schedule'
    assert loaded.get_resource_assignments('0')
    assert all(v.subject_table=='TASK' for v in loaded.get_activity_udf_values('0'))


@pytest.mark.parametrize('value',[None,False,0,-0.0,1.25,float('inf'),'raw',datetime(2026,1,1,0,0,0,123456),date(2026,1,1),time(22,0),{'t':'datetime','v':'not a date'},(1,None,['a']),{1:'integer key'}])
def test_raw_diagnostic_codec(value):
    assert decode_raw(encode_raw(value))==value


@pytest.mark.parametrize('name',['../bad.xer','C:\\work\\bad.xer','/tmp/bad.xer','nested/bad.xer','bad\x00.xer'])
def test_storage_rejects_workstation_or_traversal_names(tmp_path,name):
    with pytest.raises(UnsafeStoragePath):LocalSourceStorage(tmp_path).store(b'XER',name,uuid4())


def test_storage_generated_identity_and_safe_cleanup(tmp_path):
    storage=LocalSourceStorage(tmp_path);v=uuid4();source=storage.store(b'canonical bytes','original.xer',v)
    assert source.original_filename=='original.xer' and source.storage_filename!='original.xer'
    assert not Path(source.relative_path).is_absolute() and '\\' not in source.relative_path
    assert storage.resolve(source.relative_path).read_bytes()==b'canonical bytes'
    storage.remove(source);assert not list(tmp_path.rglob('*.xer'))
    with pytest.raises(UnsafeStoragePath):storage.resolve('../outside.xer')
    with pytest.raises(ImportRejected):LocalSourceStorage(tmp_path,maximum_bytes=1).store(b'ab','a.xer',uuid4())
    with pytest.raises(ImportRejected):storage.store(b'','a.xer',uuid4())


def test_storage_symlink_escape_is_refused(tmp_path):
    storage=LocalSourceStorage(tmp_path/'root');storage.root.mkdir();outside=tmp_path/'outside';outside.mkdir()
    link=storage.root/'link'
    try:link.symlink_to(outside,target_is_directory=True)
    except OSError:
        import os,subprocess
        if os.name!='nt':raise
        def quoted(path):return "'"+str(path).replace("'","''")+"'"
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
            'New-Item -ItemType Junction -Path '+quoted(link)+' -Target '+quoted(outside)],
            check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with pytest.raises(UnsafeStoragePath):storage.resolve('link/attack.xer')


def test_calendar_exception_overnight_and_fractional_times_are_lossless():
    from tests.test_cpm import make_calendar
    calendar=make_calendar(exceptions=(CalendarException(date(2026,1,10),True,(WorkPeriod(time(22,0,0,123456),time(4)),)),))
    data=calendar_values(calendar)
    record=SimpleNamespace(**data)
    values={f.name:getattr(calendar,f.name) for f in fields(calendar) if f.name not in {'weekly_pattern','exceptions','diagnostics'}}
    assert calendar_from_record(record,values)==calendar


def test_schema_compiles_for_postgresql_with_native_types_and_no_blobs():
    ddl='\n'.join(str(CreateTable(table).compile(dialect=postgresql.dialect())) for table in Base.metadata.sorted_tables)
    assert 'UUID' in ddl and 'JSONB' in ddl
    assert 'BLOB' not in ddl and 'BYTEA' not in ddl
    assert 'uq_activities_source_id' in ddl and 'uq_versions_project_sha256' in ddl
    assert any(i.name=='ix_activities_version_code' for i in orm.ActivityRecord.__table__.indexes)


def test_settings_are_postgres_only_and_credentials_are_redacted():
    settings=PersistenceSettings(database_url='postgresql+psycopg://u:example-password@localhost/db')
    assert 'example-password' not in repr(settings)
    with pytest.raises(ValidationError):PersistenceSettings(database_url='sqlite:///not-postgres.db')
    with pytest.raises(ValidationError):PersistenceSettings(maximum_upload_bytes=0)



def test_malformed_database_url_is_a_configuration_validation_error():
    with pytest.raises(ValidationError):PersistenceSettings(database_url='not-a-database-url',_env_file=None)
