from dataclasses import replace
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import copy
import json

import pytest
from openpyxl import load_workbook

from app.comparison.engine import ScheduleComparisonEngine
from app.comparison.models import ScheduleVersion, ScheduleVersionType
from app.reporting.builder import ForensicReportBuilder
from app.reporting.change_values import change_value
from app.reporting.excel_renderer import ExcelReportRenderer
from app.reporting.limits import ReportLimitError, ReportLimits
from app.reporting.models import Availability as A, ChangeClassification as C, Provenance as P, ReportRow
from app.reporting.sections import SECTION_DEFINITIONS
from app.reporting.serialization import report_json, serialize_report
from app.reporting.service import ForensicReportingService, ReportInputError
from app.services.schedule_import import ScheduleImportService

ROOT=Path(__file__).resolve().parents[1]
NOW=datetime(2026,11,25,12,tzinfo=timezone.utc)


@pytest.fixture
def comparison():
    versions=[]
    for name,kind in [('baseline',ScheduleVersionType.BASELINE),('current',ScheduleVersionType.CURRENT)]:
        result=ScheduleImportService().import_file(ROOT/f'sample_data/sample_{name}.xer')
        assert result.succeeded
        versions.append(ScheduleVersion(name,name,kind,f'sample_{name}.xer',result.schedule.project.data_date,NOW,result.schedule))
    return ScheduleComparisonEngine().compare(*versions)


@pytest.fixture
def report(comparison):
    return ForensicReportBuilder().build(comparison,generated_at=NOW,report_identifier='controlled-report')


def activity_row(report,key,code):
    return next(row for row in report.section(key).rows if row.context and row.context.activity_id==code)


def test_section_order_identity_and_counts(report):
    assert [(s.key,s.title,s.sheet_name) for s in report.sections]==list(SECTION_DEFINITIONS)
    assert len(report.sections)==29
    assert report.section('activities').count==8
    assert report.section('relationships').count==5
    for s in report.sections:
        assert s.count==len(s.rows)
        assert len(s.columns)==len({c.key for c in s.columns})
    assert report.metadata.completion_authority_status=='NOT_ESTABLISHED'
    assert report.metadata.selected_analysis_anchor is None


def test_controlled_fixture_changes(report):
    assert activity_row(report,'activities','A1500').classification=='REMOVED'
    assert activity_row(report,'activities','A1700').classification=='ADDED'
    rename=activity_row(report,'description','A1200')
    assert rename.cells['baseline_value']=='A1200'
    assert rename.cells['current_value']=='Revised build'
    moved=activity_row(report,'activities','A1300')
    assert 'WBS_MOVED' in moved.cells['change_categories']
    assert moved.context.baseline_wbs=='ROOT > AREA1'
    assert moved.context.current_wbs=='ROOT > AREA2'
    delayed=activity_row(report,'planned_finish','A1200')
    assert delayed.cells['variance']==168
    assert delayed.cells['elapsed_days']==7
    assert delayed.classification=='DELAYED'
    duration=activity_row(report,'original_duration','A1200')
    assert duration.cells['baseline_value']==40
    assert duration.cells['current_value']==80
    assert duration.cells['variance']==40
    assert duration.cells['percentage']==1
    tf=activity_row(report,'total_float','A1200')
    assert tf.cells['variance']==-56
    assert tf.classification=='BECAME_NEGATIVE'
    assert tf.cells['application_calculated'] is None
    assert tf.cells['calculation_availability']=='NOT_EVALUATED'
    assert tf.cells['calculation_provenance']=='APPLICATION_CALCULATED'
    assert tf.cells['baseline_free_float']==0
    assert tf.cells['application_free_float'] is None
    assert tf.provenance==(P.IMPORTED_P6,P.BASELINE_COMPARISON)


