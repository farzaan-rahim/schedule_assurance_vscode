from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from app.comparison.engine import ScheduleComparisonEngine
from app.comparison.models import ScheduleVersion, ScheduleVersionType
from app.services.schedule_import import ScheduleImportService
from app.reporting.builder import ForensicReportBuilder
from app.reporting.excel_renderer import ExcelReportRenderer
from app.reporting.limits import ReportLimits, ReportLimitError


class ReportInputError(ValueError):
    pass


class ForensicReportingService:
    def __init__(self, limits=None):
        self.limits=limits or ReportLimits()
        self.builder=ForensicReportBuilder(self.limits)

    def from_comparison(self, comparison, **kwargs):
        return self.builder.build(comparison,**kwargs)

    def from_files(self, baseline_path, current_path, *, baseline_filename=None, current_filename=None, generated_by=None, analysis_selection=None):
        critical_definition=None
        if analysis_selection is None:
            imports=[ScheduleImportService().import_file(Path(path)) for path in (baseline_path,current_path)]
        else:
            from app.cpm.analysis_io import import_analysis_file
            current_import,critical_definition=import_analysis_file(Path(current_path))
            imports=[ScheduleImportService().import_file(Path(baseline_path)),current_import]
        for label,result in zip(('Baseline','Current'),imports):
            if not result.succeeded or result.schedule is None:
                raise ReportInputError(label+' XER import failed: '+'; '.join(d.message for d in result.diagnostics))
        schedules=[i.schedule for i in imports]
        projects=[s.project for s in schedules]
        if all(projects) and all(p.project_code for p in projects) and projects[0].project_code!=projects[1].project_code:
            raise ReportInputError('Baseline and current project codes differ; select schedules from the same project.')
        now=datetime.now(timezone.utc)
        versions=[ScheduleVersion(label,label,kind,filename or Path(path).name,
            schedule.project.data_date if schedule.project else None,now,schedule)
            for label,kind,filename,path,schedule in zip(('BASELINE','CURRENT'),
                (ScheduleVersionType.BASELINE,ScheduleVersionType.CURRENT),
                (baseline_filename,current_filename),(baseline_path,current_path),schedules)]
        comparison=ScheduleComparisonEngine().compare(*versions)
        analysis=None
        if analysis_selection is not None:
            from app.cpm.selected_analysis import SelectedAnchorService
            analysis=SelectedAnchorService().analyze(schedules[1],imports[1].graph,analysis_selection,critical_definition=critical_definition)
        return self.builder.build(comparison,analysis_result=analysis,generated_at=now,generated_by=generated_by,
            import_diagnostics=tuple(d for result in imports for d in result.diagnostics))

    def from_bytes(self, baseline, current, baseline_filename, current_filename, *, generated_by=None, analysis_selection=None):
        for content,filename in ((baseline,baseline_filename),(current,current_filename)):
            if not filename.lower().endswith('.xer'):
                raise ReportInputError('Only .xer source schedules are supported.')
            if len(content)>self.limits.maximum_upload_bytes:
                raise ReportLimitError('XER upload exceeds the configured size limit.')
        with TemporaryDirectory(prefix='schedule-assurance-report-') as folder:
            paths=[Path(folder)/'baseline.xer',Path(folder)/'current.xer']
            for path,content in zip(paths,(baseline,current)):path.write_bytes(content)
            return self.from_files(*paths,baseline_filename=Path(baseline_filename.replace('\\','/')).name,
                current_filename=Path(current_filename.replace('\\','/')).name,generated_by=generated_by,analysis_selection=analysis_selection)

    def excel(self, report):
        return ExcelReportRenderer().render(report)
