from __future__ import annotations

from collections import Counter

from app.comparison.models import ComparisonResult, MatchClassification
from app.comparison.wbs import wbs_path
from app.dcma.config import DCMAConfig
from app.dcma.eligibility import eligible_activities
from app.dcma.models import DCMADiagnostic, DCMAFinding, DCMAMetricResult, DCMAStatus
from app.dcma.thresholds import finding_percentage, percentage_status
from app.importers.p6_normalization import normalize_status
from app.models.schedule import Activity, Schedule


def _activity_finding(metric: str, activity: Activity, schedule: Schedule, reason: str, observed=None) -> DCMAFinding:
    try:
        path = wbs_path(schedule, activity.wbs_id)
    except Exception:
        path = None
    return DCMAFinding(
        finding_type=metric,
        message=reason,
        activity_id=activity.activity_id,
        activity_code=activity.activity_code,
        activity_name=activity.activity_name,
        wbs_path=path,
        observed_value=observed,
        metadata={"status": activity.status, "activity_type": activity.activity_type},
    )


def not_evaluated(metric_id: str, name: str, description: str, reason: str, source_fields: tuple[str, ...]) -> DCMAMetricResult:
    return DCMAMetricResult(
        metric_id, name, description, DCMAStatus.NOT_EVALUATED,
        0, 0, None, None,
        "No threshold; metric cannot be evaluated.",
        "NOT_EVALUATED", (), 0, {},
        (reason,), source_fields, (reason,), {},
    )


def missing_logic(schedule: Schedule, graph, config: DCMAConfig) -> DCMAMetricResult:
    activities, exclusions = eligible_activities(
        list(schedule.activities.values()), exclude_completed=True, exclude_milestones=True
    )
    findings: list[DCMAFinding] = []
    missing_predecessor = missing_successor = missing_both = 0
    valid_ids = set(schedule.activities_by_id)

    for activity in activities:
        predecessors = graph.predecessor_relationships.get(activity.activity_id, [])
        successors = graph.successor_relationships.get(activity.activity_id, [])
        no_pred = not any(r.predecessor_activity_id in valid_ids for r in predecessors)
        no_succ = not any(r.successor_activity_id in valid_ids for r in successors)
        if no_pred:
            missing_predecessor += 1
        if no_succ:
            missing_successor += 1
        if no_pred and no_succ:
            missing_both += 1
        if no_pred or no_succ:
            findings.append(_activity_finding(
                "missing_logic", activity, schedule,
                "Missing predecessor" if no_pred and not no_succ else
                "Missing successor" if no_succ and not no_pred else
                "Missing both predecessor and successor",
            ))

    pct = finding_percentage(len(findings), len(activities))
    status = percentage_status(pct, config.missing_logic_warning_pct, config.missing_logic_fail_pct)
    return DCMAMetricResult(
        "missing_logic", "Missing Logic", "Activities missing eligible predecessor/successor links.", status,
        len(activities), len(findings), pct,
        {"warning_percent": config.missing_logic_warning_pct, "fail_percent": config.missing_logic_fail_pct},
        "Warning/fail when finding percentage reaches configured thresholds",
        "Finding percentage threshold",
        tuple(findings[:config.detail_limit]), len(list(schedule.activities.values())) - len(activities), exclusions,
        ("Excludes completed activities and milestones; start/finish milestones are handled as exclusions.",),
        ("TASKPRED", "TASK.task_id", "TASK.task_type", "TASK.status_code"),
        (), {"missing_predecessor": missing_predecessor, "missing_successor": missing_successor, "missing_both": missing_both},
    )


