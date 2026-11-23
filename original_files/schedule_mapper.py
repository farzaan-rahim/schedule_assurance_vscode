from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.schedule import Activity
from app.models.schedule import Calendar
from app.models.schedule import Project
from app.models.schedule import Relationship
from app.models.schedule import Schedule
from app.models.schedule import WBS

class ScheduleMapper:
    def map(
            self,
            tables: dict[str, list[dict[str, Any]]],
    ) -> Schedule:
        schedule = Schedule()

        schedule.project = self._map_project(
            tables.get("PROJECT", [])
        )

        schedule.wbs_nodes = self._map_wbs(
            tables.get("PROJWBS", [])
        )

        schedule.calendars = self._map_calendars(
            tables.get("CALENDAR", [])
        )

        schedule.activities = self._map_activities(
            tables.get("TASK", [])
        )

        schedule.activities_by_id = {
            activity.activity_id :activity
            for activity in schedule.activities.values()}

        schedule.relationships = self._map_relationships(
            tables.get("TASKPRED", [])
        )

        return schedule
    
    def _map_project(
            self,
            rows: list[dict[str, Any]],
    ) -> Project | None:
        if not rows:
            return None
        row = rows[0]

        return Project(
            project_id = self._get_value(
                row,
                "proj_id",
            ),
            project_code = self._get_value(
                row,
                "proj_short_name",
                "proj_code",
            ),
            project_name = self._get_value(
                row,
                "proj_name",
                "proj_short_name",
            ),
            data_date = self._parse_datetime(
                self._get_value(
                    row,
                    "last_recalc_date",
                    "data_date",
                )
            ),
            planned_start = self._parse_datetime(
                self._get_value(
                    row,
                    "plan_start_date",
                    "planned_start_date",
                )
            ),
            planned_finished = self._parse_datetime(
                self._get_value(
                    row,
                    "plan_end_date",
                    "planned_end_date",
                    "scd_end_date",
                )
            ),
        )
    
    def _map_wbs(
            self,
            rows: list[dict[str, Any]],
    ) -> dict[str, WBS]:
        wbs_nodes: dict[str, WBS] = {}

        for row in rows:
            wbs_id = self._get_value(
                row,
                "wbs_id",
            )

            if not wbs_id:
                continue

            wbs_nodes[wbs_id] = WBS(
                wbs_id = wbs_id,
                wbs_code = self._get_value(
                    row,
                    "wbs_short_name",
                    "wbs_code",
                ),
                wbs_name = self._get_value(
                    row,
                    "wbs_name",
                ),
                parent_wbs_id = self._get_optional_value(
                    row,
                    "parent_wbs_id",
                ),
            )
        return wbs_nodes
    def _map_calendars (
            self,
            rows: list[dict[str, Any]],
    ) ->dict [str, Calendar]:
        calendars: dict[str, Calendar] = {}

        for row in rows:
            calendar_id = self._get_value(
                row,
                "clndr_id",
                "calendar_id",
            )

            if not calendar_id:
                continue

            calendars[calendar_id] = Calendar(
                calendar_id=calendar_id,
                calendar_name = self._get_value(
                    row,
                    "clndr_name",
                    "calendar_name",
                ),
                project_id = self._get_optional_value(
                    row,
                    "proj_id",
                ),
            )
        return calendars
    def _map_activities(
            self,
            rows: list[dict[str, Any]],
    ) -> dict[str, Activity]:
        activities: dict[str, Activity] = {}

        for row in rows:
            activity_id = self._get_value(
                row,
                "task_id",
            )

            activity_code = self._get_value(
                row,
                "task_code",
            )

            if not activity_id or not activity_code:
                continue

            activity = Activity(
                activity_id = activity_id,
                activity_code = activity_code,
                activity_name = self._get_value(
                    row,
                    "task_name",
                ),
                project_id = self._get_value(
                    row,
                    "proj_id",
                ),
                wbs_id = self._get_optional_value(
                    row,
                    "wbs_id",
                ),
                activity_type = self._get_optional_value(
                    row,
                    "task_type",
                ),
                status = self._get_optional_value(
                    row,
                    "status_code",
                    "task_status",
                ),
                calendar_id = self._get_optional_value(
                    row,
                    "clndr_id",
                ),
                planned_start = self._parse_datetime(
                    self._get_optional_value(
                        row,
                        "target_start_date",
                        "early_start_date",
                        "start_date",
                    )
                ),
                planned_finish = self._parse_datetime(
                    self._get_optional_value(
                        row,
                        "target_end_date",
                        "early_end_date",
                        "end_date",
                    )
                ),
                actual_start = self._parse_datetime(
                    self._get_optional_value(
                        row,
                        "act_start_date",
                    )
                ),
                actual_finish = self._parse_datetime(
                    self._get_optional_value(
                        row,
                        "act_end_date",
                    )
                ),
                original_duration_hours = self._parse_float(
                    self._get_optional_value(
                        row,
                        "target_drtn_hr_cnt",
                        "orgi_drtn_hr_cnt",
                    )
                ),
                remaining_duration_hours = self._parse_float(
                    self._get_optional_value(
                        row,
                        "remain_drtn_hr_cnt",
                    )
                ),
                total_float_hours = self._parse_float(
                    self._get_optional_value(
                        row,
                        "total_float_hr_cnt",
                    )
                ),
                free_float_hours = self._parse_float(
                    self._get_optional_value(
                        row,
                        "free_float_hr_cnt",
                    )
                ),
                percent_complete = self._map_percent_complete(
                    row
                ),
            )
            
            activities[activity_code] = activity
        return activities
    
    def _map_relationships(
            self,
            rows: list[dict[str, Any]],
    ) -> list[Relationship]:
        relationships: list [Relationship] = []

        for row in rows:
            predecessor_id = self._get_value(
                row,
                "pred_task_id",
            )

            successor_id = self._get_value(
                row,
                "task_id",
            )

            if not predecessor_id or not successor_id:
                continue

            relationship_id = self._get_value(
                row,
                "task_pred_id",
                "pred_id",
            )

            relationship_type = self._normalise_relationship_type(
                self._get_value(
                    row,
                    "pred_type",
                )
            )

            relationships.append(
                Relationship(
                    relationship_id=relationship_id,
                    predecessor_activity_id=predecessor_id,
                    successor_activity_id=successor_id,
                    relationship_type=relationship_type,
                    lag_hours=self._parse_float(
                        self._get_optional_value(
                            row,
                            "lag_hr_cnt",
                        )
                    ) 
                    or 0.0,
                )
            )
        return relationships
    def _map_percent_complete(
            self,
            row: dict[str, Any],            
    ) -> float | None:
        percent_value = self._parse_float(
            self._get_optional_value(
                row,
                "phys_complete_pct",
                "complete_pct",
                "pct_complete",
            )
        )

        if percent_value is None:
            return None
        if 0 <= percent_value <= 1:
            return percent_value*100
        
        return percent_value
    
    def _normalise_relationship_type(
            self,
            value: str,
    ) -> str:
        relationship_types = {
            "PR_FS": "FS",
            "PR_SS": "SS",
            "PR_FF": "FF",
            "PR_SF": "SF",
            "FS": "FS",
            "SS": "SS",
            "FF": "FF",
            "SF": "SF",
        }

        cleaned_value = value.strip().upper()

        return relationship_types.get(
            cleaned_value,
            cleaned_value,
        )
    
    def _get_value(
            self,
            row: dict[str, Any],
            *field_names: str,
    ) -> str:
        for field_name in field_names:
            value = row.get(field_name)

            if value is not None and str(value).strip():
                return str(value).strip()
        return ""
    
    def _get_optional_value(
            self,
            row: dict[str, Any],
            *field_names: str,
    ) -> str | None:
        value = self._get_value(
            row,
            *field_names,
        )

        return value if value else None
    
    def _parse_float(
        self,
        value: Any,
    ) -> float | None:
        if value is None:
            return None
        cleaned_value = str(value).strip()
        if not cleaned_value:
            return None
        try:
            return float(cleaned_value)
        except ValueError:
            return None
    def _parse_datetime(
        self,
        value: Any,
    ) -> datetime | None:
        if value is None:
            return None
        cleaned_value = str(value).strip()
        if not cleaned_value:
            return None
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%d-%b-%Y",
            "%d-%b-%Y %H:%M",
        ]
        for date_format in formats:
            try:
                return datetime.strptime(
                    cleaned_value,
                    date_format,
                )
            except ValueError:
                continue
        return None

