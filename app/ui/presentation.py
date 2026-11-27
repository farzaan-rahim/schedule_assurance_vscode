"""Formatting/filtering only: no schedule arithmetic or classification formulas."""
from dataclasses import fields,is_dataclass
from enum import Enum
from datetime import datetime,date
import json
from fastapi.encoders import jsonable_encoder
from app.reporting.serialization import to_json_value
from app.ui.state import TableQuery

STATUS_COLORS={'PASS':'positive','WARNING':'warning','FAIL':'negative','NOT_EVALUATED':'grey-7',
    'NOT_APPLICABLE':'grey-7','BLOCKED':'negative','EXCLUDED':'grey-7','AVAILABLE':'positive',
    'ADDED':'positive','REMOVED':'negative','DELAYED':'warning','DETERIORATED':'negative'}

def text(value):
    if value is None:return 'Not available'
    if isinstance(value,Enum):return value.value
    if isinstance(value,(datetime,date)):return value.isoformat(sep=' ') if isinstance(value,datetime) else value.isoformat()
    if isinstance(value,(dict,list,tuple)):return json.dumps(to_json_value(value),ensure_ascii=False)
    return str(value)

def record(value):
    if isinstance(value,dict):return value
    return {f.name:getattr(value,f.name) for f in fields(value)} if is_dataclass(value) else {'value':value}

def report_record(row):
    context=record(row.context) if row.context else {}
    return {**context,**row.cells,'classification':row.classification,'availability':row.availability,
        'provenance':row.provenance,'diagnostics':row.diagnostics,'change_values':row.change_values}

def page_rows(rows,query=None,*,projector=record):
    q=query or TableQuery();matched=[]
    for index,item in enumerate(rows):
        row=projector(item)
        if q.search and q.search.casefold() not in ' '.join(text(row.get(k,'')) for k in
            ('activity_id','activity_code','activity_name','description','name','message','predecessor_activity_id','successor_activity_id','predecessor_activity_code','successor_activity_code','predecessor_activity_name','successor_activity_name','code','project_code','project_name')).casefold():continue
        if q.wbs and q.wbs.casefold() not in text(row.get('wbs_path',row.get('wbs',''))).casefold():continue
        if any(getattr(q,k) and getattr(q,k).casefold()!=text(row.get(k,'')).casefold() for k in ('status','activity_type','classification','severity','category')):continue
        matched.append((index,item))
    if q.sort:
        def order(pair):
            v=projector(pair[1]).get(q.sort)
            if isinstance(v,Enum):v=v.value
            return (v is None, 0 if isinstance(v,(int,float)) else 1, v if isinstance(v,(int,float)) else text(v).casefold(),pair[0])
        matched.sort(key=order,reverse=q.descending)
    selected=matched[q.offset:q.offset+q.limit]
    return dict(rows=[dict(jsonable_encoder(to_json_value(projector(item))),_row_key=index) for index,item in selected],total=len(matched),
        offset=q.offset,limit=q.limit,has_more=q.offset+len(selected)<len(matched))

def metric_evidence(metric):
    """Bounded audit view; do not send complete CPM networks to the browser."""
    d=metric.details
    if metric.metric_id=='critical_path_test':
        sim=d.get('simulation') or {}
        keys=('source_completion_timestamp','simulated_completion_timestamp','completion_movement_working_hours',
            'completion_movement_elapsed_hours','completion_calendar_id','anchor_policy','original_effective_duration_hours',
            'simulated_effective_duration_hours','duration_change_hours','source_completion_anchor','simulated_completion_anchor','diagnostics')
        return dict(status=metric.status,selected_activity_id=d.get('selected_activity_id'),selected_activity_code=sim.get('selected_activity_code'),selection_reason=d.get('selection_reason'),
            injected_delay_hours=d.get('injected_delay_hours'),response_ratio=d.get('response_ratio'),configuration=d.get('config'),
            cpm_configuration=d.get('cpm_config'),diagnostics=d.get('diagnostics'),**{k:sim.get(k) for k in keys if k!='diagnostics'},simulation_diagnostics=sim.get('diagnostics'))
    keys=('status','critical_path_length_hours','required_finish','required_finish_source','calculated_finish','total_float_hours',
        'native_anchor_total_float_hours','float_source','numerator_hours','denominator_hours','value','formula','formula_version',
        'calendar_id','sum_effective_activity_duration_hours','relationship_lag_contribution_hours','config','cpm_config','diagnostics')
    result={k:d.get(k) for k in keys}
    result['unrounded_cpli']=d.get('value')
    result['displayed_cpli']=format(d['value'],'.3f') if d.get('value') is not None else None
    return result



def selected_analysis_rows(analysis,early_comparisons=()):
    """Join existing per-metric comparisons to directional rows; no variances computed."""
    results={r.activity_id:r for r in analysis.cpm_result.activity_results}
    comparisons={}
    for c in analysis.comparisons:
        row=comparisons.setdefault(c['activity_id'],{})
        row[c['metric']+'_variance_hours']=c.get('variance_hours')
        row[c['metric']+'_working_variance_hours']=c.get('working_variance_hours')
        row[c['metric']+'_comparison']=c.get('classification')
    for c in early_comparisons:
        row=comparisons.setdefault(c.activity_id,{})
        row['early_start_variance_hours']=c.early_start_variance_hours
        row['early_finish_variance_hours']=c.early_finish_variance_hours
    rows=[]
    for d in analysis.activity_dispositions:
        a=analysis.cpm_result.schedule.activities.get(d.activity_id)
        r=record(results[d.activity_id]) if d.activity_id in results else dict(activity_id=d.activity_id,activity_code=d.activity_code)
        if a:
            for name in ('early_start','early_finish','late_start','late_finish','total_float_hours','free_float_hours'):
                r['imported_'+name]=getattr(a,name)
            r.update(activity_name=a.activity_name,status=a.status,activity_type=a.activity_type)
        r.update(comparisons.get(d.activity_id,{}));r.update(availability=d.late_status,es_availability=d.es_availability,ef_availability=d.ef_availability,
            ls_availability=d.ls_availability,lf_availability=d.lf_availability,total_float_availability=d.total_float_availability,free_float_availability=d.free_float_availability)
        if d.reason_codes:r['availability_diagnostics']=d.reason_codes
        rows.append(r)
    return rows
