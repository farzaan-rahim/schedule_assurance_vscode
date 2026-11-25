"""Proprietary-free remaining-work progress and directional availability cases."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime

import pytest

from app.cpm.config import CPMConfig
from app.cpm.service import CPMService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from app.models.scheduling_options import P6SchedulingOptions
from tests.test_cpm import activity, make_schedule

DD = datetime(2026, 1, 5, 8)


def options(**changes):
    return replace(P6SchedulingOptions('P1', retained_logic=True, progress_override=False,
                   ss_lag_from_early_start=True, use_expected_finish=True,
                   lag_calendar_policy='PREDECESSOR', external_relationship_policy='BOTH'), **changes)


def active(code, duration=2, actual=datetime(2026, 1, 2, 8)):
    a = activity(code, code, duration, status='TK_Active')
    a.actual_start = actual
    return a


def complete(code, start=datetime(2026, 1, 2, 8), finish=datetime(2026, 1, 2, 16)):
    a = activity(code, code, 0, status='TK_Complete')
    a.actual_start, a.actual_finish = start, finish
    return a


def run(items, links=(), setting=None, **config):
    s = make_schedule(items, list(links))
    s.scheduling_options = setting or options()
    snapshot = deepcopy(s)
    result = CPMService().calculate(s, ScheduleGraph(s), CPMConfig(
        component_calculation_policy='DIRECTIONAL_FORWARD', progress_scheduling_policy='P6_RETAINED_LOGIC', **config))
    assert s == snapshot
    return result


def rows(result):
    return {r.activity_id: r for r in result.activity_results}


def availability(result):
    return {a.activity_id: a for a in result.activity_calculability}


def test_fs_started_successor_keeps_actual_segment_and_retains_remaining_logic():
    p = activity('P', 'P', 4)
    q = active('Q', 2)
    result = run([p, q], [Relationship('R', 'P', 'Q', 'FS', 0)])
    q_result = rows(result)['Q']
    assert q_result.calculated_early_start == datetime(2026, 1, 5, 12)
    assert q_result.calculated_early_finish == datetime(2026, 1, 5, 14)
    assert q_result.imported_actual_start == datetime(2026, 1, 2, 8)
    assert q_result.progress_state.actual_start == q.actual_start
    assert q_result.progress_state.actual_finish is None
    assert q_result.progress_state.observed_through == DD
    assert q_result.progress_state.remaining_duration_hours == 2
    assert q_result.calculated_late_start is None and q_result.calculated_total_float_hours is None


@pytest.mark.parametrize('lag,expected', [(0, DD), (4, datetime(2026, 1, 5, 11))])
def test_completed_predecessor_lag_partly_consumed_before_data_date(lag, expected):
    result = run([complete('P'), active('Q')], [Relationship('R', 'P', 'Q', 'FS', lag)])
    assert rows(result)['Q'].calculated_early_start == expected


def test_incomplete_predecessor_remains_after_data_date_and_controls_successor():
    result = run([active('P', 6), active('Q')], [Relationship('R', 'P', 'Q', 'FS', 2)])
    assert rows(result)['P'].calculated_early_finish == datetime(2026, 1, 5, 14)
    assert rows(result)['Q'].calculated_early_start == datetime(2026, 1, 5, 16)
    assert rows(result)['Q'].calculated_early_finish == datetime(2026, 1, 6, 9)


@pytest.mark.parametrize('started_successor', [False, True])
@pytest.mark.parametrize('lag,expected', [(2, DD), (5, datetime(2026, 1, 5, 11))])
def test_progressed_ss_uses_expired_calendar_lag(started_successor, lag, expected):
    p = active('P', 6, datetime(2026, 1, 2, 15))  # two work hours before DD
    q = active('Q') if started_successor else activity('Q', 'Q', 2)
    result = run([p, q], [Relationship('R', 'P', 'Q', 'SS', lag)])
    assert rows(result)['Q'].calculated_early_start == expected
    detail = result.relationship_calculability[0]
    assert detail.expired_lag_hours == 2
    assert detail.remaining_lag_hours == lag - 2


def test_progressed_ss_uses_calculated_predecessor_eligibility_not_imported_restart():
    p = active('P', 6, datetime(2026, 1, 2, 15))
    p.primary_constraint_type = 'START_ON_OR_AFTER'
    p.primary_constraint_date = datetime(2026, 1, 6, 10)
    p.remaining_start = datetime(2026, 1, 20, 8)  # imported evidence, not a hidden bound
    result = run([p, active('Q')], [Relationship('R', 'P', 'Q', 'SS', 5)])
    assert rows(result)['Q'].calculated_early_start == datetime(2026, 1, 6, 13)
    assert rows(result)['P'].progress_state.imported_remaining_start == p.remaining_start


def test_multiple_predecessors_retain_maximum_remaining_requirement():
    result = run([activity('P', 'P', 4), activity('R', 'R', 6), active('Q')],
                 [Relationship('1', 'P', 'Q', 'FS', 0), Relationship('2', 'R', 'Q', 'FS', 0)])
    assert rows(result)['Q'].calculated_early_start == datetime(2026, 1, 5, 14)
    assert rows(result)['Q'].controlling_predecessor_ids == ('R',)


def test_completed_successor_preserves_history_without_retaining_nonexistent_work():
    q = complete('Q')
    result = run([activity('P', 'P', 6), q], [Relationship('R', 'P', 'Q', 'FS', 0)])
    assert rows(result)['Q'].calculated_early_start == q.actual_start
    assert rows(result)['Q'].calculated_early_finish == q.actual_finish
    assert result.relationship_calculability[0].forward_status == 'HISTORICAL_ONLY'
    assert len(result.schedule.relationships) == 1


def test_loe_sink_does_not_block_normal_early_dates_or_fabricate_late_dates():
    loe = activity('L', 'L', 100)
    loe.raw_activity_type = 'TT_LOE'
    result = run([activity('A', 'A', 2), loe], [Relationship('R', 'A', 'L', 'FS', 0)])
    assert rows(result)['A'].calculated_early_finish == datetime(2026, 1, 5, 10)
    assert 'L' not in rows(result)
    assert availability(result)['A'].early_date_status == 'EARLY_DATES_CALCULATED'
    assert availability(result)['A'].late_date_status == 'LATE_DATES_BLOCKED'
    assert availability(result)['A'].float_status == 'FLOAT_BLOCKED'
    assert rows(result)['A'].calculated_late_finish is None


def test_loe_predecessor_blocks_only_unfinished_downstream():
    loe = activity('L', 'L', 100)
    loe.raw_activity_type = 'TT_LOE'
    result = run([activity('A', 'A', 2), loe, activity('B', 'B', 2), activity('C', 'C', 2)],
                 [Relationship('1', 'A', 'L', 'FS', 0), Relationship('2', 'L', 'B', 'FS', 0), Relationship('3', 'B', 'C', 'FS', 0)])
    assert set(rows(result)) == {'A'}
    assert availability(result)['B'].early_date_status == 'EARLY_DATES_BLOCKED'
    assert availability(result)['C'].early_date_status == 'EARLY_DATES_BLOCKED'


@pytest.mark.parametrize('enabled', [True, False, None])
def test_expected_finish_enabled_unknown_blocks_but_disabled_preserves_only(enabled):
    a = activity('A', 'A', 2)
    a.expected_finish = datetime(2026, 1, 9, 17)
    result = run([a, activity('B', 'B', 2), activity('C', 'C', 2)], [Relationship('R', 'A', 'B', 'FS', 0)], setting=options(use_expected_finish=enabled))
    assert set(rows(result)) == ({'A', 'B', 'C'} if enabled is False else {'C'})
    assert len(result.comparisons) == (3 if enabled is False else 1)
    assert all(m.name in {'early_start', 'early_finish'} for c in result.comparisons for m in c.metrics)


def test_forward_only_does_not_call_backward_float_or_paths(monkeypatch):
    from app.cpm import service
    def forbidden(*args, **kwargs):
        raise AssertionError('Forward availability must not require late/float/path calculation')
    monkeypatch.setattr(service, 'backward_pass', forbidden)
    monkeypatch.setattr(service, 'total_float', forbidden)
    result = run([activity('A', 'A', 2)])
    assert rows(result)['A'].calculated_early_finish == datetime(2026, 1, 5, 10)
    assert result.completion_anchor is None and not result.critical_paths
    assert result.project_finish_anchor is None


def test_progress_override_is_not_activated():
    result = run([active('A')], setting=options(retained_logic=False, progress_override=True))
    assert not result.activity_results
    assert any(d.code == 'unsupported_p6_progress_options' for d in result.diagnostics)


def test_unsupported_ss_option_blocks_relationship_direction_not_predecessor():
    result = run([active('A'), activity('B', 'B', 2)], [Relationship('R', 'A', 'B', 'SS', 5)], setting=options(ss_lag_from_early_start=False))
    assert set(rows(result)) == {'A'}
    assert result.relationship_calculability[0].forward_status == 'FORWARD_BLOCKED'


def test_cycle_does_not_poison_unrelated_forward_work():
    result = run([activity(c, c, 2) for c in 'ABC'], [Relationship('1', 'A', 'B', 'FS', 0), Relationship('2', 'B', 'A', 'FS', 0)])
    assert set(rows(result)) == {'C'}


def test_deep_forward_calculation_is_iterative_and_deterministic():
    items = [activity(str(i), str(i), 1) for i in range(1101)]
    links = [Relationship(str(i), str(i), str(i+1), 'FS', 0) for i in range(1100)]
    first, second = run(items, links), run(items, links)
    assert len(first.activity_results) == 1101
    assert first == second


def test_forward_date_before_data_date_is_rejected_even_if_duration_matches(monkeypatch):
    from app.cpm import directional
    original = directional.forward_pass
    def damaged(*args, **kwargs):
        result = original(*args, **kwargs)
        result['early_starts']['A'] = datetime(2026, 1, 2, 8)
        result['early_finishes']['A'] = datetime(2026, 1, 2, 10)
        return result
    monkeypatch.setattr(directional, 'forward_pass', damaged)
    result = run([activity('A', 'A', 2)])
    assert not result.activity_results
    assert any(d.code == 'early_date_invariant_failed' for d in result.diagnostics)


def test_observed_canonical_options_are_not_reported_as_unobserved():
    result = run([activity('A', 'A', 2)])
    hints = {d.code: d for d in result.comparison_diagnostics}
    assert 'p6_scheduling_options_unobserved' not in hints
    assert hints['p6_scheduling_options_observed'].metadata['evidence']['retained_logic'] is True


@pytest.mark.parametrize('fault', ['timezone', 'data_date', 'empty'])
def test_directional_global_failures_remain_blocked(fault):
    from datetime import timezone
    s = make_schedule([] if fault == 'empty' else [active('A')], [])
    s.scheduling_options = options()
    if fault == 'timezone':
        s.activities['A'].actual_start = datetime(2026, 1, 2, 8, tzinfo=timezone.utc)
    if fault == 'data_date':
        s.project.data_date = None
    r = CPMService().calculate(s, ScheduleGraph(s), CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD', progress_scheduling_policy='P6_RETAINED_LOGIC'))
    assert r.status == 'BLOCKED' and not r.activity_results


def test_completed_actuals_survive_but_do_not_erase_excluded_boundary_uncertainty():
    loe = activity('L', 'L', 100)
    loe.raw_activity_type = 'TT_LOE'
    result = run([loe, complete('H'), activity('A', 'A', 2)], [Relationship('1', 'L', 'H', 'FS', 0), Relationship('2', 'H', 'A', 'FS', 0)])
    assert set(rows(result)) == {'H'}
    assert availability(result)['H'].forward_boundary_status == 'FORWARD_BOUNDARY_BLOCKED'
    assert len(result.schedule.relationships) == 2


def test_new_progress_policy_does_not_silently_enable_old_backward_pass():
    s = make_schedule([active('A')], [])
    s.scheduling_options = options()
    r = CPMService().calculate(s, ScheduleGraph(s), CPMConfig(progress_scheduling_policy='P6_RETAINED_LOGIC'))
    assert r.status == 'FAILED'
    assert any(d.code == 'unsupported_progress_scope' for d in r.diagnostics)

@pytest.mark.parametrize('fault', ['original_preference', 'missing_remaining'])
def test_retained_work_does_not_invent_remaining_hours_from_original(fault):
    a = active('A', 2)
    config = {}
    if fault == 'original_preference':
        config['remaining_duration_preference'] = False
    else:
        a.remaining_duration_hours = None
    result = run([a], **config)
    assert not result.activity_results
    assert any(d.code == 'unsupported_retained_duration_policy' for d in result.diagnostics)


@pytest.mark.parametrize('lag,start,finish', [(0, 10, 12), (1, 11, 13)])
def test_ff_progress_uses_remaining_duration_and_keeps_history(lag, start, finish):
    result = run([activity('P', 'P', 4), active('Q', 2)], [Relationship('R', 'P', 'Q', 'FF', lag)])
    q = rows(result)['Q']
    assert q.calculated_early_start == datetime(2026, 1, 5, start)
    assert q.calculated_early_finish == datetime(2026, 1, 5, finish)
    assert q.imported_actual_start == datetime(2026, 1, 2, 8)


def test_progressed_sf_is_explicitly_blocked_only_in_forward_dependency():
    result = run([active('P'), activity('Q', 'Q', 2)], [Relationship('R', 'P', 'Q', 'SF', 0)])
    assert set(rows(result)) == {'P'}
    assert any(d.code == 'unsupported_progressed_sf' for d in result.diagnostics)


@pytest.mark.parametrize('holiday,day', [(False, 5), (True, 6)])
def test_ss_expired_lag_uses_split_shifts_and_holiday_engine(holiday, day):
    from datetime import date, time
    from app.calendars.models import CalendarException, WorkPeriod
    from tests.test_cpm import make_calendar
    s = make_schedule([active('P', 6, datetime(2026, 1, 2, 11)), activity('Q', 'Q', 2)], [Relationship('R', 'P', 'Q', 'SS', 7)])
    s.scheduling_options = options()
    s.calendars['C1'] = make_calendar(periods=(WorkPeriod(time(8), time(12)), WorkPeriod(time(13), time(17))), exceptions=(CalendarException(date(2026, 1, 5), False),) if holiday else ())
    snapshot = deepcopy(s)
    result = CPMService().calculate(s, ScheduleGraph(s), CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD', progress_scheduling_policy='P6_RETAINED_LOGIC'))
    assert s == snapshot
    assert rows(result)['Q'].calculated_early_start == datetime(2026, 1, day, 10)
    assert rows(result)['Q'].calculated_early_finish == datetime(2026, 1, day, 12)
    assert result.relationship_calculability[0].expired_lag_hours == 5


def test_forward_only_does_not_claim_to_apply_a_late_finish_constraint():
    a = activity('A', 'A', 2)
    a.primary_constraint_type = 'FINISH_ON_OR_BEFORE'
    a.primary_constraint_date = datetime(2026, 1, 2, 12)
    result = run([a])
    q = rows(result)['A']
    assert q.calculated_early_start == DD
    assert q.calculated_late_finish is None
    assert 'FINISH_ON_OR_BEFORE' not in q.applied_constraints


def test_directional_availability_keeps_actual_component_identity():
    result = run([activity('A', 'A', 2), activity('B', 'B', 2)], [Relationship('R', 'A', 'B', 'FS', 0)])
    assert availability(result)['A'].component_id == availability(result)['B'].component_id
    assert len(result.components) == 1
    assert result.components[0].activity_count == 2
    assert result.components[0].status == 'PARTIALLY_CALCULATED'

@pytest.mark.parametrize('unknown_source', [False, True])
def test_completed_history_does_not_certify_an_unimplemented_retained_release(unknown_source):
    p = active('P', 4)
    if unknown_source:
        p.expected_finish = datetime(2026, 1, 9, 17)
    h = complete('H')
    c = activity('C', 'C', 2)
    result = run([p, h, c], [Relationship('1', 'P', 'H', 'FS', 0), Relationship('2', 'H', 'C', 'FS', 0)])
    assert rows(result)['H'].calculated_early_finish == h.actual_finish
    assert 'C' not in rows(result)
    assert availability(result)['H'].early_date_status == 'EARLY_DATES_CALCULATED'
    assert availability(result)['H'].forward_boundary_status == 'FORWARD_BOUNDARY_BLOCKED'
    assert any(d.code == 'completed_retained_boundary_unimplemented' for d in result.diagnostics)


def test_completed_fs_predecessor_lag_audit_reports_already_consumed_work():
    result = run([complete('P'), active('Q')], [Relationship('R', 'P', 'Q', 'FS', 4)])
    detail = result.relationship_calculability[0]
    assert detail.expired_lag_hours == 1
    assert detail.remaining_lag_hours == 3
    assert rows(result)['Q'].calculated_early_start == datetime(2026, 1, 5, 11)
