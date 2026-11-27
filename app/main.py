from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from app.api.reports import router as reporting_router
from app.api.cpm_analysis import router as cpm_analysis_router
from app.api.persistence import router as persistence_router

from app.comparison.engine import ScheduleComparisonEngine
from app.comparison.models import ScheduleVersion, ScheduleVersionType
from app.services.schedule_health import ScheduleHealthService
from app.services.schedule_import import ScheduleImportService
from app.milestones.service import MilestoneAnalysisService
from app.dcma.service import DCMAAssessmentService

app = FastAPI(
    title="Schedule Assurance API",
    description="Clean-room Primavera P6 schedule analysis platform.",
    version="0.1.0",
)


app.include_router(reporting_router)
app.include_router(cpm_analysis_router)
app.include_router(persistence_router)


@app.get("/api/health", tags=["System"])
def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "application": "Schedule Assurance",
        "version": "0.1.0",
        "database_required": False,
    }


@app.post("/api/schedules/analyze", tags=["Schedules"])
async def analyze_schedule(file: UploadFile = File(...)) -> dict[str, object]:
    filename = file.filename or ""
    if not filename.lower().endswith(".xer"):
        raise HTTPException(status_code=415, detail="Unsupported file type; upload a .xer file.")

    suffix = Path(filename).suffix
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_path = Path(temp_file.name)

        import_result = ScheduleImportService().import_file(temp_path)
        if not import_result.succeeded or import_result.schedule is None or import_result.graph is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "XER import failed.",
                    "diagnostics": [
                        {
                            "code": diagnostic.code,
                            "message": diagnostic.message,
                            "severity": diagnostic.severity.value,
                            "table": diagnostic.table,
                            "field_name": diagnostic.field_name,
                            "raw_value": diagnostic.raw_value,
                        }
                        for diagnostic in import_result.diagnostics
                    ],
                },
            )

        health = ScheduleHealthService().analyze(
            import_result.schedule,
            import_result.graph,
        )
        project = import_result.schedule.project

        return {
            "project": {
                "project_id": project.project_id if project else None,
                "project_code": project.project_code if project else None,
                "project_name": project.project_name if project else None,
                "data_date": project.data_date.isoformat() if project and project.data_date else None,
            },
            "import_statistics": {
                "activities": import_result.statistics.activities,
                "relationships": import_result.statistics.relationships,
                "wbs_nodes": import_result.statistics.wbs_nodes,
                "calendars": import_result.statistics.calendars,
                "duplicate_activity_codes": import_result.statistics.duplicate_activity_codes,
                "invalid_references": import_result.statistics.invalid_references,
                "parsing_warnings": import_result.statistics.parsing_warnings,
                "resources": import_result.statistics.resources,
                "resource_assignments": import_result.statistics.resource_assignments,
                "activity_code_types": import_result.statistics.activity_code_types,
                "activity_code_values": import_result.statistics.activity_code_values,
                "activity_code_assignments": import_result.statistics.activity_code_assignments,
                "udf_definitions": import_result.statistics.udf_definitions,
                "udf_values": import_result.statistics.udf_values,
            },
            "import_diagnostics": [
                {
                    "code": diagnostic.code,
                    "message": diagnostic.message,
                    "severity": diagnostic.severity.value,
                    "table": diagnostic.table,
                    "row_number": diagnostic.row_number,
                    "field_name": diagnostic.field_name,
                    "raw_value": diagnostic.raw_value,
                }
                for diagnostic in import_result.diagnostics
            ],
            "health_score": health.score,
            "health_rating": health.rating,
            "issue_totals": {
                "total": health.total_issues,
                "critical": health.critical_issues,
                "warning": health.warning_issues,
                "info": health.info_issues,
            },
            "rule_results": [
                {
                    "rule_id": result.rule_id,
                    "rule_name": result.rule_name,
                    "severity": result.severity.value,
                    "issue_count": result.issue_count,
                    "returned_count": result.returned_count,
                    "issues": [issue.__dict__ for issue in result.issues],
                }
                for result in health.rule_results
            ],
        }
    finally:
        if "temp_path" in locals():
            temp_path.unlink(missing_ok=True)


