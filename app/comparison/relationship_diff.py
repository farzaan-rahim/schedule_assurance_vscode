from __future__ import annotations

from app.comparison.models import (
    ActivityMatch,
    ComparisonDiagnostic,
    RelationshipChangeType,
    RelationshipVariance,
)
from app.models.schedule import Activity, Relationship, Schedule


def _activity_by_id(schedule: Schedule) -> dict[str, Activity]:
    return dict(schedule.activities_by_id)


def compare_relationships(
    baseline: Schedule,
    current: Schedule,
    matches: list[ActivityMatch],
) -> tuple[list[RelationshipVariance], tuple[ComparisonDiagnostic, ...]]:
    baseline_by_id = _activity_by_id(baseline)
    current_by_id = _activity_by_id(current)

    baseline_code_by_id = {
        activity.activity_id: activity.activity_code
        for activity in baseline.activities.values()
    }
    current_code_by_id = {
        activity.activity_id: activity.activity_code
        for activity in current.activities.values()
    }

    matched_baseline_to_current: dict[str, Activity] = {}
    matched_current_to_baseline: dict[str, Activity] = {}
    for match in matches:
        if match.baseline_activity is not None and match.current_activity is not None:
            matched_baseline_to_current[match.baseline_activity.activity_id] = match.current_activity
            matched_current_to_baseline[match.current_activity.activity_id] = match.baseline_activity

    def baseline_key(rel: Relationship) -> tuple[str, str, str, float]:
        pred = matched_baseline_to_current.get(rel.predecessor_activity_id)
        succ = matched_baseline_to_current.get(rel.successor_activity_id)
        pred_code = pred.activity_code if pred else baseline_code_by_id.get(rel.predecessor_activity_id)
        succ_code = succ.activity_code if succ else baseline_code_by_id.get(rel.successor_activity_id)
        return (pred_code or "", succ_code or "", rel.relationship_type, rel.lag_hours)

    def current_key(rel: Relationship) -> tuple[str, str, str, float]:
        pred = matched_current_to_baseline.get(rel.predecessor_activity_id)
        succ = matched_current_to_baseline.get(rel.successor_activity_id)
        pred_code = pred.activity_code if pred else current_code_by_id.get(rel.predecessor_activity_id)
        succ_code = succ.activity_code if succ else current_code_by_id.get(rel.successor_activity_id)
        return (pred_code or "", succ_code or "", rel.relationship_type, rel.lag_hours)

    baseline_topology: dict[tuple[str, str], list[Relationship]] = {}
    current_topology: dict[tuple[str, str], list[Relationship]] = {}

    for rel in baseline.relationships:
        pred_match = matched_baseline_to_current.get(rel.predecessor_activity_id)
        succ_match = matched_baseline_to_current.get(rel.successor_activity_id)
        pred_code = pred_match.activity_code if pred_match else baseline_code_by_id.get(rel.predecessor_activity_id)
        succ_code = succ_match.activity_code if succ_match else baseline_code_by_id.get(rel.successor_activity_id)
        if pred_code and succ_code:
            baseline_topology.setdefault((pred_code, succ_code), []).append(rel)

    for rel in current.relationships:
        pred_match = matched_current_to_baseline.get(rel.predecessor_activity_id)
        succ_match = matched_current_to_baseline.get(rel.successor_activity_id)
        pred_code = pred_match.activity_code if pred_match else current_code_by_id.get(rel.predecessor_activity_id)
        succ_code = succ_match.activity_code if succ_match else current_code_by_id.get(rel.successor_activity_id)
        if pred_code and succ_code:
            current_topology.setdefault((pred_code, succ_code), []).append(rel)

    variances: list[RelationshipVariance] = []
    diagnostics: list[ComparisonDiagnostic] = []

    all_pairs = sorted(set(baseline_topology) | set(current_topology))
    for pair in all_pairs:
        baseline_rels = baseline_topology.get(pair, [])
        current_rels = current_topology.get(pair, [])

        if not baseline_rels:
            for rel in current_rels:
                variances.append(_relationship_variance(
                    RelationshipChangeType.ADDED,
                    pair[0], pair[1],
                    None,
                    rel,
                    baseline_by_id,
                    current_by_id,
                ))
            continue

        if not current_rels:
            for rel in baseline_rels:
                variances.append(_relationship_variance(
                    RelationshipChangeType.REMOVED,
                    pair[0], pair[1],
                    rel,
                    None,
                    baseline_by_id,
                    current_by_id,
                ))
            continue

        used_current: set[int] = set()
        for baseline_rel in baseline_rels:
            candidates = [
                (index, rel)
                for index, rel in enumerate(current_rels)
                if index not in used_current
            ]
            if not candidates:
                variances.append(_relationship_variance(
                    RelationshipChangeType.REMOVED,
                    pair[0], pair[1], baseline_rel, None,
                    baseline_by_id, current_by_id,
                ))
                continue

            index, current_rel = candidates[0]
            used_current.add(index)

            if baseline_rel.relationship_type != current_rel.relationship_type:
                variances.append(_relationship_variance(
                    RelationshipChangeType.TYPE_CHANGED,
                    pair[0], pair[1], baseline_rel, current_rel,
                    baseline_by_id, current_by_id,
                ))
            if baseline_rel.lag_hours != current_rel.lag_hours:
                variances.append(_relationship_variance(
                    RelationshipChangeType.LAG_CHANGED,
                    pair[0], pair[1], baseline_rel, current_rel,
                    baseline_by_id, current_by_id,
                ))

        for index, current_rel in enumerate(current_rels):
            if index not in used_current:
                variances.append(_relationship_variance(
                    RelationshipChangeType.ADDED,
                    pair[0], pair[1], None, current_rel,
                    baseline_by_id, current_by_id,
                ))

    for match in matches:
        if match.classification.value == "AMBIGUOUS":
            diagnostics.append(ComparisonDiagnostic(
                code="relationship_endpoint_ambiguous",
                message="Relationship comparison skipped because an endpoint activity is ambiguous.",
                activity_code=(match.baseline_activity or match.current_activity).activity_code,
                baseline_activity_id=match.baseline_activity.activity_id if match.baseline_activity else None,
                current_activity_id=match.current_activity.activity_id if match.current_activity else None,
            ))

    return variances, tuple(diagnostics)