def test_relationships_preserve_both_sides(report):
    changes=report.section('relationships').rows
    assert {r.classification for r in changes}=={'ADDED','REMOVED','TYPE_CHANGED','LAG_CHANGED'}
    pair=[r for r in changes if r.cells['predecessor_activity_id']=='A1100' and r.cells['successor_activity_id']=='A1200']
    assert {r.classification for r in pair}=={'TYPE_CHANGED','LAG_CHANGED'}
    for r in pair:
        assert r.cells['baseline_type']=='FS' and r.cells['current_type']=='SS'
        assert r.cells['baseline_lag']==0 and r.cells['current_lag']==40
        assert r.cells['current_successor_name']=='Revised build'


@pytest.mark.parametrize('key',['resources','calendars','calendar_exceptions','controlling_paths','budget_cost','actual_cost','remaining_cost','total_cost'])
def test_unsupported_sections_are_explicit(report,key):
    s=report.section(key)
    assert s.availability==A.NOT_EVALUATED and s.count==0
    assert s.message.startswith('Not evaluated:') and s.diagnostics


def test_empty_supported_section_and_missing_dates(report):
    section=report.section('primary_constraint')
    assert section.availability==A.AVAILABLE
    assert section.message=='No changes identified'
    assert any(c.key=='baseline_date' for c in section.columns)
    for key in ('early_start','early_finish','late_start','late_finish'):
        s=report.section(key)
        assert s.availability==A.NOT_EVALUATED
        assert 'Neither source schedule' in s.diagnostics[0]
        assert all(r.cells['variance'] is None for r in s.rows)
        assert any(c.key=='application_calculated' for c in s.columns)


@pytest.mark.parametrize('baseline,current,variance,percentage',[(40,80,40,1),(40,20,-20,-0.5),(0,5,5,None),(-10,-20,-10,None),(None,20,None,None),(10,None,None,None),(0,0,0,None),(1.25,1.5,0.25,0.2)])
def test_missing_zero_negative_fractional_percentage(baseline,current,variance,percentage):
    value=change_value(baseline,current,'hours')
    assert value.absolute_variance==variance
    assert value.percentage_variance==percentage
    assert value.baseline==baseline and value.current==current
    if baseline is None or current is None:
        assert value.availability==A.NOT_APPLICABLE
        assert value.classification==C.NOT_COMPARABLE


def test_date_variance_and_timezone_guard():
    start=datetime(2026,1,1,8)
    v=change_value(start,start-timedelta(minutes=30),'elapsed_hours',direction='date')
    assert v.absolute_variance==-0.5 and v.classification==C.IMPROVED
    assert v.percentage_variance is None
    bad=change_value(start,start.replace(tzinfo=timezone.utc),'elapsed_hours')
    assert bad.availability==A.BLOCKED and bad.absolute_variance is None


def test_ambiguity_does_not_get_variances(comparison):
    a=comparison.current_version.schedule.get_activity('A1200')
    dup=replace(a,activity_id='ambiguous-task')
    comparison.current_version.schedule.activities[dup.activity_id]=dup
    comparison.current_version.schedule.rebuild_activity_indexes()
    result=ScheduleComparisonEngine().compare(comparison.baseline_version,comparison.current_version)
    report=ForensicReportBuilder().build(result)
    ambiguous=[r for r in report.section('activities').rows if r.cells['match_classification']=='AMBIGUOUS']
    assert ambiguous and all(r.classification=='NOT_COMPARABLE' for r in ambiguous)
    assert all(r.availability==A.NOT_APPLICABLE for r in ambiguous)
    assert all(r.cells['variance'] is None for r in report.section('original_duration').rows if r.context.activity_id=='A1200')


def test_source_immutability_and_no_analysis_calls(comparison,monkeypatch):
    before=copy.deepcopy(comparison)
    monkeypatch.setattr(ScheduleComparisonEngine,'compare',lambda *a,**kw:pytest.fail('Builder recalculated comparison'))
    a=ForensicReportBuilder().build(comparison,generated_at=NOW,report_identifier='same')
    b=ForensicReportBuilder().build(comparison,generated_at=NOW,report_identifier='same')
    assert report_json(a)==report_json(b)
    assert comparison==before


