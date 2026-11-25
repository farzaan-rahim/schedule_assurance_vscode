"""Exact elapsed comparisons with classification-only tolerances.

No imported value is replaced with a calculated value or a zero. Capability
hints describe observed/unsupported features, never inferred discrepancy causes.
"""
from collections import Counter
from datetime import datetime
from math import isfinite

from app.cpm.models import (CPMActivityComparison, CPMComparisonMetric,
                            CPMComparisonSummary, CPMDiagnostic, CPMFindingSeverity)
from app.cpm.constraint_math import SUPPORTED_CONSTRAINTS
from app.importers.p6_normalization import normalize_status

DATE_METRICS = ("early_start", "early_finish", "late_start", "late_finish")
FLOAT_METRICS = ("total_float", "free_float")


def _metric(name, imported, calculated, tolerance=None, date=False):
    if imported is None or calculated is None:
        status = "BOTH_MISSING" if imported is None and calculated is None else ("MISSING_IMPORTED" if imported is None else "MISSING_CALCULATED")
        return CPMComparisonMetric(name, imported, calculated, status, tolerance=tolerance,
            tolerance_unit="SECONDS" if date else ("HOURS" if tolerance is not None else None))
    if name == "critical_state":
        return CPMComparisonMetric(name, imported, calculated, "MATCH" if imported == calculated else "DIFFERENCE")
    difference = (calculated - imported).total_seconds() if date else calculated - imported
    return CPMComparisonMetric(name, imported, calculated,
        "MATCH" if abs(difference) <= tolerance else "DIFFERENCE",
        variance_hours=difference / 3600 if date else difference,
        variance_seconds=difference if date else None,
        tolerance=tolerance, tolerance_unit="SECONDS" if date else "HOURS")


def compare_activities(schedule, activity_results, config):
    by_id = {a.activity_id:a for a in activity_results}
    records = []
    counts = {name:Counter() for name in DATE_METRICS + FLOAT_METRICS + ("critical_state",)}
    missing_dates = missing_activity_dates = 0
    for a in sorted(schedule.activities.values(), key=lambda a:(a.activity_code,a.activity_id)):
        calculated = by_id.get(a.activity_id)
        metrics, fields = [], {}
        for name in DATE_METRICS + FLOAT_METRICS:
            date = name in DATE_METRICS
            suffix = "" if date else "_hours"
            imported = getattr(a, name + suffix)
            current = getattr(calculated, "calculated_" + name + suffix) if calculated else None
            tolerance = config.comparison_date_tolerance_seconds if date else config.comparison_float_tolerance_hours
            metrics.append(_metric(name, imported, current, tolerance, date))
            fields["imported_"+name+suffix] = imported
            fields["calculated_"+name+suffix] = current
            fields[name+"_variance_hours"] = metrics[-1].variance_hours
        imported_critical = a.total_float_hours <= config.critical_float_threshold_hours if a.total_float_hours is not None else None
        current_critical = calculated.calculated_critical if calculated and calculated.calculated_total_float_hours is not None else None
        metrics.append(_metric("critical_state", imported_critical, current_critical))
        disagreement = imported_critical != current_critical if imported_critical is not None and current_critical is not None else None
        records.append(CPMActivityComparison(activity_id=a.activity_id, activity_code=a.activity_code,
            critical_disagreement=disagreement, imported_critical=imported_critical,
            calculated_critical=current_critical, metrics=tuple(metrics), **fields))
        activity_missing = sum(m.imported is None for m in metrics[:4])
        missing_dates += activity_missing
        missing_activity_dates += bool(activity_missing)
        for m in metrics:
            counts[m.name][m.status] += 1
    summary_fields = {}
    for name in DATE_METRICS + FLOAT_METRICS:
        summary_fields[name+"_matches"] = counts[name]["MATCH"]
        summary_fields[name+"_differences"] = counts[name]["DIFFERENCE"]
    statuses = ("MATCH", "DIFFERENCE", "MISSING_IMPORTED", "MISSING_CALCULATED", "BOTH_MISSING")
    summary = CPMComparisonSummary(activities_compared=len(by_id), activity_records=len(records),
        imported_dates_missing=missing_dates, activities_with_missing_imported_dates=missing_activity_dates,
        critical_state_agreements=counts["critical_state"]["MATCH"],
        critical_state_disagreements=counts["critical_state"]["DIFFERENCE"],
        metric_counts=tuple((name, tuple((status, counts[name][status]) for status in statuses)) for name in counts),
        **summary_fields)
    return tuple(records), summary