def _relationship_variance(
    change_type: RelationshipChangeType,
    predecessor_code: str,
    successor_code: str,
    baseline_rel: Relationship | None,
    current_rel: Relationship | None,
    baseline_by_id: dict[str, Activity],
    current_by_id: dict[str, Activity],
) -> RelationshipVariance:
    baseline_pred = baseline_by_id.get(baseline_rel.predecessor_activity_id) if baseline_rel else None
    baseline_succ = baseline_by_id.get(baseline_rel.successor_activity_id) if baseline_rel else None
    current_pred = current_by_id.get(current_rel.predecessor_activity_id) if current_rel else None
    current_succ = current_by_id.get(current_rel.successor_activity_id) if current_rel else None

    return RelationshipVariance(
        change_type=change_type,
        predecessor_activity_code=predecessor_code,
        successor_activity_code=successor_code,
        baseline_relationship=baseline_rel,
        current_relationship=current_rel,
        baseline_predecessor_activity=baseline_pred,
        baseline_successor_activity=baseline_succ,
        current_predecessor_activity=current_pred,
        current_successor_activity=current_succ,
        baseline_relationship_type=baseline_rel.relationship_type if baseline_rel else None,
        current_relationship_type=current_rel.relationship_type if current_rel else None,
        baseline_lag_hours=baseline_rel.lag_hours if baseline_rel else None,
        current_lag_hours=current_rel.lag_hours if current_rel else None,
    )
