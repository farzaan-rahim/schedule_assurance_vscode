from datetime import datetime

from app.dcma.config import DCMAConfig
from app.dcma.models import DCMAStatus
from app.dcma.service import DCMAAssessmentService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Activity, Project, Relationship, Schedule, WBS


def activity(
    task_id,
    code,
    status="TK_NotStart",
    activity_type="TT_Task",
    wbs_id="W1",
    start=None,
    finish=None,
    actual_start=None,
    actual_finish=None,
    duration=40,
    float_hours=10,
    constraint_type=None,
    constraint_date=None,
):
    return Activity(
        activity_id=task_id,
        activity_code=code,
        activity_name=code,
        project_id="P1",
        wbs_id=wbs_id,
        raw_status=status,
        status=status,
        raw_activity_type=activity_type,
        activity_type=activity_type,
        planned_start=start,
        planned_finish=finish,
        actual_start=actual_start,
        actual_finish=actual_finish,
        original_duration_hours=duration,
        total_float_hours=float_hours,
        free_float_hours=float_hours,
        primary_constraint_type=constraint_type,
        primary_constraint_date=constraint_date,
    )


def schedule(activities, relationships=None, data_date=datetime(2026, 4, 1)):
    result = Schedule(
        project=Project("P1", "P1", "Project", data_date),
        relationships=relationships or [],
        wbs_nodes={"W1": WBS("W1", "W1", "WBS 1")},
    )
    result.activities = {a.activity_id: a for a in activities}
    result.rebuild_activity_indexes()
    return result


def test_missing_logic_leads_lags_relationships_and_float():
    data_date = datetime(2026, 4, 1)
    a = activity("1", "A", start=datetime(2026, 3, 1), finish=datetime(2026, 3, 2), float_hours=-5)
    b = activity("2", "B", start=datetime(2026, 4, 2), finish=datetime(2026, 4, 3), duration=400, float_hours=1400)
    c = activity("3", "C", activity_type="TT_Mile", start=datetime(2026, 4, 2), finish=datetime(2026, 4, 2), float_hours=None)
    s = schedule([a, b, c], [
        Relationship("R1", "1", "2", "FS", -10),
        Relationship("R2", "2", "3", "SS", 100),
        Relationship("R3", "1", "3", "XX", 0),
    ], data_date)

    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    by_id = {metric.metric_id: metric for metric in result.metric_results}

    missing = by_id["missing_logic"]
    assert missing.eligible_count == 2
    assert missing.finding_count >= 1

    assert by_id["leads"].details["largest_negative_lag_magnitude"] == 10
    assert by_id["lags"].details["positive_lag_count"] == 1
    assert by_id["lags"].details["excessive_lag_count"] == 1
    assert by_id["relationship_types"].details["counts"]["UNKNOWN"] == 1

    assert by_id["high_float"].eligible_count == 2
    assert by_id["high_float"].finding_count == 1
    assert by_id["negative_float"].finding_count == 1
    assert by_id["negative_float"].details["missing_float_count"] == 0


def test_hard_constraints_and_resource_metric():
    hard = activity(
        "1", "A", constraint_type="MANDATORY_START",
        constraint_date=datetime(2026, 5, 1),
    )
    soft = activity("2", "B", constraint_type="START_ON_OR_AFTER")
    s = schedule([hard, soft])
    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    by_id = {metric.metric_id: metric for metric in result.metric_results}

    assert by_id["hard_constraints"].finding_count == 1
    assert by_id["resources"].status == DCMAStatus.FAIL
    assert by_id["resources"].details["resource_loaded_count"] == 0


def test_invalid_dates_subtypes():
    s = schedule([
        activity("1", "A", status="TK_Complete", actual_finish=None, finish=datetime(2026, 3, 1)),
        activity("2", "B", status="TK_NotStart", actual_start=datetime(2026, 3, 1), finish=datetime(2026, 4, 2)),
        activity("3", "C", status="TK_Active", actual_start=None, finish=datetime(2026, 4, 2)),
        activity("4", "D", status="TK_NotStart", finish=datetime(2026, 3, 1)),
        activity("5", "E", status="TK_Complete", actual_finish=datetime(2026, 5, 1), finish=datetime(2026, 4, 1)),
    ])
    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    metric = next(metric for metric in result.metric_results if metric.metric_id == "invalid_dates")

    subtype_counts = metric.details["subtype_counts"]
    assert subtype_counts["completed_missing_actual_finish"] >= 1
    assert subtype_counts["not_started_with_actual_dates"] >= 1
    assert subtype_counts["in_progress_missing_actual_start"] >= 1
    assert subtype_counts["forecast_finish_before_data_date"] >= 1
    assert subtype_counts["actual_finish_after_data_date"] >= 1