def relationship_lags(schedule: Schedule, config: DCMAConfig) -> tuple[DCMAMetricResult, DCMAMetricResult, DCMAMetricResult]:
    eligible = [r for r in schedule.relationships if r.relationship_type in {"FS", "SS", "FF", "SF"}]
    unknown = [r for r in schedule.relationships if r.relationship_type not in {"FS", "SS", "FF", "SF"}]
    eligible_count = len(schedule.relationships)

    leads = [r for r in schedule.relationships if r.lag_hours < 0]
    lead_pct = finding_percentage(len(leads), eligible_count)
    lead_status = percentage_status(lead_pct, config.lead_warning_pct, config.lead_fail_pct)
    lead_findings = tuple(_relationship_finding("lead", r, schedule) for r in leads)
    leads_result = DCMAMetricResult(
        "leads", "Leads", "Negative-lag relationships.", lead_status, eligible_count,
        len(leads), lead_pct,
        {"warning_percent": config.lead_warning_pct, "fail_percent": config.lead_fail_pct},
        "Any negative lag percentage at configured thresholds",
        "Finding percentage threshold",
        lead_findings[:config.detail_limit],
        0, {},
        ("Negative lag is represented directly in lag hours.",),
        ("TASKPRED.pred_type", "TASKPRED.lag_hr_cnt", "TASKPRED.pred_task_id", "TASKPRED.task_id"),
        (), {"negative_lag_hours": sum(r.lag_hours for r in leads), "largest_negative_lag_magnitude": abs(min((r.lag_hours for r in leads), default=0.0))},
    )

    positive = [r for r in schedule.relationships if r.lag_hours > 0]
    excessive = [r for r in positive if r.lag_hours > config.excessive_lag_hours]
    positive_pct = finding_percentage(len(positive), eligible_count)
    positive_status = percentage_status(positive_pct, config.lag_warning_pct, config.lag_fail_pct)
    lags_result = DCMAMetricResult(
        "lags", "Lags", "Positive relationship lags and excessive positive lags.", positive_status,
        eligible_count, len(positive), positive_pct,
        {"excessive_lag_hours": config.excessive_lag_hours, "warning_percent": config.lag_warning_pct, "fail_percent": config.lag_fail_pct},
        "Positive lag and excessive lag reported separately",
        "Finding percentage threshold",
        tuple(_relationship_finding("positive_lag", r, schedule) for r in positive)[:config.detail_limit],
        0, {},
        ("Lag hours are not converted to working days.",),
        ("TASKPRED.lag_hr_cnt", "TASKPRED.pred_type"), (),
        {"positive_lag_count": len(positive), "excessive_lag_count": len(excessive), "excessive_lag_hours": sum(r.lag_hours for r in excessive)},
    )

    counts = Counter(r.relationship_type if r.relationship_type in {"FS", "SS", "FF", "SF"} else "UNKNOWN" for r in schedule.relationships)
    non_fs = sum(counts[k] for k in ("SS", "FF", "SF", "UNKNOWN"))
    pct = finding_percentage(non_fs, eligible_count)
    status = percentage_status(pct, config.non_fs_warning_pct, config.non_fs_fail_pct)
    relationship_result = DCMAMetricResult(
        "relationship_types", "Relationship Types", "Distribution and non-FS relationship policy.", status,
        eligible_count, non_fs, pct,
        {"warning_percent": config.non_fs_warning_pct, "fail_percent": config.non_fs_fail_pct},
        "Non-FS or unknown percentage at configured thresholds",
        "Finding percentage threshold",
        tuple(_relationship_finding("non_fs_relationship", r, schedule) for r in schedule.relationships if r.relationship_type not in {"FS", ""})[:config.detail_limit],
        0, {},
        ("Relationship types are schedule-quality risk indicators, not proof of defect.",),
        ("TASKPRED.pred_type",), (),
        {"counts": dict(counts), "percentages": {k: round(100.0 * counts[k] / eligible_count, 2) if eligible_count else 0.0 for k in ("FS", "SS", "FF", "SF", "UNKNOWN")}},
    )
    return leads_result, lags_result, relationship_result


