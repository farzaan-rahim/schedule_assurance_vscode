"""Proprietary-free authority gates, separate from scheduling mathematics."""
from copy import deepcopy
from datetime import datetime

import pytest

from app.cpm.config import CPMConfig
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import ActivityCodeType, ActivityCodeValue, ActivityCodeAssignment, UDFDefinition, UDFValue, Relationship
from tests.test_cpm import activity, make_schedule

FINISH = datetime(2026, 1, 7, 17)


def milestone(key='F', name='Project completion'):
    a = activity(key, key, 0)
    a.activity_name = name
    a.raw_activity_type = 'TT_FinMile'
    a.activity_type = 'finish_milestone'
    a.early_finish = a.late_finish = a.planned_finish = FINISH
    a.total_float_hours = a.free_float_hours = 0
    return a


def code(schedule, activity_id, value='Final Completion', type_name='Milestone Classification'):
    schedule.activity_code_types['T'] = ActivityCodeType('T', type_name)
    schedule.activity_code_values['V'] = ActivityCodeValue('V', 'T', value)
    schedule.activity_code_assignments.append(ActivityCodeAssignment(activity_id, 'T', 'V'))
    schedule.rebuild_optional_indexes()


def udf(schedule, activity_id, value='PROJECT_FINAL', label='Contractual completion role'):
    schedule.udf_definitions['U'] = UDFDefinition('U', 'TASK', 'user_field_U', label, 'FT_TEXT')
    schedule.udf_values.append(UDFValue('U', activity_id, 'TASK', raw_string_value=value, text_value=value))
    schedule.rebuild_optional_indexes()


def inspect(schedule, **kwargs):
    from app.cpm.completion_evidence import investigate_completion_anchors, project_finish_evidence
    snapshot = deepcopy(schedule)
    fields = kwargs.pop('project_fields', project_finish_evidence({'proj_id': 'P1', 'scd_end_date': '2026-01-07 17:00', 'plan_end_date': ''}))
    result = investigate_completion_anchors(schedule, ScheduleGraph(schedule), project_fields=fields, **kwargs)
    assert schedule == snapshot
    return result


def by_id(result):
    return {a.activity_id: a for a in result.candidates}


def test_configured_explicit_anchor_is_authoritative():
    s = make_schedule([milestone()], [])
    r = inspect(s, config=CPMConfig(completion_activity_id='F'))
    assert r.selection_status == 'ANCHOR_SELECTED'
    assert r.selected_activity_id == 'F'
    assert by_id(r)['F'].evidence_class.value == 'AUTHORITATIVE'
    assert r.selected_date is None  # Identity alone never fabricates a required date.


def test_unique_strong_candidate_and_scheduled_date_do_not_authorize_selection():
    s = make_schedule([milestone()], [])
    code(s, 'F')
    r = inspect(s)
    assert by_id(r)['F'].evidence_class.value == 'STRONG_CANDIDATE'
    assert r.selection_status == 'ANCHOR_NOT_SELECTED' and r.selected_activity_id is None
    assert r.selected_date is None


def test_multiple_strong_candidates_preserved_and_rank_is_not_selection():
    s = make_schedule([milestone('B'), milestone('A')], [])
    code(s, 'A');code(s, 'B')
    r = inspect(s)
    assert len([a for a in r.candidates if a.evidence_class.value == 'STRONG_CANDIDATE']) == 2
    assert [a.activity_code for a in r.candidates] == ['A', 'B']
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'


def test_activity_code_type_and_value_are_candidate_evidence_only():
    s = make_schedule([milestone()], [])
    code(s, 'F')
    c = by_id(inspect(s))['F']
    assert any(e.type_name == 'Milestone Classification' and e.value == 'Final Completion' for e in c.activity_codes)
    assert c.completion_role == 'FINAL_COMPLETION'
    assert not c.authority_sources


def test_udf_label_alone_is_not_authority():
    s = make_schedule([milestone()], [])
    udf(s, 'F')
    assert inspect(s).selection_status == 'ANCHOR_NOT_SELECTED'


