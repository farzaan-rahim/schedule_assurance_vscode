"""Upload/response orchestration only; report services own all domain work."""
from datetime import datetime
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.reporting.excel_renderer import FILENAME, MEDIA_TYPE
from app.cpm.analysis_anchors import AnalysisAnchorConfig, AnchorSelectionError
from app.reporting.limits import ReportLimitError
from app.reporting.serialization import serialize_report
from app.reporting.service import ForensicReportingService, ReportInputError

router=APIRouter(prefix='/api/reports/forensic-change',tags=['Reports'])


async def _build(baseline, current, generated_by, analysis_selection=None):
    service=ForensicReportingService()
    data=[]
    for label,upload in (('baseline',baseline),('current',current)):
        if not (upload.filename or '').lower().endswith('.xer'):
            raise HTTPException(415,f'Unsupported {label} file type; upload a .xer file.')
        content=bytearray()
        while chunk:=await upload.read(1024*1024):
            if len(content)+len(chunk)>service.limits.maximum_upload_bytes:
                raise HTTPException(413,f'{label.title()} upload exceeds the configured size limit.')
            content.extend(chunk)
        data.append(bytes(content))
    try:
        report=await run_in_threadpool(service.from_bytes,*data,baseline.filename,current.filename,generated_by=generated_by,analysis_selection=analysis_selection)
        return service,report
    except ReportLimitError as exc:
        raise HTTPException(413,str(exc)) from exc
    except AnchorSelectionError as exc:
        raise HTTPException(422,detail={'code':exc.code,'message':str(exc),'details':exc.details}) from exc
    except ReportInputError as exc:
        raise HTTPException(422,str(exc)) from exc


def _analysis_selection(code,key,mode,finish,selected_by):
    if code is None and key is None and finish is None and mode=='CALIBRATION':return None
    return AnalysisAnchorConfig(analysis_anchor_activity_code=code,analysis_anchor_internal_id=key,
        mode=mode,required_finish=finish,selected_by=selected_by)


@router.post('/preview')
async def forensic_preview(baseline: UploadFile=File(...),current: UploadFile=File(...),
        generated_by: str | None=Form(None),analysis_anchor_activity_code: str | None=Form(None),
        analysis_anchor_internal_id: str | None=Form(None),analysis_mode: str=Form('CALIBRATION'),
        analysis_required_finish: datetime | None=Form(None),offset: int=Query(0,ge=0),limit: int=Query(500,ge=1,le=5000)):
    selection=_analysis_selection(analysis_anchor_activity_code,analysis_anchor_internal_id,analysis_mode,analysis_required_finish,generated_by)
    _,report=await _build(baseline,current,generated_by,selection)
    return serialize_report(report,offset=offset,limit=limit)


@router.post('/excel')
async def forensic_excel(baseline: UploadFile=File(...),current: UploadFile=File(...),generated_by: str | None=Form(None),
        analysis_anchor_activity_code: str | None=Form(None),analysis_anchor_internal_id: str | None=Form(None),
        analysis_mode: str=Form('CALIBRATION'),analysis_required_finish: datetime | None=Form(None)):
    selection=_analysis_selection(analysis_anchor_activity_code,analysis_anchor_internal_id,analysis_mode,analysis_required_finish,generated_by)
    service,report=await _build(baseline,current,generated_by,selection)
    try:
        content=await run_in_threadpool(service.excel,report)
    except ReportLimitError as exc:
        raise HTTPException(413,str(exc)) from exc
    return Response(content=content,media_type=MEDIA_TYPE,
        headers={'Content-Disposition':f'attachment; filename="{FILENAME}"'})
