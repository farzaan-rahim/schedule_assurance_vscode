"""Bounded iterative traces to one selected completion activity.

Ranking is within the deterministically inspected/returned subset when bounded.
No schedule dates, float, imported values or control records are modified.
"""
from dataclasses import replace
from datetime import datetime, timedelta

from app.calendars.working_time import next_working_time, working_hours_between
from app.cpm.models import (CPMPath, CPMPathTraceStatistics, CPMPathConstraintCause,
                            CPMRelationshipControl, CPMDiagnostic, CPMFindingSeverity)
from app.cpm.relationship_math import forward_successor_requirement


def trace_paths(result, graph, anchor):
    config = result.calculation_config
    by_id = {a.activity_id: a for a in result.activity_results}
    critical_incoming = {}
    near_incoming = {}
    for key, item in by_id.items():
        controls = {r.relationship_id: r for r in item.controlling_relationships if r.direction == "FORWARD"}
        critical_incoming[key] = [r for r in controls.values() if _eligible(by_id[r.predecessor_id], config.critical_float_threshold_hours)]
        near_incoming[key] = []
        # A dominating constraint genuinely stops predecessor-based control.
        if item.controlling_constraints and any(c.direction == "FORWARD" for c in item.controlling_constraints) and not controls:
            continue
        for relationship in graph.predecessor_relationships.get(key, ()):
            predecessor = by_id[relationship.predecessor_activity_id]
            if not _eligible(predecessor, config.near_critical_float_threshold_hours):
                continue
            if relationship.relationship_id in controls:
                near_incoming[key].append(controls[relationship.relationship_id])
                continue
            slack = dict(predecessor.relationship_free_float_hours).get(relationship.relationship_id)
            if slack is None or not 0 <= slack <= max(0.0, config.near_critical_float_threshold_hours):
                continue
            raw_pre = result.schedule.activities_by_id[predecessor.activity_id]
            raw_suc = result.schedule.activities_by_id[key]
            calendar = result.schedule.calendars[raw_suc.calendar_id]
            requirement = forward_successor_requirement(relationship, predecessor, item,
                result.schedule.calendars[raw_pre.calendar_id], calendar, relationship.lag_hours)
            if item.effective_duration_hours > 0:
                requirement = next_working_time(calendar, requirement)
            near_incoming[key].append(CPMRelationshipControl(relationship.relationship_id,
                predecessor.activity_id, predecessor.activity_code, key, item.activity_code,
                relationship.relationship_type.upper(), float(relationship.lag_hours), config.lag_calendar_policy,
                raw_pre.calendar_id, "NEAR_QUALIFYING", "EARLY_START_LOWER_BOUND", requirement,
                False, False, "NONCONTROLLING_WITHIN_NEAR_THRESHOLD", slack))
    order = lambda rel: (by_id[rel.predecessor_id].activity_code, rel.predecessor_id, rel.relationship_id)
    for incoming in (critical_incoming, near_incoming):
        for key in incoming:
            incoming[key].sort(key=order)
    # Prune all-critical branches from near tracing without enumerating them.
    has_near_upstream = {}
    for a in graph.topological_sort().ordered_activities:
        key = a.activity_id
        item = by_id[key]
        has_near_upstream[key] = _eligible(item, config.near_critical_float_threshold_hours) and (
            item.calculated_total_float_hours > config.critical_float_threshold_hours
            or any(has_near_upstream.get(r.predecessor_id, False) for r in near_incoming[key]))
    critical, critical_stats, critical_diags = _enumerate(result, graph, anchor, by_id,
        critical_incoming, "CRITICAL", config.maximum_critical_paths if config.maximum_critical_paths is not None else config.maximum_path_count,
        config.maximum_path_nodes_inspected, {})
    near, near_stats, near_diags = _enumerate(result, graph, anchor, by_id,
        near_incoming, "NEAR_CRITICAL", config.maximum_near_critical_paths if config.maximum_near_critical_paths is not None else config.maximum_path_count,
        max(0, config.maximum_path_nodes_inspected - critical_stats.nodes_inspected), has_near_upstream)
    return critical, near, (critical_stats, near_stats), critical_diags + near_diags


