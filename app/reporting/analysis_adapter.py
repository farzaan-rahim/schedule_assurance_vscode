"""Optional projection of completed selected analysis; no analytical calls."""
from dataclasses import replace
from app.cpm.completion_evidence import _wbs_path
from app.reporting.models import Availability as A, Provenance as P, ReportColumn, ReportFilter, ReportRow
from app.reporting.limits import ReportLimitError, ReportLimits


def attach_analysis(report,analysis,*,current_schedule,limits=None):
    if analysis.cpm_result.schedule is not current_schedule:
        raise ValueError('Selected analysis must belong to the current comparison schedule.')
    limits=limits or ReportLimits();a=analysis.anchor
    metadata=replace(report.metadata,selected_analysis_anchor=a,completion_authority_status=a.contractual_authority_status,
        analysis_anchor_selection_method=a.selection_method,analysis_anchor_timestamp=a.selected_timestamp,
        analysis_anchor_timestamp_source=a.timestamp_source,analysis_mode=analysis.mode)
    sections=[]
    by_id={r.activity_id:r for r in analysis.cpm_result.activity_results}
    availability={r.activity_id:r for r in analysis.activity_dispositions}
    for section in report.sections:
        if section.key=='summary':
            rows=[]
            for row in section.rows:
                if row.cells.get('metric')=='Selected analysis anchor':
                    rows.append(replace(row,cells={**row.cells,'value':a.activity_code},availability=A.AVAILABLE))
                elif row.cells.get('metric')=='Completion authority':
                    rows.append(replace(row,cells={**row.cells,'value':a.contractual_authority_status}))
                else:rows.append(row)
            for label,value in [('Analysis mode',analysis.mode),('Analysis anchor name',a.activity_name),('Analysis anchor selection method',a.selection_method),
                ('Analysis anchor timestamp',a.selected_timestamp),('Analysis anchor timestamp source',a.timestamp_source),
                ('Analysis selection reason',a.selection_reason),('Application calculated controlling paths',len(analysis.cpm_result.critical_paths))]:
                rows.append(ReportRow({'metric':label,'value':value},provenance=(P.APPLICATION_CALCULATED,)))
            if len(rows)>limits.maximum_rows_per_section:raise ReportLimitError('Selected analysis summary exceeds the report row limit.')
            section=replace(section,rows=tuple(rows),count=len(rows),pagination={'offset':0,'returned':len(rows),'total':len(rows)})
        elif section.key=='controlling_paths':
            columns=tuple(ReportColumn(k,title,kind,width) for k,title,kind,width in (
                ('anchor_activity_id','Anchor Activity ID','text',28),('anchor_name','Anchor Name','text',48),
                ('completion_authority','Completion Authority','text',26),('timestamp_source','Anchor Timestamp Source','text',38),
                ('path_id','Path ID','text',20),('rank','Rank','integer',10),('sequence','Sequence','integer',12),
                ('activity_id','Activity ID','text',28),('internal_task_id','Internal Task ID','text',20),('description','Activity Name','text',48),
                ('wbs_path','WBS','text',48),('relationship_id','Relationship From Predecessor','text',30),
                ('relationship_type','Relationship Type','text',20),('lag_hours','Signed Lag (h)','hours',20),
                ('early_start','Calculated ES','date',26),('early_finish','Calculated EF','date',26),
                ('late_start','Calculated LS','date',26),('late_finish','Calculated LF','date',26),('total_float','Calculated TF (h)','hours',24),
                ('critical','Calculated Critical','boolean',24),('availability','Availability','text',24),
                ('es_availability','ES Availability','text',24),('ls_availability','LS Availability','text',24),
                ('tf_availability','TF Availability','text',24),('path_complete','Path Complete','boolean',20),('truncated','Truncated','boolean',18)))
            rows=[]
            for path in analysis.cpm_result.critical_paths:
                for seq,key in enumerate(path.activity_ids,1):
                    if len(rows)>=limits.maximum_rows_per_section:raise ReportLimitError('Selected path rows exceed the explicit report row limit.')
                    r=by_id[key];d=availability[key];raw=current_schedule.activities[key]
                    edge=path.relationships[seq-2] if seq>1 else None
                    rows.append(ReportRow(dict(anchor_activity_id=a.activity_code,anchor_name=a.activity_name,
                        completion_authority=a.contractual_authority_status,timestamp_source=a.timestamp_source,path_id=path.path_id,rank=path.rank,
                        sequence=seq,activity_id=r.activity_code,internal_task_id=key,description=r.activity_name,
                        wbs_path=' > '.join(_wbs_path(current_schedule,raw.wbs_id)),relationship_id=edge.relationship_id if edge else None,
                        relationship_type=edge.relationship_type if edge else None,lag_hours=edge.lag_hours if edge else None,
                        early_start=r.calculated_early_start,early_finish=r.calculated_early_finish,late_start=r.calculated_late_start,
                        late_finish=r.calculated_late_finish,total_float=r.calculated_total_float_hours,critical=r.calculated_critical,
                        es_availability=d.es_availability,ls_availability=d.ls_availability,tf_availability=d.total_float_availability,
                        path_complete=path.trace_complete,truncated=path.truncated),classification='APPLICATION_CALCULATED_CONTROLLING_PATH',
                        provenance=(P.APPLICATION_CALCULATED,),diagnostics=tuple(x.code for x in path.diagnostics)))
            status=A.AVAILABLE if rows else A.BLOCKED
            reason=None if rows else 'Not evaluated: selected analysis endpoint or controlling predecessors lack reliable early/float/path availability. '+analysis.path_status
            section=replace(section,columns=columns,rows=tuple(rows),count=len(rows),availability=status,message=reason,
                diagnostics=tuple(d.code for d in analysis.diagnostics) if rows else (reason,),
                filters=tuple(ReportFilter(c.key,('equals','is_missing')) for c in columns),sort_metadata=('Path rank','Sequence'),
                pagination={'offset':0,'returned':len(rows),'total':len(rows)},truncated=any(s.truncated for s in analysis.cpm_result.path_statistics))
        sections.append(section)
    return replace(report,metadata=metadata,sections=tuple(sections))
