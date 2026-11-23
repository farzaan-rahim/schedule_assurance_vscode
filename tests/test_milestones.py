from datetime import datetime, timedelta

from app.graph.schedule_graph import ScheduleGraph
from app.milestones.analysis import build_milestone_inventory, preferred_planned_date
from app.milestones.classifier import classify_milestone
from app.milestones.drivers import candidate_drivers
from app.milestones.models import MilestoneClassification
from app.milestones.service import MilestoneAnalysisService
from app.models.schedule import Activity, Project, Relationship, Schedule, WBS


def make_activity(
    task_id: str,
    code: str,
    activity_type: str = "TT_Task",
    status: str = "TK_NotStart",
    wbs_id: str = "W1",
    start: datetime | None = None,
    finish: datetime | None = None,
    total_float: float | None = 10,
    percent: float = 0,
) -> Activity:
    return Activity(
        activity_id=task_id,
        activity_code=code,
        activity_name=code,
        project_id="P1",
        wbs_id=wbs_id,
        raw_activity_type=activity_type,
        activity_type=activity_type,
        raw_status=status,
        status=status,
        planned_start=start,
        planned_finish=finish,
        actual_start=start if status == "TK_Active" else None,
        actual_finish=finish if status == "TK_Complete" else None,
        total_float_hours=total_float,
        free_float_hours=total_float,
        percent_complete=percent,
    )


def make_schedule(activities, relationships=None, wbs_nodes=None, data_date=None):
    schedule = Schedule(
        project=Project("P1", "P1", "Project", data_date or datetime(2026, 4, 1)),
        relationships=relationships or [],
        wbs_nodes=wbs_nodes or {"W1": WBS("W1", "W1", "WBS 1")},
    )
    schedule.activities = {a.activity_id: a for a in activities}
    schedule.rebuild_activity_indexes()
    return schedule


def test_milestone_classification_variations():
    assert classify_milestone(make_activity("1", "A", "TT_StartMile")) == MilestoneClassification.START_MILESTONE
    assert classify_milestone(make_activity("2", "B", "TT_FinMile")) == MilestoneClassification.FINISH_MILESTONE
    assert classify_milestone(make_activity("3", "C", "TT_Mile")) == MilestoneClassification.GENERIC_MILESTONE
    assert classify_milestone(make_activity("4", "D", "TT_Task")) == MilestoneClassification.NON_MILESTONE


def test_milestone_inventory_states_and_date_policy():
    completed_finish = make_activity(
        "1", "F", "TT_FinMile", "TK_Complete",
        start=datetime(2026, 3, 1), finish=datetime(2026, 3, 2),
        total_float=-5, percent=100,
    )
    start_mile = make_activity(
        "2", "S", "TT_StartMile", "TK_NotStart",
        start=datetime(2026, 3, 5), finish=datetime(2026, 3, 6),
        total_float=-2,
    )
    ordinary_zero = make_activity(
        "3", "Z", "TT_Task", "TK_NotStart",
        start=datetime(2026, 3, 1), finish=datetime(2026, 3, 1),
        total_float=0,
    )

    schedule = make_schedule([completed_finish, start_mile, ordinary_zero])
    records, findings = build_milestone_inventory(schedule, critical_threshold_hours=0)

    assert len(records) == 2
    assert records[0].completed or records[1].completed
    assert any(r.negative_float for r in records)
    assert any(r.critical for r in records)
    assert preferred_planned_date(start_mile, MilestoneClassification.START_MILESTONE) == start_mile.planned_start
    assert preferred_planned_date(completed_finish, MilestoneClassification.FINISH_MILESTONE) == completed_finish.planned_finish
    assert any(f.code == "milestone_negative_float" for f in findings)


def test_candidate_drivers_are_ranked_deterministically():
    milestone = make_activity(
        "4", "M", "TT_FinMile", "TK_NotStart",
        start=datetime(2026, 4, 10), finish=datetime(2026, 4, 10),
        total_float=-5,
    )
    pred1 = make_activity("1", "P1", "TT_Task", "TK_Active", finish=datetime(2026, 4, 9), total_float=-10)
    pred2 = make_activity("2", "P2", "TT_Task", "TK_NotStart", finish=datetime(2026, 4, 10), total_float=50)
    schedule = make_schedule(
        [pred1, pred2, milestone],
        relationships=[
            Relationship("R1", "1", "4", "FS", 0),
            Relationship("R2", "2", "4", "SS", 24),
        ],
    )
    graph = ScheduleGraph(schedule)

    drivers, stats = candidate_drivers(schedule, graph, milestone, milestone.planned_finish)

    assert stats["direct_predecessors"] == 2
    assert stats["upstream_activities"] == 2
    assert drivers[0].activity_code == "P1"
    assert drivers[0].negative_float is True
    assert drivers[0].incomplete is True
    assert drivers[0].relationship_type == "FS"
    assert drivers[0].lag_hours == 0
    assert "Direct predecessor of the milestone" in drivers[0].reasons


