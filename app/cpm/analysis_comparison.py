"""Availability-filtered selected-analysis comparisons; no calculation tuning."""
from statistics import median
from app.calendars.working_time import working_hours_between


def compare_selected(schedule,results,config):
    metrics={}
    records=[]
    for name in ('late_start','late_finish','total_float','free_float'):
        suffix='_hours' if 'float' in name else ''
        rows=[];missing_imported=0;unavailable=0
        for r in results:
            if r.date_basis=='PRESERVED_ACTUALS':continue
            imported=getattr(schedule.activities[r.activity_id],name+suffix)
            calculated=getattr(r,'calculated_'+name+suffix)
            if calculated is None:
                unavailable+=1;continue
            if imported is None:
                missing_imported+=1;continue
            date='float' not in name
            variance=(calculated-imported).total_seconds()/3600 if date else calculated-imported
            working=working_hours_between(schedule.calendars[r.effective_calendar_id],imported,calculated) if date else None
            tolerance=config.comparison_date_tolerance_seconds/3600 if date else config.comparison_float_tolerance_hours
            status='EXACT_MATCH' if variance==0 else 'WORKING_TIME_EQUIVALENT' if date and working==0 else 'TOLERANCE_MATCH' if abs(variance)<=tolerance else 'DIFFERENCE'
            row=dict(activity_id=r.activity_id,activity_code=r.activity_code,metric=name,imported=imported,calculated=calculated,
                variance_hours=variance,working_variance_hours=working,classification=status)
            rows.append(row);records.append(row)
        metrics[name]=dict(comparable_count=len(rows),exact_matches=sum(r['classification']=='EXACT_MATCH' for r in rows),
            working_equivalent_matches=sum(r['classification']=='WORKING_TIME_EQUIVALENT' for r in rows),
            tolerance_matches=sum(r['classification']=='TOLERANCE_MATCH' for r in rows),differences=sum(r['classification']=='DIFFERENCE' for r in rows),
            missing_imported=missing_imported,missing_calculated=unavailable,
            median_absolute_variance_hours=median(abs(r['variance_hours']) for r in rows) if rows else None,
            maximum_absolute_variance_hours=max((abs(r['variance_hours']) for r in rows),default=None),
            largest_differences=tuple(sorted(rows,key=lambda r:(-abs(r['variance_hours']),r['activity_code'],r['activity_id']))[:20]))
    proxy=[r for r in results if r.calculated_total_float_hours is not None and r.imported_total_float_hours is not None]
    critical=dict(basis='IMPORTED_TOTAL_FLOAT_THRESHOLD_PROXY_NOT_AUTHORITATIVE_P6_CRITICAL_FLAG',threshold_hours=config.critical_float_threshold_hours,
        comparable_count=len(proxy),agreements=sum(r.imported_critical==r.calculated_critical for r in proxy),
        application_only_critical=sum(r.calculated_critical and not r.imported_critical for r in proxy),
        imported_proxy_only_critical=sum(r.imported_critical and not r.calculated_critical for r in proxy),
        authoritative_p6_critical_agreement='NOT_EVALUATED')
    return metrics,tuple(records),critical