@app.post("/api/schedules/compare", tags=["Schedules"])
async def compare_schedules(
    baseline: UploadFile = File(...),
    current: UploadFile = File(...),
) -> dict[str, object]:
    for label, upload in (("baseline", baseline), ("current", current)):
        filename = upload.filename or ""
        if not filename.lower().endswith(".xer"):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported {label} file type; upload a .xer file.",
            )

    temp_paths: list[Path] = []
    try:
        import_results = []
        for label, upload in (("baseline", baseline), ("current", current)):
            filename = upload.filename or f"{label}.xer"
            with NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(await upload.read())
                temp_path = Path(temp_file.name)
            temp_paths.append(temp_path)
            import_results.append((label, ScheduleImportService().import_file(temp_path)))

        baseline_label, baseline_import = import_results[0]
        current_label, current_import = import_results[1]

        for label, import_result in import_results:
            if not import_result.succeeded or import_result.schedule is None:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": f"{label.title()} XER import failed.",
                        "diagnostics": [
                            {
                                "code": diagnostic.code,
                                "message": diagnostic.message,
                                "severity": diagnostic.severity.value,
                                "table": diagnostic.table,
                                "row_number": diagnostic.row_number,
                                "field_name": diagnostic.field_name,
                                "raw_value": diagnostic.raw_value,
                            }
                            for diagnostic in import_result.diagnostics
                        ],
                    },
                )

        baseline_project = baseline_import.schedule.project
        current_project = current_import.schedule.project
        if (
            baseline_project is not None
            and current_project is not None
            and baseline_project.project_code
            and current_project.project_code
            and baseline_project.project_code != current_project.project_code
        ):
            raise HTTPException(
                status_code=422,
                detail="Baseline and current project codes differ; select schedules from the same project.",
            )

        imported_at = datetime.now(timezone.utc)
        baseline_version = ScheduleVersion(
            version_id="BASELINE",
            version_label="BASELINE",
            version_type=ScheduleVersionType.BASELINE,
            source_filename=baseline.filename or "baseline.xer",
            data_date=baseline_project.data_date if baseline_project else None,
            imported_at=imported_at,
            schedule=baseline_import.schedule,
        )
        current_version = ScheduleVersion(
            version_id="CURRENT",
            version_label="CURRENT",
            version_type=ScheduleVersionType.CURRENT,
            source_filename=current.filename or "current.xer",
            data_date=current_project.data_date if current_project else None,
            imported_at=imported_at,
            schedule=current_import.schedule,
        )

        result = ScheduleComparisonEngine().compare(baseline_version, current_version)

        def project_payload(project: object | None) -> dict[str, object]:
            if project is None:
                return {"project_id": None, "project_code": None, "project_name": None, "data_date": None}
            return {
                "project_id": getattr(project, "project_id", None),
                "project_code": getattr(project, "project_code", None),
                "project_name": getattr(project, "project_name", None),
                "data_date": getattr(project, "data_date", None).isoformat()
                if getattr(project, "data_date", None) else None,
            }

        def import_payload(import_result: object) -> dict[str, object]:
            return {
                "statistics": getattr(import_result, "statistics", None).__dict__,
                "diagnostics": [
                    {
                        "code": diagnostic.code,
                        "message": diagnostic.message,
                        "severity": diagnostic.severity.value,
                        "table": diagnostic.table,
                        "row_number": diagnostic.row_number,
                        "field_name": diagnostic.field_name,
                        "raw_value": diagnostic.raw_value,
                    }
                    for diagnostic in getattr(import_result, "diagnostics", [])
                ],
            }

        activity_payload = []
        for variance in result.activity_variances:
            baseline_activity = variance.baseline_activity
            current_activity = variance.current_activity
            activity_payload.append({
                "activity_code": variance.activity_code,
                "classification": variance.classification.value,
                "match_method": variance.match_method.value if variance.match_method else None,
                "baseline_activity": {
                    "activity_id": baseline_activity.activity_id,
                    "activity_code": baseline_activity.activity_code,
                    "activity_name": baseline_activity.activity_name,
                } if baseline_activity else None,
                "current_activity": {
                    "activity_id": current_activity.activity_id,
                    "activity_code": current_activity.activity_code,
                    "activity_name": current_activity.activity_name,
                } if current_activity else None,
                "baseline_wbs_path": variance.baseline_wbs_path,
                "current_wbs_path": variance.current_wbs_path,
                "name_changed": variance.name_changed,
                "wbs_changed": variance.wbs_changed,
                "calendar_changed": variance.calendar_changed,
                "activity_type_changed": variance.activity_type_changed,
                "status_changed": variance.status_changed,
                "finish_variance_hours": variance.finish_variance_hours,
                "finish_variance_calendar_days": variance.finish_variance_calendar_days,
                "start_variance_hours": variance.start_variance_hours,
                "start_variance_calendar_days": variance.start_variance_calendar_days,
                "original_duration_variance_hours": variance.original_duration_variance_hours,
                "remaining_duration_variance_hours": variance.remaining_duration_variance_hours,
                "total_float_variance_hours": variance.total_float_variance_hours,
                "float_deteriorated": variance.float_deteriorated,
                "float_improved": variance.float_improved,
                "became_negative_float": variance.became_negative_float,
                "recovered_from_negative_float": variance.recovered_from_negative_float,
                "became_critical": variance.became_critical,
                "left_critical_status": variance.left_critical_status,
            })

        relationship_payload = []
        for variance in result.relationship_variances:
            relationship_payload.append({
                "change_type": variance.change_type.value,
                "predecessor_activity_code": variance.predecessor_activity_code,
                "successor_activity_code": variance.successor_activity_code,
                "baseline_relationship_type": variance.baseline_relationship_type,
                "current_relationship_type": variance.current_relationship_type,
                "baseline_lag_hours": variance.baseline_lag_hours,
                "current_lag_hours": variance.current_lag_hours,
            })

        return {
            "baseline_project": project_payload(baseline_project),
            "current_project": project_payload(current_project),
            "import_diagnostics": {
                "baseline": import_payload(baseline_import)["diagnostics"],
                "current": import_payload(current_import)["diagnostics"],
            },
            "comparison_summary": vars(result.summary),
            "activity_comparison": activity_payload,
            "relationship_comparison": relationship_payload,
            "comparison_diagnostics": [
                {
                    "code": diagnostic.code,
                    "message": diagnostic.message,
                    "severity": diagnostic.severity,
                    "activity_code": diagnostic.activity_code,
                    "metadata": diagnostic.metadata,
                }
                for diagnostic in result.diagnostics
            ],
        }
    finally:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)


