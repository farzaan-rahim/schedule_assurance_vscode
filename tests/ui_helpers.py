from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timezone
from types import SimpleNamespace
from uuid import uuid4
from app.persistence.services.imports import ProjectInfo,ScheduleVersionInfo
from app.persistence.services.analyses import StoredAnalysisService
from app.ui.service import PlannerService
from tests.test_analysis_anchors import fixture

class MemoryCatalog:
    sessions=None
    def __init__(self):
        now=datetime(2026,1,5,tzinfo=timezone.utc);p=uuid4()
        self.project=ProjectInfo(p,'P1','Controlled UI Project',None,True,now,now)
        self.projects=[self.project];self.versions=[];self.schedules={}
        for kind in ('BASELINE','CURRENT'):
            v=ScheduleVersionInfo(uuid4(),p,kind.title(),kind,'controlled.xer',uuid4().hex*2,'P1','P1','Controlled UI',datetime(2026,1,5,8),now,'SUCCEEDED',6,5,1,1,0,0)
            s=fixture();s.activities.pop('X');s.rebuild_activity_indexes()
            s.activities['5'].primary_constraint_type='FINISH_ON_OR_BEFORE';s.activities['5'].primary_constraint_date=datetime(2026,1,5,14)
            self.versions.append(v);self.schedules[v.id]=s
    def get_project(self,key):return next(p for p in self.projects if p.id==key)
    def find_project_by_code(self,code):return next((p for p in self.projects if p.project_code==code),None)
    def get_version(self,key):return next(v for v in self.versions if v.id==key)
    def load_version(self,key):return self.get_version(key),deepcopy(self.schedules[key])
    def diagnostics(self,key):return ()
    def create_project(self,code,name,description=None):
        from app.persistence.exceptions import ImportRejected
        if self.find_project_by_code(code):raise ImportRejected('Project code already exists.')
        if not code.strip() or not name.strip():raise ImportRejected('Project code and name are required.')
        p=replace(self.project,id=uuid4(),project_code=code,project_name=name,description=description)
        self.projects.append(p);return p

class MemoryNavigation:
    def __init__(self,catalog):self.catalog=catalog
    def projects(self,offset=0,limit=50,search='',*,sort='',descending=False):
        rows=[p for p in self.catalog.projects if not search or search.casefold() in (p.project_code+' '+p.project_name).casefold()]
        return tuple(rows[offset:offset+limit]),len(rows)
    def versions(self,key,offset=0,limit=50,*,sort='',descending=False):
        rows=[v for v in reversed(self.catalog.versions) if v.project_id==key];return tuple(rows[offset:offset+limit]),len(rows)

def memory_service():
    catalog=MemoryCatalog()
    services=SimpleNamespace(catalog=catalog,analyses=StoredAnalysisService(catalog),maximum_upload_bytes=104857600)
    def import_bytes(content,filename,**kwargs):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from app.services.schedule_import import ScheduleImportService
        from app.persistence.exceptions import ImportRejected
        from app.persistence.services.storage import LocalSourceStorage
        LocalSourceStorage('.').validate(content,filename)
        with TemporaryDirectory() as d:
            p=Path(d)/'input.xer';p.write_bytes(content);result=ScheduleImportService().import_file(p,**({"source_project_id":kwargs["source_project_id"]} if kwargs.get("source_project_id") is not None else {}))
        if not result.succeeded:raise ImportRejected('Import failed',result.diagnostics)
        if result.schedule.project.project_code!=catalog.get_project(kwargs['project_id']).project_code:raise ImportRejected('Source project code does not match the selected project.')
        v=replace(catalog.versions[-1],id=uuid4(),project_id=kwargs['project_id'],label=kwargs['label'],source_filename=filename,version_type=kwargs['version_type'],activity_count=len(result.schedule.activities),relationship_count=len(result.schedule.relationships))
        catalog.versions.append(v);catalog.schedules[v.id]=result.schedule
        return v
    services.importer=SimpleNamespace(import_bytes=import_bytes)
    service=PlannerService(services);service.navigation=MemoryNavigation(catalog)
    return service
