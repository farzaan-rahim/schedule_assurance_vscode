from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from io import BytesIO

import pytest
from openpyxl import load_workbook

from app.cpm.analysis_anchors import AnalysisAnchorConfig, AnchorSelectionError, resolve_analysis_anchor, analysis_anchor_catalog
from app.cpm.selected_analysis import SelectedAnchorService
from app.graph.schedule_graph import ScheduleGraph
from app.models.schedule import Relationship
from tests.test_cpm import activity, make_schedule
from tests.test_cpm_progress import options

D=datetime(2026,1,5,8)


def fixture():
    items=[]
    for i,code in enumerate(('A','F1','B','F2','C','F3')):
        a=activity(str(i),code,0 if code.startswith('F') else 2)
        if code.startswith('F'):a.activity_type='finish_milestone';a.raw_activity_type='TT_FinMile'
        es=D+timedelta(hours=(i//2)*2 if not code.startswith('F') else ((i+1)//2)*2)
        a.early_start=es;a.early_finish=es+timedelta(hours=a.remaining_duration_hours)
        a.late_start=a.early_start;a.late_finish=a.early_finish;a.free_float_hours=0
        items.append(a)
    items.append(activity('X','UNRELATED',8))
    s=make_schedule(items,[Relationship('R'+str(i),str(i),str(i+1),'FS',0) for i in range(5)])
    s.scheduling_options=options()
    return s


def cfg(code='F3',**kwargs):
    return AnalysisAnchorConfig(analysis_anchor_activity_code=code,**kwargs)


def test_code_selection_is_analysis_not_authority():
    s=fixture();a=resolve_analysis_anchor(s,ScheduleGraph(s),cfg())
    assert a.activity_id=='5' and a.activity_code=='F3'
    assert a.selection_method=='EXPLICIT_ACTIVITY_CODE'
    assert a.contractual_authority_status=='NOT_ESTABLISHED'
    assert a.selected_timestamp==D+timedelta(hours=6)
    assert a.timestamp_source=='CALIBRATION_IMPORTED_LATE_FINISH'
    assert a.required_finish is None


def test_internal_and_configured_selection():
    s=fixture();g=ScheduleGraph(s)
    a=resolve_analysis_anchor(s,g,AnalysisAnchorConfig(analysis_anchor_internal_id='3',selected_by='Caller'))
    assert a.activity_code=='F2' and a.selection_method=='EXPLICIT_INTERNAL_ID' and a.selected_by=='Caller'
    a=resolve_analysis_anchor(s,g,AnalysisAnchorConfig(configured_analysis_milestone='F1'))
    assert a.selection_method=='CONFIGURED_ANALYSIS_MILESTONE'


@pytest.mark.parametrize('config,code',[(cfg('missing'),'analysis_anchor_not_found'),(AnalysisAnchorConfig(),'analysis_anchor_required'),
    (cfg('F3',analysis_anchor_internal_id='1'),'analysis_anchor_selector_conflict'),(cfg(mode='bad'),'invalid_analysis_mode')])
def test_controlled_selection_errors(config,code):
    s=fixture()
    with pytest.raises(AnchorSelectionError) as exc:resolve_analysis_anchor(s,ScheduleGraph(s),config)
    assert exc.value.code==code


def test_ambiguous_code_never_falls_back():
    s=fixture();s.activities['DUP']=replace(s.activities['5'],activity_id='DUP');s.rebuild_activity_indexes()
    with pytest.raises(AnchorSelectionError,match='unique') as e:resolve_analysis_anchor(s,ScheduleGraph(s),cfg())
    assert e.value.code=='analysis_anchor_ambiguous'
    assert resolve_analysis_anchor(s,ScheduleGraph(s),AnalysisAnchorConfig(analysis_anchor_internal_id='5')).activity_id=='5'


@pytest.mark.parametrize('kind,raw', [('wbs_summary','TT_WBS'),('level_of_effort','TT_LOE')])
def test_excluded_anchor_rejected(kind,raw):
    s=fixture();s.activities['5'].activity_type=kind;s.activities['5'].raw_activity_type=raw
    with pytest.raises(AnchorSelectionError) as e:resolve_analysis_anchor(s,ScheduleGraph(s),cfg())
    assert e.value.code=='unsuitable_analysis_anchor'


def test_normal_activity_explicit_only_and_calendar_project_timestamp_gates():
    s=fixture();a=resolve_analysis_anchor(s,ScheduleGraph(s),cfg('A'))
    assert not a.milestone and 'analysis_anchor_not_milestone' in [d.code for d in a.suitability_diagnostics]
    with pytest.raises(AnchorSelectionError):resolve_analysis_anchor(s,ScheduleGraph(s),AnalysisAnchorConfig(configured_analysis_milestone='A'))
    s.activities['0'].calendar_id='missing'
    with pytest.raises(AnchorSelectionError):resolve_analysis_anchor(s,ScheduleGraph(s),cfg('A'))
    s=fixture();s.activities['5'].project_id='OTHER'
    with pytest.raises(AnchorSelectionError):resolve_analysis_anchor(s,ScheduleGraph(s),cfg())
    s=fixture();s.activities['5'].late_finish=None
    with pytest.raises(AnchorSelectionError):resolve_analysis_anchor(s,ScheduleGraph(s),cfg())


def test_independent_mode_never_borrows_p6_finish():
    s=fixture();g=ScheduleGraph(s)
    with pytest.raises(AnchorSelectionError) as e:resolve_analysis_anchor(s,g,cfg(mode='INDEPENDENT'))
    assert e.value.code=='analysis_required_finish_missing'
    stamp=D+timedelta(hours=4)
    a=resolve_analysis_anchor(s,g,cfg(mode='INDEPENDENT',required_finish=stamp))
    assert a.selected_timestamp==stamp and a.required_finish==stamp
    assert a.timestamp_source=='CALLER_REQUIRED_FINISH'
    assert a.contractual_authority_status=='NOT_ESTABLISHED'


def test_catalog_has_selector_evidence_and_no_selection():
    s=fixture();catalog=analysis_anchor_catalog(s,ScheduleGraph(s))
    assert catalog['selected_analysis_anchor'] is None and catalog['completion_authority_status']=='NOT_ESTABLISHED'
    assert len(catalog['candidates'])==3
    row=next(x for x in catalog['candidates'] if x['activity_code']=='F3')
    assert row['suitable_for_calibration'] and row['activity_id']=='5'
    assert row['imported_late_finish']==D+timedelta(hours=6)
    assert row['selection_requires_caller']


def test_independent_three_anchors_scope_dates_and_immutability():
    s=fixture();before=deepcopy(s);service=SelectedAnchorService();out=[]
    for code,size in [('F1',2),('F2',4),('F3',6)]:
        a=service.analyze(s,ScheduleGraph(s),cfg(code));out.append(a)
        assert len(a.activity_dispositions)==size and 'X' not in a.upstream_activity_ids
        assert a.summary['late_calculable']==size and a.summary['total_float_valid']==size
        assert a.summary['metrics']['late_start']['exact_matches']==size
        assert a.summary['metrics']['late_finish']['exact_matches']==size
        assert len(a.cpm_result.critical_paths)==1
        assert a.cpm_result.critical_paths[0].activity_codes[-1]==code
        assert a.cpm_result.critical_paths[0].activity_count==size
        assert a.summary['completion_authority_status']=='NOT_ESTABLISHED'
    assert [x.anchor.activity_code for x in out]==['F1','F2','F3']
    assert s==before


def test_required_finish_negative_float_and_controlling_path():
    s=fixture();out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg(mode='INDEPENDENT',required_finish=D+timedelta(hours=4)))
    assert {r.calculated_total_float_hours for r in out.cpm_result.activity_results if r.effective_state!='COMPLETE'}=={-2}
    assert all(r.calculated_critical for r in out.cpm_result.activity_results)
    assert out.cpm_result.critical_paths[0].minimum_total_float_hours==-2
    assert out.anchor.contractual_authority_status=='NOT_ESTABLISHED'


def test_expected_finish_blocks_upstream_late_not_downstream_or_early():
    s=fixture();s.activities['2'].expected_finish=D+timedelta(hours=4)
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    by={x.activity_id:x for x in out.activity_dispositions}
    assert by['2'].late_status=='BLOCKED' and 'expected_finish_unimplemented' in by['2'].reason_codes
    assert by['0'].late_status=='BLOCKED' and by['5'].late_status=='BACKWARD_CALCULABLE'
    # The upstream A early dates stay reliable; downstream early uncertainty is preserved.
    assert by['0'].es_availability=='AVAILABLE' and by['5'].es_availability=='BLOCKED'
    rows={r.activity_id:r for r in out.cpm_result.activity_results}
    assert rows['0'].calculated_early_start==D and rows['0'].calculated_late_start is None
    assert rows['5'].calculated_late_finish==s.activities['5'].late_finish
    assert out.summary['total_float_valid']==0
    assert out.path_status=='BLOCKED'


def test_loe_boundary_is_preserved_not_bypassed():
    s=fixture();s.activities['2'].raw_activity_type='TT_LOE';s.activities['2'].activity_type='level_of_effort'
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    by={a.activity_id:a for a in out.activity_dispositions}
    assert by['2'].late_status=='EXCLUDED'
    assert by['0'].late_status=='BLOCKED' and by['5'].late_status=='BACKWARD_CALCULABLE'
    assert any(r.backward_status=='EXCLUDED_ENDPOINT' for r in out.relationship_dispositions)


def test_history_is_not_rescheduled():
    s=fixture();a=s.activities['0'];a.raw_status='TK_Complete';a.status='complete'
    a.actual_start=datetime(2026,1,2,8);a.actual_finish=datetime(2026,1,2,10);a.remaining_duration_hours=0
    before=deepcopy(s);out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    assert next(d for d in out.activity_dispositions if d.activity_id=='0').late_status=='HISTORICAL_ONLY'
    assert s==before


def test_payload_contract_omits_schedule_and_preserves_directional_status():
    from app.cpm.analysis_serialization import analysis_payload
    s=fixture();out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    p=analysis_payload(out)
    assert p['analysis_anchor']['timestamp_source']=='CALIBRATION_IMPORTED_LATE_FINISH'
    assert p['completion_authority_status']=='NOT_ESTABLISHED'
    assert 'schedule' not in p and 'cpm_result' not in p
    assert p['controlling_paths'][0]['classification']=='APPLICATION_CALCULATED_CONTROLLING_PATH'
    assert p['directional_availability']['activities']


def test_missing_external_successor_cannot_be_ignored_for_free_float():
    s=fixture();s.relationships.append(Relationship('EXTERNAL','0','UNKNOWN','FS',0))
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    a=next(r for r in out.cpm_result.activity_results if r.activity_id=='0')
    assert a.calculated_free_float_hours is None
    d=next(r for r in out.activity_dispositions if r.activity_id=='0')
    assert d.free_float_availability=='BLOCKED'


@pytest.mark.parametrize('kind,lag,expected_start',[('FS',0,12),('FS',1,11),('FS',-1,13),('SS',1,13),('FF',1,13),('SF',0,14)])
def test_existing_reverse_formulas_are_used_for_selected_work(kind,lag,expected_start):
    p,q=activity('P','P',2),activity('Q','Q',2)
    q.late_finish=datetime(2026,1,5,16)
    s=make_schedule([p,q],[Relationship('R','P','Q',kind,lag)]);s.scheduling_options=options()
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg('Q'))
    row=next(r for r in out.cpm_result.activity_results if r.activity_id=='P')
    assert row.calculated_late_start==datetime(2026,1,5,expected_start)


