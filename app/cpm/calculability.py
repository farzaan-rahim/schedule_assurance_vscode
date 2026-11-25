"""Opt-in, conservative weak-component isolation around the validated CPM core.

Both early and late dates/float are published together. Forward dependencies and
backward dependencies therefore require quarantining the whole weak component;
this module never reconnects logic or treats an excluded endpoint as an anchor.
"""
from collections import defaultdict, deque
from dataclasses import replace
from math import isfinite

from app.cpm.activity_state import activity_decision
from app.cpm.models import (
    CPMActivityCalculability, CPMComponentCalculability, CPMDiagnostic,
    CPMFindingSeverity, CPMRelationshipCalculability,
)
from app.cpm.validation import validate_schedule
from app.graph.schedule_graph import ScheduleGraph
from app.importers.p6_normalization import normalize_status


def calculate_valid_components(service, schedule, graph, config):
    from app.cpm.service import _failed_calculation

    diagnostics, _ = validate_schedule(schedule, graph, config)
    components, component_for = _components(schedule, graph)
    reasons, roots = defaultdict(set), defaultdict(set)
    excluded = set()
    data_date = (schedule.project.data_date if schedule.project else None) or config.project_start_override

    def block(activity_id, code):
        if activity_id in component_for:
            key = component_for[activity_id]
            reasons[key].add(code)
            roots[key].add(activity_id)

    def error_scope(finding):
        if finding.activity_id in component_for:
            block(finding.activity_id, finding.code)
            return True
        if finding.relationship_id in relationships:
            r = relationships[finding.relationship_id]
            for key in (r.predecessor_activity_id, r.successor_activity_id):
                block(key, finding.code)
            return True
        return False

    relationships = {r.relationship_id: r for r in schedule.relationships}
    global_errors = []
    for finding in diagnostics:
        if finding.severity == CPMFindingSeverity.ERROR and finding.code != "circular_logic":
            if not error_scope(finding):
                global_errors.append(finding)
    if any(d.code == "circular_logic" for d in diagnostics):
        diagnostics = [d for d in diagnostics if d.code != "circular_logic"]
        for a in graph.topological_sort().unresolved_activities:
            block(a.activity_id, "circular_component")
        diagnostics.append(CPMDiagnostic("circular_component", "Cycle and dependent component withheld; unrelated components may calculate.", CPMFindingSeverity.ERROR))

    for a in (() if global_errors else schedule.activities.values()):
        _, _, disposition = activity_decision(a, config, data_date)
        if disposition == "EXCLUDE" or (a.calendar_id not in schedule.calendars and config.missing_calendar_policy == "EXCLUDE"):
            excluded.add(a.activity_id)
            if graph.predecessor_relationships[a.activity_id] or graph.successor_relationships[a.activity_id]:
                block(a.activity_id, "excluded_network_endpoint")
                diagnostics.append(CPMDiagnostic("excluded_network_endpoint", "Excluded endpoint has incident logic; its whole date/float component is withheld.", CPMFindingSeverity.ERROR, activity_id=a.activity_id))
        if a.activity_id in excluded:
            continue
        # Compatibility gates are explicit for this opt-in conservative mode.
        # Expected Finish is already preserved; no option is silently applied.
        if a.expected_finish is not None and normalize_status(a.raw_status if a.raw_status is not None else a.status) != "complete":
            block(a.activity_id, "unconfirmed_expected_finish")
            diagnostics.append(CPMDiagnostic("unconfirmed_expected_finish", "Imported Expected Finish scheduling is unsupported; component withheld.", CPMFindingSeverity.ERROR, activity_id=a.activity_id))
    for r in (() if global_errors else schedule.relationships):
        p = schedule.activities.get(r.predecessor_activity_id)
        q = schedule.activities.get(r.successor_activity_id)
        if p is None or q is None or p.activity_id in excluded or q.activity_id in excluded:
            continue
        if not isinstance(r.lag_hours, (int, float)) or not isfinite(r.lag_hours):
            continue
        pstatus = normalize_status(p.raw_status if p.raw_status is not None else p.status)
        case = None
        if r.relationship_type.upper() == "SS" and r.lag_hours > 0 and pstatus == "in_progress" and p.actual_start:
            case, root = "PROGRESSED_POSITIVE_SS_LAG", p.activity_id
        elif r.relationship_type.upper() == "FS" and r.lag_hours >= 0 and pstatus in {"not_started", "in_progress"} and q.actual_start:
            case, root = "OUT_OF_SEQUENCE_FS", q.activity_id
        if case:
            block(root, "unconfirmed_progress_methodology")
            diagnostics.append(CPMDiagnostic("unconfirmed_progress_methodology", "Observed progressed relationship has unconfirmed P6 retained/expired-lag semantics; component withheld.", CPMFindingSeverity.ERROR, activity_id=root, relationship_id=r.relationship_id, metadata={"condition": case}))
    if global_errors:
        for key in schedule.activities:
            for d in global_errors:
                block(key, d.code)

    if reasons and config.disconnected_component_policy == "PROJECT_FINISH" and config.required_project_finish is None:
        for key in schedule.activities:
            if key not in excluded:
                block(key, "unknown_shared_finish_anchor")
        diagnostics.append(CPMDiagnostic("unknown_shared_finish_anchor", "An implicit shared finish cannot be established while a component is blocked.", CPMFindingSeverity.ERROR))

    core = None
    # Every unsuccessful iteration blocks at least one additional component.
    # Collect all identifiable runtime failures before retrying, with no recursion.
    for _ in range(len(components) + 1):
        included = {key for key in schedule.activities if key not in excluded and component_for[key] not in reasons}
        if not included:
            break
        subset = replace(schedule, activities={k: a for k, a in schedule.activities.items() if k in included},
                         relationships=[r for r in schedule.relationships if r.predecessor_activity_id in included and r.successor_activity_id in included])
        subset.rebuild_activity_indexes()
        current = service.calculate(subset, ScheduleGraph(subset), replace(config, component_calculation_policy="STRICT"))
        if current.status == "CALCULATED":
            core = current
            diagnostics.extend(current.diagnostics)
            break
        previous = len(reasons)
        for finding in current.diagnostics:
            diagnostics.append(finding)
            if finding.severity == CPMFindingSeverity.ERROR:
                if not error_scope(finding):
                    for key in included:
                        block(key, finding.code)
        if len(reasons) == previous:
            for key in included:
                block(key, "unlocalized_calculation_failure")

    activity_states = tuple(CPMActivityCalculability(
        key, component_for[key], "EXCLUDED" if key in excluded else ("BLOCKED" if component_for[key] in reasons else "CALCULATED"),
        tuple(sorted({d.code for d in diagnostics if d.activity_id == key})) if key in excluded else (("blocked_component",) if component_for[key] in reasons else ()),
    ) for key in sorted(schedule.activities))
    blocked_count = sum(a.status == "BLOCKED" for a in activity_states)
    calculated_ids = {a.activity_id for a in activity_states if a.status == "CALCULATED"}
    relation_states = tuple(CPMRelationshipCalculability(r.relationship_id,
        "CALCULABLE" if r.predecessor_activity_id in calculated_ids and r.successor_activity_id in calculated_ids else "BLOCKED",
        () if r.predecessor_activity_id in calculated_ids and r.successor_activity_id in calculated_ids else ("unavailable_component_endpoint",),
    ) for r in sorted(schedule.relationships, key=lambda r: r.relationship_id))
    relationship_counts = defaultdict(int)
    for r in schedule.relationships:
        key = component_for.get(r.predecessor_activity_id, component_for.get(r.successor_activity_id))
        relationship_counts[key] += 1
    by_id = {a.activity_id: a for a in core.activity_results} if core else {}
    summaries = tuple(CPMComponentCalculability(
        key, len(ids), relationship_counts[key],
        "BLOCKED" if key in reasons else ("CALCULATED" if any(i in calculated_ids for i in ids) else "EXCLUDED"),
        tuple(sorted(reasons.get(key, ()))), tuple(sorted(roots.get(key, ()))),
        max((by_id[i].calculated_early_finish for i in ids if i in by_id), default=None),
    ) for key, ids in components.items())
    # Keep diagnostics from blocked components with their original severity.
    unique = {}
    for d in diagnostics:
        unique[(d.code, d.severity, d.activity_id, d.relationship_id, d.message, repr(d.metadata))] = d
    diagnostics = tuple(unique.values())
    if core is None:
        core = _failed_calculation(schedule, config, diagnostics, len(excluded))
    has_blocked_scope = bool(reasons or global_errors) or any(r.status == "BLOCKED" for r in relation_states)
    status = ("PARTIALLY_CALCULATED" if has_blocked_scope else "CALCULATED") if calculated_ids else ("BLOCKED" if has_blocked_scope else "EXCLUDED")
    from app.cpm.comparison import capability_diagnostics
    changes = dict(status=status, schedule=schedule, calculation_config=config,
                   comparison_diagnostics=capability_diagnostics(schedule, config),
                   eligible_activity_count=len(calculated_ids), excluded_activity_count=len(excluded),
                   blocked_activity_count=blocked_count, relationship_count=len(schedule.relationships),
                   diagnostics=diagnostics, activity_calculability=activity_states,
                   relationship_calculability=relation_states, components=summaries,
                   reliability_scope="VALIDATED_COMPONENTS")
    if status != "CALCULATED":
        changes.update(completion_anchor=None, completion_anchor_candidates=(),
                       project_finish_anchor=None, calculated_completion=None,
                       critical_paths=(), near_critical_paths=(), path_statistics=(),
                       anchor_selection_status="INCOMPLETE_NETWORK", path_status="BLOCKED_COMPONENTS")
    return replace(core, **changes)


def _components(schedule, graph):
    remaining = set(schedule.activities)
    components, component_for = {}, {}
    for seed in sorted(schedule.activities):
        if seed not in remaining:
            continue
        remaining.remove(seed)
        queue, members = deque([seed]), []
        while queue:
            key = queue.popleft()
            members.append(key)
            for r in graph.predecessor_relationships[key] + graph.successor_relationships[key]:
                other = r.predecessor_activity_id if r.successor_activity_id == key else r.successor_activity_id
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        components[seed] = tuple(sorted(members))
        component_for.update((key, seed) for key in members)
    return components, component_for