def test_primary_secondary_constraints_preserved(comparison):
    b=comparison.baseline_version.schedule.get_activity('A1000')
    c=comparison.current_version.schedule.get_activity('A1000')
    b.primary_constraint_type='START_ON_OR_AFTER';b.raw_primary_constraint_type='CS_MSOA';b.primary_constraint_date=datetime(2026,2,1)
    c.primary_constraint_type='START_ON_OR_AFTER';c.raw_primary_constraint_type='CS_MSOA';c.primary_constraint_date=datetime(2026,2,2)
    c.secondary_constraint_type='FINISH_ON_OR_BEFORE';c.raw_secondary_constraint_type='CS_MEOB';c.secondary_constraint_date=datetime(2026,4,1)
    report=ForensicReportBuilder().build(comparison)
    primary=activity_row(report,'primary_constraint','A1000')
    assert not primary.cells['type_changed'] and primary.cells['date_changed']
    assert primary.cells['baseline_raw_type']=='CS_MSOA'
    secondary=activity_row(report,'secondary_constraint','A1000')
    assert secondary.cells['baseline_type'] is None
    assert secondary.cells['current_type']=='FINISH_ON_OR_BEFORE'
    assert secondary.cells['type_changed'] and secondary.cells['date_changed']


def test_granular_cpm_availability_does_not_leak_blocked_values(comparison):
    a=comparison.current_version.schedule.get_activity('A1200')
    a.early_start=datetime(2026,2,25,8);a.late_start=datetime(2026,2,25,8)
    result=SimpleNamespace(activity_id=a.activity_id,early_date_status='EARLY_DATES_CALCULATED',late_date_status='LATE_DATES_BLOCKED',float_status='FLOAT_BLOCKED',
        calculated_early_start=datetime(2026,2,26,8),calculated_early_finish=datetime(2026,3,10,17),calculated_late_finish=None,calculated_late_start=datetime(2026,3,1,8),calculated_total_float_hours=999,
        calculated_free_float_hours=999,calculated_critical=False,diagnostics=())
    cpm=SimpleNamespace(schedule=comparison.current_version.schedule,activity_results=[result])
    report=ForensicReportBuilder().build(comparison,cpm_result=cpm)
    early=activity_row(report,'early_start','A1200')
    assert early.cells['application_calculated']==datetime(2026,2,26,8)
    assert early.cells['calculation_availability']=='AVAILABLE'
    late=activity_row(report,'late_start','A1200')
    assert late.cells['application_calculated'] is None and late.cells['calculation_availability']=='BLOCKED'
    tf=activity_row(report,'total_float','A1200')
    assert tf.cells['application_calculated'] is None and tf.cells['calculation_availability']=='BLOCKED'
    assert tf.cells['application_free_float'] is None
    assert report.metadata.selected_analysis_anchor is None
    with pytest.raises(ValueError,match='current schedule'):
        ForensicReportBuilder().build(comparison,cpm_result=SimpleNamespace(schedule=copy.deepcopy(cpm.schedule)))


def test_summary_exposes_counts_tops_and_no_merged_scores(report):
    metrics={r.cells['metric']:r.cells.get('value') for r in report.section('summary').rows}
    assert metrics['Matched Activity Count']==6
    assert metrics['Baseline Only Count']==1 and metrics['Current Only Count']==1
    assert metrics['Wbs Changes']==1
    assert metrics['DCMA Critical Path Test']=='NOT_EVALUATED'
    assert metrics['CPLI']=='NOT_EVALUATED'
    assert metrics['Completion authority']=='NOT_ESTABLISHED'
    tops=[r for r in report.section('summary').rows if r.cells['metric']=='Top finish delay']
    assert tops[0].cells['activity_id']=='A1200' and tops[0].cells['variance']==168


