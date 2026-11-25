"""Manually checked, proprietary-free Phase 6C constraint and exclusion cases."""
from copy import deepcopy
from datetime import datetime

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule


def calculate(items, relationships=(), **options):
    schedule = make_schedule(items, list(relationships))
    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig(**options))
    return schedule, result


@pytest.mark.parametrize("slot", ["primary", "secondary"])
@pytest.mark.parametrize("kind,date,field,expected", [
    ("FINISH_ON_OR_AFTER", datetime(2026, 1, 6, 12), "calculated_early_start", datetime(2026, 1, 6, 10)),
    ("START_ON_OR_BEFORE", datetime(2026, 1, 6, 10), "calculated_late_finish", datetime(2026, 1, 6, 12)),
])
def test_constraint_bounds_in_both_slots(slot, kind, date, field, expected):
    a = activity("A", "A", 2)
    setattr(a, slot + "_constraint_type", kind)
    setattr(a, slot + "_constraint_date", date)
    _, result = calculate([a], required_project_finish=datetime(2026, 1, 7, 17))
    assert result.status == "CALCULATED"
    value = result.activity_results[0]
    assert getattr(value, field) == expected
    assert any(c.constraint_type == kind for c in value.controlling_constraints)


def test_finish_lower_bound_in_weekend_uses_exact_inverse():
    a = activity("A", "A", 2)
    a.primary_constraint_type = "FINISH_ON_OR_AFTER"
    a.primary_constraint_date = datetime(2026, 1, 10, 12)  # Saturday
    _, result = calculate([a])
    assert result.status == "CALCULATED"
    value = result.activity_results[0]
    # Friday 15:00 finishes Friday 17:00, before the raw Saturday bound.
    assert value.calculated_early_start == datetime(2026, 1, 9, 15, 0, 0, 1)
    assert value.calculated_early_finish == datetime(2026, 1, 12, 8, 0, 0, 1)


def test_start_upper_bound_in_weekend_uses_exact_inverse():
    a = activity("A", "A", 2)
    a.primary_constraint_type = "START_ON_OR_BEFORE"
    a.primary_constraint_date = datetime(2026, 1, 10, 12)
    _, result = calculate([a], required_project_finish=datetime(2026, 1, 13, 17))
    assert result.status == "CALCULATED"
    value = result.activity_results[0]
    assert value.calculated_late_finish == datetime(2026, 1, 12, 9, 59, 59, 999999)
    assert value.calculated_late_start == datetime(2026, 1, 9, 16, 59, 59, 999999)


@pytest.mark.parametrize("duration", [0, 2])
@pytest.mark.parametrize("conflict", [False, True])
def test_dual_constraints_preserved_and_conflict_diagnosed(duration, conflict):
    a = activity("A", "A", duration)
    a.primary_constraint_type = "FINISH_ON_OR_AFTER"
    a.primary_constraint_date = datetime(2026, 1, 7, 12)
    a.secondary_constraint_type = "FINISH_ON_OR_BEFORE"
    a.secondary_constraint_date = datetime(2026, 1, 6 if conflict else 8, 12)
    _, result = calculate([a])
    assert result.status == "CALCULATED"
    value = result.activity_results[0]
    assert value.calculated_early_finish == datetime(2026, 1, 7, 12)
    assert value.calculated_late_finish == min(value.calculated_early_finish, a.secondary_constraint_date)
    assert (value.calculated_total_float_hours < 0) == conflict
    assert any(d.code == "conflicting_constraint_window" for d in result.diagnostics) == conflict
    assert set(value.applied_constraints) == {"FINISH_ON_OR_AFTER", "FINISH_ON_OR_BEFORE"}


@pytest.mark.parametrize("kind", ["MANDATORY_START", "MANDATORY_FINISH"])
def test_mandatory_constraint_never_becomes_soft_bound(kind):
    a = activity("A", "A", 2)
    a.primary_constraint_type = kind
    a.primary_constraint_date = datetime(2026, 1, 6, 12)
    _, result = calculate([a])
    assert result.status == "FAILED"
    assert any(d.code == "unsupported_constraint" for d in result.diagnostics)


