from __future__ import annotations

from app.models.schedule import Schedule


class WBSHierarchyError(Exception):
    pass


def wbs_path(schedule: Schedule, wbs_id: str | None) -> str | None:
    if not wbs_id:
        return None

    nodes = schedule.wbs_nodes
    if wbs_id not in nodes:
        raise WBSHierarchyError(f"WBS ID '{wbs_id}' is missing from schedule WBS nodes")

    names: list[str] = []
    visited: set[str] = set()
    current_id: str | None = wbs_id

    while current_id:
        if current_id in visited:
            raise WBSHierarchyError("Circular WBS parent hierarchy detected")
        visited.add(current_id)

        node = nodes.get(current_id)
        if node is None:
            raise WBSHierarchyError(f"WBS parent ID '{current_id}' is missing")

        names.append(node.wbs_code or node.wbs_name)
        current_id = node.parent_wbs_id

    names.reverse()
    return " > ".join(name for name in names if name)
