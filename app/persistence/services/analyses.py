"""Reload canonical schedules, then delegate to existing analytical services."""
from app.comparison.engine import ScheduleComparisonEngine
from app.comparison.models import ScheduleVersion,ScheduleVersionType
from app.graph.schedule_graph import ScheduleGraph
from app.services.schedule_health import ScheduleHealthService
from app.dcma.service import DCMAAssessmentService
from app.milestones.service import MilestoneAnalysisService
from app.cpm.service import CPMService
from app.cpm.selected_analysis import SelectedAnchorService
from app.reporting.builder import ForensicReportBuilder
from app.reporting.excel_renderer import ExcelReportRenderer
from app.persistence.exceptions import ImportRejected


class StoredAnalysisService:
    def __init__(self,catalog):self.catalog=catalog

    def health(self,version_id):
        _,schedule=self.catalog.load_version(version_id)
        return ScheduleHealthService().analyze(schedule,ScheduleGraph(schedule))

    def dcma(self,version_id):
        info,schedule=self.catalog.load_version(version_id)
        return DCMAAssessmentService().analyze(schedule,ScheduleGraph(schedule),source_filename=info.source_filename)

    def cpm(self,version_id,config=None):
        _,schedule=self.catalog.load_version(version_id)
        return CPMService().calculate(schedule,ScheduleGraph(schedule),config)

    def analyze_anchor(self,version_id,selection):
        _,schedule=self.catalog.load_version(version_id)
        return SelectedAnchorService().analyze(schedule,ScheduleGraph(schedule),selection)

    def _pair(self,baseline_id,current_id):
        binfo,baseline=self.catalog.load_version(baseline_id)
        cinfo,current=(binfo,baseline) if baseline_id==current_id else self.catalog.load_version(current_id)
        if binfo.project_id!=cinfo.project_id:raise ImportRejected('Stored versions must belong to the same project.')
        def version(info,schedule,role):
            # Analysis role is independent of stored BASELINE/UPDATE/CURRENT/SNAPSHOT classification.
            return ScheduleVersion(str(info.id),info.label,role,info.source_filename,info.data_date,info.imported_at,schedule)
        comparison=ScheduleComparisonEngine().compare(version(binfo,baseline,ScheduleVersionType.BASELINE),version(cinfo,current,ScheduleVersionType.CURRENT))
        return baseline,current,comparison

    def compare(self,baseline_id,current_id):return self._pair(baseline_id,current_id)[2]

    def milestones(self,baseline_id,current_id):
        baseline,current,comparison=self._pair(baseline_id,current_id)
        return MilestoneAnalysisService().compare(baseline,current,comparison,ScheduleGraph(baseline),ScheduleGraph(current))

    def forensic(self,baseline_id,current_id,*,analysis_selection=None,generated_by=None):
        baseline,current,comparison=self._pair(baseline_id,current_id)
        analysis=SelectedAnchorService().analyze(current,ScheduleGraph(current),analysis_selection) if analysis_selection else None
        return ForensicReportBuilder().build(comparison,analysis_result=analysis,generated_by=generated_by)

    def excel(self,report):return ExcelReportRenderer().render(report)
