from pathlib import Path

from fastapi.testclient import TestClient

from app.graph.schedule_graph import ScheduleGraph
from app.health.models import HealthCheckConfig, HealthRuleResult, Severity
from app.health.scoring import ScoringConfig, calculate_health_score
from app.importers.p6_normalization import (
    normalize_activity_type,
    normalize_relationship_type,
    normalize_status,
)
from app.importers.schedule_mapper import ScheduleMapper
from app.importers.xer_parser import XERParser
from app.main import app
from app.services.schedule_health import ScheduleHealthService
from app.services.schedule_import import ScheduleImportService


FIXTURE = Path(__file__).with_name("synthetic.xer")


def test_xer_parser_and_import_service():
    tables = XERParser().parse(FIXTURE)
    assert set(tables["TASK"][0]) >= {"task_id", "task_code", "task_name"}

    result = ScheduleImportService().import_file(FIXTURE)
    assert result.succeeded
    assert result.schedule is not None
    assert result.graph is not None
    assert result.statistics.activities == 4
    assert result.statistics.relationships == 4
    assert result.statistics.duplicate_activity_codes == 1
    assert result.statistics.invalid_references == 1


def test_mapper_preserves_duplicate_task_codes():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))
    assert set(schedule.activities) == {"101", "102", "103", "104"}
    assert len(schedule.activities_by_code["A100"]) == 2
    assert schedule.get_activity("A100") is None


def test_p6_normalization():
    assert normalize_status("TK_Complete") == "complete"
    assert normalize_status("TK_Active") == "in_progress"
    assert normalize_status("TK_NotStart") == "not_started"
    assert normalize_activity_type("TT_StartMile") == "start_milestone"
    assert normalize_activity_type("TT_FinMile") == "finish_milestone"
    assert normalize_activity_type("TT_Mile") == "milestone"
    assert normalize_relationship_type("PR_FS") == "FS"
    assert normalize_relationship_type("PR_SS") == "SS"
    assert normalize_relationship_type("PR_FF") == "FF"
    assert normalize_relationship_type("PR_SF") == "SF"


def test_graph_traversal():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))
    graph = ScheduleGraph(schedule)
    assert [a.activity_id for a in graph.get_direct_successors("102")] == ["104"]
    assert graph.get_activity_by_id("102") is not None


def test_cycles_and_topological_sort():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))
    graph = ScheduleGraph(schedule)
    assert graph.detect_cycles()
    sorted_result = graph.topological_sort()
    assert not sorted_result.is_valid


def test_health_service_and_scoring():
    result = ScheduleImportService().import_file(FIXTURE)
    assert result.schedule is not None and result.graph is not None

    health = ScheduleHealthService().analyze(
        result.schedule,
        result.graph,
        HealthCheckConfig(detail_limit_per_rule=1),
    )
    assert health.rules_evaluated == 20
    assert health.total_issues == sum(r.issue_count for r in health.rule_results)
    assert all(r.returned_count <= 1 for r in health.rule_results)


def test_negative_float_negative_lag_long_duration_and_status_rules():
    result = ScheduleImportService().import_file(FIXTURE)
    assert result.schedule is not None and result.graph is not None
    health = ScheduleHealthService().analyze(result.schedule, result.graph)
    ids = {rule.rule_id: rule for rule in health.rule_results}

    assert ids["negative_total_float"].issue_count >= 1
    assert ids["negative_lag"].issue_count >= 1
    assert ids["long_duration"].issue_count == 0
    assert ids["not_started_above_0_percent"].issue_count == 0
    assert ids["in_progress_missing_actual_start"].issue_count == 1


def test_open_start_and_finish_detection():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))
    graph = ScheduleGraph(schedule)
    health = ScheduleHealthService().analyze(schedule, graph)
    ids = {rule.rule_id: rule for rule in health.rule_results}
    assert "open_starts" in ids
    assert "open_finishes" in ids


def test_scoring_boundaries():
    from app.health.models import HealthRuleResult, Severity

    clean = HealthRuleResult("clean", "Clean", Severity.WARNING, 0, 0, [])
    score, rating = calculate_health_score([clean])
    assert score == 100.0 and rating == "Excellent"

    critical = HealthRuleResult("critical", "Critical", Severity.CRITICAL, 100, 0, [])
    score, rating = calculate_health_score([critical], ScoringConfig())
    assert score == 75.0


def test_api_rejects_unsupported_extension():
    client = TestClient(app)
    response = client.post("/api/schedules/analyze", files={"file": ("bad.txt", b"data", "text/plain")})
    assert response.status_code == 415


def test_api_analyze_xer():
    client = TestClient(app)
    response = client.post(
        "/api/schedules/analyze",
        files={"file": ("synthetic.xer", FIXTURE.read_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project"]["project_code"] == "P1"
    assert body["import_statistics"]["activities"] == 4
    assert body["import_statistics"]["duplicate_activity_codes"] == 1
    assert "health_score" in body
    assert "rule_results" in body


def test_mapper_selects_dominant_project():
    tables = {
        "PROJECT": [
            {"proj_id": "1", "proj_short_name": "P1", "proj_name": "Project 1"},
            {"proj_id": "2", "proj_short_name": "P2", "proj_name": "Project 2"},
        ],
        "TASK": [
            {"task_id": "101", "task_code": "A", "task_name": "Minor", "proj_id": "1", "task_type": "TT_Task", "status_code": "TK_NotStart"},
            {"task_id": "201", "task_code": "B", "task_name": "Main One", "proj_id": "2", "task_type": "TT_Task", "status_code": "TK_NotStart"},
            {"task_id": "202", "task_code": "C", "task_name": "Main Two", "proj_id": "2", "task_type": "TT_Mile", "status_code": "TK_NotStart"},
        ],
        "PROJWBS": [],
        "CALENDAR": [],
        "TASKPRED": [],
    }
    schedule = ScheduleMapper().map(tables)
    assert schedule.project is not None
    assert schedule.project.project_id == "2"
    assert set(schedule.activities) == {"201", "202"}