def test_json_contract_pagination_keeps_counts_and_exact_values(report):
    data=serialize_report(report,offset=0,limit=1)
    section=next(s for s in data['sections'] if s['key']=='activities')
    assert section['count']==8 and len(section['rows'])==1
    assert section['has_more'] and not section['truncated']
    assert section['pagination']=={'offset':0,'limit':1,'returned':1,'total':8}
    assert section['filters'] and section['sort_metadata'] and section['columns']
    assert section['filters'][0]['column_key']=='sequence'
    assert 'is_missing' in section['filters'][0]['operators']
    payload=json.loads(report_json(report))
    assert payload['metadata']['generated_at']==NOW.isoformat()
    row=next(r for r in payload['sections'] if r['key']=='original_duration')['rows'][0]
    assert 'change_values' in row and 'context' in row
    assert payload['metadata']['selected_analysis_anchor'] is None
    with pytest.raises(ValueError):serialize_report(report,limit=0)


def test_explicit_resource_limits(comparison):
    with pytest.raises(ReportLimitError):
        ForensicReportBuilder(ReportLimits(maximum_rows_per_section=2)).build(comparison)
    with pytest.raises(ValueError):ReportLimits(maximum_rows_per_section=0)


def test_excel_structure_typed_dates_formats_filters_freeze(report):
    workbook=load_workbook(BytesIO(ExcelReportRenderer().render(report)))
    assert workbook.sheetnames==[s.sheet_name for s in report.sections]
    for s in report.sections:
        ws=workbook[s.sheet_name]
        assert [c.value for c in ws[6]]==[c.title for c in s.columns]
        assert ws.freeze_panes in ('D7','A7')
        assert ws.auto_filter.ref is not None
        assert ws['A1'].value=='Schedule Assurance Forensic Change Report'
        if not s.rows:assert ws['A7'].value==s.message
    ws=workbook['Planned Finish'];section=report.section('planned_finish')
    idx=next(i for i,r in enumerate(section.rows,7) if r.context.activity_id=='A1200')
    keys=[c.key for c in section.columns]
    date=ws.cell(idx,keys.index('current_value')+1)
    assert isinstance(date.value,datetime) and date.number_format=='yyyy-mm-dd hh:mm'
    assert ws.cell(idx,keys.index('elapsed_days')+1).value==7
    ws=workbook['Original Duration'];keys=[c.key for c in report.section('original_duration').columns]
    assert ws.cell(7,keys.index('percentage')+1).number_format=='0.00%'
    ws=workbook['Total Float'];keys=[c.key for c in report.section('total_float').columns]
    idx=next(i for i,r in enumerate(report.section('total_float').rows,7) if r.context.activity_id=='A1200')
    assert ws.cell(idx,keys.index('application_calculated')+1).value is None
    assert ws.cell(idx,keys.index('calculation_availability')+1).value=='NOT_EVALUATED'
    assert ws.cell(idx,keys.index('classification')+1).fill.fgColor.rgb.endswith('F7DBDC')
    assert not any(cell.data_type=='f' for ws in workbook for row in ws for cell in row)


def test_untrusted_text_is_never_an_excel_formula(report):
    section=report.section('diagnostics')
    row=ReportRow({'code':'=1+1','severity':'@SUM(A1)','message':'=HYPERLINK("https://example.org","x")'})
    report=replace(report,sections=(replace(section,rows=(row,),count=1),))
    wb=load_workbook(BytesIO(ExcelReportRenderer().render(report)))
    assert wb.active['A7'].value=='=1+1' and wb.active['A7'].data_type=='s'
    assert wb.active['D7'].data_type=='s'