def test_progressed_ss_remains_blocked_backward_with_reason():
    s=fixture();p=s.activities['0'];p.raw_status='TK_Active';p.status='in_progress';p.actual_start=datetime(2026,1,2,16)
    s.relationships[0]=Relationship('R0','0','1','SS',2)
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    d=next(d for d in out.activity_dispositions if d.activity_id=='0')
    assert d.es_availability=='AVAILABLE' and d.late_status=='BLOCKED'
    assert 'backward_progressed_ss_unimplemented' in d.reason_codes


def test_positive_float_controlling_trace_is_not_mislabeled_critical():
    s=fixture();out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg(mode='INDEPENDENT',required_finish=datetime(2026,1,5,16)))
    assert all(not r.calculated_critical for r in out.cpm_result.activity_results)
    assert len(out.cpm_result.critical_paths)==1
    assert out.cpm_result.critical_paths[0].classification=='APPLICATION_CALCULATED_CONTROLLING_PATH'
    assert out.cpm_result.critical_paths[0].minimum_total_float_hours==2


def test_deep_scope_and_trace_use_iteration():
    count=1102;items=[activity(str(i),str(i),0) for i in range(count)]
    items[-1].late_finish=D
    s=make_schedule(items,[Relationship(str(i),str(i),str(i+1),'FS',0) for i in range(count-1)]);s.scheduling_options=options()
    from app.cpm.config import CPMConfig
    config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC',maximum_path_depth=1200,maximum_path_nodes_inspected=3000)
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg(str(count-1)),engine_config=config)
    assert out.summary['late_calculable']==count
    assert out.cpm_result.critical_paths[0].activity_count==count
    assert not out.cpm_result.critical_paths[0].truncated


