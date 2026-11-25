from datetime import datetime
from typing import Literal
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.cpm.analysis_anchors import AnalysisAnchorConfig, AnchorSelectionError
from app.cpm.analysis_io import AnalysisXERService
from app.cpm.analysis_serialization import analysis_payload
from app.reporting.serialization import to_json_value

router=APIRouter(prefix='/api/schedules/cpm',tags=['Selected CPM analysis'])


async def _source(file,service):
    if not (file.filename or '').lower().endswith('.xer'):
        raise HTTPException(415,'Upload a .xer file.')
    content=bytearray()
    while chunk:=await file.read(1024*1024):
        if len(content)+len(chunk)>service.maximum_upload_bytes:raise HTTPException(413,'XER exceeds the upload limit.')
        content.extend(chunk)
    return bytes(content)


def _selection_error(exc):
    return HTTPException(422,detail={'code':exc.code,'message':str(exc),'details':exc.details})


@router.post('/analysis-anchors')
async def analysis_anchors(file: UploadFile=File(...),offset: int=Query(0,ge=0),limit: int=Query(500,ge=1,le=5000)):
    service=AnalysisXERService();content=await _source(file,service)
    try:catalog=await run_in_threadpool(service.candidates,content,file.filename)
    except AnchorSelectionError as exc:raise _selection_error(exc) from exc
    total=catalog['count'];catalog['candidates']=catalog['candidates'][offset:offset+limit]
    catalog['pagination']=dict(offset=offset,limit=limit,returned=len(catalog['candidates']),total=total)
    catalog['has_more']=offset+len(catalog['candidates'])<total
    return to_json_value(catalog)


@router.post('/analyze-anchor')
async def analyze_anchor(file: UploadFile=File(...),activity_code: str | None=Form(None),internal_id: str | None=Form(None),
        mode: Literal['CALIBRATION','INDEPENDENT']=Form('CALIBRATION'),required_finish: datetime | None=Form(None),
        selected_by: str | None=Form(None),selection_reason: str=Form('Explicit caller-selected endpoint for analysis, not contractual completion.')):
    service=AnalysisXERService();content=await _source(file,service)
    selection=AnalysisAnchorConfig(activity_code,internal_id,mode=mode,required_finish=required_finish,selected_by=selected_by,selection_reason=selection_reason)
    try:analysis=await run_in_threadpool(service.analyze,content,file.filename,selection)
    except AnchorSelectionError as exc:raise _selection_error(exc) from exc
    return analysis_payload(analysis)