def _relationship_finding(kind: str, relationship, schedule: Schedule) -> DCMAFinding:
    pred = schedule.activities_by_id.get(relationship.predecessor_activity_id)
    succ = schedule.activities_by_id.get(relationship.successor_activity_id)
    return DCMAFinding(
        finding_type=kind,
        message=f"{kind} relationship finding",
        relationship_id=relationship.relationship_id,
        predecessor_activity_id=relationship.predecessor_activity_id,
        successor_activity_id=relationship.successor_activity_id,
        relationship_type=relationship.relationship_type,
        lag_hours=relationship.lag_hours,
        observed_value=relationship.lag_hours,
        metadata={"predecessor_code": pred.activity_code if pred else None, "successor_code": succ.activity_code if succ else None},
    )


def hard_constraints(schedule: Schedule, config: DCMAConfig) -> DCMAMetricResult:
    activities, exclusions = eligible_activities(list(schedule.activities.values()), exclude_completed=False, exclude_milestones=False)
    findings: list[DCMAFinding] = []
    for activity in activities:
        types = {activity.primary_constraint_type, activity.secondary_constraint_type}
        hard = types & set(config.hard_constraint_types)
        if hard:
            findings.append(_activity_finding("hard_constraint", activity, schedule, "Configured hard constraint present", sorted(hard)))

    pct = finding_percentage(len(findings), len(activities))
    status = percentage_status(pct, config.hard_constraint_warning_pct, config.hard_constraint_fail_pct)
    return DCMAMetricResult(
        "hard_constraints", "Hard Constraints", "Configured hard P6 constraint types.", status,
        len(activities), len(findings), pct,
        {"hard_constraint_types": sorted(config.hard_constraint_types)},
        "Warning/fail when configured hard-constraint percentage reaches thresholds",
        "Finding percentage threshold",
        tuple(findings
        [:config.detail_limit]), len(list(schedule.activities.values())) - len(activities), exclusions,
        (), ("TASK.cstr_type", "TASK.cstr_date", "TASK.cstr_type2", "TASK.cstr_date2"),
        ("Constraint semantics remain user-configurable.",), {},
    )


def float_metrics(schedule: Schedule, config: DCMAConfig) -> tuple[DCMAMetricResult, DCMAMetricResult]:
    activities, exclusions = eligible_activities(list(schedule.activities.values()), exclude_completed=True, exclude_milestones=True)
    float_values = [a for a in activities if a.total_float_hours is not None]
    missing = [a for a in activities if a.total_float_hours is None]

    high = [a for a in float_values if a.total_float_hours > config.high_float_threshold_hours]
    high_pct = finding_percentage(len(high), len(float_values))
    high_status = percentage_status(high_pct, config.high_float_warning_pct, config.high_float_fail_pct)
    high_result = DCMAMetricResult(
        "high_float", "High Float", "Activities with imported total float above configured hours.", high_status,
        len(float_values), len(high), high_pct,
        {"threshold_hours": config.high_float_threshold_hours},
        "Finding percentage uses eligible activities containing float",
        "Finding percentage threshold",
        tuple(_activity_finding
        ("high_float", a, schedule, "High imported total float", a.total_float_hours) for a in high)[:config.detail_limit],
        len(missing) + (len(list(schedule.activities.values())) - len(activities)),
        {**exclusions, "Missing total float": len(missing)},
        ("Completed activities and milestones excluded; blank float is not assumed zero.",),
        ("TASK.total_float_hr_cnt",), (),
        {"maximum_float": max((a.total_float_hours for a in float_values), default=None), "missing_float_count": len(missing)},
    )

    negative = [a for a in float_values if a.total_float_hours < 0]
    negative_pct = finding_percentage(len(negative), len(float_values))
    negative_status = percentage_status(negative_pct, config.negative_float_warning_pct, config.negative_float_fail_pct)
    negative_result = DCMAMetricResult(
        "negative_float", "Negative Float", "Activities with imported negative total float.", negative_status,
        len(float_values), len(negative), negative_pct,
        {"warning_percent": config.negative_float_warning_pct, "fail_percent": config.negative_float_fail_pct},
        "Finding percentage uses eligible activities containing float",
        "Finding percentage threshold",
        tuple(_activity_finding("negative_float", a, schedule, "Negative imported total float", a.total_float_hours) for a in negative)[:config.detail_limit],
        len(missing) + (len(list(schedule.activities.values())) - len(activities)),
        {**exclusions, "Missing total float": len(missing)},
        ("Imported P6 float only; no working-day conversion.",),
        ("TASK.total_float_hr_cnt",), (),
        {"most_negative_float": min((a.total_float_hours for a in float_values), default=None), "missing_float_count": len(missing)},
    )
    return high_result, negative_result


