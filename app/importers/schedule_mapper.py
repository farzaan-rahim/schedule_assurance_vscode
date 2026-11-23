from __future__ import annotations

from datetime import datetime
from typing import Any

from app.importers.models import ImportDiagnostic, ImportDiagnosticSeverity
from app.importers.p6_normalization import (
    normalize_activity_type,
    normalize_constraint_type,
    normalize_relationship_type,
    normalize_status,
)
from app.models.schedule import (
    Activity,
    ActivityCodeAssignment,
    ActivityCodeType,
    ActivityCodeValue,
    Resource,
    ResourceAssignment,
    UDFDefinition,
    UDFValue,
)
from app.models.schedule import Calendar
from app.models.schedule import Project
from app.models.schedule import Relationship
from app.models.schedule import Schedule
from app.models.schedule import WBS
from app.calendars.parser import parse_calendar_data
from app.calendars.resolver import resolve_calendar_inheritance

class ScheduleMapper:
    def map(
            self,
            tables: dict[str, list[dict[str, Any]]],
            diagnostics: list[ImportDiagnostic] | None = None,
    ) -> Schedule:
        diagnostics = diagnostics if diagnostics is not None else []
        schedule = Schedule()

        project_rows = tables.get("PROJECT", [])
        task_rows = tables.get("TASK", [])
        if project_rows and task_rows:
            project_counts: dict[str, int] = {}
            for task_row in task_rows:
                project_id = self._get_value(task_row, "proj_id")
                if project_id:
                    project_counts[project_id] = project_counts.get(project_id, 0) + 1
            selected_project_id = max(project_counts, key=project_counts.get) if project_counts else ""
            selected_rows = [
                row for row in project_rows
                if self._get_value(row, "proj_id") == selected_project_id
            ]
            schedule.project = self._map_project(selected_rows or project_rows[:1])
        else:
            schedule.project = self._map_project(project_rows)

        project_id = schedule.project.project_id if schedule.project else None

        wbs_rows = tables.get("PROJWBS", [])
        if project_id:
            wbs_rows = [
                row for row in wbs_rows
                if self._get_value(row, "proj_id") in {"", project_id}
            ]
        schedule.wbs_nodes = self._map_wbs(wbs_rows)

        schedule.calendars = self._map_calendars(
            tables.get("CALENDAR", []), diagnostics
        )

        task_rows = tables.get("TASK", [])
        if project_id:
            task_rows = [
                row for row in task_rows
                if self._get_value(row, "proj_id") == project_id
            ]
        schedule.activities = self._map_activities(task_rows, diagnostics)

        schedule.rebuild_activity_indexes()

        relationship_rows = tables.get("TASKPRED", [])
        if project_id:
            relationship_rows = [
                row for row in relationship_rows
                if self._get_value(row, "proj_id") in {"", project_id}
            ]
        schedule.relationships = self._map_relationships(
            relationship_rows, diagnostics
        )

        schedule.resources = self._map_resources(tables.get("RSRC", []), diagnostics)
        schedule.resource_assignments = self._map_resource_assignments(
            tables.get("TASKRSRC", []), schedule, diagnostics
        )
        schedule.activity_code_types = self._map_activity_code_types(
            tables.get("ACTVTYPE", []), diagnostics
        )
        schedule.activity_code_values = self._map_activity_code_values(
            tables.get("ACTVCODE", []), diagnostics
        )
        schedule.activity_code_assignments = self._map_activity_code_assignments(
            tables.get("TASKACTV", []), schedule, diagnostics
        )
        schedule.udf_definitions = self._map_udf_definitions(
            tables.get("UDFTYPE", []), diagnostics
        )
        schedule.udf_values = self._map_udf_values(
            tables.get("UDFVALUE", []), schedule, diagnostics
        )
        schedule.rebuild_optional_indexes()

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
            diagnostics: list[ImportDiagnostic] | None = None,
    ) ->dict [str, Calendar]:
        diagnostics = diagnostics if diagnostics is not None else []
        calendars: dict[str, Calendar] = {}

        for row_number, row in enumerate(rows, start=1):
            calendar_id = self._get_value(row, "clndr_id", "calendar_id")
            if not calendar_id:
                diagnostics.append(ImportDiagnostic(
                    "missing_calendar_id", "CALENDAR row has no clndr_id.",
                    ImportDiagnosticSeverity.ERROR, "CALENDAR", row_number,
                ))
                continue

            raw_data = self._get_optional_value(row, "clndr_data")
            calendar = Calendar(
                calendar_id=calendar_id,
                calendar_name=self._get_value(row, "clndr_name", "calendar_name"),
                project_id=self._get_optional_value(row, "proj_id"),
                default_flag=self._get_optional_value(row, "default_flag") in {"Y", "y"},
                base_calendar_id=self._get_optional_value(row, "base_clndr_id"),
                last_change_date=self._parse_datetime(
                    self._get_optional_value(row, "last_chng_date"), diagnostics,
                    "CALENDAR", row_number, "last_chng_date",
                ),
                calendar_type=self._get_optional_value(row, "clndr_type"),
                hours_per_day=self._parse_float(
                    self._get_optional_value(row, "day_hr_cnt"), diagnostics,
                    "CALENDAR", row_number, "day_hr_cnt",
                ),
                hours_per_week=self._parse_float(
                    self._get_optional_value(row, "week_hr_cnt"), diagnostics,
                    "CALENDAR", row_number, "week_hr_cnt",
                ),
                hours_per_month=self._parse_float(
                    self._get_optional_value(row, "month_hr_cnt"), diagnostics,
                    "CALENDAR", row_number, "month_hr_cnt",
                ),
                hours_per_year=self._parse_float(
                    self._get_optional_value(row, "year_hr_cnt"), diagnostics,
                    "CALENDAR", row_number, "year_hr_cnt",
                ),
                resource_private=self._get_optional_value(row, "rsrc_private") in {"Y", "y"},
                raw_clndr_data=raw_data,
            )
            calendars[calendar_id] = parse_calendar_data(calendar)

        calendars, inheritance_diagnostics = resolve_calendar_inheritance(calendars)
        for diagnostic in inheritance_diagnostics:
            diagnostics.append(ImportDiagnostic(
                diagnostic.code,
                diagnostic.message,
                ImportDiagnosticSeverity.ERROR if diagnostic.severity.value == "error" else ImportDiagnosticSeverity.WARNING,
                "CALENDAR",
                None,
                "base_clndr_id",
                diagnostic.raw_value,
            ))

        return calendars
    def _map_activities(
            self,
            rows: list[dict[str, Any]],
            diagnostics: list[ImportDiagnostic] | None = None,
    ) -> dict[str, Activity]:
        diagnostics = diagnostics if diagnostics is not None else []
        activities: dict[str, Activity] = {}

        for row_number, row in enumerate(rows, start=1):
            activity_id = self._get_value(row, "task_id")
            activity_code = self._get_value(row, "task_code")

            if not activity_id:
                diagnostics.append(ImportDiagnostic(
                    code="missing_task_id", message="TASK row has no task_id.",
                    severity=ImportDiagnosticSeverity.ERROR, table="TASK", row_number=row_number,
                ))
                continue
            if not activity_code:
                diagnostics.append(ImportDiagnostic(
                    code="missing_task_code", message="TASK row has no task_code.",
                    severity=ImportDiagnosticSeverity.WARNING, table="TASK", row_number=row_number,
                    raw_value=activity_id,
                ))

            raw_status = self._get_optional_value(row, "status_code", "task_status")
            raw_activity_type = self._get_optional_value(row, "task_type")
            raw_primary_constraint = self._get_optional_value(row, "cstr_type")
            raw_secondary_constraint = self._get_optional_value(row, "cstr_type2")

            def parsed_date(field_name: str, *names: str) -> datetime | None:
                raw = self._get_optional_value(row, *names)
                return self._parse_datetime(raw, diagnostics, "TASK", row_number, field_name)

            activity = Activity(
                activity_id=activity_id,
                activity_code=activity_code,
                activity_name=self._get_value(row, "task_name"),
                project_id=self._get_value(row, "proj_id"),
                wbs_id=self._get_optional_value(row, "wbs_id"),
                activity_type=normalize_activity_type(raw_activity_type),
                status=normalize_status(raw_status),
                raw_activity_type=raw_activity_type,
                raw_status=raw_status,
                raw_primary_constraint_type=raw_primary_constraint,
                raw_secondary_constraint_type=raw_secondary_constraint,
                primary_constraint_type=normalize_constraint_type(raw_primary_constraint),
                secondary_constraint_type=normalize_constraint_type(raw_secondary_constraint),
                primary_constraint_date=parsed_date("primary_constraint_date", "cstr_date"),
                secondary_constraint_date=parsed_date("secondary_constraint_date", "cstr_date2"),
                calendar_id=self._get_optional_value(row, "clndr_id"),
                planned_start=parsed_date("planned_start", "target_start_date", "early_start_date", "start_date"),
                planned_finish=parsed_date("planned_finish", "target_end_date", "early_end_date", "end_date"),
                actual_start=parsed_date("actual_start", "act_start_date"),
                actual_finish=parsed_date("actual_finish", "act_end_date"),
                original_duration_hours=self._parse_float(
                    self._get_optional_value(row, "target_drtn_hr_cnt", "orgi_drtn_hr_cnt"),
                    diagnostics, "TASK", row_number, "original_duration_hours",
                ),
                remaining_duration_hours=self._parse_float(
                    self._get_optional_value(row, "remain_drtn_hr_cnt"),
                    diagnostics, "TASK", row_number, "remaining_duration_hours",
                ),
                total_float_hours=self._parse_float(
                    self._get_optional_value(row, "total_float_hr_cnt"),
                    diagnostics, "TASK", row_number, "total_float_hours",
                ),
                free_float_hours=self._parse_float(
                    self._get_optional_value(row, "free_float_hr_cnt"),
                    diagnostics, "TASK", row_number, "free_float_hours",
                ),
                percent_complete=self._map_percent_complete(row, diagnostics, row_number),
            )

            if activity_id in activities:
                diagnostics.append(ImportDiagnostic(
                    code="duplicate_task_id", message="Multiple TASK rows use the same task_id.",
                    severity=ImportDiagnosticSeverity.ERROR, table="TASK", row_number=row_number,
                    field_name="task_id", raw_value=activity_id,
                ))
            activities[activity_id] = activity

        return activities
    
    def _map_relationships(
            self,
            rows: list[dict[str, Any]],
            diagnostics: list[ImportDiagnostic] | None = None,
    ) -> list[Relationship]:
        diagnostics = diagnostics if diagnostics is not None else []
        relationships: list[Relationship] = []

        for row_number, row in enumerate(rows, start=1):
            predecessor_id = self._get_value(row, "pred_task_id")
            successor_id = self._get_value(row, "task_id")

            if not predecessor_id or not successor_id:
                diagnostics.append(ImportDiagnostic(
                    code="missing_relationship_endpoint",
                    message="TASKPRED row is missing a predecessor or successor task_id.",
                    severity=ImportDiagnosticSeverity.ERROR,
                    table="TASKPRED",
                    row_number=row_number,
                ))
                continue

            relationship_id = self._get_value(row, "task_pred_id", "pred_id")
            raw_type = self._get_value(row, "pred_type")
            raw_lag = self._get_optional_value(row, "lag_hr_cnt")

            relationships.append(Relationship(
                relationship_id=relationship_id,
                predecessor_activity_id=predecessor_id,
                successor_activity_id=successor_id,
                relationship_type=normalize_relationship_type(raw_type),
                raw_relationship_type=raw_type or None,
                lag_hours=self._parse_float(
                    raw_lag,
                    diagnostics,
                    "TASKPRED",
                    row_number,
                    "lag_hr_cnt",
                ) or 0.0,
            ))

        return relationships
    def _map_percent_complete(
            self,
            row: dict[str, Any],
            diagnostics: list[ImportDiagnostic] | None = None,
            row_number: int | None = None,
    ) -> float | None:
        diagnostics = diagnostics if diagnostics is not None else []
        raw_value = self._get_optional_value(row, "phys_complete_pct", "complete_pct", "pct_complete")
        percent_value = self._parse_float(
            raw_value,
            diagnostics,
            "TASK",
            row_number,
            "percent_complete",
        )

        if percent_value is None:
            return None
        if 0 <= percent_value <= 1:
            return percent_value * 100
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
        diagnostics: list[ImportDiagnostic] | None = None,
        table: str | None = None,
        row_number: int | None = None,
        field_name: str | None = None,
    ) -> float | None:
        if value is None:
            return None
        cleaned_value = str(value).strip()
        if not cleaned_value:
            return None
        try:
            return float(cleaned_value)
        except (TypeError, ValueError):
            if diagnostics is not None:
                diagnostics.append(ImportDiagnostic(
                    code="invalid_number",
                    message=f"Invalid populated number for {field_name or 'field'}.",
                    severity=ImportDiagnosticSeverity.WARNING,
                    table=table,
                    row_number=row_number,
                    field_name=field_name,
                    raw_value=value,
                ))
            return None
    def _parse_datetime(
        self,
        value: Any,
        diagnostics: list[ImportDiagnostic] | None = None,
        table: str | None = None,
        row_number: int | None = None,
        field_name: str | None = None,
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
                return datetime.strptime(cleaned_value, date_format)
            except ValueError:
                continue
        if diagnostics is not None:
            diagnostics.append(ImportDiagnostic(
                code="invalid_datetime",
                message=f"Invalid populated date for {field_name or 'field'}.",
                severity=ImportDiagnosticSeverity.WARNING,
                table=table,
                row_number=row_number,
                field_name=field_name,
                raw_value=value,
            ))
        return None

    def _map_resources(
        self,
        rows: list[dict[str, Any]],
        diagnostics: list[ImportDiagnostic],
    ) -> dict[str, Resource]:
        resources: dict[str, Resource] = {}
        for row_number, row in enumerate(rows, start=1):
            resource_id = self._get_value(row, "rsrc_id")
            if not resource_id:
                diagnostics.append(ImportDiagnostic("missing_resource_id", "RSRC row has no rsrc_id.", ImportDiagnosticSeverity.ERROR, "RSRC", row_number))
                continue
            resources[resource_id] = Resource(
                resource_id=resource_id,
                resource_code=self._get_optional_value(row, "rsrc_short_name"),
                resource_name=self._get_optional_value(row, "rsrc_name", "rsrc_title_name"),
                parent_resource_id=self._get_optional_value(row, "parent_rsrc_id") or None,
                resource_type=self._get_optional_value(row, "rsrc_type"),
                active_flag=self._get_optional_value(row, "active_flag"),
                employee_id=self._get_optional_value(row, "employee_code"),
                email=self._get_optional_value(row, "email_addr"),
                calendar_id=self._get_optional_value(row, "clndr_id"),
                role_id=self._get_optional_value(row, "role_id"),
                cost_qty_type=self._get_optional_value(row, "cost_qty_type"),
                unit_id=self._get_optional_value(row, "unit_id"),
                location_id=self._get_optional_value(row, "location_id"),
                raw=dict(row),
            )
        return resources

    def _map_resource_assignments(
        self,
        rows: list[dict[str, Any]],
        schedule: Schedule,
        diagnostics: list[ImportDiagnostic],
    ) -> dict[str, ResourceAssignment]:
        assignments: dict[str, ResourceAssignment] = {}
        for row_number, row in enumerate(rows, start=1):
            assignment_id = self._get_value(row, "taskrsrc_id")
            activity_id = self._get_value(row, "task_id")
            resource_id = self._get_value(row, "rsrc_id")

            if not assignment_id:
                diagnostics.append(ImportDiagnostic("missing_assignment_id", "TASKRSRC row has no taskrsrc_id.", ImportDiagnosticSeverity.ERROR, "TASKRSRC", row_number))
                continue
            if activity_id not in schedule.activities_by_id:
                diagnostics.append(ImportDiagnostic("assignment_missing_activity", "TASKRSRC references an activity outside the selected schedule.", ImportDiagnosticSeverity.WARNING, "TASKRSRC", row_number, "task_id", activity_id))
                continue
            if resource_id and resource_id not in schedule.resources:
                diagnostics.append(ImportDiagnostic("assignment_missing_resource", "TASKRSRC references a resource not present in RSRC.", ImportDiagnosticSeverity.WARNING, "TASKRSRC", row_number, "rsrc_id", resource_id))

            def parsed(field_name: str, *names: str) -> float | None:
                return self._parse_float(self._get_optional_value(row, *names), diagnostics, "TASKRSRC", row_number, field_name)

            def date(field_name: str, *names: str) -> datetime | None:
                return self._parse_datetime(self._get_optional_value(row, *names), diagnostics, "TASKRSRC", row_number, field_name)

            assignments[assignment_id] = ResourceAssignment(
                assignment_id=assignment_id,
                activity_id=activity_id,
                resource_id=resource_id,
                role_id=self._get_optional_value(row, "role_id"),
                account_id=self._get_optional_value(row, "acct_id"),
                remain_quantity=parsed("remain_quantity", "remain_qty"),
                target_quantity=parsed("target_quantity", "target_qty"),
                actual_regular_quantity=parsed("actual_regular_quantity", "act_reg_qty"),
                actual_overtime_quantity=parsed("actual_overtime_quantity", "act_ot_qty"),
                planned_cost=parsed("planned_cost", "target_cost"),
                actual_regular_cost=parsed("actual_regular_cost", "act_reg_cost"),
                actual_overtime_cost=parsed("actual_overtime_cost", "act_ot_cost"),
                remaining_cost=parsed("remaining_cost", "remain_cost"),
                planned_start=date("planned_start", "target_start_date"),
                planned_finish=date("planned_finish", "target_end_date"),
                actual_start=date("actual_start", "act_start_date"),
                actual_finish=date("actual_finish", "act_end_date"),
                remaining_start=date("remaining_start", "restart_date"),
                remaining_finish=date("remaining_finish", "reend_date"),
                cost_per_quantity=parsed("cost_per_quantity", "cost_per_qty"),
                cost_quantity_type=self._get_optional_value(row, "cost_qty_type"),
                rate_type=self._get_optional_value(row, "rate_type"),
                resource_type=self._get_optional_value(row, "rsrc_type"),
                raw=dict(row),
            )
        return assignments

    def _map_activity_code_types(
        self,
        rows: list[dict[str, Any]],
        diagnostics: list[ImportDiagnostic],
    ) -> dict[str, ActivityCodeType]:
        result: dict[str, ActivityCodeType] = {}
        for row_number, row in enumerate(rows, start=1):
            type_id = self._get_value(row, "actv_code_type_id")
            if not type_id:
                diagnostics.append(ImportDiagnostic("missing_activity_code_type_id", "ACTVTYPE row has no actv_code_type_id.", ImportDiagnosticSeverity.ERROR, "ACTVTYPE", row_number))
                continue
            sequence = self._parse_int(row.get("seq_num"), "ACTVTYPE", row_number, "seq_num", diagnostics)
            result[type_id] = ActivityCodeType(
                activity_code_type_id=type_id,
                name=self._get_value(row, "actv_code_type"),
                scope=self._get_optional_value(row, "actv_code_type_scope"),
                project_id=self._get_optional_value(row, "proj_id"),
                wbs_id=self._get_optional_value(row, "wbs_id"),
                sequence=sequence,
                raw=dict(row),
            )
        return result

    def _map_activity_code_values(
        self,
        rows: list[dict[str, Any]],
        diagnostics: list[ImportDiagnostic],
    ) -> dict[str, ActivityCodeValue]:
        result: dict[str, ActivityCodeValue] = {}
        for row_number, row in enumerate(rows, start=1):
            code_id = self._get_value(row, "actv_code_id")
            type_id = self._get_value(row, "actv_code_type_id")
            if not code_id:
                diagnostics.append(ImportDiagnostic("missing_activity_code_id", "ACTVCODE row has no actv_code_id.", ImportDiagnosticSeverity.ERROR, "ACTVCODE", row_number))
                continue
            sequence = self._parse_int(row.get("seq_num"), "ACTVCODE", row_number, "seq_num", diagnostics)
            result[code_id] = ActivityCodeValue(
                activity_code_id=code_id,
                activity_code_type_id=type_id,
                name=self._get_value(row, "actv_code_name"),
                short_name=self._get_optional_value(row, "short_name"),
                parent_activity_code_id=self._get_optional_value(row, "parent_actv_code_id"),
                sequence=sequence,
                color=self._get_optional_value(row, "color"),
                raw=dict(row),
            )
        return result

    def _map_activity_code_assignments(
        self,
        rows: list[dict[str, Any]],
        schedule: Schedule,
        diagnostics: list[ImportDiagnostic],
    ) -> list[ActivityCodeAssignment]:
        result: list[ActivityCodeAssignment] = []
        for row_number, row in enumerate(rows, start=1):
            activity_id = self._get_value(row, "task_id")
            type_id = self._get_value(row, "actv_code_type_id")
            code_id = self._get_value(row, "actv_code_id")
            if activity_id not in schedule.activities_by_id:
                diagnostics.append(ImportDiagnostic("activity_code_missing_activity", "TASKACTV references an activity outside the selected schedule.", ImportDiagnosticSeverity.WARNING, "TASKACTV", row_number, "task_id", activity_id))
                continue
            if type_id not in schedule.activity_code_types:
                diagnostics.append(ImportDiagnostic("activity_code_missing_type", "TASKACTV references a missing ACTVTYPE record.", ImportDiagnosticSeverity.WARNING, "TASKACTV", row_number, "actv_code_type_id", type_id))
            if code_id not in schedule.activity_code_values:
                diagnostics.append(ImportDiagnostic("activity_code_missing_value", "TASKACTV references a missing ACTVCODE record.", ImportDiagnosticSeverity.WARNING, "TASKACTV", row_number, "actv_code_id", code_id))
            result.append(ActivityCodeAssignment(activity_id, type_id, code_id, self._get_optional_value(row, "proj_id"), dict(row)))
        return result

    def _map_udf_definitions(
        self,
        rows: list[dict[str, Any]],
        diagnostics: list[ImportDiagnostic],
    ) -> dict[str, UDFDefinition]:
        result: dict[str, UDFDefinition] = {}
        for row_number, row in enumerate(rows, start=1):
            udf_id = self._get_value(row, "udf_type_id")
            if not udf_id:
                diagnostics.append(ImportDiagnostic("missing_udf_type_id", "UDFTYPE row has no udf_type_id.", ImportDiagnosticSeverity.ERROR, "UDFTYPE", row_number))
                continue
            result[udf_id] = UDFDefinition(
                udf_type_id=udf_id,
                table_name=self._get_value(row, "table_name"),
                name=self._get_value(row, "udf_type_name", "udf_type_label"),
                label=self._get_optional_value(row, "udf_type_label"),
                data_type=self._get_optional_value(row, "logical_data_type"),
                sequence=self._parse_int(row.get("seq_num"), "UDFTYPE", row_number, "seq_num", diagnostics),
                raw=dict(row),
            )
        return result

    def _map_udf_values(
        self,
        rows: list[dict[str, Any]],
        schedule: Schedule,
        diagnostics: list[ImportDiagnostic],
    ) -> list[UDFValue]:
        result: list[UDFValue] = []
        for row_number, row in enumerate(rows, start=1):
            udf_id = self._get_value(row, "udf_type_id")
            foreign_id = self._get_value(row, "fk_id")
            if udf_id not in schedule.udf_definitions:
                diagnostics.append(ImportDiagnostic("udf_missing_definition", "UDFVALUE references a missing UDFTYPE record.", ImportDiagnosticSeverity.WARNING, "UDFVALUE", row_number, "udf_type_id", udf_id))

            definition = schedule.udf_definitions.get(udf_id)
            subject = definition.table_name if definition else ""

            text_value = self._get_optional_value(row, "udf_text")
            code_value = self._get_optional_value(row, "udf_code_id")
            raw_number = self._get_optional_value(row, "udf_number")
            numeric_value = self._parse_float(raw_number, diagnostics, "UDFVALUE", row_number, "udf_number")
            date_value = self._parse_datetime(self._get_optional_value(row, "udf_date"), diagnostics, "UDFVALUE", row_number, "udf_date")

            result.append(UDFValue(
                udf_type_id=udf_id,
                foreign_object_id=foreign_id,
                subject_table=subject,
                raw_string_value=text_value or code_value or raw_number or (self._get_optional_value(row, "udf_date") or None),
                text_value=text_value,
                numeric_value=numeric_value,
                date_value=date_value,
                code_value=code_value,
                raw=dict(row),
            ))

            if subject == "TASK" and foreign_id not in schedule.activities_by_id:
                diagnostics.append(ImportDiagnostic("udf_missing_activity", "Activity UDF references an activity outside the selected schedule.", ImportDiagnosticSeverity.WARNING, "UDFVALUE", row_number, "fk_id", foreign_id))
        return result

    def _parse_int(
        self,
        value: Any,
        table: str,
        row_number: int,
        field_name: str,
        diagnostics: list[ImportDiagnostic],
    ) -> int | None:
        if value is None or not str(value).strip():
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            diagnostics.append(ImportDiagnostic("invalid_integer", f"Invalid populated integer for {field_name}.", ImportDiagnosticSeverity.WARNING, table, row_number, field_name, value))
            return None

