from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from app.models.scheduling_options import P6SchedulingOptions

@dataclass
class Project:
    project_id: str
    project_code: str
    project_name: str
    data_date: datetime | None = None
    planned_start: datetime | None = None
    planned_finished: datetime | None = None

@dataclass
class WBS:
    wbs_id: str
    wbs_code: str
    wbs_name: str
    parent_wbs_id: str | None = None

@dataclass
class Activity:
    activity_id: str
    activity_code: str
    activity_name: str
    project_id: str

    wbs_id: str | None = None
    activity_type: str | None = None
    status: str | None = None
    calendar_id: str | None = None
    raw_activity_type: str | None = None
    raw_status: str | None = None
    primary_constraint_type: str | None = None
    primary_constraint_date: datetime | None = None
    secondary_constraint_type: str | None = None
    secondary_constraint_date: datetime | None = None
    raw_primary_constraint_type: str | None = None
    raw_secondary_constraint_type: str | None = None

    planned_start: datetime | None = None
    planned_finish: datetime | None = None
    actual_start: datetime | None = None
    actual_finish: datetime | None = None

    original_duration_hours: float | None = None
    remaining_duration_hours: float | None = None
    total_float_hours: float | None = None
    free_float_hours: float | None = None

    percent_complete: float | None = None

    # Imported P6 dates remain independent of planned dates and CPM results.
    early_start: datetime | None = None
    early_finish: datetime | None = None
    late_start: datetime | None = None
    late_finish: datetime | None = None
    expected_finish: datetime | None = None
    remaining_start: datetime | None = None
    remaining_finish: datetime | None = None
    duration_type: str | None = None
    suspend_date: datetime | None = None
    resume_date: datetime | None = None


@dataclass
class Relationship:
    relationship_id: str
    predecessor_activity_id: str
    successor_activity_id: str
    relationship_type: str
    lag_hours: float = 0.0
    raw_relationship_type: str | None = None

@dataclass
class Calendar:
    calendar_id: str
    calendar_name: str
    project_id: str | None = None
    default_flag: bool = False
    base_calendar_id: str | None = None
    last_change_date: datetime | None = None
    calendar_type: str | None = None
    hours_per_day: float | None = None
    hours_per_week: float | None = None
    hours_per_month: float | None = None
    hours_per_year: float | None = None
    resource_private: bool | None = None
    raw_clndr_data: str | None = None
    weekly_pattern: Any | None = None
    exceptions: tuple[Any, ...] = ()
    diagnostics: tuple[Any, ...] = ()