def duration_metric(schedule: Schedule, config: DCMAConfig) -> DCMAMetricResult:
    activities, exclusions = eligible_activities(list(schedule.activities.values()), exclude_completed=False, exclude_milestones=True)
    duration_values = [a for a in activities if a.original_duration_hours is not None]
    missing = [a for a in activities if a.original_duration_hours is None]
    high = [a for a in duration_values if a.original_duration_hours > config.high_duration_threshold_hours]
    pct = finding_percentage(len(high), len(duration_values))
    status = percentage_status(pct, config.high_duration_warning_pct, config.high_duration_fail_pct)
    return DCMAMetricResult(
        "high_duration", "High Duration", "Activities with original duration above configured hours.", status,
        len(duration_values), len(high), pct,
        {"threshold_hours": config.high_duration_threshold_hours},
        "Finding percentage uses activities with original duration",
        "Finding percentage threshold",
        tuple(_activity_finding
        ("high_duration", a, schedule, "Duration above configured threshold", a.original_duration_hours) for a in high)[:config.detail_limit],
        len(missing) + (len(list(schedule.activities.values())) - len(activities)),
        {**exclusions, "Missing original duration": len(missing)},
        ("Threshold is hours, not assumed working days.",),
        ("TASK.target_drtn_hr_cnt",), (),
        {"largest_duration": max((a.original_duration_hours for a in duration_values), default=None)},
    )


def invalid_dates(schedule: Schedule, config: DCMAConfig) -> DCMAMetricResult:
    data_date = schedule.project.data_date if schedule.project else None
    findings: list[DCMAFinding] = []
    subtype_counts: Counter[str] = Counter()

    for activity in schedule.activities.values():
        status = normalize_status(activity.raw_status)
        reasons: list[str] = []
        if activity.actual_start and data_date and activity.actual_start > data_date:
            reasons.append("actual_start_after_data_date")
        if activity.actual_finish and data_date and activity.actual_finish > data_date:
            reasons.append("actual_finish_after_data_date")
        if data_date and status not in {"complete"} and activity.planned_finish and activity.planned_finish < data_date:
            reasons.append("forecast_finish_before_data_date")
        if status == "complete" and activity.actual_finish is None:
            reasons.append("completed_missing_actual_finish")
        if status == "not_started" and (activity.actual_start or activity.actual_finish):
            reasons.append("not_started_with_actual_dates")
        if status == "in_progress" and activity.actual_start is None:
            reasons.append("in_progress_missing_actual_start")

        for reason in reasons:
            subtype_counts[reason] += 1
        if reasons:
            findings.append(_activity_finding("invalid_dates", activity, schedule, "; ".join(reasons), reasons))

    pct = finding_percentage(len(findings), len(schedule.activities))
    status = percentage_status(pct, config.invalid_date_warning_pct, config.invalid_date_fail_pct)
    return DCMAMetricResult(
        "invalid_dates", "Invalid Dates", "Transparent P6 date-quality checks against data date.", status,
        len(schedule.activities), len(findings), pct,
        {"warning_percent": config.invalid_date_warning_pct, "fail_percent": config.invalid_date_fail_pct},
        "Unique affected activity percentage at configured thresholds",
        "Finding percentage threshold",
        tuple(findings
        [:config.detail_limit]), 0, {},
        ("Uses calendar elapsed values only as dates; no scheduling recalculation.",),
        ("PROJECT.last_recalc_date", "TASK.act_start_date", "TASK.act_end_date", "TASK.target_start_date", "TASK.target_end_date", "TASK.status_code"),
        (), {"subtype_counts": dict(subtype_counts)},
    )