def test_documented_unambiguous_udf_rule_is_authoritative():
    from app.cpm.completion_evidence import CompletionMetadataRule
    s = make_schedule([milestone()], [])
    udf(s, 'F')
    rule = CompletionMetadataRule('UDF', 'U', 'PROJECT_FINAL', 'Owner dictionary: this value identifies project contractual completion.')
    r = inspect(s, metadata_rules=(rule,))
    assert r.selection_status == 'ANCHOR_SELECTED'
    assert r.selected_activity_id == 'F'
    assert any('Owner dictionary' in x for x in by_id(r)['F'].authority_sources)


def test_multiple_authoritative_metadata_matches_are_not_chosen_arbitrarily():
    from app.cpm.completion_evidence import CompletionMetadataRule
    s = make_schedule([milestone('A'), milestone('B')], [])
    udf(s, 'A');udf(s, 'B')
    r = inspect(s, metadata_rules=(CompletionMetadataRule('UDF', 'U', 'PROJECT_FINAL', 'Owner-defined role'),))
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'
    assert r.selected_activity_id is None
    assert any(d.code == 'ambiguous_completion_authority' for d in r.diagnostics)


def test_required_project_finish_alone_does_not_identify_an_activity():
    s = make_schedule([milestone()], [])
    r = inspect(s, config=CPMConfig(required_project_finish=FINISH))
    assert r.required_finish == FINISH
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'


def test_required_finish_explicitly_associated_with_activity_is_retained():
    s = make_schedule([milestone()], [])
    r = inspect(s, config=CPMConfig(required_finish_activity_id='F', required_project_finish=FINISH))
    assert r.selection_status == 'ANCHOR_SELECTED'
    assert r.selected_date == FINISH and r.required_finish == FINISH
    assert r.selected_date_source == 'CONFIGURED_REQUIRED_PROJECT_FINISH'


@pytest.mark.parametrize('bad', ['missing', 'conflicting', 'duplicate'])
def test_invalid_explicit_selector_does_not_fall_through_to_other_evidence(bad):
    s = make_schedule([milestone('A'), milestone('B')], [])
    if bad == 'duplicate':
        s.activities['A'].activity_code = s.activities['B'].activity_code = 'SAME'
        s.rebuild_activity_indexes()
        config = CPMConfig(completion_activity_code='SAME')
    elif bad == 'conflicting':
        config = CPMConfig(completion_activity_id='A', completion_activity_code='B')
    else:
        config = CPMConfig(completion_activity_id='MISSING')
    r = inspect(s, config=config)
    assert r.selected_activity_id is None
    assert r.selection_status == 'INVALID_CONFIGURED_ANCHOR'


def test_finish_constraint_is_not_global_contract_authority():
    f = milestone()
    f.primary_constraint_type = 'FINISH_ON_OR_BEFORE'
    f.primary_constraint_date = FINISH
    s = make_schedule([f], [])
    r = inspect(s)
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'
    assert by_id(r)['F'].constraints[0].constraint_type == 'FINISH_ON_OR_BEFORE'
    assert r.required_finish is None


def test_name_and_zero_float_do_not_become_authority():
    f = milestone(name='AUTHORITATIVE FINAL PROJECT COMPLETION')
    r = inspect(make_schedule([f], []))
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'
    assert by_id(r)['F'].evidence_class.value != 'AUTHORITATIVE'


def test_backward_scope_is_only_selected_anchor_ancestors():
    from app.cpm.completion_evidence import anchor_ancestor_scope
    s = make_schedule([activity('A', 'A', 2), milestone(), activity('AFTER', 'AFTER', 2), activity('OTHER', 'OTHER', 2)],
                      [Relationship('1', 'A', 'F', 'FS', 0), Relationship('2', 'F', 'AFTER', 'FS', 0)])
    selected = inspect(s, config=CPMConfig(completion_activity_id='F'))
    assert anchor_ancestor_scope(s, ScheduleGraph(s), selected) == ('A', 'F')
    assert anchor_ancestor_scope(s, ScheduleGraph(s), inspect(s)) == ()