def test_ties_and_explicit_path_limit():
    a,b,f=activity('A','A',2),activity('B','B',2),activity('F','F',0)
    f.raw_activity_type='TT_FinMile';f.activity_type='finish_milestone';f.late_finish=D+timedelta(hours=2)
    s=make_schedule([a,b,f],[Relationship('AF','A','F','FS',0),Relationship('BF','B','F','FS',0)]);s.scheduling_options=options()
    from app.cpm.config import CPMConfig
    config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
    both=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg('F'),engine_config=config)
    assert len(both.cpm_result.critical_paths)==2
    cut=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg('F'),engine_config=replace(config,maximum_critical_paths=1))
    assert len(cut.cpm_result.critical_paths)==1 and cut.path_status=='TRUNCATED'
    assert cut.cpm_result.path_statistics[0].truncated


def test_reporting_anchor_adapter_preserves_other_comparison_values():
    from app.comparison.engine import ScheduleComparisonEngine
    from app.comparison.models import ScheduleVersion, ScheduleVersionType
    from app.reporting.builder import ForensicReportBuilder
    from app.reporting.serialization import serialize_report
    from app.reporting.excel_renderer import ExcelReportRenderer
    s=fixture();analysis=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    v=ScheduleVersion('v','Current',ScheduleVersionType.CURRENT,'synthetic.xer',D,D,s)
    comparison=ScheduleComparisonEngine().compare(v,v)
    plain=ForensicReportBuilder().build(comparison,generated_at=D,report_identifier='report')
    report=ForensicReportBuilder().build(comparison,generated_at=D,report_identifier='report',analysis_result=analysis)
    for section in plain.sections:
        if section.key not in ('summary','controlling_paths'):assert report.section(section.key)==section
    assert report.metadata.completion_authority_status=='NOT_ESTABLISHED'
    assert report.metadata.selected_analysis_anchor.activity_code=='F3'
    assert report.metadata.analysis_anchor_timestamp_source=='CALIBRATION_IMPORTED_LATE_FINISH'
    assert report.section('controlling_paths').availability.value=='AVAILABLE'
    assert report.section('controlling_paths').count==6
    data=serialize_report(report)
    assert data['metadata']['selected_analysis_anchor']['anchor_kind']=='ANALYSIS_ANCHOR'
    wb=load_workbook(BytesIO(ExcelReportRenderer().render(report)))
    ws=wb['App Controlling Paths'];headers=[c.value for c in ws[6]]
    assert 'Anchor Activity ID' in headers and 'Calculated LF' in headers and 'Completion Authority' in headers
    assert 'Selected Analysis Anchor: F3' in ws['A5'].value
    assert ws.cell(7,headers.index('Anchor Activity ID')+1).value=='F3'
    assert 'Contractual Project Completion' not in str(ws['A5'].value)