def resource_metric(schedule: Schedule, config: DCMAConfig) -> DCMAMetricResult:
    activities, exclusions = eligible_activities(
        list(schedule.activities.values()),
        exclude_completed=config.resource_exclude_completed,
        exclude_milestones=config.resource_exclude_milestones,
        exclude_loe=config.resource_exclude_loe,
    )
    loaded = [a for a in activities if schedule.assignments_by_activity_id.get(a.activity_id)]
    unloaded = [a for a in activities if not schedule.assignments_by_activity_id.get(a.activity_id)]

    loaded_pct = 100.0 * len(loaded) / len(activities) if activities else 0.0
    unloaded_pct = 100.0 * len(unloaded) / len(activities) if activities else 0.0
    if unloaded_pct >= config.resource_fail_pct:
        status = DCMAStatus.FAIL
    elif unloaded_pct >= config.resource_warning_pct:
        status = DCMAStatus.WARNING
    else:
        status = DCMAStatus.PASS

    findings = tuple(
        _activity_finding("resource_not_loaded", a, schedule, "Eligible activity has no resource assignment")
        for a in unloaded
    )[:config.detail_limit]

    return DCMAMetricResult(
        "resources", "Resources", "Percentage of eligible activities with at least one resource assignment.", status,
        len(activities), len(unloaded), round(unloaded_pct, 2),
        {"resource_warning_pct_unloaded": config.resource_warning_pct, "resource_fail_pct_unloaded": config.resource_fail_pct},
        "Finding percentage is the percentage of eligible activities without a resource assignment",
        "Finding percentage threshold",
        findings,
        len(list(schedule.activities.values())) - len(activities),
        exclusions,
        ("Resource assignment presence does not prove resource loading, leveling, utilization, or cost accuracy.",),
        ("TASKRSRC.task_id", "TASKRSRC.rsrc_id"),
        (),
        {"resource_loaded_count": len(loaded), "resource_unloaded_count": len(unloaded), "resource_loaded_percentage": round(loaded_pct, 2)},
    )


def critical_path_test() -> DCMAMetricResult:
    return not_evaluated(
        "critical_path_test", "Critical Path Test", "Traditional controlled-delay critical-path test.",
        "Calendar-aware CPM recalculation required.",
        ("Schedule network", "calendar", "duration", "lags", "constraint dates"),
    )


def cpli_metric() -> DCMAMetricResult:
    return not_evaluated(
        "cpli", "Critical Path Length Index", "Imported critical-path length ratio.",
        "Required critical-path length and target-finish information cannot be reliably derived without CPM recalculation.",
        ("critical path length", "target finish", "project duration"),
    )