def test_project_required_blank_and_scheduled_output_are_distinct():
    from app.cpm.completion_evidence import project_finish_evidence
    fields = project_finish_evidence({'proj_id': 'P1', 'plan_end_date': '', 'scd_end_date': '2026-01-07 17:00', 'base_proj_id': '999'})
    by_field = {f.field_name:f for f in fields}
    assert by_field['plan_end_date'].raw_value == '' and by_field['plan_end_date'].parsed_date is None
    assert by_field['plan_end_date'].semantic_role == 'REQUIRED_PROJECT_FINISH'
    assert by_field['scd_end_date'].semantic_role == 'SCHEDULED_FINISH_OUTPUT'
    assert by_field['base_proj_id'].parsed_date is None
    assert 'fcst_end_date' not in by_field  # Do not invent an absent export field.


def test_undocumented_authority_rule_is_rejected():
    from app.cpm.completion_evidence import CompletionMetadataRule
    with pytest.raises(ValueError):
        CompletionMetadataRule('UDF', 'U', 'Y', '')


def test_false_udf_assertion_cannot_match_an_authoritative_rule():
    from app.cpm.completion_evidence import CompletionMetadataRule
    s = make_schedule([milestone()], [])
    udf(s, 'F', value='NO')
    r = inspect(s, metadata_rules=(CompletionMetadataRule('UDF', 'U', 'YES', 'Owner-defined marker'),))
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'


def test_candidate_ranking_is_deterministic():
    s = make_schedule([milestone('C'), milestone('B'), milestone('A')], [])
    code(s, 'B')
    assert inspect(s) == inspect(s)


def test_conflicting_values_in_one_authoritative_udf_do_not_certify_identity():
    from app.cpm.completion_evidence import CompletionMetadataRule
    s = make_schedule([milestone()], [])
    udf(s, 'F', 'PROJECT_FINAL')
    udf(s, 'F', 'OTHER_ROLE')
    r = inspect(s, metadata_rules=(CompletionMetadataRule('UDF', 'U', 'PROJECT_FINAL', 'Owner dictionary'),))
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'
    assert any(d.code == 'conflicting_completion_metadata_values' for d in r.diagnostics)


def test_exported_required_date_is_preserved_without_inventing_its_activity():
    from app.cpm.completion_evidence import project_finish_evidence
    s = make_schedule([milestone()], [])
    fields = project_finish_evidence({'proj_id':'P1','plan_end_date':'2026-01-07 17:00','scd_end_date':'2026-01-07 17:00'})
    r = inspect(s, project_fields=fields)
    assert r.required_finish == FINISH
    assert r.selected_activity_id is None and r.selected_date is None


def test_explicit_unsupported_summary_cannot_become_schedulable_by_authority():
    a = milestone()
    a.raw_activity_type = 'TT_WBS'
    r = inspect(make_schedule([a], []), config=CPMConfig(completion_activity_id='F'))
    assert r.selection_status == 'ANCHOR_NOT_SELECTED'
    assert any(d.code == 'unsupported_completion_anchor_type' for d in r.diagnostics)


def test_anchor_ancestor_scope_is_iterative_above_recursion_limit():
    from app.cpm.completion_evidence import anchor_ancestor_scope
    items = [activity(str(i), str(i), 1) for i in range(1101)] + [milestone()]
    links = [Relationship(str(i), str(i), str(i+1), 'FS', 0) for i in range(1100)] + [Relationship('LAST','1100','F','FS',0)]
    s = make_schedule(items, links)
    r = inspect(s, config=CPMConfig(completion_activity_id='F'))
    assert len(anchor_ancestor_scope(s, ScheduleGraph(s), r)) == 1102


def test_ranking_explanation_exposes_date_and_terminal_priorities():
    s = make_schedule([milestone()], [])
    code(s, 'F')
    reasons = by_id(inspect(s))['F'].ranking_reason
    assert 'SCHEDULED_FINISH_AGREEMENT' in reasons
    assert 'TERMINAL' in reasons
