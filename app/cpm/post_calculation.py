"""Add selected-anchor traces without changing the validated CPM calculation."""
from dataclasses import replace

from app.cpm.anchors import select_completion_anchor
from app.cpm.paths import trace_paths
from app.cpm.comparison import compare_activities, capability_diagnostics


def finalize_result(result, graph):
    hints = capability_diagnostics(result.schedule, result.calculation_config)
    if result.status != "CALCULATED":
        return replace(result, comparison_diagnostics=hints)
    comparisons, summary = compare_activities(result.schedule, result.activity_results, result.calculation_config)
    result = replace(result, comparisons=comparisons, comparison_summary=summary, comparison_diagnostics=hints)
    selection, anchor, candidates, findings = select_completion_anchor(result, graph)
    changes = dict(completion_anchor=anchor, completion_anchor_candidates=candidates,
                   anchor_selection_status=selection, diagnostics=result.diagnostics + findings)
    if anchor is None:
        return replace(result, path_status="ANCHOR_REQUIRED" if selection == "AMBIGUOUS" else "INVALID_ANCHOR", **changes)
    if anchor.activity_id is None:
        return replace(result, path_status="NO_ACTIVITY_ANCHOR", **changes)
    critical, near, statistics, trace_findings = trace_paths(result, graph, anchor)
    truncated = dict(result.truncation)
    truncated.update(critical_paths_truncated=statistics[0].truncated,
                     near_critical_paths_truncated=statistics[1].truncated,
                     path_nodes_inspected=sum(s.nodes_inspected for s in statistics))
    changes["diagnostics"] += trace_findings
    return replace(result, critical_paths=critical, near_critical_paths=near,
        path_statistics=statistics, truncation=truncated,
        path_status="TRUNCATED" if any(s.truncated for s in statistics) else ("TRACED" if critical or near else "NO_QUALIFYING_PATHS"), **changes)
