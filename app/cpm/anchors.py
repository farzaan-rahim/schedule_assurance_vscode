"""Completion selection is independent of validated date/float calculation."""
from dataclasses import replace

from app.cpm.models import CPMCompletionAnchor, CPMDiagnostic, CPMFindingSeverity


def select_completion_anchor(result, graph):
    config = result.calculation_config
    by_id = {a.activity_id: a for a in result.activity_results}
    def snapshot(activity_id, source):
        a, calculated = result.schedule.activities_by_id[activity_id], by_id[activity_id]
        return CPMCompletionAnchor(
            source=source, activity_id=a.activity_id, activity_code=a.activity_code,
            activity_name=a.activity_name,
            calculated_early_finish=calculated.calculated_early_finish,
            calculated_late_finish=calculated.calculated_late_finish,
            imported_finish=a.early_finish if a.early_finish is not None else a.planned_finish,
            required_finish=config.required_project_finish,
            configured_completion_timestamp=config.project_completion_timestamp,
        )
    terminals = sorted((a.activity_id for a in graph.get_finish_activities()),
                       key=lambda key: (by_id[key].activity_code, key))
    candidates = tuple(snapshot(key, "TERMINAL_CANDIDATE") for key in terminals)
    for activity_id, code, source in (
        (config.completion_activity_id, config.completion_activity_code, "CONFIGURED_ACTIVITY"),
        (config.required_finish_activity_id, config.required_finish_activity_code, "CONFIGURED_REQUIRED_FINISH_ACTIVITY"),
    ):
        if activity_id is None and code is None:
            continue
        matches = [a for a in result.activity_results
                   if (activity_id is None or a.activity_id == activity_id)
                   and (code is None or a.activity_code == code)]
        if len(matches) == 1:
            return "SELECTED", snapshot(matches[0].activity_id, source), candidates, ()
        ambiguous = len(matches) > 1
        diagnostic = CPMDiagnostic(
            "completion_anchor_ambiguous" if ambiguous else "configured_completion_anchor_not_found",
            "Completion selection must identify exactly one calculated activity; no fallback was selected.",
            CPMFindingSeverity.WARNING, metadata={"activity_id": activity_id, "activity_code": code,
                "candidate_ids": tuple(sorted(a.activity_id for a in matches))},
        )
        selected_candidates = tuple(snapshot(a.activity_id, "CONFIGURED_CANDIDATE") for a in sorted(matches, key=lambda a: (a.activity_code, a.activity_id)))
        return "AMBIGUOUS" if ambiguous else "INVALID", None, selected_candidates or candidates, (diagnostic,)
    if config.project_completion_timestamp is not None:
        matches = [a for a in candidates if a.calculated_early_finish == config.project_completion_timestamp]
        if len(matches) == 1:
            return "SELECTED", replace(matches[0], source="CONFIGURED_PROJECT_TIMESTAMP"), candidates, ()
        anchor = CPMCompletionAnchor(source="CONFIGURED_PROJECT_TIMESTAMP",
            required_finish=config.required_project_finish,
            configured_completion_timestamp=config.project_completion_timestamp)
        diagnostic = CPMDiagnostic("timestamp_anchor_requires_activity", "Timestamp is preserved as a project event; it does not invent a terminal relationship. Select an activity for path tracing.", CPMFindingSeverity.INFORMATIONAL)
        return "SELECTED_TIMESTAMP", anchor, candidates, (diagnostic,)
    if len(candidates) == 1:
        return "SELECTED", replace(candidates[0], source="UNAMBIGUOUS_TERMINAL"), candidates, ()
    diagnostic = CPMDiagnostic("completion_anchor_ambiguous", "Multiple terminal activities require explicit completion selection.", CPMFindingSeverity.WARNING,
        metadata={"candidate_ids": tuple(a.activity_id for a in candidates)})
    return "AMBIGUOUS", None, candidates, (diagnostic,)
