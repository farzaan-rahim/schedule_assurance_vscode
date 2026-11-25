"""Narrow read-only source evidence and ephemeral XER orchestration."""
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from app.importers.xer_parser import XERParser
from app.services.schedule_import import ScheduleImportService
from app.cpm.analysis_anchors import AnchorSelectionError
from app.cpm.selected_analysis import SelectedAnchorService


@dataclass(frozen=True)
class CriticalDefinitionEvidence:
    project_id: str
    raw_path_type: str | None
    raw_threshold_hours: str | None
    source: str = 'XER_PROJECT_FIELDS'

    @property
    def total_float_threshold_hours(self):
        if self.raw_path_type!='CT_TotFloat':return None
        try:
            value=float(self.raw_threshold_hours)
            return value if isfinite(value) else None
        except (ValueError,TypeError):return None


class _EvidenceParser(XERParser):
    def parse(self,path):
        rows=super().parse(path)
        self.project_evidence=tuple((r.get('proj_id'),r.get('critical_path_type'),r.get('critical_drtn_hr_cnt')) for r in rows.get('PROJECT',()))
        return rows


def import_analysis_file(path):
    parser=_EvidenceParser()
    result=ScheduleImportService(parser=parser).import_file(Path(path))
    if not result.succeeded or result.schedule is None or result.graph is None:
        raise AnchorSelectionError('analysis_import_failed','XER import failed.',diagnostics=tuple(d.message for d in result.diagnostics))
    rows=[r for r in parser.project_evidence if r[0]==result.schedule.project.project_id]
    evidence=CriticalDefinitionEvidence(*rows[0]) if len(rows)==1 else None
    return result,evidence


class AnalysisXERService:
    def __init__(self,maximum_upload_bytes=100*1024*1024):
        self.maximum_upload_bytes=maximum_upload_bytes

    def _import(self,content,filename):
        if not filename.lower().endswith('.xer'):
            raise AnchorSelectionError('unsupported_analysis_file','Upload a .xer file.')
        if len(content)>self.maximum_upload_bytes:
            raise AnchorSelectionError('analysis_upload_too_large','XER exceeds the upload limit.')
        with TemporaryDirectory(prefix='schedule-assurance-anchor-') as folder:
            path=Path(folder)/'schedule.xer';path.write_bytes(content)
            return import_analysis_file(path)

    def candidates(self,content,filename):
        from app.cpm.analysis_anchors import analysis_anchor_catalog
        result,evidence=self._import(content,filename)
        catalog=analysis_anchor_catalog(result.schedule,result.graph)
        catalog['p6_critical_definition_evidence']=evidence
        return catalog

    def analyze(self,content,filename,selection):
        result,evidence=self._import(content,filename)
        return SelectedAnchorService().analyze(result.schedule,result.graph,selection,critical_definition=evidence)
