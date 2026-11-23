from datetime import datetime, timedelta

from app.comparison.engine import ScheduleComparisonEngine
from app.comparison.models import (
    MatchClassification,
    RelationshipChangeType,
    ScheduleVersion,
    ScheduleVersionType,
)
from app.models.schedule import Activity, Project, Relationship, Schedule, WBS


def dt(day: int = 1) -> datetime:
    return datetime(2026, 1, day)


def make_schedule(
    activities: list[Activity],
    relationships: list[Relationship] | None = None,
    wbs_nodes: dict[str, WBS] | None = None,
) -> Schedule:
    schedule = Schedule(
        project=Project("P1", "P1", "Project 1", dt()),
        relationships=relationships or [],
        wbs_nodes=wbs_nodes or {},
    )
    schedule.activities = {activity.activity_id: activity for activity in activities}
    schedule.rebuild_activity_indexes()
    return schedule


def activity(
    task_id: str,
    code: str,
    wbs_id: str = "W1",
    name: str | None = None,
    start: datetime | None = None,
    finish: datetime | None = None,
    original_duration: float | None = 40,
    remaining_duration: float | None = 40,
    float_hours: float | None = 10,
    status: str = "not_started",
    calendar_id: str | None = "C1",
    activity_type: str = "task",
) -> Activity:
    return Activity(
        activity_id=task_id,
        activity_code=code,
        activity_name=name or code,
        project_id="P1",
        wbs_id=wbs_id,
        planned_start=start,
        planned_finish=finish,
        original_duration_hours=original_duration,
        remaining_duration_hours=remaining_duration,
        total_float_hours=float_hours,
        free_float_hours=float_hours,
        status=status,
        calendar_id=calendar_id,
        activity_type=activity_type,
    )


def version(schedule: Schedule, label: str, kind: ScheduleVersionType) -> ScheduleVersion:
    return ScheduleVersion(
        version_id=label,
        version_label=label,
        version_type=kind,
        source_filename=f"{label}.xer",
        data_date=schedule.project.data_date,
        imported_at=dt(2),
        schedule=schedule,
    )


def wbs() -> dict[str, WBS]:
    return {
        "ROOT": WBS("ROOT", "R", "Root", None),
        "W1": WBS("W1", "S", "Systems", "ROOT"),
    }


def compare(base: Schedule, current: Schedule):
    return ScheduleComparisonEngine().compare(
        version(base, "BASE", ScheduleVersionType.BASELINE),
        version(current, "CUR", ScheduleVersionType.CURRENT),
    )


def test_identical_and_internal_task_id_changed():
    baseline = make_schedule([activity("100", "A1", name="Alpha")], wbs_nodes=wbs())
    current = make_schedule([activity("900", "A1", name="Alpha")], wbs_nodes=wbs())
    result = compare(baseline, current)
    assert result.summary.matched_activity_count == 1
    assert result.activity_variances[0].match_method.value == "ACTIVITY_CODE"


def test_duplicate_codes_resolved_by_wbs_and_ambiguous():
    baseline_wbs = {
        "ROOT": WBS("ROOT", "R", "Root", None),
        "WA": WBS("WA", "A", "Area A", "ROOT"),
        "WB": WBS("WB", "B", "Area B", "ROOT"),
    }
    current_wbs = {
        "ROOTX": WBS("ROOTX", "R", "Root", None),
        "WAX": WBS("WAX", "A", "Area A", "ROOTX"),
        "WBX": WBS("WBX", "B", "Area B", "ROOTX"),
    }
    baseline = make_schedule([
        activity("101", "DUP", "WA"), activity("102", "DUP", "WB"),
    ], wbs_nodes=baseline_wbs)
    current = make_schedule([
        activity("201", "DUP", "WAX"), activity("202", "DUP", "WBX"),
    ], wbs_nodes=current_wbs)
    result = compare(baseline, current)
    assert result.summary.matched_activity_count == 2
    assert result.summary.ambiguous_count == 0

    ambiguous_baseline = make_schedule([
        activity("101", "DUP", "WA"), activity("102", "DUP", "WA"),
    ], wbs_nodes=baseline_wbs)
    ambiguous_current = make_schedule([
        activity("201", "DUP", "WAX"), activity("202", "DUP", "WAX"),
    ], wbs_nodes=current_wbs)
    result = compare(ambiguous_baseline, ambiguous_current)
    assert result.summary.ambiguous_count == 4
    assert any(d.code == "duplicate_activity_code" for d in result.diagnostics)


def test_added_deleted_and_renamed_activities():
    baseline = make_schedule([activity("1", "OLD", name="Old")])
    current = make_schedule([activity("2", "NEW", name="New")])
    result = compare(baseline, current)
    assert result.summary.baseline_only_count == 1
    assert result.summary.current_only_count == 1


