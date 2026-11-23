from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from app.models.schedule import Activity
from app.models.schedule import Relationship
from app.models.schedule import Schedule


@dataclass
class TopologicalSortResult:
    ordered_activities: list[Activity]
    unresolved_activities: list[Activity]

    @property
    def is_valid(self) -> bool:
        return not self.unresolved_activities


class ScheduleGraph:
    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

        # Key: internal P6 task_id
        # Value: Activity object
        self.activities_by_id: dict[str, Activity] = {
            activity.activity_id: activity
            for activity in schedule.activities.values()
        }

        # Key: predecessor task_id
        # Value: relationships leaving that activity
        self.successor_relationships: dict[
            str,
            list[Relationship],
        ] = {}

        # Key: successor task_id
        # Value: relationships entering that activity
        self.predecessor_relationships: dict[
            str,
            list[Relationship],
        ] = {}

        self._build_graph()

    def _build_graph(self) -> None:
        print("Build adjacency indexes from the schedule relationships.")
        

        for activity_id in self.activities_by_id:
            self.successor_relationships[activity_id] = []
            self.predecessor_relationships[activity_id] = []

        for relationship in self.schedule.relationships:
            predecessor_id = (
                relationship.predecessor_activity_id
            )
            successor_id = (
                relationship.successor_activity_id
            )

            # Ignore relationships pointing to activities that
            # are not included in the imported schedule.
            if predecessor_id not in self.activities_by_id:
                continue

            if successor_id not in self.activities_by_id:
                continue

            self.successor_relationships[
                predecessor_id
            ].append(relationship)

            self.predecessor_relationships[
                successor_id
            ].append(relationship)

    def get_activity_by_code(
        self,
        activity_code: str,
    ) -> Activity | None:
        return self.schedule.activities.get(activity_code)

    def get_activity_by_id(
        self,
        activity_id: str,
    ) -> Activity | None:
        return self.activities_by_id.get(activity_id)

    def get_direct_predecessors(
        self,
        activity_code: str,
    ) -> list[Activity]:
        print("Return activities directly connected as predecessors.")
        

        activity = self.get_activity_by_code(activity_code)

        if activity is None:
            return []

        relationships = self.predecessor_relationships.get(
            activity.activity_id,
            [],
        )

        return [
            self.activities_by_id[
                relationship.predecessor_activity_id
            ]
            for relationship in relationships
            if relationship.predecessor_activity_id
            in self.activities_by_id
        ]

    def get_direct_successors(
        self,
        activity_code: str,
    ) -> list[Activity]:
        print("Return activities directly connected as successors.")

        activity = self.get_activity_by_code(activity_code)

        if activity is None:
            return []

        relationships = self.successor_relationships.get(
            activity.activity_id,
            [],
        )

        return [
            self.activities_by_id[
                relationship.successor_activity_id
            ]
            for relationship in relationships
            if relationship.successor_activity_id
            in self.activities_by_id
        ]

    def get_all_predecessors(
        self,
        activity_code: str,
    ) -> list[Activity]:
        print("Use breadth-first search to find every upstream activity.")

        activity = self.get_activity_by_code(activity_code)

        if activity is None:
            return []

        visited: set[str] = {activity.activity_id}
        queue: deque[str] = deque([activity.activity_id])
        predecessors: list[Activity] = []

        while queue:
            current_activity_id = queue.popleft()

            relationships = self.predecessor_relationships.get(
                current_activity_id,
                [],
            )

            for relationship in relationships:
                predecessor_id = (
                    relationship.predecessor_activity_id
                )

                if predecessor_id in visited:
                    continue

                predecessor = self.activities_by_id.get(
                    predecessor_id
                )

                if predecessor is None:
                    continue

                visited.add(predecessor_id)
                queue.append(predecessor_id)
                predecessors.append(predecessor)

        return predecessors

    def get_all_successors(
        self,
        activity_code: str,
    ) -> list[Activity]:
        print("Use breadth-first search to find every downstream activity.")

        activity = self.get_activity_by_code(activity_code)

        if activity is None:
            return []

        visited: set[str] = {activity.activity_id}
        queue: deque[str] = deque([activity.activity_id])
        successors: list[Activity] = []

        while queue:
            current_activity_id = queue.popleft()

            relationships = self.successor_relationships.get(
                current_activity_id,
                [],
            )

            for relationship in relationships:
                successor_id = (
                    relationship.successor_activity_id
                )

                if successor_id in visited:
                    continue

                successor = self.activities_by_id.get(
                    successor_id
                )

                if successor is None:
                    continue

                visited.add(successor_id)
                queue.append(successor_id)
                successors.append(successor)

        return successors

    def get_start_activities(self) -> list[Activity]:
        print("Return activities with no valid predecessor relationships.")

        return [
            activity
            for activity_id, activity
            in self.activities_by_id.items()
            if not self.predecessor_relationships.get(
                activity_id
            )
        ]

    def get_finish_activities(self) -> list[Activity]:
        print("Return activities with no valid successor relationships.")

        return [
            activity
            for activity_id, activity
            in self.activities_by_id.items()
            if not self.successor_relationships.get(
                activity_id
            )
        ]

    def get_relationship(
        self,
        predecessor_code: str,
        successor_code: str,
    ) -> Relationship | None:
        predecessor = self.get_activity_by_code(
            predecessor_code
        )
        successor = self.get_activity_by_code(
            successor_code
        )

        if predecessor is None or successor is None:
            return None

        relationships = self.successor_relationships.get(
            predecessor.activity_id,
            [],
        )

        for relationship in relationships:
            if (
                relationship.successor_activity_id
                == successor.activity_id
            ):
                return relationship

        return None
    
    def detect_cycles(self) -> list[list[Activity]]:
        """
        Detect circular logic using depth-first search.

        Returns:
            A list of cycles. Each cycle is represented as a list
            of Activity objects, with the starting activity repeated
            at the end.

        Example:
            A1000 -> A1010 -> A1020 -> A1000
        """

        unvisited = 0
        visiting = 1
        visited = 2

        states: dict[str, int] = {
            activity_id: unvisited
            for activity_id in self.activities_by_id
        }

        current_path: list[str] = []
        path_positions: dict[str, int] = {}
        cycles: list[list[Activity]] = []
        cycle_signatures: set[tuple[str, ...]] = set()

        def visit(activity_id: str) -> None:
            states[activity_id] = visiting
            path_positions[activity_id] = len(current_path)
            current_path.append(activity_id)

            relationships = self.successor_relationships.get(
                activity_id,
                [],
            )

            for relationship in relationships:
                successor_id = relationship.successor_activity_id

                if successor_id not in states:
                    continue

                if states[successor_id] == unvisited:
                    visit(successor_id)

                elif states[successor_id] == visiting:
                    cycle_start_index = path_positions[
                        successor_id
                    ]

                    cycle_ids = (
                        current_path[cycle_start_index:]
                        + [successor_id]
                    )

                    signature = self._normalise_cycle_signature(
                        cycle_ids
                    )

                    if signature in cycle_signatures:
                        continue

                    cycle_signatures.add(signature)

                    cycle_activities = [
                        self.activities_by_id[node_id]
                        for node_id in cycle_ids
                        if node_id in self.activities_by_id
                    ]

                    cycles.append(cycle_activities)

            current_path.pop()
            path_positions.pop(activity_id, None)
            states[activity_id] = visited

        for activity_id in self.activities_by_id:
            if states[activity_id] == unvisited:
                visit(activity_id)

        return cycles
    
    def _normalise_cycle_signature(
        self,
        cycle_ids: list[str],
    ) -> tuple[str, ...]:
        """
        Create a consistent signature so the same cycle is not
        reported multiple times from different starting points.
        """

        if len(cycle_ids) < 2:
            return tuple(cycle_ids)

        # Remove the repeated final node temporarily.
        unique_cycle = cycle_ids[:-1]

        rotations = [
            tuple(
                unique_cycle[index:]
                + unique_cycle[:index]
            )
            for index in range(len(unique_cycle))
        ]

        return min(rotations)
    
    def topological_sort(self) -> TopologicalSortResult:
        """
        Arrange activities so every valid predecessor appears before
        its successor.

        Uses Kahn's algorithm, which is iterative and suitable for
        large schedules.
        """

        in_degree: dict[str, int] = {
            activity_id: len(
                self.predecessor_relationships.get(
                    activity_id,
                    [],
                )
            )
            for activity_id in self.activities_by_id
        }

        ready_queue: deque[str] = deque(
            activity_id
            for activity_id, degree in in_degree.items()
            if degree == 0
        )

        ordered_activities: list[Activity] = []

        while ready_queue:
            current_activity_id = ready_queue.popleft()

            current_activity = self.activities_by_id.get(
                current_activity_id
            )

            if current_activity is None:
                continue

            ordered_activities.append(current_activity)

            outgoing_relationships = (
                self.successor_relationships.get(
                    current_activity_id,
                    [],
                )
            )

            for relationship in outgoing_relationships:
                successor_id = (
                    relationship.successor_activity_id
                )

                if successor_id not in in_degree:
                    continue

                in_degree[successor_id] -= 1

                if in_degree[successor_id] == 0:
                    ready_queue.append(successor_id)

        unresolved_activities = [
            self.activities_by_id[activity_id]
            for activity_id, remaining_degree
            in in_degree.items()
            if remaining_degree > 0
            and activity_id in self.activities_by_id
        ]

        return TopologicalSortResult(
            ordered_activities=ordered_activities,
            unresolved_activities=unresolved_activities,
        )