def _eligible(item, threshold):
    return item.calculated_total_float_hours is not None and item.calculated_total_float_hours <= threshold


def _enumerate(result, graph, anchor, by_id, incoming, classification, limit, budget, has_near_upstream):
    config = result.calculation_config
    root = anchor.activity_id
    near = classification == "NEAR_CRITICAL"
    threshold = config.near_critical_float_threshold_hours if near else config.critical_float_threshold_hours
    if not _eligible(by_id[root], threshold) or (near and not has_near_upstream.get(root, False)):
        return (), CPMPathTraceStatistics(classification, 0, 0, 0, 0, 0, False), ()
    paths, reasons = [], set()
    inspected = completed = 0
    ids, edges = [root], []
    frames = [{"entered": False}]
    stopped = False

    def emit(reason, truncated=False):
        nonlocal completed, stopped
        if not ids or (near and not any(by_id[key].calculated_total_float_hours > config.critical_float_threshold_hours for key in ids)):
            return
        if not truncated:
            completed += 1
        if len(paths) >= limit:
            reasons.add("MAXIMUM_NEAR_CRITICAL_PATHS" if near else "MAXIMUM_CRITICAL_PATHS")
            stopped = True
            return
        paths.append(_make_path(result, graph, anchor, by_id, tuple(reversed(ids)),
            tuple(reversed(edges)), classification, reason, truncated))

    def leave():
        frames.pop()
        ids.pop()
        if edges:
            edges.pop()

    while frames and not stopped:
        frame = frames[-1]
        key = ids[-1]
        if not frame["entered"]:
            if inspected >= budget:
                reasons.add("MAXIMUM_PATH_NODES_INSPECTED")
                # The new child was not inspected; retain only known nodes.
                ids.pop()
                if edges:
                    edges.pop()
                emit("MAXIMUM_PATH_NODES_INSPECTED", True)
                break
            inspected += 1
            frame["entered"] = True
            seen_near = near and any(by_id[value].calculated_total_float_hours > config.critical_float_threshold_hours for value in ids)
            choices = incoming[key] if _eligible(by_id[key], threshold) else []
            if near and not seen_near:
                choices = [r for r in choices if has_near_upstream.get(r.predecessor_id, False)]
            frame.update(choices=choices, index=0)
            if choices and len(ids) >= config.maximum_path_depth:
                reasons.add("MAXIMUM_PATH_DEPTH")
                emit("MAXIMUM_PATH_DEPTH", True)
                leave()
                continue
            if not choices:
                item = by_id[key]
                if any(c.direction == "FORWARD" for c in item.controlling_constraints):
                    reason = "CONSTRAINT"
                elif not graph.predecessor_relationships.get(key):
                    reason = "NETWORK_START"
                else:
                    reason = "FLOAT_OR_DATA_DATE_BOUNDARY"
                emit(reason)
                leave()
                continue
        if frame["index"] < len(frame["choices"]):
            relationship = frame["choices"][frame["index"]]
            frame["index"] += 1
            ids.append(relationship.predecessor_id)
            edges.append(relationship)
            frames.append({"entered": False})
        else:
            leave()
    truncated = bool(reasons)
    def duration_ticks(path):
        duration = sum((timedelta(hours=by_id[key].effective_duration_hours) for key in path.activity_ids), timedelta())
        return duration // datetime.resolution
    paths.sort(key=lambda p: (p.minimum_total_float_hours, -duration_ticks(p),
                             p.activity_codes, p.activity_ids, p.relationship_ids))
    prefix = "NCP" if near else "CP"
    paths = tuple(replace(p, path_id=f"{prefix}-{rank:03d}", rank=rank) for rank, p in enumerate(paths, 1))
    stats = CPMPathTraceStatistics(classification, len(paths), completed,
        None if truncated else completed, completed, inspected, truncated, tuple(sorted(reasons)))
    diagnostics = ()
    if truncated:
        diagnostics = (CPMDiagnostic("path_trace_truncated", "Path tracing stopped at explicit limits; returned ranking is not a claim of global top paths.",
            CPMFindingSeverity.WARNING, metadata={"classification": classification, "limits": stats.limit_reasons,
                "paths_lower_bound": completed, "nodes_inspected": inspected}),)
    return paths, stats, diagnostics


