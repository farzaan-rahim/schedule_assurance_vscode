from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

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

    planned_start: datetime | None = None
    planned_finish: datetime | None = None
    actual_start: datetime | None = None
    actual_finish: datetime | None = None

    original_duration_hours: float | None = None
    remaining_duration_hours: float | None = None
    total_float_hours: float | None = None
    free_float_hours: float | None = None

    percent_complete: float | None = None

@dataclass
class Relationship:
    relationship_id: str
    predecessor_activity_id: str
    successor_activity_id: str
    relationship_type: str
    lag_hours: float = 0.0

@dataclass
class Calendar:
    calendar_id: str
    calendar_name: str
    project_id: str | None = None

@dataclass
class Schedule:
    project: Project | None = None

    activities: dict[str, Activity] = field(default_factory=dict)
    activities_by_id: dict[str, Activity] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)
    wbs_nodes: dict[str, WBS] = field(default_factory=dict)
    calendars: dict[str, Calendar] = field(default_factory=dict)

    def get_activity(self, activity_code: str) -> Activity | None:
        return self.activities.get(activity_code)
    
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