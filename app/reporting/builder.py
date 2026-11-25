from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from uuid import uuid4

from app.comparison.models import ComparisonResult, MatchClassification as M
from app.reporting.change_values import change_value
from app.reporting.limits import ReportLimits, ReportLimitError
from app.reporting.models import (
    ActivityRowContext, Availability as A, ChangeClassification as C, ForensicChangeReport,
    Provenance as P, ReportColumn, ReportFilter, ReportMetadata, ReportRow, ReportSection, ScheduleReference,
)
from app.reporting.sections import AUDIT_COLUMNS, COMMON_COLUMNS, SECTION_DEFINITIONS


class ForensicReportBuilder:
    """Project existing results; never import or invoke an analytical engine here."""

    def __init__(self, limits=None):
        self.limits = limits or ReportLimits()

    def build(self, comparison: ComparisonResult, *, generated_at=None, generated_by=None,
              report_identifier=None, critical_threshold_hours=0.0, cpm_result=None,
              import_diagnostics=(), analysis_result=None):
        baseline = comparison.baseline_version.schedule
        current = comparison.current_version.schedule
        if cpm_result is not None and cpm_result.schedule is not current:
            raise ValueError("Supplied CPM result must belong to the current schedule object.")
        project = current.project
        def reference(version):
            p = version.schedule.project
            return ScheduleReference(version.version_id, version.version_label, version.source_filename,
                version.data_date, p.project_id if p else None, p.project_code if p else None,
                p.project_name if p else None)
        metadata = ReportMetadata(report_identifier or str(uuid4()),
            "Schedule Assurance Forensic Change Report", generated_at or datetime.now(timezone.utc),
            generated_by, project.project_id if project else None, project.project_code if project else None,
            project.project_name if project else None, reference(comparison.baseline_version),
            reference(comparison.current_version),
            {"critical_threshold_hours": critical_threshold_hours,
             "date_variance": "CURRENT_MINUS_BASELINE_ELAPSED_HOURS",
             "percentage": "CURRENT_MINUS_BASELINE_DIVIDED_BY_POSITIVE_BASELINE",
             "matching": "EXISTING_ACTIVITY_CODE_AND_WBS_MATCHER"})
        rows = {key: [] for key, _, _ in SECTION_DEFINITIONS}
        columns = {}
        unavailable = {
            "resources": "RSRC/TASKRSRC are imported; a cross-version resource-assignment comparison service is not implemented.",
            "calendars": "Calendar definition comparison (workweek, shifts and inheritance) is not implemented. Calendar Assignment is separate.",
            "calendar_exceptions": "Cross-version calendar exception comparison is not implemented.",
            "controlling_paths": "Completion authority is NOT_ESTABLISHED; no selected analysis anchor. Real controlling paths are not evaluated.",
        }
        for key in ('budget_cost', 'actual_cost', 'remaining_cost', 'total_cost'):
            unavailable[key] = "Cross-version resource/cost comparison and a validated currency basis are not implemented. Imported assignment costs are not aggregated here."
        def add(key, row):
            if len(rows[key]) >= self.limits.maximum_rows_per_section:
                raise ReportLimitError(f"Section {key} exceeds the explicit report row limit; narrow the comparison or increase the configured limit.")
            rows[key].append(row)
        def col(key, title, kind='text', width=24):
            return ReportColumn(key, title, kind, width)
        def context(v, sequence):
            b, c = v.baseline_activity, v.current_activity
            a = c or b
            schedule = current if c else baseline
            w = schedule.wbs_nodes.get(a.wbs_id)
            def calendar(s, a):
                if a is None: return None
                cal = s.calendars.get(a.calendar_id)
                return cal.calendar_name if cal else a.calendar_id
            return ActivityRowContext(sequence, a.activity_id, a.activity_code, a.activity_name,
                a.activity_type, a.status, a.remaining_duration_hours, w.wbs_code if w else None,
                w.wbs_name if w else None, v.current_wbs_path if c else v.baseline_wbs_path,
                b.activity_id if b else None, c.activity_id if c else None,
                v.baseline_wbs_path, v.current_wbs_path, calendar(baseline,b), calendar(current,c))
        cpm_by_id = {r.activity_id:r for r in cpm_result.activity_results} if cpm_result else {}
        def calculated(a, field, family):
            result = cpm_by_id.get(a.activity_id) if a else None
            if result is None:
                return None, A.NOT_EVALUATED, 'No application CPM result was supplied for this activity.'
            state = getattr(result, {'early':'early_date_status','late':'late_date_status','float':'float_status'}[family])
            allowed = state in {'EARLY_DATES_CALCULATED','LATE_DATES_CALCULATED','FLOAT_CALCULATED','CALCULATED'}
            value = getattr(result, field)
            if allowed and value is not None:
                return value, A.AVAILABLE, None
            availability = A.EXCLUDED if state == 'EXCLUDED' else A.BLOCKED if 'BLOCKED' in state else A.NOT_EVALUATED
            return None, availability, '; '.join([state] + [d.code for d in result.diagnostics])
        critical_sets = [set(a.activity_id for a in s.get_critical_activities(critical_threshold_hours)) for s in (baseline,current)]
        classifications = {M.BASELINE_ONLY:C.REMOVED, M.CURRENT_ONLY:C.ADDED, M.AMBIGUOUS:C.NOT_COMPARABLE}
        # Context objects are shared across category views; schedules are never copied into reports.
        ordered = sorted(comparison.activity_variances, key=lambda v:(v.activity_code.casefold(),
            v.baseline_activity.activity_id if v.baseline_activity else '',
            v.current_activity.activity_id if v.current_activity else ''))
        for seq,v in enumerate(ordered,1):
            b,c = v.baseline_activity,v.current_activity
            ctx=context(v,seq); matched=v.classification == M.MATCHED
            flag_changes = [(v.name_changed,'DESCRIPTION'),(v.wbs_changed,'WBS_MOVED'),
                (v.calendar_changed,'CALENDAR_ASSIGNMENT'),(v.activity_type_changed,'TYPE_CHANGED'),
                (v.status_changed,'STATUS_CHANGED'),(v.start_changed,'PLANNED_START'),(v.finish_changed,'PLANNED_FINISH')]
            for name in ('original_duration_variance_hours','remaining_duration_variance_hours','total_float_variance_hours','free_float_variance_hours'):
                flag_changes.append((getattr(v,name) not in (None,0),name))
            # Include imported early/late and constraint changes even when not exposed as flags by the comparison engine.
            extra_fields = ('early_start','early_finish','late_start','late_finish','primary_constraint_type',
                'primary_constraint_date','secondary_constraint_type','secondary_constraint_date','free_float_hours')
            changed_fields = [name for flag,name in flag_changes if flag]
            if matched:
                changed_fields += [name for name in extra_fields if getattr(b,name) != getattr(c,name)]
            cls=classifications.get(v.classification,C.CHANGED if changed_fields else C.UNCHANGED)
            if v.wbs_changed: changed_fields.append('WBS_MOVED') if 'WBS_MOVED' not in changed_fields else None
            add('activities',ReportRow({'match_classification':v.classification.value,'match_method':v.match_method.value if v.match_method else None,
                'baseline_description':b.activity_name if b else None,'current_description':c.activity_name if c else None,
                'change_categories':tuple(changed_fields)},context=ctx,classification=cls.value,
                availability=A.NOT_APPLICABLE if v.classification==M.AMBIGUOUS else A.AVAILABLE,
                diagnostics=('Ambiguous identity; no comparative variance is asserted.',) if v.classification==M.AMBIGUOUS else ()))
            specifications = [
                ('description','activity_name','text',None,None),
                ('activity_type','activity_type','text',None,None),
                ('original_duration','original_duration_hours','hours','hours','duration'),
                ('remaining_duration','remaining_duration_hours','hours','hours','duration'),
                ('total_float','total_float_hours','hours','hours','float'),
                ('status','status','text',None,None),
                *[(name,name,'date','elapsed_hours','date') for name in ('planned_start','planned_finish','early_start','early_finish','late_start','late_finish')],
            ]
            for key,field,kind,unit,direction in specifications:
                old=getattr(b,field) if b else None;new=getattr(c,field) if c else None
                value=change_value(old,new,unit,comparable=matched,direction=direction)
                # Category sheets contain changed/missing-side records; unchanged detail stays in Activities.
                if matched and old==new and not (key=='total_float' and b.free_float_hours!=c.free_float_hours): continue
                cells={'baseline_value':old,'current_value':new,'variance':value.absolute_variance,
                    'percentage':value.percentage_variance,'elapsed_days':value.absolute_variance/24 if kind=='date' and value.absolute_variance is not None else None}
                if key=='total_float' or key in ('early_start','early_finish','late_start','late_finish','planned_start','planned_finish'):
                    family='float' if key=='total_float' else 'late' if key.startswith('late') else 'early'
                    calcfield='calculated_total_float_hours' if key=='total_float' else 'calculated_'+key.replace('planned','early')
                    calc,availability,reason=calculated(c,calcfield,family)
                    cells.update(application_calculated=calc,calculation_availability=availability.value,
                                 calculation_provenance=P.APPLICATION_CALCULATED.value,calculation_diagnostics=reason)
                if key=='total_float':
                    ff,ff_avail,ff_reason=calculated(c,'calculated_free_float_hours','float')
                    cells.update(baseline_free_float=b.free_float_hours if b else None,current_free_float=c.free_float_hours if c else None,
                        free_float_variance=v.free_float_variance_hours,application_free_float=ff,free_float_availability=ff_avail.value,free_float_diagnostics=ff_reason)
                if key=='total_float' and value.classification==C.UNCHANGED:
                    label=change_value(b.free_float_hours if b else None,c.free_float_hours if c else None,'hours',comparable=matched,direction='float').classification
                elif key=='activity_type' and value.classification==C.CHANGED: label=C.TYPE_CHANGED
                elif key=='status' and value.classification==C.CHANGED:label=C.STATUS_CHANGED
                else:label=value.classification
                values={field:value}
                if key=='total_float':
                    values['free_float_hours']=change_value(b.free_float_hours if b else None,c.free_float_hours if c else None,'hours',comparable=matched,direction='float')
                add(key,ReportRow(cells,values,ctx, label.value,value.availability,diagnostics=value.diagnostics))
                columns[key]=COMMON_COLUMNS+(col('baseline_value','Baseline Imported Value',kind),col('current_value','Current Imported Value',kind),
                    col('variance','Variance (elapsed h)' if kind=='date' else 'Variance (h)','hours'),
                    col('percentage','Percentage Variance','percentage'))
                if kind=='date':columns[key]+=(col('elapsed_days','Variance (elapsed calendar days)','number',30),)
                if 'application_calculated' in cells:
                    columns[key]+=(col('application_calculated','Application Calculated '+('TF (h)' if key=='total_float' else key.replace('planned','early').replace('_',' ').title()),kind,30),
                        col('calculation_availability','Calculation Availability',width=26),col('calculation_provenance','Calculation Provenance',width=30),
                        col('calculation_diagnostics','Calculation Diagnostics',width=60))
            if not matched or v.calendar_changed:
                value=change_value(ctx.baseline_calendar,ctx.current_calendar,comparable=matched)
                add('calendar_assignment',ReportRow({'baseline_value':ctx.baseline_calendar,'current_value':ctx.current_calendar},
                    {'calendar_assignment':value},ctx,value.classification.value,value.availability,diagnostics=value.diagnostics))
            for slot in ('primary','secondary'):
                fields=[slot+'_constraint_'+suffix for suffix in ('type','date')]
                old=[getattr(b,f) if b else None for f in fields];new=[getattr(c,f) if c else None for f in fields]
                if old==new:continue
                values={f:change_value(x,y,'elapsed_hours' if f.endswith('date') else None,comparable=matched) for f,x,y in zip(fields,old,new)}
                add(slot+'_constraint',ReportRow({'baseline_type':old[0],'baseline_date':old[1],
                    'current_type':new[0],'current_date':new[1],
                    'baseline_raw_type':getattr(b,'raw_'+slot+'_constraint_type') if b else None,
                    'current_raw_type':getattr(c,'raw_'+slot+'_constraint_type') if c else None,
                    'type_changed':old[0]!=new[0] if matched else None,'date_changed':old[1]!=new[1] if matched else None},
                    values,ctx,C.CHANGED.value if matched else C.NOT_COMPARABLE.value,A.AVAILABLE if matched else A.NOT_APPLICABLE))
            # Explicit imported TF-threshold interpretation, not a claim about P6's configured longest-path critical flag.
            oldcrit=b.activity_id in critical_sets[0] if b and b.total_float_hours is not None else None
            newcrit=c.activity_id in critical_sets[1] if c and c.total_float_hours is not None else None
            if not matched or oldcrit!=newcrit:
                val=change_value(oldcrit,newcrit,comparable=matched)
                calc,avail,reason=calculated(c,'calculated_critical','float')
                add('criticality',ReportRow({'baseline_value':oldcrit,'current_value':newcrit,
                    'imported_basis':'IMPORTED_TOTAL_FLOAT_THRESHOLD', 'threshold_hours':critical_threshold_hours,
                    'application_calculated':calc,'calculation_availability':avail.value,'calculation_diagnostics':reason},
                    {'criticality':val},ctx,val.classification.value,val.availability,diagnostics=val.diagnostics))
        # Define schemas even for empty supported or unavailable sections.
        for key,kind in [('description','text'),('activity_type','text'),('original_duration','hours'),('remaining_duration','hours'),
                         ('total_float','hours'),('status','text'),*[(k,'date') for k in ('planned_start','planned_finish','early_start','early_finish','late_start','late_finish')]]:
            if key not in columns:
                columns[key]=COMMON_COLUMNS+(col('baseline_value','Baseline Imported Value',kind),col('current_value','Current Imported Value',kind),
                    col('variance','Variance (elapsed h)' if kind=='date' else 'Variance (h)','hours'),col('percentage','Percentage Variance','percentage'))
                if kind=='date':columns[key]+=(col('elapsed_days','Variance (elapsed calendar days)','number',30),)
                if key=='total_float' or kind=='date':
                    columns[key]+=(col('application_calculated','Application Calculated TF (h)' if key=='total_float' else 'Application Calculated '+key.replace('planned','early').replace('_',' ').title(),kind,30),
                        col('calculation_availability','Calculation Availability',width=26),col('calculation_provenance','Calculation Provenance',width=30),col('calculation_diagnostics','Calculation Diagnostics',width=60))
        columns['total_float']+=(col('baseline_free_float','Baseline Imported FF (h)','hours'),col('current_free_float','Current Imported FF (h)','hours'),
            col('free_float_variance','Imported FF Variance (h)','hours'),col('application_free_float','Application Calculated FF (h)','hours',30),
            col('free_float_availability','FF Calculation Availability',width=28),col('free_float_diagnostics','FF Calculation Diagnostics',width=60))
        columns['activities']=COMMON_COLUMNS+tuple(col(k,t,width=w) for k,t,w in (
            ('match_classification','Match Classification',24),('match_method','Match Method',26),
            ('baseline_description','Baseline Description',48),('current_description','Current Description',48),('change_categories','Change Categories',50)))
        columns['calendar_assignment']=COMMON_COLUMNS+(col('baseline_value','Baseline Calendar'),col('current_value','Current Calendar'))
        columns['criticality']=COMMON_COLUMNS+(col('baseline_value','Baseline Imported Critical'),col('current_value','Current Imported Critical'),
            col('imported_basis','Imported Critical Basis',width=36),col('threshold_hours','Threshold (h)','hours'),
            col('application_calculated','Application Calculated Critical',width=30),col('calculation_availability','Calculation Availability',width=26),
            col('calculation_diagnostics','Calculation Diagnostics',width=60))
        for slot in ('primary','secondary'):
            columns[slot+'_constraint']=COMMON_COLUMNS+tuple(col(k,t,kind,width) for k,t,kind,width in (
                ('baseline_type','Baseline Canonical Type','text',30),('baseline_raw_type','Baseline Raw P6 Type','text',24),
                ('baseline_date','Baseline Constraint Date','date',26),('current_type','Current Canonical Type','text',30),
                ('current_raw_type','Current Raw P6 Type','text',24),('current_date','Current Constraint Date','date',26),
                ('type_changed','Type Changed','boolean',18),('date_changed','Date Changed','boolean',18)))
        for v in comparison.relationship_variances:
            if v.change_type.value=='UNCHANGED':continue
            bp,bs,cp,cs=v.baseline_predecessor_activity,v.baseline_successor_activity,v.current_predecessor_activity,v.current_successor_activity
            add('relationships',ReportRow({'predecessor_activity_id':v.predecessor_activity_code,
                'successor_activity_id':v.successor_activity_code,
                'baseline_predecessor_name':bp.activity_name if bp else None,'current_predecessor_name':cp.activity_name if cp else None,
                'baseline_successor_name':bs.activity_name if bs else None,'current_successor_name':cs.activity_name if cs else None,
                'baseline_type':v.baseline_relationship_type,'current_type':v.current_relationship_type,
                'baseline_lag':v.baseline_lag_hours,'current_lag':v.current_lag_hours,
                'baseline_relationship_id':v.baseline_relationship.relationship_id if v.baseline_relationship else None,
                'current_relationship_id':v.current_relationship.relationship_id if v.current_relationship else None},classification=v.change_type.value))
        columns['relationships']=tuple(col(k,t,kind,width) for k,t,kind,width in (
            ('predecessor_activity_id','Predecessor Activity ID','text',26),('baseline_predecessor_name','Baseline Predecessor Name','text',48),
            ('current_predecessor_name','Current Predecessor Name','text',48),('successor_activity_id','Successor Activity ID','text',26),
            ('baseline_successor_name','Baseline Successor Name','text',48),('current_successor_name','Current Successor Name','text',48),
            ('baseline_type','Baseline Relationship Type','text',28),('current_type','Current Relationship Type','text',28),
            ('baseline_lag','Baseline Lag (h)','hours',22),('current_lag','Current Lag (h)','hours',22),
            ('baseline_relationship_id','Baseline Relationship ID','text',26),('current_relationship_id','Current Relationship ID','text',26)))
        for version in (comparison.baseline_version,comparison.current_version):
            ref=reference(version)
            add('projects',ReportRow(dict(version=ref.label,filename=ref.filename,project_id=ref.project_id,
                project_code=ref.project_code,project_name=ref.project_name,data_date=ref.data_date,
                activity_count=len(version.schedule.activities),relationship_count=len(version.schedule.relationships))))
        columns['projects']=tuple(col(k,t,kind,width) for k,t,kind,width in (
            ('version','Version','text',18),('filename','Source File','text',42),('project_id','Project ID','text',20),
            ('project_code','Project Code','text',26),('project_name','Project Name','text',48),('data_date','Data Date','date',26),
            ('activity_count','Activities','integer',18),('relationship_count','Relationships','integer',18)))
        for label,value in [('Project ID',metadata.project_id),('Project Code',metadata.project_code),('Project Name',metadata.project_name),
            ('Source Schedule',metadata.baseline.filename),('Current Schedule',metadata.current.filename),('Baseline Data Date',metadata.baseline.data_date),
            ('Current Data Date',metadata.current.data_date),('Generated By',metadata.generated_by),('Generated At',metadata.generated_at)]:
            add('summary',ReportRow({'metric':label,'value':value}))
        for key,value in asdict(comparison.summary).items():
            add('summary',ReportRow({'metric':key.replace('_',' ').title(),'value':value,'activity_id':None,'variance':None,'unit':'count'}))
        extra_counts={'Constraint changes':sum(len(rows[s+'_constraint']) for s in ('primary','secondary')),
            'Date change records':sum(1 for s in ('planned_start','planned_finish','early_start','early_finish','late_start','late_finish') for r in rows[s] if r.availability==A.AVAILABLE and r.classification not in {'UNCHANGED','NOT_COMPARABLE'})}
        for label,value in extra_counts.items():add('summary',ReportRow({'metric':label,'value':value,'unit':'records'}))
        for key,field,ascending,title in [('planned_finish','finish_variance_hours',False,'Top finish delay'),
            ('total_float','total_float_variance_hours',True,'Top float deterioration'),
            ('original_duration','original_duration_variance_hours',False,'Top original duration increase')]:
            eligible=[v for v in comparison.activity_variances if v.classification==M.MATCHED and getattr(v,field) is not None and (getattr(v,field)<0 if ascending else getattr(v,field)>0)]
            eligible.sort(key=lambda v:(getattr(v,field) if ascending else -getattr(v,field),v.activity_code))
            for v in eligible[:10]:add('summary',ReportRow({'metric':title,'activity_id':v.activity_code,'value':None,'variance':getattr(v,field),'unit':'hours'}))
        for label,value in [('Completion authority','NOT_ESTABLISHED'),('Selected analysis anchor',None),
            ('DCMA Critical Path Test','NOT_EVALUATED'),('CPLI','NOT_EVALUATED')]:
            add('summary',ReportRow({'metric':label,'value':value},availability=A.NOT_EVALUATED))
        columns['summary']=(col('metric','Metric',width=48),col('value','Value',width=30),col('activity_id','Activity ID'),
            col('variance','Variance (h)','hours'),col('unit','Unit',width=18))
        for diagnostic in (*comparison.diagnostics,*import_diagnostics):
            code=getattr(diagnostic,'code','import_diagnostic');message=getattr(diagnostic,'message',str(diagnostic))
            add('diagnostics',ReportRow({'code':code,'message':message,'activity_id':getattr(diagnostic,'activity_code',None),
                'severity':getattr(diagnostic,'severity',None)},classification=C.NOT_COMPARABLE.value))
        for key,reason in unavailable.items():
            add('diagnostics',ReportRow({'code':key+'_not_evaluated','message':reason,'severity':'information'},
                availability=A.NOT_EVALUATED,diagnostics=(reason,)))
        columns['diagnostics']=(col('code','Diagnostic Code',width=38),col('severity','Severity'),col('activity_id','Activity ID'),col('message','Message',width=90))
        sections=[]
        for key,title,sheet in SECTION_DEFINITIONS:
            unavailable_reason=unavailable.get(key)
            section_rows=tuple(rows[key])
            section_columns=columns.get(key,COMMON_COLUMNS)
            availability=A.NOT_EVALUATED if unavailable_reason else A.AVAILABLE
            # A supported date field with no source population must not imply a successful no-change evaluation.
            if key in ('early_start','early_finish','late_start','late_finish') and not any(
                getattr(v.baseline_activity,key,None) is not None or getattr(v.current_activity,key,None) is not None for v in ordered):
                availability=A.NOT_EVALUATED;unavailable_reason='Neither source schedule contains imported '+title+' values.'
            if key in ('description','activity_type','status'):
                section_columns=tuple(c for c in section_columns if c.key not in ('variance','percentage'))
            elif key in ('planned_start','planned_finish','early_start','early_finish','late_start','late_finish'):
                section_columns=tuple(c for c in section_columns if c.key!='percentage')
            if key in ('original_duration','remaining_duration','total_float','description','activity_type','status','planned_start','planned_finish','early_start','early_finish','late_start','late_finish'):
                label='Duration (h)' if key in ('original_duration','remaining_duration') else 'Imported TF (h)' if key=='total_float' else 'Imported '+title if key.endswith(('start','finish')) else title
                section_columns=tuple(replace(c,title=('Baseline ' if c.key=='baseline_value' else 'Current ')+label,width=48 if key=='description' else 28) if c.key in ('baseline_value','current_value') else c for c in section_columns)
            sections.append(ReportSection(key,title,sheet,section_columns+AUDIT_COLUMNS,section_rows,len(section_rows),availability,
                (unavailable_reason,) if unavailable_reason else (),
                'Not evaluated: '+unavailable_reason if unavailable_reason else None if section_rows else 'No changes identified',
                filters=tuple(ReportFilter(c.key,('equals','is_missing','contains') if c.data_type=='text' else ('equals','is_missing','greater_than','less_than')) for c in section_columns+AUDIT_COLUMNS),
                sort_metadata=('Activity ID, baseline internal ID, current internal ID',) if key not in ('summary','projects','relationships','diagnostics') else ('Domain result order',),
                pagination={'offset':0,'returned':len(section_rows),'total':len(section_rows)}))
        report=ForensicChangeReport(metadata,tuple(sections))
        if analysis_result is not None:
            from app.reporting.analysis_adapter import attach_analysis
            return attach_analysis(report,analysis_result,current_schedule=current,limits=self.limits)
        return report