@dataclass
class Schedule:
    project: Project | None = None

    activities: dict[str, Activity] = field(default_factory=dict)
    activities_by_id: dict[str, Activity] = field(default_factory=dict)
    activities_by_code: dict[str, list[Activity]] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)
    wbs_nodes: dict[str, WBS] = field(default_factory=dict)
    calendars: dict[str, Calendar] = field(default_factory=dict)

    resources: dict[str, Resource] = field(default_factory=dict)
    resource_assignments: dict[str, ResourceAssignment] = field(default_factory=dict)
    assignments_by_activity_id: dict[str, list[ResourceAssignment]] = field(default_factory=dict)
    assignments_by_resource_id: dict[str, list[ResourceAssignment]] = field(default_factory=dict)

    activity_code_types: dict[str, ActivityCodeType] = field(default_factory=dict)
    activity_code_values: dict[str, ActivityCodeValue] = field(default_factory=dict)
    activity_code_assignments: list[ActivityCodeAssignment] = field(default_factory=list)
    code_assignments_by_activity_id: dict[str, list[ActivityCodeAssignment]] = field(default_factory=dict)

    udf_definitions: dict[str, UDFDefinition] = field(default_factory=dict)
    udf_values: list[UDFValue] = field(default_factory=list)
    udf_values_by_activity_id: dict[str, list[UDFValue]] = field(default_factory=dict)

    scheduling_options: P6SchedulingOptions | None = None

    def get_activity(self, activity_code: str) -> Activity | None:
        matches = self.activities_by_code.get(activity_code, [])
        return matches[0] if len(matches) == 1 else None

    def get_activity_by_id(self, activity_id: str) -> Activity | None:
        return self.activities_by_id.get(activity_id)

    def get_activities_by_code(self, activity_code: str) -> list[Activity]:
        return list(self.activities_by_code.get(activity_code, []))

    def rebuild_activity_indexes(self) -> None:
        self.activities_by_id = {
            activity.activity_id: activity
            for activity in self.activities.values()
        }
        self.activities_by_code = {}
        for activity in self.activities.values():
            self.activities_by_code.setdefault(activity.activity_code, []).append(activity)

    def get_predecessor_relationships(
            self,
            activity_code: str,
    ) -> list[Relationship]:
        activity = self.get_activity(activity_code)

        if activity is None:
            return []
        return [
            relationship
            for relationship in self.relationships
            if relationship.successor_activity_id == activity.activity_id
        ]
    
    def get_successor_relationships(
            self,
            activity_code: str,
    ) -> list[Relationship]:
        activity = self.get_activity(activity_code)

        if activity is None:
            return[]
        
        return[
            relationship
            for relationship in self.relationships
            if relationship.predecessor_activity_id == activity.activity_id
        ]

    def get_predecessors(
            self,
            activity_code: str,
    ) -> list [Activity]:
        relationships = self.get_predecessor_relationships(activity_code)

        # activity_by_internal_id = {activity.activity_id: activity
        #                            for activity in self.activities.values()}
        
        # return [
        #     activity_by_internal_id[relationship.predecessor_activity_id]
        #     for relationship in relationships
        #     if relationship.predecessor_activity_id
        #     in activity_by_internal_id
        # ]

        return [
            self.activities_by_id[relationship.predecessor_activity_id]
            for relationship in relationships
            if relationship.predecessor_activity_id
            in self.activities_by_id
        ]
    
    def get_successors(
            self,
            activity_code: str
    ) -> list [Activity]:
        relationships = self.get_successor_relationships(activity_code)

        # activity_by_internal_id = {
        #     activity.activity_id: activity
        #     for activity in self.activities.values()}
        # return [
        #     activity_by_internal_id[relationship.successor_activity_id]
        #     for relationship in relationships
        #     if relationship.successor_activity_id
        #     in activity_by_internal_id            
        # ]

        return [
            self.activities_by_id[relationship.successor_activity_id]
            for relationship in relationships
            if relationship.successor_activity_id
            in self.activities_by_id            
        ]
    
    def get_critical_activities(
        self,
        float_threshold_hours: float = 0,
    ) -> list[Activity]:
        return[
            activity
            for activity in self.activities.values()
            if activity.total_float_hours is not None
            and activity.total_float_hours <= float_threshold_hours
        ]
    
    def get_negative_float_activities(self) -> list[Activity]:
        return[
            activity
            for activity in self.activities.values()
            if activity.total_float_hours is not None
            and activity.total_float_hours < 0
        ]

    def rebuild_optional_indexes(self) -> None:
        self.assignments_by_activity_id = {}
        self.assignments_by_resource_id = {}
        for assignment in self.resource_assignments.values():
            self.assignments_by_activity_id.setdefault(assignment.activity_id, []).append(assignment)
            self.assignments_by_resource_id.setdefault(assignment.resource_id, []).append(assignment)

        self.code_assignments_by_activity_id = {}
        for assignment in self.activity_code_assignments:
            self.code_assignments_by_activity_id.setdefault(assignment.activity_id, []).append(assignment)

        self.udf_values_by_activity_id = {}
        for udf_value in self.udf_values:
            definition = self.udf_definitions.get(udf_value.udf_type_id)
            if udf_value.subject_table.upper() == "TASK" and definition is not None:
                self.udf_values_by_activity_id.setdefault(udf_value.foreign_object_id, []).append(udf_value)

    def get_resource_assignments(self, activity_id: str) -> list[ResourceAssignment]:
        return list(self.assignments_by_activity_id.get(activity_id, []))

    def get_activity_code_assignments(self, activity_id: str) -> list[ActivityCodeAssignment]:
        return list(self.code_assignments_by_activity_id.get(activity_id, []))

    def get_activity_udf_values(self, activity_id: str) -> list[UDFValue]:
        return list(self.udf_values_by_activity_id.get(activity_id, []))

    def get_activity_code(self, activity_id: str, type_name: str) -> list[ActivityCodeValue]:
        type_ids = {
            code_type.activity_code_type_id
            for code_type in self.activity_code_types.values()
            if code_type.name == type_name
        }
        values: list[ActivityCodeValue] = []
        for assignment in self.code_assignments_by_activity_id.get(activity_id, []):
            if assignment.activity_code_type_id in type_ids:
                value = self.activity_code_values.get(assignment.activity_code_id)
                if value is not None:
                    values.append(value)
        return values

    def get_calendar(self, calendar_id: str) -> Calendar | None:
        return self.calendars.get(calendar_id)

    def get_activity_calendar(self, activity: Activity) -> Calendar | None:
        if activity.calendar_id is None:
            return None
        return self.calendars.get(activity.calendar_id)

@dataclass(frozen=True)
class Resource:
    resource_id: str
    resource_code: str | None = None
    resource_name: str | None = None
    parent_resource_id: str | None = None
    resource_type: str | None = None
    active_flag: str | None = None
    employee_id: str | None = None
    email: str | None = None
    calendar_id: str | None = None
    role_id: str | None = None
    cost_qty_type: str | None = None
    unit_id: str | None = None
    location_id: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceAssignment:
    assignment_id: str
    activity_id: str
    resource_id: str
    role_id: str | None = None
    account_id: str | None = None
    remain_quantity: float | None = None
    target_quantity: float | None = None
    actual_regular_quantity: float | None = None
    actual_overtime_quantity: float | None = None
    planned_cost: float | None = None
    actual_regular_cost: float | None = None
    actual_overtime_cost: float | None = None
    remaining_cost: float | None = None
    planned_start: datetime | None = None
    planned_finish: datetime | None = None
    actual_start: datetime | None = None
    actual_finish: datetime | None = None
    remaining_start: datetime | None = None
    remaining_finish: datetime | None = None
    cost_per_quantity: float | None = None
    cost_quantity_type: str | None = None
    rate_type: str | None = None
    resource_type: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivityCodeType:
    activity_code_type_id: str
    name: str
    scope: str | None = None
    project_id: str | None = None
    wbs_id: str | None = None
    sequence: int | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivityCodeValue:
    activity_code_id: str
    activity_code_type_id: str
    name: str
    short_name: str | None = None
    parent_activity_code_id: str | None = None
    sequence: int | None = None
    color: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivityCodeAssignment:
    activity_id: str
    activity_code_type_id: str
    activity_code_id: str
    project_id: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class UDFDefinition:
    udf_type_id: str
    table_name: str
    name: str
    label: str | None = None
    data_type: str | None = None
    sequence: int | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class UDFValue:
    udf_type_id: str
    foreign_object_id: str
    subject_table: str
    raw_string_value: str | None = None
    text_value: str | None = None
    numeric_value: float | None = None
    date_value: datetime | None = None
    code_value: str | None = None
    raw: dict[str, str] = field(default_factory=dict)