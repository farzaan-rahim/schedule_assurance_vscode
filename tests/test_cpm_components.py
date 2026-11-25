"""Scoped calculations never invent boundaries across excluded network logic."""
from copy import deepcopy
from datetime import datetime

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule


def run(items, links=(), **kwargs):
    schedule = make_schedule(items, list(links))
    snapshot = deepcopy(schedule)
    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig(component_calculation_policy="VALID_COMPONENTS", **kwargs))
    assert schedule == snapshot
    return result


def states(result):
    return {a.activity_id: a.status for a in result.activity_calculability}


@pytest.mark.parametrize("raw_type", ["TT_LOE", "TT_WBS"])
def test_isolated_informational_exclusion_does_not_block_work(raw_type):
    excluded = activity("X", "X", 100)
    excluded.raw_activity_type = raw_type
    r = run([excluded, activity("A", "A", 2)])
    assert r.status == "CALCULATED"
    assert states(r) == {"A": "CALCULATED", "X": "EXCLUDED"}
    assert len(r.comparisons) == 1
    assert r.relationship_count == 0


@pytest.mark.parametrize("direction", [False, True])
@pytest.mark.parametrize("raw_type", ["TT_LOE", "TT_WBS"])
def test_incident_exclusion_blocks_whole_dependency_component_only(raw_type, direction):
    excluded = activity("X", "X", 100)
    excluded.raw_activity_type = raw_type
    links = [Relationship("R1", "X" if direction else "A", "A" if direction else "X", "FS", 0), Relationship("R2", "A", "B", "FS", 0)]
    r = run([excluded, activity("A", "A", 2), activity("B", "B", 2), activity("C", "C", 3)], links)
    assert r.status == "PARTIALLY_CALCULATED"
    assert states(r) == {"A": "BLOCKED", "B": "BLOCKED", "C": "CALCULATED", "X": "EXCLUDED"}
    assert [a.activity_id for a in r.activity_results] == ["C"]
    assert len(r.comparisons) == 1
    assert r.blocked_activity_count == 2
    assert all(a.status == "BLOCKED" for a in r.relationship_calculability)
    assert r.completion_anchor is None and r.calculated_completion is None
    assert all(c.reason_codes for c in r.components if c.status == "BLOCKED")


def test_invalid_duration_does_not_poison_unrelated_component():
    bad = activity("X", "X", -2)
    r = run([bad, activity("A", "A", 2)])
    assert states(r) == {"A": "CALCULATED", "X": "BLOCKED"}
    assert any(d.code == "negative_duration" for d in r.diagnostics)


def test_unknown_constraint_does_not_turn_into_a_warning_or_fake_bound():
    bad = activity("X", "X", 2)
    bad.primary_constraint_type = "MANDATORY_START"
    bad.primary_constraint_date = datetime(2026, 1, 6, 12)
    r = run([bad, activity("A", "A", 2)])
    assert states(r) == {"A": "CALCULATED", "X": "BLOCKED"}
    assert any(d.code == "unsupported_constraint" and d.severity.value == "ERROR" for d in r.diagnostics)


def test_cycle_blocks_only_its_component_iteratively():
    r = run([activity(k, k, 2) for k in "ABC"], [Relationship("R1", "A", "B", "FS", 0), Relationship("R2", "B", "A", "FS", 0)])
    assert states(r) == {"A": "BLOCKED", "B": "BLOCKED", "C": "CALCULATED"}
    assert any(d.code == "circular_component" for d in r.diagnostics)


def test_missing_endpoint_blocks_connected_work_only():
    r = run([activity(k, k, 2) for k in "AC"], [Relationship("R1", "MISSING", "A", "FS", 0)])
    assert states(r) == {"A": "BLOCKED", "C": "CALCULATED"}


@pytest.mark.parametrize("source", ["expected_finish", "progress"])
def test_unconfirmed_p6_conditions_are_component_blocks(source):
    a = activity("A", "A", 2)
    if source == "expected_finish":
        a.expected_finish = datetime(2026, 1, 6, 12)
    else:
        a.raw_status = "TK_Active"
        a.actual_start = datetime(2026, 1, 2, 8)
    # Progress evidence here is specifically positive SS expired-lag behavior.
    link = Relationship("R", "A", "B", "SS" if source == "progress" else "FS", 1 if source == "progress" else 0)
    r = run([a, activity("B", "B", 2), activity("C", "C", 2)], [link])
    assert states(r) == {"A": "BLOCKED", "B": "BLOCKED", "C": "CALCULATED"}
    code = "unconfirmed_expected_finish" if source == "expected_finish" else "unconfirmed_progress_methodology"
    assert any(d.code == code for d in r.diagnostics)


