from datetime import datetime

import pytest

from app.importers.schedule_mapper import ScheduleMapper
from app.importers.xer_parser import XERParser


def test_xer_preserves_scheduling_options_table(tmp_path):
    p = tmp_path / 'options.xer'
    p.write_text('ERMHDR\t26.5\n%T\tSCHEDOPTIONS\n%F\tproj_id\tsched_retained_logic\tsched_progress_override\n%R\tP\tY\tN\n', encoding='utf-8')
    assert XERParser().parse(p)['SCHEDOPTIONS'][0]['sched_retained_logic'] == 'Y'


def options_row(**kwargs):
    return dict(proj_id='P', sched_retained_logic='Y', sched_progress_override='N',
                sched_lag_early_start_flag='Y', sched_use_expect_end_flag='Y',
                sched_calendar_on_relationship_lag='rcal_Predecessor',
                sched_outer_depend_type='SD_Both', sched_setplantoforecast='N', **kwargs)


def test_selected_project_options_are_typed_and_raw_fields_retained():
    row = options_row(future_field='DO_NOT_APPLY')
    schedule = ScheduleMapper().map({'PROJECT': [{'proj_id': 'P'}], 'SCHEDOPTIONS': [dict(row, proj_id='OTHER'), row]})
    o = schedule.scheduling_options
    assert o.project_id == 'P' and o.retained_logic is True and o.progress_override is False
    assert o.ss_lag_from_early_start is True and o.use_expected_finish is True
    assert o.lag_calendar_policy == 'PREDECESSOR' and o.external_relationship_policy == 'BOTH'
    assert o.set_planned_to_forecast is False
    assert dict(o.raw_fields)['future_field'] == 'DO_NOT_APPLY'


@pytest.mark.parametrize('problem', ['duplicate', 'malformed'])
def test_ambiguous_or_malformed_options_do_not_get_guessed(problem):
    row = options_row()
    rows = [row, row] if problem == 'duplicate' else [dict(row, sched_retained_logic='MAYBE')]
    findings = []
    schedule = ScheduleMapper().map({'PROJECT': [{'proj_id': 'P'}], 'SCHEDOPTIONS': rows}, findings)
    assert schedule.scheduling_options is None if problem == 'duplicate' else schedule.scheduling_options.retained_logic is None
    assert any(d.severity.value == 'error' for d in findings)


def test_missing_options_remain_unknown():
    schedule = ScheduleMapper().map({'PROJECT': [{'proj_id': 'P'}]})
    assert schedule.scheduling_options is None


def test_mapper_preserves_remaining_dates_and_duration_type():
    row = dict(task_id='A', task_code='A', proj_id='P', task_type='TT_Task', status_code='TK_Active',
               act_start_date='2026-01-02 08:00', restart_date='2026-01-05 10:00',
               reend_date='2026-01-06 12:00', remain_drtn_hr_cnt='11', expect_end_date='2026-01-09 17:00',
               duration_type='DT_FixedDrtn', suspend_date='', resume_date='')
    schedule = ScheduleMapper().map({'PROJECT': [{'proj_id': 'P'}], 'TASK': [row]})
    a = schedule.activities['A']
    assert a.remaining_start == datetime(2026, 1, 5, 10)
    assert a.remaining_finish == datetime(2026, 1, 6, 12)
    assert a.duration_type == 'DT_FixedDrtn'
    assert a.expected_finish == datetime(2026, 1, 9, 17)
    assert a.actual_start == datetime(2026, 1, 2, 8)