def capability_diagnostics(schedule, config):
    hints = []
    def hint(code, message, support, evidence=None):
        hints.append(CPMDiagnostic(code, message, CPMFindingSeverity.INFORMATIONAL,
            metadata={"support":support, "observed":evidence is not None,
                      "evidence":evidence, "cause_established":False}))
    options = schedule.scheduling_options
    if options is None:
        hint("p6_scheduling_options_unobserved",
            "SCHEDOPTIONS was not available for the selected project; no P6 option is guessed or applied.",
            "INFORMATIONAL_ONLY")
    else:
        hint("p6_scheduling_options_observed", "Identified typed P6 options are observed; only explicitly selected supported policies are applied.", "PARTIALLY_SUPPORTED",
             {"retained_logic": options.retained_logic, "progress_override": options.progress_override,
              "ss_lag_from_early_start": options.ss_lag_from_early_start,
              "use_expected_finish": options.use_expected_finish,
              "lag_calendar_policy": options.lag_calendar_policy})
    hint("p6_critical_definition_capability",
        "Imported critical state is a Total-Float-threshold proxy, not an imported P6 critical flag/definition. Possible capability difference; no discrepancy cause is established.",
        "UNSUPPORTED")
    progress = tuple(sorted(a.activity_id for a in schedule.activities.values()
        if normalize_status(a.raw_status if a.raw_status is not None else a.status) == "in_progress"))
    if progress:
        message = ("Narrow retained remaining-work and SS expired-lag support is forward-only; full P6 progress/late-date equivalence is not established."
                   if config.component_calculation_policy == "DIRECTIONAL_FORWARD" and config.progress_scheduling_policy == "P6_RETAINED_LOGIC"
                   else "Remaining work starts at Data Date. This scope does not implement P6 Retained Logic/Progress Override; possible capability difference only.")
        hint("progress_policy_capability", message, "PARTIALLY_SUPPORTED", progress)
    def naive(value):
        return isinstance(value, datetime) and value.tzinfo is None
    out_of_sequence = []
    valid_ids = set(schedule.activities_by_id)
    external = []
    unsupported_relationships = set()
    for r in schedule.relationships:
        if r.predecessor_activity_id not in valid_ids or r.successor_activity_id not in valid_ids:
            external.append(r.relationship_id)
            continue
        pre, suc = schedule.activities_by_id[r.predecessor_activity_id], schedule.activities_by_id[r.successor_activity_id]
        kind = r.relationship_type.upper()
        source = pre.actual_start if kind in {"SS", "SF"} else pre.actual_finish
        target = suc.actual_start if kind in {"FS", "SS"} else suc.actual_finish
        if kind in {"FS", "SS", "FF", "SF"} and naive(source) and naive(target) and config.lag_calendar_policy == "PREDECESSOR":
            calendar = schedule.calendars.get(pre.calendar_id)
            if isinstance(r.lag_hours, (int, float)) and isfinite(r.lag_hours) and (r.lag_hours == 0 or calendar is not None):
                from app.cpm.relationship_math import lag_datetime
                try:
                    required = source if r.lag_hours == 0 else lag_datetime(calendar, source, r.lag_hours)
                    if target < required:
                        out_of_sequence.append(r.relationship_id)
                except (ValueError, OverflowError, IndexError, TypeError):
                    # Unusable calendar/lag evidence cannot establish a progress ordering.
                    pass
        if r.relationship_type.upper() not in {"FS", "SS", "FF", "SF"}:
            unsupported_relationships.add(r.relationship_type)
    if out_of_sequence:
        hint("observed_out_of_sequence_progress", "Actual relationship endpoints violate the application signed-lag requirement on these relationships. This observed progress condition does not identify P6 scheduling options or prove a comparison-difference cause.", "UNSUPPORTED", tuple(sorted(out_of_sequence)))
    if any(r.lag_hours != 0 for r in schedule.relationships):
        hint("lag_calendar_capability", "Application lag uses the configured predecessor calendar; typed P6 lag policy is retained when observed. No discrepancy cause is inferred.", "PARTIALLY_SUPPORTED", {"application": config.lag_calendar_policy, "p6": options.lag_calendar_policy if options else None})
    expected = tuple(sorted(a.activity_id for a in schedule.activities.values() if a.expected_finish is not None))
    if expected:
        hint("expected_finish_capability", "Expected Finish is preserved as imported evidence but is not applied to CPM; possible capability difference only.", "UNSUPPORTED", expected)
    inheritance = tuple(sorted(c.calendar_id for c in schedule.calendars.values() if c.base_calendar_id))
    if inheritance:
        hint("calendar_inheritance_capability", "CPM consumes Phase 5B resolved calendars; full P6 inheritance/option equivalence has not been established. Possible capability difference only.", "PARTIALLY_SUPPORTED", inheritance)
    if external:
        hint("external_relationship_capability", "External/missing endpoints prevent supported CPM calculation; they are not silently supplied. No discrepancy cause is inferred.", "UNSUPPORTED", tuple(sorted(external)))
    constraints = tuple(sorted({kind for a in schedule.activities.values() for kind in (a.primary_constraint_type,a.secondary_constraint_type)
                               if kind and kind not in SUPPORTED_CONSTRAINTS}))
    if constraints:
        hint("unsupported_constraint_capability", "Observed constraints are outside the supported subset; possible capability difference only.", "UNSUPPORTED", constraints)
    resource_dependent = tuple(sorted(a.activity_id for a in schedule.activities.values() if a.activity_type in {"resource_dependent","tt_rsrc"}))
    if resource_dependent:
        hint("resource_dependent_logic_capability", "Observed resource-dependent activity types are unsupported; resource assignments alone do not establish this behavior or a discrepancy cause.", "UNSUPPORTED", resource_dependent)
    if unsupported_relationships:
        hint("unsupported_relationship_capability", "Observed relationship types (including exclusive types if present) are outside FS/SS/FF/SF; no scheduling rule is guessed.", "UNSUPPORTED", tuple(sorted(unsupported_relationships)))
    return tuple(hints)