def test_no_valid_component_returns_no_dates_or_comparisons():
    a = activity("A", "A", -2)
    r = run([a])
    assert r.status == "BLOCKED"
    assert not r.activity_results and not r.comparisons


def test_empty_remaining_population_is_excluded():
    a = activity("A", "A", 2)
    a.raw_activity_type = "TT_LOE"
    r = run([a])
    assert r.status == "EXCLUDED"
    assert states(r) == {"A": "EXCLUDED"}


def test_shared_implicit_project_finish_cannot_ignore_a_blocked_component():
    r = run([activity("A", "A", -2), activity("B", "B", 2)], disconnected_component_policy="PROJECT_FINISH")
    assert r.status == "BLOCKED"
    assert not r.activity_results
    assert any(d.code == "unknown_shared_finish_anchor" for d in r.diagnostics)


def test_explicit_required_finish_is_a_valid_independent_bound():
    r = run([activity("A", "A", -2), activity("B", "B", 2)], required_project_finish=datetime(2026, 1, 6, 12))
    assert states(r) == {"A": "BLOCKED", "B": "CALCULATED"}
    assert r.activity_results[0].calculated_late_finish == datetime(2026, 1, 6, 12)


def test_repeated_component_results_are_deterministic():
    items = [activity("A", "A", -2), activity("B", "B", 2)]
    first = run(items)
    second = run(items)
    assert first == second


def test_historical_actual_relationship_failure_is_scoped_before_float():
    a = activity("A", "A", 0, status="TK_Complete")
    b = activity("B", "B", 0, status="TK_Complete")
    a.actual_start = a.actual_finish = datetime(2026, 1, 2, 10)
    b.actual_start = b.actual_finish = datetime(2026, 1, 2, 9)
    r = run([a, b, activity("C", "C", 2)], [Relationship("R", "A", "B", "FS", 0)])
    assert states(r) == {"A": "BLOCKED", "B": "BLOCKED", "C": "CALCULATED"}
    assert any(d.code == "unsupported_calendar_relationship_boundary" for d in r.diagnostics)

@pytest.mark.parametrize("failure", ["timezone", "data_date", "configuration"])
def test_global_input_failures_do_not_escape_as_partial_calculations(failure):
    from datetime import timezone
    a = activity("A", "A", 2)
    a.raw_status = "TK_Active"
    a.actual_start = datetime(2026, 1, 2, 8)
    schedule = make_schedule([a, activity("B", "B", 2)], [])
    kwargs = {}
    if failure == "timezone":
        a.actual_start = a.actual_start.replace(tzinfo=timezone.utc)
    elif failure == "data_date":
        schedule.project.data_date = None
    else:
        kwargs["lag_calendar_policy"] = "UNKNOWN"
    result = CPMService().calculate(schedule, ScheduleGraph(schedule), CPMConfig(component_calculation_policy="VALID_COMPONENTS", **kwargs))
    assert result.status == "BLOCKED"
    assert all(a.status == "BLOCKED" for a in result.activity_calculability)
    assert not result.activity_results


def test_deep_component_quarantine_is_iterative_and_keeps_unrelated_work():
    items = [activity(str(i), str(i), 1) for i in range(1101)]
    items[0].raw_activity_type = "TT_LOE"
    links = [Relationship(str(i), str(i), str(i+1), "FS", 0) for i in range(1100)]
    result = run(items + [activity("SAFE", "SAFE", 2)], links)
    assert result.status == "PARTIALLY_CALCULATED"
    assert result.blocked_activity_count == 1100
    assert result.excluded_activity_count == 1
    assert [a.activity_id for a in result.activity_results] == ["SAFE"]


def test_empty_schedule_does_not_look_like_a_successful_exclusion():
    result = run([])
    assert result.status == "BLOCKED"
    assert any(d.code == "no_eligible_activities" for d in result.diagnostics)


def test_unresolved_relationship_does_not_disappear_from_overall_status():
    result = run([activity("A", "A", 2)], [Relationship("R", "MISSING1", "MISSING2", "FS", 0)])
    assert result.status == "PARTIALLY_CALCULATED"
    assert states(result) == {"A": "CALCULATED"}
    assert result.relationship_calculability[0].status == "BLOCKED"
    assert result.completion_anchor is None

@pytest.mark.parametrize("linked", [False, True])
def test_progress_without_unconfirmed_logic_is_not_a_component_block(linked):
    a = activity("A", "A", 2)
    a.raw_status = "TK_Active"
    a.actual_start = datetime(2026, 1, 2, 8)
    b = activity("B", "B", 2)
    result = run([a, b], [Relationship("R", "A", "B", "FS", 0)] if linked else [])
    assert result.status == "CALCULATED"
    assert all(v.status == "CALCULATED" for v in result.activity_calculability)
    assert any(d.code == "progress_policy_capability" for d in result.comparison_diagnostics)