def test_streaming_large_row_set_and_preview_bound(report):
    section=report.section('diagnostics');count=25000
    rows=tuple(ReportRow({'code':f'R{i}','message':'Synthetic large export'}) for i in range(count))
    large=replace(report,sections=(replace(section,rows=rows,count=count),))
    xlsx=ExcelReportRenderer().render(large)
    workbook=load_workbook(BytesIO(xlsx),read_only=True)
    values=list(workbook.active.iter_rows(min_row=7,max_col=1,values_only=True))
    assert len(values)==count and values[-1][0]=='R24999'
    data=serialize_report(large,offset=24990,limit=5)['sections'][0]
    assert data['count']==count and len(data['rows'])==5 and data['has_more']


def test_service_import_and_cleanup_unsupported_input():
    service=ForensicReportingService()
    report=service.from_bytes((ROOT/'sample_data/sample_baseline.xer').read_bytes(),(ROOT/'sample_data/sample_current.xer').read_bytes(),'baseline.xer','current.xer')
    assert report.section('activities').count==8
    with pytest.raises(ReportInputError):service.from_bytes(b'',b'','bad.xlsx','current.xer')
    with pytest.raises(ReportInputError):service.from_bytes(b'not a xer',b'','baseline.xer','current.xer')
    with pytest.raises(ReportLimitError):ForensicReportingService(ReportLimits(maximum_upload_bytes=1)).from_bytes(b'ab',b'','baseline.xer','current.xer')


def test_calendar_assignment_uses_existing_name_based_domain_policy(comparison):
    current=comparison.current_version.schedule
    previous=current.calendars['C1']
    current.calendars['other']=replace(previous,calendar_id='other')
    current.get_activity('A1200').calendar_id='other'
    result=ScheduleComparisonEngine().compare(comparison.baseline_version,comparison.current_version)
    report=ForensicReportBuilder().build(result)
    assert not any(r.context.activity_id=='A1200' for r in report.section('calendar_assignment').rows)
    assert report.section('calendars').availability==A.NOT_EVALUATED


def test_unchanged_comparison_has_explicit_empty_sections(comparison):
    source=comparison.baseline_version
    result=ScheduleComparisonEngine().compare(source,source)
    report=ForensicReportBuilder().build(result)
    for key in ('relationships','description','original_duration','remaining_duration','planned_finish','primary_constraint'):
        assert report.section(key).count==0
        assert report.section(key).message=='No changes identified'
    assert report.section('activities').count==7
    assert all(r.classification=='UNCHANGED' for r in report.section('activities').rows)


def test_json_model_retains_raw_signed_variance():
    value=change_value(3,2,'hours')
    row=ReportRow({},change_values={'duration':value})
    from app.reporting.serialization import to_json_value
    data=to_json_value(row)
    assert data['change_values']['duration']['absolute_variance']==-1
    assert data['change_values']['duration']['percentage_variance']==-1/3
    assert data['change_values']['duration']['provenance']==['IMPORTED_P6','BASELINE_COMPARISON']


def test_explicit_units_and_categorical_columns(report):
    headers={c.key:c.title for c in report.section('original_duration').columns}
    assert headers['baseline_value']=='Baseline Duration (h)'
    assert headers['current_value']=='Current Duration (h)'
    assert {c.key:c.title for c in report.section('total_float').columns}['baseline_value']=='Baseline Imported TF (h)'
    assert not any(c.key=='percentage' for c in report.section('planned_finish').columns)
    assert not any(c.key in ('variance','percentage') for c in report.section('description').columns)
    records=next(r for r in report.section('summary').rows if r.cells['metric']=='Date change records')
    assert records.cells['value']==1


def test_free_float_only_change_is_visible(comparison):
    current=comparison.current_version.schedule
    current.get_activity('A1000').free_float_hours=3
    result=ScheduleComparisonEngine().compare(comparison.baseline_version,comparison.current_version)
    report=ForensicReportBuilder().build(result)
    row=activity_row(report,'total_float','A1000')
    assert row.cells['variance']==0
    assert row.cells['free_float_variance']==3
    assert row.change_values['free_float_hours'].absolute_variance==3
    assert row.classification=='IMPROVED'
