from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.graph.schedule_graph import ScheduleGraph
from app.importers.models import (
    ImportDiagnostic,
    ImportDiagnosticSeverity,
    ImportStatistics,
    ScheduleImportResult,
)
from app.importers.schedule_mapper import ScheduleMapper
from app.importers.xer_parser import XERParser


class ScheduleImportService:
    def __init__(self, parser: XERParser | None = None, mapper: ScheduleMapper | None = None) -> None:
        self.parser = parser or XERParser()
        self.mapper = mapper or ScheduleMapper()

    def import_file(self, file_path: str | Path) -> ScheduleImportResult:
        diagnostics: list[ImportDiagnostic] = []
        statistics = ImportStatistics()

        try:
            tables = self.parser.parse(file_path)
        except FileNotFoundError as exc:
            diagnostics.append(ImportDiagnostic(
                code="file_not_found",
                message=str(exc),
                severity=ImportDiagnosticSeverity.FATAL,
            ))
            return ScheduleImportResult(None, None, statistics, diagnostics)
        except Exception as exc:
            diagnostics.append(ImportDiagnostic(
                code="xer_parse_error",
                message=f"Unable to parse XER file: {exc}",
                severity=ImportDiagnosticSeverity.FATAL,
            ))
            return ScheduleImportResult(None, None, statistics, diagnostics)

        schedule = self.mapper.map(tables, diagnostics)
        graph = ScheduleGraph(schedule)

        code_counts = Counter(activity.activity_code for activity in schedule.activities.values())
        statistics.activities = len(schedule.activities)
        statistics.relationships = len(schedule.relationships)
        statistics.wbs_nodes = len(schedule.wbs_nodes)
        statistics.calendars = len(schedule.calendars)
        statistics.resources = len(schedule.resources)
        statistics.resource_assignments = len(schedule.resource_assignments)
        statistics.activity_code_types = len(schedule.activity_code_types)
        statistics.activity_code_values = len(schedule.activity_code_values)
        statistics.activity_code_assignments = len(schedule.activity_code_assignments)
        statistics.udf_definitions = len(schedule.udf_definitions)
        statistics.udf_values = len(schedule.udf_values)
        statistics.duplicate_activity_codes = sum(
            1 for count in code_counts.values() if count > 1
        )

        valid_ids = set(schedule.activities_by_id)
        invalid_references = 0
        for relationship in schedule.relationships:
            if relationship.predecessor_activity_id not in valid_ids:
                invalid_references += 1
                diagnostics.append(ImportDiagnostic(
                    code="invalid_relationship_reference",
                    message="Relationship predecessor is not present in TASK rows.",
                    severity=ImportDiagnosticSeverity.ERROR,
                    table="TASKPRED",
                    field_name="pred_task_id",
                    raw_value=relationship.predecessor_activity_id,
                ))
            if relationship.successor_activity_id not in valid_ids:
                invalid_references += 1
                diagnostics.append(ImportDiagnostic(
                    code="invalid_relationship_reference",
                    message="Relationship successor is not present in TASK rows.",
                    severity=ImportDiagnosticSeverity.ERROR,
                    table="TASKPRED",
                    field_name="task_id",
                    raw_value=relationship.successor_activity_id,
                ))
        for activity in schedule.activities.values():
            if activity.calendar_id and activity.calendar_id not in schedule.calendars:
                invalid_references += 1
                diagnostics.append(ImportDiagnostic(
                    code="missing_activity_calendar",
                    message="Activity references a calendar not present in CALENDAR rows.",
                    severity=ImportDiagnosticSeverity.WARNING,
                    table="TASK",
                    field_name="clndr_id",
                    raw_value=activity.calendar_id,
                ))
        statistics.invalid_references = invalid_references

        statistics.parsing_warnings = sum(
            1 for diagnostic in diagnostics
            if diagnostic.severity in {
                ImportDiagnosticSeverity.WARNING,
                ImportDiagnosticSeverity.ERROR,
            }
        )

        if statistics.activities == 0:
            diagnostics.append(ImportDiagnostic(
                code="no_activities",
                message="The XER file contains no mappable TASK activities.",
                severity=ImportDiagnosticSeverity.FATAL,
            ))

        return ScheduleImportResult(schedule, graph, statistics, diagnostics)