@app.post("/api/schedules/milestones/analyze", tags=["Milestones"])
async def analyze_milestones(file: UploadFile = File(...)) -> dict[str, object]:
    if not (file.filename or "").lower().endswith(".xer"):
        raise HTTPException(status_code=415, detail="Unsupported file type; upload a .xer file.")

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".xer") as temp_file:
            temp_file.write(await file.read())
            temp_path = Path(temp_file.name)

        import_result = ScheduleImportService().import_file(temp_path)
        if not import_result.succeeded or import_result.schedule is None or import_result.graph is None:
            raise HTTPException(status_code=422, detail="XER import failed.")

        result = MilestoneAnalysisService().analyze(
            import_result.schedule,
            import_result.graph,
        )
        project = import_result.schedule.project

        return {
            "project": {
                "project_id": project.project_id if project else None,
                "project_code": project.project_code if project else None,
                "project_name": project.project_name if project else None,
                "data_date": project.data_date.isoformat() if project and project.data_date else None,
            },
            "milestone_summary": vars(result.summary),
            "milestone_details": [
                {
                    "activity_id": item.activity_id,
                    "activity_code": item.activity_code,
                    "activity_name": item.activity_name,
                    "classification": item.classification.value,
                    "raw_activity_type": item.raw_activity_type,
                    "status": item.status,
                    "wbs_path": item.wbs_path,
                    "planned_start": item.planned_start.isoformat() if item.planned_start else None,
                    "planned_finish": item.planned_finish.isoformat() if item.planned_finish else None,
                    "actual_start": item.actual_start.isoformat() if item.actual_start else None,
                    "actual_finish": item.actual_finish.isoformat() if item.actual_finish else None,
                    "total_float_hours": item.total_float_hours,
                    "completed": item.completed,
                    "overdue": item.overdue,
                    "negative_float": item.negative_float,
                    "critical": item.critical,
                }
                for item in result.milestones
            ],
            "milestone_findings": [
                {
                    "code": item.code,
                    "message": item.message,
                    "severity": item.severity,
                    "activity_code": item.activity_code,
                    "activity_id": item.activity_id,
                    "metadata": item.metadata,
                }
                for item in result.findings
            ],
            "candidate_drivers": {
                code: [
                    {
                        "activity_id": driver.activity_id,
                        "activity_code": driver.activity_code,
                        "activity_name": driver.activity_name,
                        "relationship_type": driver.relationship_type,
                        "lag_hours": driver.lag_hours,
                        "status": driver.status,
                        "planned_finish": driver.planned_finish.isoformat() if driver.planned_finish else None,
                        "total_float_hours": driver.total_float_hours,
                        "negative_float": driver.negative_float,
                        "incomplete": driver.incomplete,
                        "rank_score": driver.rank_score,
                        "reasons": list(driver.reasons),
                    }
                    for driver in drivers
                ]
                for code, drivers in result.candidate_drivers.items()
            },
            "truncation": result.truncation,
        }
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@app.post("/api/schedules/milestones/compare", tags=["Milestones"])
async def compare_milestones(
    baseline: UploadFile = File(...),
    current: UploadFile = File(...),
) -> dict[str, object]:
    for label, upload in (("baseline", baseline), ("current", current)):
        if not (upload.filename or "").lower().endswith(".xer"):
            raise HTTPException(status_code=415, detail=f"Unsupported {label} file type; upload a .xer file.")

    temp_paths: list[Path] = []
    try:
        imports = []
        for label, upload in (("baseline", baseline), ("current", current)):
            with NamedTemporaryFile(delete=False, suffix=".xer") as temp_file:
                temp_file.write(await upload.read())
                temp_path = Path(temp_file.name)
            temp_paths.append(temp_path)
            imports.append((label, ScheduleImportService().import_file(temp_path)))

        baseline_label, baseline_import = imports[0]
        current_label, current_import = imports[1]

        for label, import_result in imports:
            if not import_result.succeeded or import_result.schedule is None or import_result.graph is None:
                raise HTTPException(status_code=422, detail=f"{label.title()} XER import failed.")

        baseline_project = baseline_import.schedule.project
        current_project = current_import.schedule.project
        imported_at = datetime.now(timezone.utc)
        baseline_version = ScheduleVersion(
            "BASELINE", "BASELINE", ScheduleVersionType.BASELINE,
            baseline.filename or "baseline.xer",
            baseline_project.data_date if baseline_project else None,
            imported_at, baseline_import.schedule,
        )
        current_version = ScheduleVersion(
            "CURRENT", "CURRENT", ScheduleVersionType.CURRENT,
            current.filename or "current.xer",
            current_project.data_date if current_project else None,
            imported_at, current_import.schedule,
        )

        comparison = ScheduleComparisonEngine().compare(baseline_version, current_version)
        result = MilestoneAnalysisService().compare(
            baseline_import.schedule,
            current_import.schedule,
            comparison,
            baseline_import.graph,
            current_import.graph,
        )

        return {
            "baseline_project": {
                "project_code": baseline_project.project_code if baseline_project else None,
                "project_name": baseline_project.project_name if baseline_project else None,
                "data_date": baseline_project.data_date.isoformat() if baseline_project and baseline_project.data_date else None,
            },
            "current_project": {
                "project_code": current_project.project_code if current_project else None,
                "project_name": current_project.project_name if current_project else None,
                "data_date": current_project.data_date.isoformat() if current_project and current_project.data_date else None,
            },
            "milestone_summary": vars(result.summary),
            "milestone_comparisons": [
                {
                    "activity_code": item.activity_code,
                    "classification": item.classification.value,
                    "movement": item.movement.value,
                    "match_method": item.match_method.value if item.match_method else None,
                    "baseline_wbs_path": item.baseline_wbs_path,
                    "current_wbs_path": item.current_wbs_path,
                    "baseline_planned_date": item.baseline_planned_date.isoformat() if item.baseline_planned_date else None,
                    "current_planned_date": item.current_planned_date.isoformat() if item.current_planned_date else None,
                    "planned_date_variance_hours": item.planned_date_variance_hours,
                    "planned_date_variance_calendar_days": item.planned_date_variance_calendar_days,
                    "baseline_total_float": item.baseline_total_float,
                    "current_total_float": item.current_total_float,
                    "float_variance_hours": item.float_variance_hours,
                    "float_deteriorated": item.float_deteriorated,
                    "became_negative_float": item.became_negative_float,
                    "became_critical": item.became_critical,
                    "baseline_status": item.baseline_status,
                    "current_status": item.current_status,
                }
                for item in result.comparisons
            ],
            "milestone_findings": [
                {"code": item.code, "message": item.message, "severity": item.severity, "activity_code": item.activity_code, "metadata": item.metadata}
                for item in result.findings
            ],
            "candidate_drivers": {
                code: [
                    {"activity_code": driver.activity_code, "rank_score": driver.rank_score, "reasons": list(driver.reasons)}
                    for driver in drivers
                ]
                for code, drivers in result.candidate_drivers.items()
            },
            "truncation": result.truncation,
        }
    finally:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)