def controlled_xer():
    s=fixture()
    text=['ERMHDR\t26.5\tSynthetic proprietary-free selected-analysis fixture']
    def table(name,fields,rows):
        text.append('%T\t'+name);text.append('%F\t'+'\t'.join(fields))
        for row in rows:text.append('%R\t'+'\t'.join('' if x is None else str(x) for x in row))
    table('PROJECT',['proj_id','proj_short_name','proj_name','last_recalc_date','critical_path_type','critical_drtn_hr_cnt'],
        [('P1','P1','Synthetic selected analysis','2026-01-05 08:00','CT_TotFloat','0')])
    table('PROJWBS',['wbs_id','proj_id','wbs_short_name','wbs_name','parent_wbs_id'],[('W1','P1','W1','WBS','')])
    raw='(0||CalendarData()((0||DaysOfWeek()((0||1()())(0||2()((0||0(s|08:00|f|17:00)())))(0||7()())))))'
    table('CALENDAR',['clndr_id','clndr_name','proj_id','clndr_data'],[('C1','Synthetic calendar','P1',raw)])
    fields=['task_id','task_code','task_name','proj_id','wbs_id','clndr_id','task_type','status_code','target_drtn_hr_cnt','remain_drtn_hr_cnt',
        'early_start_date','early_end_date','late_start_date','late_end_date','total_float_hr_cnt','free_float_hr_cnt']
    rows=[]
    for a in s.activities.values():
        rows.append([a.activity_id,a.activity_code,a.activity_name,'P1','W1','C1',a.raw_activity_type,a.raw_status,a.original_duration_hours,a.remaining_duration_hours,
            a.early_start,a.early_finish,a.late_start,a.late_finish,a.total_float_hours,a.free_float_hours])
    table('TASK',fields,rows)
    table('TASKPRED',['task_pred_id','pred_task_id','task_id','pred_type','lag_hr_cnt'],[(r.relationship_id,r.predecessor_activity_id,r.successor_activity_id,'PR_FS',0) for r in s.relationships])
    table('SCHEDOPTIONS',['proj_id','sched_retained_logic','sched_progress_override','sched_lag_early_start_flag','sched_use_expect_end_flag','sched_calendar_on_relationship_lag'],
        [('P1','Y','N','Y','Y','rcal_Predecessor')])
    text.append('%E');return ('\n'.join(text)+'\n').encode()


