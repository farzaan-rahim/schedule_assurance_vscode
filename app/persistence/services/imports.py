from dataclasses import dataclass,fields
from datetime import datetime,timezone
from uuid import UUID,uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError,DBAPIError
from app.persistence.models.schema import ProjectRecord,ScheduleVersionRecord,SourceFileRecord
from app.persistence.repositories.projects import ProjectRepository
from app.persistence.repositories.versions import ScheduleVersionRepository
from app.persistence.repositories.schedule_data import ScheduleDataRepository
from app.persistence.exceptions import (PersistenceError,ImportRejected,RecordNotFound,DuplicateScheduleVersion,CommitOutcomeUnknown)
from app.services.schedule_import import ScheduleImportService


@dataclass(frozen=True)
class ProjectInfo:
    id: UUID
    project_code: str
    project_name: str
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ScheduleVersionInfo:
    id: UUID
    project_id: UUID
    label: str
    version_type: str
    source_filename: str
    source_sha256: str
    source_project_id: str
    source_project_code: str
    source_project_name: str
    data_date: datetime | None
    imported_at: datetime
    import_status: str
    activity_count: int
    relationship_count: int
    wbs_count: int
    calendar_count: int
    resource_count: int
    resource_assignment_count: int


def dto(cls,row):
    values={f.name:getattr(row,f.name) for f in fields(cls)}
    for key in ('created_at','updated_at','imported_at'):
        if key in values and values[key] is not None:values[key]=values[key].astimezone(timezone.utc)
    return cls(**values)


class PersistedScheduleImportService:
    def __init__(self,session_factory,storage,importer=None):
        self.sessions=session_factory;self.storage=storage;self.importer=importer or ScheduleImportService()

    def import_bytes(self,content,filename,*,label,version_type='UPDATE',project_id=None,source_project_id=None):
        if not label or not label.strip():raise ImportRejected('A schedule version label is required.')
        if version_type not in {'BASELINE','UPDATE','CURRENT','SNAPSHOT'}:raise ImportRejected('Unknown schedule version type.')
        version_id=uuid4();source=self.storage.store(content,filename,version_id)
        commit_attempted=False;resolved_project_id=project_id
        try:
            import_options={'source_project_id':source_project_id} if source_project_id is not None else {}
            imported=self.importer.import_file(self.storage.resolve(source.relative_path),**import_options)
            if not imported.succeeded or imported.schedule is None or imported.schedule.project is None:
                raise ImportRejected('XER import failed; no version was committed.',tuple(imported.diagnostics))
            schedule=imported.schedule
            if not schedule.project.project_code:raise ImportRejected('A source project code is required to resolve project identity.')
            with self.sessions() as session:
                try:
                    projects=ProjectRepository(session)
                    project=projects.get(project_id) if project_id is not None else projects.resolve_source(schedule.project)
                    resolved_project_id=project.id
                    if project.project_code!=schedule.project.project_code:
                        raise ImportRejected('Source project code does not match the selected project.')
                    versions=ScheduleVersionRepository(session)
                    duplicate=versions.duplicate(project.id,source.sha256)
                    if duplicate:raise DuplicateScheduleVersion(project.id,duplicate.id)
                    version=versions.create_importing(version_id,project.id,schedule,source,label,version_type)
                    versions.add_source(source)
                    data=ScheduleDataRepository(session);data.persist(version.id,schedule);data.persist_diagnostics(version.id,imported.diagnostics)
                    versions.seal(version)
                    result=dto(ScheduleVersionInfo,version)
                    commit_attempted=True;session.commit()
                    return result
                except BaseException:
                    session.rollback();raise
        except BaseException as exc:
            # A failed acknowledgement does not prove the server failed to commit.
            if commit_attempted:
                try:
                    with self.sessions() as check:
                        referenced=check.get(SourceFileRecord,source.id) is not None
                except Exception:
                    raise CommitOutcomeUnknown(version_id) from exc
                if referenced:raise CommitOutcomeUnknown(version_id) from exc
            self.storage.remove(source)
            if isinstance(exc,IntegrityError) and getattr(getattr(exc.orig,'diag',None),'constraint_name',None)=='uq_versions_project_sha256':
                with self.sessions() as check:
                    duplicate=ScheduleVersionRepository(check).duplicate(resolved_project_id,source.sha256)
                    if duplicate:raise DuplicateScheduleVersion(resolved_project_id,duplicate.id) from exc
            raise


class PersistenceCatalogService:
    def __init__(self,session_factory):self.sessions=session_factory

    def create_project(self,code,name,description=None,active=True):
        if not code.strip() or not name.strip():raise ImportRejected('Project code and name are required.')
        try:
            with self.sessions.begin() as session:
                row=ProjectRepository(session).create(code,name,description,active)
                result=dto(ProjectInfo,row)
            return result
        except IntegrityError as exc:raise ImportRejected('Project code already exists.') from exc

    def find_project_by_code(self,code):
        with self.sessions() as session:
            row=ProjectRepository(session).by_code(code)
            return dto(ProjectInfo,row) if row is not None else None

    def list_projects(self,offset=0,limit=100):
        with self.sessions() as s:return tuple(dto(ProjectInfo,r) for r in ProjectRepository(s).list(offset,limit))

    def get_project(self,key):
        with self.sessions() as s:return dto(ProjectInfo,ProjectRepository(s).get(key))

    def list_versions(self,project_id,offset=0,limit=100):
        with self.sessions() as s:
            ProjectRepository(s).get(project_id)
            return tuple(dto(ScheduleVersionInfo,r) for r in ScheduleVersionRepository(s).list(project_id,offset,limit))

    def get_version(self,key):
        with self.sessions() as s:return dto(ScheduleVersionInfo,ScheduleVersionRepository(s).get(key))

    def load_version(self,key):
        with self.sessions() as s:
            row=ScheduleVersionRepository(s).get(key)
            return dto(ScheduleVersionInfo,row),ScheduleDataRepository(s).load(row)

    def diagnostics(self,key):
        with self.sessions() as s:
            ScheduleVersionRepository(s).get(key)
            return ScheduleDataRepository(s).load_diagnostics(key)