@app.post("/api/schedules/dcma/analyze", tags=["DCMA"])
async def analyze_dcma(file: UploadFile = File(...)) -> dict[str, object]:
    if not (file.filename or "").lower().endswith(".xer"):
        raise HTTPException(status_code=415, detail="Unsupported file type; upload a .xer file.")

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".xer") as temp_file:
            temp_file.write(await file.read())
            temp_path = Path(temp_file.name)

        imported = ScheduleImportService().import_file(temp_path)
        if not imported.succeeded or imported.schedule is None or imported.graph is None:
            raise HTTPException(status_code=422, detail="XER import failed.")

        result = DCMAAssessmentService().analyze(
            imported.schedule,
            imported.graph,
            source_filename=file.filename,
        )

        return _dcma_payload(result)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@app.post("/api/schedules/dcma/compare", tags=["DCMA"])
async def compare_dcma(
    baseline: UploadFile = File(...),
    current: UploadFile = File(...),
) -> dict[str, object]:
    for label, upload in (("baseline", baseline), ("current", current)):
        if not (upload.filename or "").lower().endswith(".xer"):
            raise HTTPException(status_code=415, detail=f"Unsupported {label} file type; upload a .xer file.")

    temp_paths: list[Path] = []
    try:
        imports = []
        for label, upload in (("baseline", baseline), ("current", current)):
            with NamedTemporaryFile(delete=False, suffix=".xer") as temp_file:
                temp_file.write(await upload.read())
                temp_path = Path(temp_file.name)
            temp_paths.append(temp_path)
            imports.append((label, ScheduleImportService().import_file(temp_path)))

        baseline_label, baseline_import = imports[0]
        current_label, current_import = imports[1]
        for label, imported in imports:
            if not imported.succeeded or imported.schedule is None or imported.graph is None:
                raise HTTPException(status_code=422, detail=f"{label.title()} XER import failed.")

        imported_at = datetime.now(timezone.utc)
        baseline_project = baseline_import.schedule.project
        current_project = current_import.schedule.project
        baseline_version = ScheduleVersion(
            "BASELINE", "BASELINE", ScheduleVersionType.BASELINE,
            baseline.filename or "baseline.xer",
            baseline_project.data_date if baseline_project else None,
            imported_at, baseline_import.schedule,
        )
        current_version = ScheduleVersion(
            "CURRENT", "CURRENT", ScheduleVersionType.CURRENT,
            current.filename or "current.xer",
            current_project.data_date if current_project else None,
            imported_at, current_import.schedule,
        )
        comparison = ScheduleComparisonEngine().compare(baseline_version, current_version)
        result = DCMAAssessmentService().analyze(
            current_import.schedule,
            current_import.graph,
            source_filename=current.filename,
            comparison=comparison,
        )
        return _dcma_payload(result)
    finally:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)