def baseline_metrics(
    comparison: ComparisonResult | None,
    config: DCMAConfig,
) -> tuple[DCMAMetricResult, DCMAMetricResult]:
    if comparison is None:
        reason = "Baseline/current comparison is not supplied."
        missed = not_evaluated("missed_activities", "Missed Activities / Baseline Execution", "Baseline finish commitments missed in current schedule.", reason, ("baseline TASK", "current TASK.status_code", "current PROJECT.data_date", "TASK.target_end_date"))
        bei = not_evaluated("bei", "Baseline Execution Index", "Completed baseline planned activities divided by baseline activities planned to finish by current data date.", reason, ("baseline TASK.target_end_date", "current TASK.status_code", "PROJECT.data_date", "activity matching"))
        return missed, bei

    baseline = comparison.baseline_version.schedule
    current = comparison.current_version.schedule
    data_date = current.project.data_date if current.project else None

    baseline_eligible = [
        a for a in baseline.activities.values()
        if a.planned_finish is not None
        and data_date is not None
        and a.planned_finish <= data_date
    ]

    completed_codes = {
        v.current_activity.activity_code
        for v in comparison.activity_variances
        if v.current_activity is not None
        and normalize_status(v.current_activity.raw_status) == "complete"
    }

    missed: list[DCMAFinding] = []
    denominator_ids = set()
    completed_count = 0
    for baseline_activity in baseline_eligible:
        denominator_ids.add(baseline_activity.activity_id)
        matched_variance = next((
            v for v in comparison.activity_variances
            if v.baseline_activity is not None
            and v.baseline_activity.activity_id == baseline_activity.activity_id
        ), None)
        if matched_variance is None or matched_variance.classification == MatchClassification.AMBIGUOUS:
            continue
        if matched_variance.classification == MatchClassification.MATCHED:
            if baseline_activity.activity_code in completed_codes:
                completed_count += 1
            else:
                missed.append(_activity_finding("missed_activity", baseline_activity, baseline, "Baseline planned finish was due by current data date but activity is not complete", baseline_activity.planned_finish))

    missed_pct = finding_percentage(len(missed), len(baseline_eligible))
    missed_status = percentage_status(missed_pct, 5.0, 10.0)
    missed_result = DCMAMetricResult(
        "missed_activities", "Missed Activities / Baseline Execution",
        "Baseline activities scheduled to finish by current data date and not complete.",
        missed_status,
        len(baseline_eligible), len(missed), missed_pct,
        {"methodology": "Baseline planned finish <= current data date and current status != complete"},
        "Warning/fail at 5%/10% unless configuration is customized",
        "Finding percentage threshold",
        tuple(missed), 0, {},
        ("Ambiguous matches are excluded from numerator/denominator decisions.",
         "Milestones are included if explicitly present in the baseline population."),
        ("baseline TASK.target_end_date", "current TASK.status_code", "current PROJECT.data_date", "activity matching"),
        (),
        {"baseline_expected_complete": len(baseline_eligible),
         "actually_complete": completed_count,
         "missed": len(missed),
         "ambiguous_or_unmatched_excluded": len(baseline_eligible) - len(denominator_ids)},
    )

    bei_denominator = len(baseline_eligible)
    bei_numerator = completed_count
    bei_value = bei_numerator / bei_denominator if bei_denominator else None
    if bei_value is None:
        bei_status = DCMAStatus.NOT_APPLICABLE
    elif bei_value < config.bei_fail:
        bei_status = DCMAStatus.FAIL
    elif bei_value < config.bei_warning:
        bei_status = DCMAStatus.WARNING
    else:
        bei_status = DCMAStatus.PASS

    bei_result = DCMAMetricResult(
        "bei", "Baseline Execution Index",
        "Completed baseline activities due by current data date divided by all baseline activities due by that date.",
        bei_status,
        bei_denominator, bei_numerator,
        round(100.0 * bei_numerator / bei_denominator, 2) if bei_denominator else None,
        {"bei_warning": config.bei_warning, "bei_fail": config.bei_fail, "formula": "numerator / denominator"},
        "BEI = completed due activities / baseline activities due by current data date",
        "BEI threshold comparison",
        (),
        0, {},
        ("Ambiguous matches are excluded from numerator and denominator.",
         "Added/deleted activities do not change the baseline denominator; deleted matched-to-current activities are not complete."),
        ("baseline TASK.target_end_date", "current TASK.status_code", "current PROJECT.data_date", "activity matching"),
        (),
        {"numerator": bei_numerator, "denominator": bei_denominator, "bei": bei_value},
    )
    return missed_result, bei_result