def test_readonly_critical_definition_evidence_and_real_import_path(tmp_path):
    from app.cpm.analysis_io import import_analysis_file, CriticalDefinitionEvidence, AnalysisXERService
    path=tmp_path/'synthetic.xer';path.write_bytes(controlled_xer())
    result,evidence=import_analysis_file(path)
    assert evidence.raw_path_type=='CT_TotFloat' and evidence.total_float_threshold_hours==0
    assert CriticalDefinitionEvidence('P1','UNSUPPORTED','0').total_float_threshold_hours is None
    assert CriticalDefinitionEvidence('P1','CT_TotFloat','NaN').total_float_threshold_hours is None
    out=AnalysisXERService().analyze(path.read_bytes(),'synthetic.xer',cfg())
    assert out.summary['late_calculable']==6 and out.summary['total_float_valid']==6
    assert out.summary['critical_state']['configured_definition_agreements']==6
    assert out.anchor.contractual_authority_status=='NOT_ESTABLISHED'
    assert path.read_bytes()==controlled_xer()


def test_independently_established_authority_is_preserved_not_created():
    from app.cpm.analysis_anchors import CompletionAuthorityRecord
    s=fixture();record=CompletionAuthorityRecord('ESTABLISHED',('Separately documented synthetic completion instruction',),D+timedelta(hours=5))
    a=resolve_analysis_anchor(s,ScheduleGraph(s),cfg(mode='INDEPENDENT'),authority=record)
    assert a.timestamp_source=='SEPARATELY_AUTHORITATIVE_FINISH' and a.contractual_authority_status=='ESTABLISHED'
    assert a.authority_evidence==record.evidence
    assert resolve_analysis_anchor(s,ScheduleGraph(s),cfg()).contractual_authority_status=='NOT_ESTABLISHED'


def test_critical_definition_configuration_difference_is_visible():
    from app.cpm.analysis_io import CriticalDefinitionEvidence
    from app.cpm.config import CPMConfig
    s=fixture();config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg(),engine_config=config,
        critical_definition=CriticalDefinitionEvidence('P1','CT_TotFloat','-1'))
    assert out.summary['critical_state']['definition_compatibility']=='CONFIGURATION_DIFFERENCE'
    assert out.summary['critical_state']['configured_definition_application_only']==6


def test_broken_late_invariant_withholds_float_and_preserves_early(monkeypatch):
    from app.cpm import selected_analysis
    real=selected_analysis.backward_pass
    def corrupt(*args,**kwargs):
        result=real(*args,**kwargs)
        if '0' in result['late_starts']:result['late_starts']['0']+=timedelta(hours=1)
        return result
    monkeypatch.setattr(selected_analysis,'backward_pass',corrupt)
    s=fixture();out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    row=next(r for r in out.cpm_result.activity_results if r.activity_id=='0')
    assert row.calculated_early_start==D and row.calculated_late_start is None
    assert row.calculated_total_float_hours is None
    assert any(d.code=='selected_late_invariant_failed' for d in out.diagnostics)
    assert next(d for d in out.activity_dispositions if d.activity_id=='5').ls_availability=='AVAILABLE'


def test_completed_bridge_is_not_a_remaining_backward_proxy():
    s=fixture();a=s.activities['2'];a.raw_status='TK_Complete';a.status='complete'
    a.actual_start=datetime(2026,1,2,8);a.actual_finish=datetime(2026,1,2,10);a.remaining_duration_hours=0
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    by={d.activity_id:d for d in out.activity_dispositions}
    assert by['2'].late_status=='HISTORICAL_ONLY'
    assert by['1'].late_status=='BLOCKED'
    assert 'completed_backward_bridge_unimplemented' in by['1'].reason_codes
    assert by['5'].late_status=='BACKWARD_CALCULABLE'