def _dcma_payload(result) -> dict[str, object]:
    metric_payload = []
    for metric in result.metric_results:
        metric_payload.append({
            "metric_id": metric.metric_id,
            "metric_name": metric.metric_name,
            "description": metric.description,
            "status": metric.status.value,
            "eligible_count": metric.eligible_count,
            "finding_count": metric.finding_count,
            "finding_percentage": metric.finding_percentage,
            "threshold": metric.threshold,
            "threshold_interpretation": metric.threshold_interpretation,
            "pass_fail_warning": metric.pass_fail_warning,
            "excluded_count": metric.excluded_count,
            "exclusion_reasons": metric.exclusion_reasons,
            "calculation_notes": list(metric.calculation_notes),
            "source_fields": list(metric.source_fields),
            "limitations": list(metric.limitations),
            "details": metric.details,
            "findings": [
                {
                    "finding_type": finding.finding_type,
                    "message": finding.message,
                    "activity_id": finding.activity_id,
                    "activity_code": finding.activity_code,
                    "activity_name": finding.activity_name,
                    "wbs_path": finding.wbs_path,
                    "relationship_id": finding.relationship_id,
                    "predecessor_activity_id": finding.predecessor_activity_id,
                    "successor_activity_id": finding.successor_activity_id,
                    "relationship_type": finding.relationship_type,
                    "lag_hours": finding.lag_hours,
                    "observed_value": finding.observed_value,
                    "metadata": finding.metadata,
                }
                for finding in metric.findings
            ],
        })

    return {
        "project": {
            "project_id": result.project_id,
            "project_code": result.project_code,
            "project_name": result.project_name,
            "data_date": result.data_date.isoformat() if result.data_date else None,
        },
        "source_filename": result.source_filename,
        "assessment_configuration_version": result.configuration_version,
        "metrics_evaluated": result.metrics_evaluated,
        "metrics_not_evaluated": result.metrics_not_evaluated,
        "total_activity_population": result.total_activity_population,
        "metrics": metric_payload,
        "overall_score": {
            "enabled": result.overall_score.enabled,
            "score": result.overall_score.score,
            "rating": result.overall_score.rating,
            "evaluated_weight": result.overall_score.evaluated_weight,
            "excluded_weight": result.overall_score.excluded_weight,
            "contributions": [vars(contribution) for contribution in result.overall_score.contributions],
        },
        "diagnostics": [vars(diagnostic) for diagnostic in result.diagnostics],
        "truncation": result.truncation,
    }


# Presentation is mounted separately; analytical/API routes remain unchanged.
from app.runtime import install_runtime
from app.ui.setup import install_ui
install_runtime(app)
install_ui(app)
