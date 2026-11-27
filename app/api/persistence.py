"""Persistence routes contain validation/orchestration only, never SQL."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,File,Form,HTTPException,Query,UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.persistence.exceptions import (PersistenceError,PersistenceNotConfigured,ImportRejected,RecordNotFound,
    UnsafeStoragePath,DuplicateScheduleVersion,CommitOutcomeUnknown)
from app.persistence.session import session_factory
from app.persistence.settings import PersistenceSettings
from app.persistence.services.storage import LocalSourceStorage
from app.persistence.services.imports import PersistedScheduleImportService,PersistenceCatalogService
from app.persistence.services.analyses import StoredAnalysisService
from app.cpm.analysis_anchors import AnalysisAnchorConfig,AnchorSelectionError
from app.cpm.analysis_serialization import analysis_payload
from app.reporting.serialization import to_json_value,serialize_report
from app.reporting.excel_renderer import FILENAME,MEDIA_TYPE

router=APIRouter(tags=['Stored schedules'])


@dataclass
class PersistenceServices:
    catalog: object
    importer: object
    analyses: object
    maximum_upload_bytes: int


def get_persistence_services():
    try:
        settings=PersistenceSettings();sessions=session_factory(settings)
        storage=LocalSourceStorage(settings.storage_root,settings.maximum_upload_bytes)
        catalog=PersistenceCatalogService(sessions)
        return PersistenceServices(catalog,PersistedScheduleImportService(sessions,storage),StoredAnalysisService(catalog),settings.maximum_upload_bytes)
    except (PersistenceNotConfigured,ValidationError,ValueError) as exc:
        raise HTTPException(503,'Persistence is not configured; supply a PostgreSQL SA_DATABASE_URL.') from exc


async def invoke(method,*args,**kwargs):
    try:return await run_in_threadpool(method,*args,**kwargs)
    except RecordNotFound as exc:raise HTTPException(404,str(exc)) from exc
    except DuplicateScheduleVersion as exc:
        raise HTTPException(409,detail={'code':'duplicate_source_sha256','message':str(exc),'project_id':str(exc.project_id),'existing_version_id':str(exc.version_id)}) from exc
    except CommitOutcomeUnknown as exc:
        raise HTTPException(503,detail={'code':'commit_outcome_unknown','message':str(exc),'version_id':str(exc.version_id)}) from exc
    except AnchorSelectionError as exc:
        raise HTTPException(422,detail={'code':exc.code,'message':str(exc),'details':exc.details}) from exc
    except (ImportRejected,UnsafeStoragePath) as exc:
        raise HTTPException(422,str(exc)) from exc
    except (SQLAlchemyError,PersistenceError,OSError) as exc:
        raise HTTPException(503,'Persistence operation failed; no analytical result was stored.') from exc


class ProjectCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    project_code: str=Field(min_length=1,max_length=512)
    project_name: str=Field(min_length=1,max_length=2048)
    description: str | None=None
    active: bool=True


class VersionPair(BaseModel):
    model_config=ConfigDict(extra='forbid')
    baseline_version_id: UUID
    current_version_id: UUID


class AnchorRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    activity_code: str | None=None
    internal_id: str | None=None
    mode: Literal['CALIBRATION','INDEPENDENT']='CALIBRATION'
    required_finish: datetime | None=None
    selected_by: str | None=None

    def selection(self):
        return AnalysisAnchorConfig(analysis_anchor_activity_code=self.activity_code,analysis_anchor_internal_id=self.internal_id,
            mode=self.mode,required_finish=self.required_finish,selected_by=self.selected_by)


class StoredReportRequest(VersionPair):
    analysis_anchor: AnchorRequest | None=None
    generated_by: str | None=None


@router.post('/api/projects',status_code=201)
async def create_project(body:ProjectCreate,services:PersistenceServices=Depends(get_persistence_services)):
    return jsonable_encoder(await invoke(services.catalog.create_project,body.project_code,body.project_name,body.description,body.active))


@router.get('/api/projects')
async def list_projects(offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=1000),services:PersistenceServices=Depends(get_persistence_services)):
    return jsonable_encoder(await invoke(services.catalog.list_projects,offset,limit))


@router.get('/api/projects/{project_id}')
async def get_project(project_id:UUID,services:PersistenceServices=Depends(get_persistence_services)):
    return jsonable_encoder(await invoke(services.catalog.get_project,project_id))


@router.post('/api/projects/{project_id}/schedule-versions',status_code=201)
async def import_version(project_id:UUID,file:UploadFile=File(...),label:str=Form(...),
        version_type:Literal['BASELINE','UPDATE','CURRENT','SNAPSHOT']=Form('UPDATE'),source_project_id:str | None=Form(None),services:PersistenceServices=Depends(get_persistence_services)):
    if not (file.filename or '').lower().endswith('.xer'):raise HTTPException(415,'Upload a .xer source file.')
    content=bytearray()
    while chunk:=await file.read(1024*1024):
        if len(content)+len(chunk)>services.maximum_upload_bytes:raise HTTPException(413,'Upload exceeds the configured size limit.')
        content.extend(chunk)
    result=await invoke(services.importer.import_bytes,bytes(content),file.filename,label=label,version_type=version_type,project_id=project_id,**({"source_project_id":source_project_id} if source_project_id is not None else {}))
    return jsonable_encoder(result)


@router.get('/api/projects/{project_id}/schedule-versions')
async def list_versions(project_id:UUID,offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=1000),services:PersistenceServices=Depends(get_persistence_services)):
    return jsonable_encoder(await invoke(services.catalog.list_versions,project_id,offset,limit))


@router.get('/api/schedule-versions/{version_id}')
async def get_version(version_id:UUID,services:PersistenceServices=Depends(get_persistence_services)):
    return jsonable_encoder(await invoke(services.catalog.get_version,version_id))


@router.get('/api/schedule-versions/{version_id}/health')
async def stored_health(version_id:UUID,services:PersistenceServices=Depends(get_persistence_services)):
    result=await invoke(services.analyses.health,version_id)
    return {'stored_version_id':str(version_id),'health':result.to_dict()}


@router.get('/api/schedule-versions/{version_id}/dcma')
async def stored_dcma(version_id:UUID,services:PersistenceServices=Depends(get_persistence_services)):
    return {'stored_version_id':str(version_id),'dcma':to_json_value(await invoke(services.analyses.dcma,version_id))}


@router.post('/api/schedule-versions/compare')
async def stored_compare(body:VersionPair,offset:int=Query(0,ge=0),limit:int=Query(1000,ge=1,le=5000),services:PersistenceServices=Depends(get_persistence_services)):
    result=await invoke(services.analyses.compare,body.baseline_version_id,body.current_version_id)
    return dict(baseline_version_id=str(body.baseline_version_id),current_version_id=str(body.current_version_id),summary=to_json_value(result.summary),
        activity_variances=to_json_value(result.activity_variances[offset:offset+limit]),relationship_variances=to_json_value(result.relationship_variances[offset:offset+limit]),
        diagnostics=to_json_value(result.diagnostics),pagination=dict(offset=offset,limit=limit,total_activities=len(result.activity_variances),total_relationships=len(result.relationship_variances)))


@router.post('/api/schedule-versions/compare-milestones')
async def stored_milestones(body:VersionPair,services:PersistenceServices=Depends(get_persistence_services)):
    result=await invoke(services.analyses.milestones,body.baseline_version_id,body.current_version_id)
    return to_json_value(dict(summary=result.summary,milestones=result.milestones,comparisons=result.comparisons,findings=result.findings,
        candidate_drivers=result.candidate_drivers,truncation=result.truncation))


@router.post('/api/schedule-versions/{version_id}/analyze-anchor')
async def stored_anchor(version_id:UUID,body:AnchorRequest,services:PersistenceServices=Depends(get_persistence_services)):
    result=await invoke(services.analyses.analyze_anchor,version_id,body.selection())
    return analysis_payload(result)


@router.post('/api/reports/forensic-change/stored/preview')
async def stored_report_preview(body:StoredReportRequest,offset:int=Query(0,ge=0),limit:int=Query(500,ge=1,le=5000),services:PersistenceServices=Depends(get_persistence_services)):
    report=await invoke(services.analyses.forensic,body.baseline_version_id,body.current_version_id,
        analysis_selection=body.analysis_anchor.selection() if body.analysis_anchor else None,generated_by=body.generated_by)
    return serialize_report(report,offset=offset,limit=limit)


@router.post('/api/reports/forensic-change/stored/excel')
async def stored_report_excel(body:StoredReportRequest,services:PersistenceServices=Depends(get_persistence_services)):
    report=await invoke(services.analyses.forensic,body.baseline_version_id,body.current_version_id,
        analysis_selection=body.analysis_anchor.selection() if body.analysis_anchor else None,generated_by=body.generated_by)
    content=await invoke(services.analyses.excel,report)
    return Response(content,media_type=MEDIA_TYPE,headers={'Content-Disposition':f'attachment; filename="{FILENAME}"'})