def test_wbs_status_calendar_and_type_changes():
    base_wbs = {"A": WBS("A", "A", "Area A"), "B": WBS("B", "B", "Area B")}
    cur_wbs = {"AX": WBS("AX", "A", "Area A"), "BX": WBS("BX", "B", "Area B")}
    baseline = make_schedule([activity("1", "A1", "A", status="not_started", calendar_id="C1", activity_type="task")], wbs_nodes=base_wbs)
    current = make_schedule([activity("9", "A1", "BX", status="in_progress", calendar_id="C2", activity_type="milestone")], wbs_nodes=cur_wbs)
    result = compare(baseline, current)
    variance = result.activity_variances[0]
    assert variance.name_changed is False
    assert variance.wbs_changed is True
    assert variance.status_changed is True
    assert variance.calendar_changed is True
    assert variance.activity_type_changed is True


def test_date_variance_sign_and_missing_dates():
    baseline = make_schedule([activity("1", "A1", start=dt(1), finish=dt(5))])
    later = make_schedule([activity("1", "A1", start=dt(3), finish=dt(8))])
    result = compare(baseline, later)
    variance = result.activity_variances[0]
    assert variance.start_variance_hours == 48
    assert variance.start_variance_calendar_days == 2
    assert variance.finish_variance_hours == 72
    assert variance.finish_variance_calendar_days == 3

    earlier = make_schedule([activity("1", "A1", start=dt(1) - timedelta(hours=24), finish=dt(4))])
    variance = compare(baseline, earlier).activity_variances[0]
    assert variance.start_variance_hours == -24
    assert variance.finish_variance_hours == -24

    missing = make_schedule([activity("1", "A1", start=None, finish=None)])
    variance = compare(baseline, missing).activity_variances[0]
    assert variance.start_variance_hours is None
    assert variance.finish_variance_hours is None


def test_duration_and_float_variances():
    baseline = make_schedule([activity("1", "A1", original_duration=40, remaining_duration=30, float_hours=-5)])
    recovered = make_schedule([activity("1", "A1", original_duration=48, remaining_duration=20, float_hours=10)])
    variance = compare(baseline, recovered).activity_variances[0]
    assert variance.original_duration_variance_hours == 8
    assert variance.remaining_duration_variance_hours == -10
    assert variance.total_float_variance_hours == 15
    assert variance.recovered_from_negative_float is True
    assert variance.float_improved is True

    positive_baseline = make_schedule([activity("1", "A1", float_hours=5)])
    deteriorated = make_schedule([activity("1", "A1", float_hours=-10)])
    variance = compare(positive_baseline, deteriorated).activity_variances[0]
    assert variance.became_negative_float is True
    assert variance.float_deteriorated is True
    assert variance.total_float_variance_hours == -15

    missing = make_schedule([activity("1", "A1", original_duration=None, remaining_duration=None, float_hours=None)])
    variance = compare(baseline, missing).activity_variances[0]
    assert variance.original_duration_variance_hours is None
    assert variance.remaining_duration_variance_hours is None
    assert variance.total_float_variance_hours is None


def test_relationship_changes():
    baseline = make_schedule(
        [activity("1", "A", wbs_id="W1"), activity("2", "B", wbs_id="W1")],
        [Relationship("R1", "1", "2", "FS", 0)],
        wbs(),
    )

    unchanged = make_schedule(
        [activity("10", "A", wbs_id="W1"), activity("20", "B", wbs_id="W1")],
        [Relationship("R9", "10", "20", "FS", 0)],
        wbs(),
    )
    result = compare(baseline, unchanged)
    assert not result.relationship_variances

    lagged = make_schedule(
        [activity("10", "A", wbs_id="W1"), activity("20", "B", wbs_id="W1")],
        [Relationship("R9", "10", "20", "FS", 80)],
        wbs(),
    )
    result = compare(baseline, lagged)
    assert any(r.change_type == RelationshipChangeType.LAG_CHANGED for r in result.relationship_variances)

    typed = make_schedule(
        [activity("10", "A", wbs_id="W1"), activity("20", "B", wbs_id="W1")],
        [Relationship("R9", "10", "20", "SS", 0)],
        wbs(),
    )
    result = compare(baseline, typed)
    assert any(r.change_type == RelationshipChangeType.TYPE_CHANGED for r in result.relationship_variances)


def test_relationship_added_removed_and_unmatched_endpoints():
    baseline = make_schedule([activity("1", "A"), activity("2", "B")], [Relationship("R1", "1", "2", "FS", 0)])
    removed = make_schedule([activity("1", "A"), activity("2", "B")])
    result = compare(baseline, removed)
    assert result.summary.relationships_removed == 1

    added = make_schedule([activity("1", "A"), activity("2", "B")], [Relationship("R2", "1", "2", "FS", 0)])
    empty = make_schedule([activity("1", "A"), activity("2", "B")])
    result = compare(empty, added)
    assert result.summary.relationships_added == 1