def test_invalid_dates_multiple_subtypes_count_activity_once():
    s = schedule([
        activity(
            "1", "A", status="TK_NotStart",
            start=datetime(2026, 3, 1), finish=datetime(2026, 3, 2),
            actual_start=datetime(2026, 5, 1), actual_finish=datetime(2026, 5, 2),
        ),
    ], data_date=datetime(2026, 4, 1))
    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    metric = next(metric for metric in result.metric_results if metric.metric_id == "invalid_dates")

    assert metric.eligible_count == 1
    assert metric.finding_count == 1
    assert metric.details["subtype_counts"]["actual_start_after_data_date"] == 1
    assert metric.details["subtype_counts"]["actual_finish_after_data_date"] == 1
    assert metric.details["subtype_counts"]["not_started_with_actual_dates"] == 1


def test_unsupported_cpm_metrics():
    s = schedule([activity("1", "A")])
    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    by_id = {metric.metric_id: metric for metric in result.metric_results}
    assert by_id["critical_path_test"].status == DCMAStatus.NOT_EVALUATED
    assert by_id["cpli"].status == DCMAStatus.NOT_EVALUATED


def test_dcma_controlled_xer_integration():
    from app.services.schedule_import import ScheduleImportService

    imported = ScheduleImportService().import_file("sample_data/sample_current.xer")
    assert imported.succeeded
    result = DCMAAssessmentService().analyze(imported.schedule, imported.graph, DCMAConfig(), "sample_current.xer")

    by_id = {metric.metric_id: metric for metric in result.metric_results}
    assert result.total_activity_population == 7
    assert by_id["missing_logic"].eligible_count >= 0
    assert by_id["leads"].eligible_count == 5
    assert by_id["lags"].eligible_count == 5
    assert by_id["negative_float"].eligible_count >= 1


def test_dcma_api_analyze():
    from pathlib import Path
    from fastapi.testclient import TestClient

    from app.main import app

    fixture = Path("sample_data/sample_current.xer")
    client = TestClient(app)
    response = client.post(
        "/api/schedules/dcma/analyze",
        files={"file": ("sample_current.xer", fixture.read_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_activity_population"] == 7
    assert len(body["metrics"]) == 14


def test_dcma_api_rejects_extension_and_failed_import():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    unsupported = client.post(
        "/api/schedules/dcma/analyze",
        files={"file": ("bad.txt", b"bad", "text/plain")},
    )
    assert unsupported.status_code == 415

    malformed = client.post(
        "/api/schedules/dcma/analyze",
        files={"file": ("bad.xer", b"ERMHDR\t1\n", "application/octet-stream")},
    )
    assert malformed.status_code == 422


def test_constraint_mapper_and_normalization():
    from app.importers.p6_normalization import normalize_constraint_type
    from app.importers.schedule_mapper import ScheduleMapper

    assert normalize_constraint_type("CS_MSO") == "MANDATORY_START"
    assert normalize_constraint_type("CS_FNLT") == "FINISH_ON_OR_BEFORE"

    mapped = ScheduleMapper().map({
        "PROJECT": [{"proj_id": "P1", "proj_short_name": "P1", "proj_name": "Project"}],
        "TASK": [{
            "task_id": "1", "task_code": "A", "task_name": "Activity", "proj_id": "P1",
            "cstr_type": "CS_MSO", "cstr_date": "2026-05-01",
            "cstr_type2": "CS_FNET", "cstr_date2": "2026-06-01",
        }],
        "PROJWBS": [], "CALENDAR": [], "TASKPRED": [],
    })
    mapped_activity = mapped.get_activity_by_id("1")
    assert mapped_activity is not None
    assert mapped_activity.primary_constraint_type == "MANDATORY_START"
    assert mapped_activity.primary_constraint_date.isoformat().startswith("2026-05-01")
    assert mapped_activity.secondary_constraint_type == "FINISH_ON_OR_AFTER"


def test_zero_leads_are_pass_and_unknown_relationship_types_are_not_excluded():
    from app.dcma.thresholds import percentage_status

    assert percentage_status(0.0, 0.0, 5.0) == DCMAStatus.PASS

    s = schedule([
        activity("1", "A", finish=datetime(2026, 4, 2)),
        activity("2", "B", finish=datetime(2026, 4, 3)),
    ], [Relationship("R1", "1", "2", "XX", 0)])
    result = DCMAAssessmentService().analyze(s, ScheduleGraph(s), DCMAConfig())
    by_id = {metric.metric_id: metric for metric in result.metric_results}

    assert by_id["leads"].status == DCMAStatus.PAS
    assert by_id["leads"].excluded_count == 0
    assert by_id["lags"].excluded_count == 0
    assert by_id["relationship_types"].eligible_count == 1
    assert by_id["relationship_types"].excluded_count == 0
    assert by_id["relationship_types"].details["counts"]["UNKNOWN"] == 1