def test_controlled_m1400_milestone_comparison():
    from datetime import timezone
    from pathlib import Path

    from app.comparison.engine import ScheduleComparisonEngine
    from app.comparison.models import ScheduleVersion, ScheduleVersionType
    from app.services.schedule_import import ScheduleImportService

    fixture_dir = Path(__file__).resolve().parents[1] / "sample_data"
    baseline_import = ScheduleImportService().import_file(fixture_dir / "sample_baseline.xer")
    current_import = ScheduleImportService().import_file(fixture_dir / "sample_current.xer")
    assert baseline_import.succeeded and current_import.succeeded

    baseline_schedule = baseline_import.schedule
    current_schedule = current_import.schedule
    baseline_version = ScheduleVersion(
        "BL0", "BL0", ScheduleVersionType.BASELINE,
        "sample_baseline.xer", baseline_schedule.project.data_date,
        datetime.now(timezone.utc), baseline_schedule,
    )
    current_version = ScheduleVersion(
        "CURRENT", "CURRENT", ScheduleVersionType.CURRENT,
        "sample_current.xer", current_schedule.project.data_date,
        datetime.now(timezone.utc), current_schedule,
    )
    comparison = ScheduleComparisonEngine().compare(baseline_version, current_version)

    result = MilestoneAnalysisService().compare(
        baseline_schedule,
        current_schedule,
        comparison,
        ScheduleGraph(baseline_schedule),
        ScheduleGraph(current_schedule),
    )

    m1400 = next(item for item in result.comparisons if item.activity_code == "M1400")
    assert m1400.baseline_planned_date == datetime(2026, 4, 13, 8, 0)
    assert m1400.current_planned_date == datetime(2026, 4, 13, 8, 0)
    assert m1400.planned_date_variance_hours == 0
    assert m1400.baseline_total_float == 10
    assert m1400.current_total_float == -12
    assert m1400.float_variance_hours == -22
    assert m1400.float_deteriorated is True
    assert m1400.became_negative_float is True


def test_milestone_service_truncation_preserves_totals():
    schedule = make_schedule([
        make_activity(str(i), f"M{i}", "TT_Mile", finish=datetime(2026, 5, i + 1))
        for i in range(1, 6)
    ])
    graph = ScheduleGraph(schedule)

    result = MilestoneAnalysisService().analyze(
        schedule,
        graph,
        milestone_limit=2,
        finding_limit=1,
    )

    assert result.summary.total_milestones == 5
    assert len(result.milestones) == 2
    assert result.truncation["milestones_truncated"] is True
    assert result.truncation["findings_truncated"] is False or "findings_total" in result.truncation


def test_milestone_api_analyze_and_compare():
    from pathlib import Path
    from fastapi.testclient import TestClient

    from app.main import app

    fixture_dir = Path(__file__).resolve().parents[1] / "sample_data"
    client = TestClient(app)

    analyze = client.post(
        "/api/schedules/milestones/analyze",
        files={"file": ("sample_current.xer", (fixture_dir / "sample_current.xer").read_bytes(), "application/octet-stream")},
    )
    assert analyze.status_code == 200
    analyze_body = analyze.json()
    assert analyze_body["milestone_summary"]["total_milestones"] >= 1

    compare = client.post(
        "/api/schedules/milestones/compare",
        files={
            "baseline": ("sample_baseline.xer", (fixture_dir / "sample_baseline.xer").read_bytes(), "application/octet-stream"),
            "current": ("sample_current.xer", (fixture_dir / "sample_current.xer").read_bytes(), "application/octet-stream"),
        },
    )
    assert compare.status_code == 200
    compare_body = compare.json()
    m1400 = next(item for item in compare_body["milestone_comparisons"] if item["activity_code"] == "M1400")
    assert m1400["planned_date_variance_hours"] == 0
    assert m1400["float_variance_hours"] == -22


def test_milestone_api_rejects_unsupported_and_failed_import():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    unsupported = client.post(
        "/api/schedules/milestones/analyze",
        files={"file": ("bad.txt", b"bad", "text/plain")},
    )
    assert unsupported.status_code == 415

    malformed = client.post(
        "/api/schedules/milestones/analyze",
        files={"file": ("bad.xer", b"ERMHDR\t1\n", "application/octet-stream")},
    )
    assert malformed.status_code == 422