def test_malformed_wbs_diagnostic():
    malformed = make_schedule(
        [activity("1", "A", wbs_id="W1")],
        wbs_nodes={"W1": WBS("W1", "A", "Area", "W2"), "W2": WBS("W2", "B", "Back", "W1")},
    )
    result = compare(make_schedule([activity("1", "A")]), malformed)
    assert any(d.code == "malformed_wbs_ancestry" for d in result.diagnostics)


def test_end_to_end_controlled_xer_comparison():
    from datetime import timezone
    from pathlib import Path

    from app.comparison.models import ScheduleVersion, ScheduleVersionType
    from app.services.schedule_import import ScheduleImportService

    fixture_dir = Path(__file__).resolve().parents[1] / "sample_data"
    baseline_import = ScheduleImportService().import_file(fixture_dir / "sample_baseline.xer")
    current_import = ScheduleImportService().import_file(fixture_dir / "sample_current.xer")

    assert baseline_import.succeeded and current_import.succeeded
    assert baseline_import.schedule is not None
    assert current_import.schedule is not None

    baseline = ScheduleVersion(
        "BL0", "BL0", ScheduleVersionType.BASELINE,
        "sample_baseline.xer", baseline_import.schedule.project.data_date,
        datetime.now(timezone.utc), baseline_import.schedule,
    )
    current = ScheduleVersion(
        "CURRENT", "CURRENT", ScheduleVersionType.CURRENT,
        "sample_current.xer", current_import.schedule.project.data_date,
        datetime.now(timezone.utc), current_import.schedule,
    )

    result = compare(baseline_import.schedule, current_import.schedule) if False else ScheduleComparisonEngine().compare(baseline, current)
    assert result.summary.matched_activity_count == 6
    assert result.summary.baseline_only_count == 1
    assert result.summary.current_only_count == 1
    assert result.summary.ambiguous_count == 0

    by_code = {v.activity_code: v for v in result.activity_variances}
    assert by_code["A1500"].classification == MatchClassification.BASELINE_ONLY
    assert by_code["A1700"].classification == MatchClassification.CURRENT_ONLY
    assert by_code["A1200"].name_changed is True
    assert by_code["A1300"].wbs_changed is True
    assert by_code["A1200"].finish_variance_hours == 168
    assert by_code["A1200"].finish_variance_calendar_days == 7
    assert by_code["A1200"].original_duration_variance_hours == 40
    assert by_code["A1200"].remaining_duration_variance_hours == 40
    assert by_code["A1200"].total_float_variance_hours == -56
    assert by_code["A1200"].became_negative_float is True

    relationship_changes = {
        (r.predecessor_activity_code, r.successor_activity_code, r.change_type): r
        for r in result.relationship_variances
    }
    assert relationship_changes[("A1100", "A1200", RelationshipChangeType.TYPE_CHANGED)].baseline_relationship_type == "FS"
    assert relationship_changes[("A1100", "A1200", RelationshipChangeType.TYPE_CHANGED)].current_relationship_type == "SS"
    assert relationship_changes[("A1100", "A1200", RelationshipChangeType.LAG_CHANGED)].baseline_lag_hours == 0
    assert relationship_changes[("A1100", "A1200", RelationshipChangeType.LAG_CHANGED)].current_lag_hours == 40
    lag_1200_1300 = relationship_changes[("A1200", "A1300", RelationshipChangeType.LAG_CHANGED)]
    assert lag_1200_1300.baseline_lag_hours == 0
    assert lag_1200_1300.current_lag_hours == 16
    assert ("A1600", "A1700", RelationshipChangeType.ADDED) in relationship_changes


def test_comparison_api_controlled_xer():
    from pathlib import Path
    from fastapi.testclient import TestClient

    from app.main import app

    fixture_dir = Path(__file__).resolve().parents[1] / "sample_data"
    client = TestClient(app)
    response = client.post(
        "/api/schedules/compare",
        files={
            "baseline": ("sample_baseline.xer", (fixture_dir / "sample_baseline.xer").read_bytes(), "application/octet-stream"),
            "current": ("sample_current.xer", (fixture_dir / "sample_current.xer").read_bytes(), "application/octet-stream"),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comparison_summary"]["matched_activity_count"] == 6
    assert body["comparison_summary"]["baseline_only_count"] == 1
    assert body["comparison_summary"]["current_only_count"] == 1


def test_comparison_api_rejects_extensions_and_malformed_xer():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    unsupported = client.post(
        "/api/schedules/compare",
        files={
            "baseline": ("baseline.txt", b"bad", "text/plain"),
            "current": ("current.txt", b"bad", "text/plain"),
        },
    )
    assert unsupported.status_code == 415

    malformed = client.post(
        "/api/schedules/compare",
        files={
            "baseline": ("malformed.xer", b"ERMHDR\t1\n", "application/octet-stream"),
            "current": ("sample_current.xer", b"ERMHDR\t1\n", "application/octet-stream"),
        },
    )
    assert malformed.status_code == 422