def _make_path(result, graph, anchor, by_id, ids, edges, classification, reason, truncated):
    items = [by_id[key] for key in ids]
    duration_sum = sum(a.effective_duration_hours for a in items)
    lag_sum = sum(r.lag_hours for r in edges)
    calendars = {a.effective_calendar_id for a in items}
    duration = None
    method = "SEPARATE_ACTIVITY_AND_LAG_HOURS"
    if len(calendars) == 1 and all(r.relationship_type == "FS" for r in edges) and all(a.date_basis == "REMAINING_WORK" for a in items):
        calendar = result.schedule.calendars[next(iter(calendars))]
        span = working_hours_between(calendar, items[0].calculated_early_start, items[-1].calculated_early_finish)
        expected = sum((timedelta(hours=a.effective_duration_hours) for a in items), timedelta())
        expected += sum((timedelta(hours=r.lag_hours) for r in edges), timedelta())
        # Compare exact calendar-resolution durations, not binary float sums
        # such as 0.1 + 0.2. Raw component sums remain exposed unchanged.
        if span >= 0 and timedelta(hours=span) == expected:
            duration, method = span, "SINGLE_CALENDAR_FS_WORKING_SPAN"
    causes = tuple(CPMPathConstraintCause(a.activity_id, a.activity_code, cause)
                   for a in items for cause in a.controlling_constraints)
    ties = tuple(a.activity_id for a in items
                 if sum(r.direction == "FORWARD" for r in a.controlling_relationships) > 1)
    complete = not truncated and reason in {"NETWORK_START", "CONSTRAINT"}
    diagnostics = ()
    if not complete:
        diagnostics = (CPMDiagnostic("partial_path_trace", "Connected trace ends at a declared limit or control boundary.",
            CPMFindingSeverity.WARNING if truncated else CPMFindingSeverity.INFORMATIONAL,
            activity_id=ids[0], metadata={"end_reason": reason}),)
    floats = [a.calculated_total_float_hours for a in items]
    return CPMPath(path_id="", terminal_activity_id=anchor.activity_id,
        activity_ids=ids, relationship_ids=tuple(r.relationship_id for r in edges),
        minimum_total_float_hours=min(floats), maximum_total_float_hours=max(floats),
        duration_hours=duration, rank=0,
        ranking_reason="Selected anchor; lower minimum float; longer effective activity-hour sum; lexical codes, IDs and relationships. Ranking covers returned paths only.",
        anchor=anchor, classification=classification,
        qualification_reason=("Connected calculated controlling chain; every activity is at/below the critical float threshold."
            if classification == "CRITICAL" else "Connected chain to selected anchor; every activity is at/below the near threshold, at least one is above the critical threshold, and noncontrolling relationship slack is within the declared near bound."),
        activity_codes=tuple(a.activity_code for a in items),
        relationships=edges, activity_count=len(ids), relationship_count=len(edges),
        sum_effective_activity_duration_hours=duration_sum, relationship_lag_contribution_hours=lag_sum,
        duration_method=method, start_timestamp=items[0].calculated_early_start,
        finish_timestamp=items[-1].calculated_early_finish,
        controlling_tie_activity_ids=ties, constraint_causes=causes, end_reason=reason,
        trace_complete=complete, truncated=truncated, diagnostics=diagnostics)