def test_wbs_summary_inside_scope_stays_excluded():
    s=fixture();s.activities['2'].raw_activity_type='TT_WBS';s.activities['2'].activity_type='wbs_summary'
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    assert next(d for d in out.activity_dispositions if d.activity_id=='2').late_status=='EXCLUDED'
    assert next(d for d in out.activity_dispositions if d.activity_id=='0').ls_availability=='BLOCKED'
    assert next(d for d in out.activity_dispositions if d.activity_id=='5').ls_availability=='AVAILABLE'


def test_cycle_blocks_affected_ancestors_not_selected_late_boundary():
    s=fixture();s.relationships.append(Relationship('CYCLE','1','0','FS',0))
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    by={d.activity_id:d for d in out.activity_dispositions}
    assert by['0'].late_status=='BLOCKED' and by['1'].late_status=='BLOCKED'
    assert by['5'].ls_availability=='AVAILABLE' and by['5'].es_availability=='BLOCKED'
    assert out.summary['total_float_valid']==0


def test_selected_result_rejects_forward_result_from_another_schedule():
    from app.cpm.service import CPMService
    from app.cpm.config import CPMConfig
    s=fixture();config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
    f=CPMService().calculate(s,ScheduleGraph(s),config)
    other=fixture()
    with pytest.raises(ValueError,match='Reused forward result'):
        SelectedAnchorService().analyze(other,ScheduleGraph(other),cfg(),engine_config=config,forward_result=f)


def test_blocked_selected_path_reporting_retains_explicit_reason():
    from app.comparison.engine import ScheduleComparisonEngine
    from app.comparison.models import ScheduleVersion,ScheduleVersionType
    from app.reporting.builder import ForensicReportBuilder
    s=fixture();s.activities['2'].expected_finish=D+timedelta(hours=4)
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg())
    v=ScheduleVersion('v','v',ScheduleVersionType.CURRENT,'synthetic.xer',D,D,s)
    report=ForensicReportBuilder().build(ScheduleComparisonEngine().compare(v,v),analysis_result=out)
    section=report.section('controlling_paths')
    assert section.count==0 and section.availability.value=='BLOCKED'
    assert section.message.startswith('Not evaluated:')
    assert report.metadata.selected_analysis_anchor.activity_code=='F3'


def test_exported_duration_precision_remains_raw_and_tolerance_only_classifies():
    from app.cpm.config import CPMConfig
    p=activity('P','P',2.016667);p.late_start=datetime(2026,1,5,8,59);p.late_finish=datetime(2026,1,5,11)
    s=make_schedule([p],[]);s.scheduling_options=options()
    config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
    exact=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg('P'),engine_config=config)
    row=exact.cpm_result.activity_results[0]
    assert row.calculated_late_start==datetime(2026,1,5,8,58,59,998800)
    record=next(r for r in exact.comparisons if r['metric']=='late_start')
    assert record['classification']=='DIFFERENCE' and record['variance_hours']==-0.0012/3600
    tolerant=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg('P'),engine_config=replace(config,comparison_date_tolerance_seconds=0.01))
    record2=next(r for r in tolerant.comparisons if r['metric']=='late_start')
    assert record2['classification']=='TOLERANCE_MATCH' and record2['variance_hours']==record['variance_hours']
    assert tolerant.cpm_result.activity_results[0].calculated_late_start==row.calculated_late_start


def test_selected_relationship_records_preserve_forward_progress_audit():
    from app.cpm.config import CPMConfig
    from app.cpm.service import CPMService
    s=fixture();p=s.activities['0'];p.raw_status='TK_Active';p.status='in_progress';p.actual_start=datetime(2026,1,2,16)
    s.relationships[0]=Relationship('R0','0','1','SS',2)
    config=CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')
    original=CPMService().calculate(s,ScheduleGraph(s),config)
    out=SelectedAnchorService().analyze(s,ScheduleGraph(s),cfg(),engine_config=config,forward_result=original)
    before=next(r for r in original.relationship_calculability if r.relationship_id=='R0')
    after=next(r for r in out.relationship_dispositions if r.relationship_id=='R0')
    assert after.forward_requirement_timestamp==before.forward_requirement_timestamp
    assert after.expired_lag_hours==before.expired_lag_hours==1
    assert after.remaining_lag_hours==before.remaining_lag_hours==1
    assert after.forward_reason_codes==before.reason_codes
    assert 'backward_progressed_ss_unimplemented' in after.backward_reason_codes