def test_isolated_wbs_summary_excluded_and_preserved():
    a = activity("S", "Summary", 100)
    a.raw_activity_type = "TT_WBS"
    schedule, result = calculate([a, activity("A", "A", 2)])
    assert result.status == "CALCULATED"
    assert result.excluded_activity_count == 1
    assert [v.activity_id for v in result.activity_results] == ["A"]
    assert schedule.activities["S"].original_duration_hours == 100
    assert any(d.code == "wbs_summary_not_scheduled" for d in result.diagnostics)


def test_linked_wbs_summary_still_blocks_strict_calculation():
    a = activity("S", "Summary", 100)
    a.raw_activity_type = "TT_WBS"
    _, result = calculate([a, activity("A", "A", 2)], [Relationship("R", "S", "A", "FS", 0)])
    assert result.status == "FAILED"
    assert not result.activity_results


def test_historical_planned_fields_do_not_schedule_remaining_work():
    a = activity("A", "A", 2, status="TK_Active", start=datetime(2025, 12, 1, 8), finish=datetime(2025, 12, 2, 17))
    a.actual_start = datetime(2025, 12, 1, 8)
    snapshot = deepcopy(a)
    schedule, result = calculate([a])
    assert result.status == "CALCULATED"
    assert result.activity_results[0].calculated_early_start == datetime(2026, 1, 5, 8)
    assert schedule.activities["A"] == snapshot
    finding = next(d for d in result.diagnostics if d.code == "planned_start_before_data_date")
    assert finding.severity.value == "INFORMATIONAL"

@pytest.mark.parametrize("kind", ["FINISH_ON_OR_AFTER", "START_ON_OR_BEFORE"])
def test_new_constraints_do_not_reschedule_completed_actuals(kind):
    a = activity("A", "A", 0, status="TK_Complete")
    a.actual_start = datetime(2026, 1, 2, 8)
    a.actual_finish = datetime(2026, 1, 2, 10)
    a.primary_constraint_type = kind
    a.primary_constraint_date = datetime(2026, 1, 6, 12)
    _, result = calculate([a])
    assert result.status == "CALCULATED"
    v = result.activity_results[0]
    assert (v.calculated_early_start, v.calculated_early_finish) == (a.actual_start, a.actual_finish)
    assert v.calculated_total_float_hours is None
    assert any(d.code == "historical_constraint_not_applied" for d in result.diagnostics)


def test_unusable_calendar_with_constraint_returns_diagnostic():
    from dataclasses import replace
    a = activity("A", "A", 2)
    a.primary_constraint_type = "FINISH_ON_OR_AFTER"
    a.primary_constraint_date = datetime(2026, 1, 6, 12)
    schedule = make_schedule([a], [])
    cal = schedule.calendars["C1"]
    cal.weekly_pattern = replace(cal.weekly_pattern, days=())
    result = CPMService().calculate(schedule, ScheduleGraph(schedule))
    assert result.status == "FAILED"
    assert any(d.code == "unusable_activity_calendar" for d in result.diagnostics)


def test_new_early_bound_audit_withholds_float_if_pass_ignores_constraint(monkeypatch):
    from app.cpm import service
    original = service.forward_pass
    def invalid_forward(*args):
        result = original(*args)
        result["early_starts"]["A"] = datetime(2026, 1, 5, 8)
        result["early_finishes"]["A"] = datetime(2026, 1, 5, 10)
        return result
    monkeypatch.setattr(service, "forward_pass", invalid_forward)
    a = activity("A", "A", 2)
    a.primary_constraint_type = "FINISH_ON_OR_AFTER"
    a.primary_constraint_date = datetime(2026, 1, 6, 12)
    _, result = calculate([a])
    assert result.status == "FAILED" and not result.activity_results
    assert any(d.code == "date_invariant_failed" for d in result.diagnostics)

@pytest.mark.parametrize("raw_type", ["TT_WBS", "TT_LOE"])
def test_isolated_excluded_information_does_not_require_a_work_calendar(raw_type):
    a = activity("X", "X", 2, calendar_id=None)
    a.raw_activity_type = raw_type
    _, result = calculate([a, activity("A", "A", 2)])
    assert result.status == "CALCULATED"
    assert result.excluded_activity_count == 1
    assert [v.activity_id for v in result.activity_results] == ["A"]
