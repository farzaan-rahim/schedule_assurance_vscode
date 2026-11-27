"""Thin adapters: scheduling/simulation mathematics belong to CPM services."""
from dataclasses import fields,is_dataclass,asdict
from app.cpm.simulation import CriticalPathTestService
from app.cpm.cpli import CPLIService
from app.cpm.models import CPMResult
from app.dcma.models import DCMAMetricResult,DCMAStatus,DCMAFinding


def _audit(value):
    # Preserve calculation evidence without repeating complete canonical schedules
    # and their indexes in every DCMA metric/API response.
    if isinstance(value,CPMResult):
        names=('status','calculation_config','completion_anchor','anchor_selection_status','activity_results',
            'critical_paths','path_statistics','diagnostics','reliability_scope')
        return {key:_audit(getattr(value,key)) for key in names}
    if is_dataclass(value):return {f.name:_audit(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,dict):return {k:_audit(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return tuple(_audit(v) for v in value)
    return value


def _metric(key,name,result,threshold,source_fields):
    status=DCMAStatus(result.status);evaluated=status!=DCMAStatus.NOT_EVALUATED
    finding=status in {DCMAStatus.WARNING,DCMAStatus.FAIL}
    reasons=result.diagnostics
    return DCMAMetricResult(key,name,'Application-defined auditable CPM methodology.',status,
        int(evaluated),int(finding),None,threshold,'Application defaults; no claim of official DCMA thresholds.',
        status.value,(DCMAFinding(key,'Application threshold exceeded.',observed_value=getattr(result,'response_ratio',getattr(result,'value',None))),) if finding else (),
        int(not evaluated),{reason:1 for reason in reasons},
        ('See docs/phase8_calculation_contract.md.','Full network recalculation; imported P6 values are not substituted.'),
        source_fields,tuple(reasons),_audit(result))


def critical_path_test(schedule,cpm_config,config):
    result=CriticalPathTestService().evaluate(schedule,cpm_config,config)
    return _metric('critical_path_test','Critical Path Test',result,asdict(config),
        ('canonical durations','activity calendar','network','explicit/unambiguous completion anchor','immutable recalculation'))


def cpli_metric(schedule,cpm_config,config):
    result=CPLIService().calculate(schedule,cpm_config,config)
    return _metric('cpli','Critical Path Length Index',result,asdict(config),
        ('connected controlling path','explicit required finish/selected finish deadline constraint','calculated anchor float','working calendar'))
