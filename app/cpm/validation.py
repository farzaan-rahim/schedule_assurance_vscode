from __future__ import annotations

from datetime import datetime

from app.cpm.config import CPMConfig
from app.cpm.models import CPMDiagnostic, CPMFindingSeverity
from app.importers.p6_normalization import normalize_status


def validate_schedule(schedule, graph, config: CPMConfig) -> tuple[list[CPMDiagnostic], bool]:
    diagnostics: list[CPMDiagnostic] = []
    fatal = False

    cycles = graph.detect_cycles()
    if cycles:
        fatal = True
        diagnostics.append(CPMDiagnostic(
            "circular_logic", "Circular logic prevents CPM calculation.",
            CPMFindingSeverity.ERROR, metadata={"cycle_count": len(cycles)},
        ))

    if schedule.project is None or schedule.project.data_date is None:
        if config.project_start_override is None:
            fatal = True
            diagnostics.append(CPMDiagnostic(
                "missing_data_date", "Project Data Date is missing and no project-start override is configured.",
                CPMFindingSeverity.ERROR,
            ))

    if schedule.project is not None and schedule.project.data_date is not None:
        data_date = schedule.project.data_date
        if data_date.tzinfo is not None:
            fatal = True
            diagnostics.append(CPMDiagnostic(
                "timezone_mixing", "Project Data Date is timezone-aware; CP M requires naive project-local timestamps.",
                CPMFindingSeverity.ERROR,
            ))

    valid_ids = set(schedule.activities_by_id)
    for relationship in schedule.relationships:
        if relationship.predecessor_activity_id not in valid_ids:
            fatal = True
            diagnostics.append(CPMDiagnostic(
                "external_or_missing_predecessor", "Relationship predecessor is outside or missing from the selected schedule.",
                CPMFindingSeverity.ERROR,
                relationship_id=relationship.relationship_id,
                metadata={"predecessor_activity_id": relationship.predecessor_activity_id},
            ))
        if relationship.successor_activity_id not in valid_ids:
            fatal = True
            diagnostics.append(CPMDiagnostic(
                "external_or_missing_successor", "Relationship successor is outside or missing from the selected schedule.",
                CPMFindingSeverity.ERROR,
                relationship_id=relationship.relationship_id,
                metadata={"successor_activity_id": relationship.successor_activity_id},
            ))

    for activity in schedule.activities.values():
        if isinstance(activity.planned_start, datetime) and activity.planned_start.tzinfo is not None:
            fatal = True
            diagnostics.append(CPMDiagnostic(
                "timezone_mixing", "Activity contains a timezone-aware timestamp.",
                CPMFindingSeverity.ERROR,
                activity_id=activity.activity_id,
            ))

        if activity.calendar_id and activity.calendar_id not in schedule.calendars:
            if config.missing_calendar_policy == "ERROR":
                fatal = True
            diagnostics.append(CPMDiagnostic(
                "missing_activity_calendar", "Activity calendar is not present in the imported schedule.",
                CPMFindingSeverity.ERROR if config.missing_calendar_policy == "ERROR" else CPMFindingSeverity.WARNING,
                activity_id=activity.activity_id,
                metadata={"calendar_id": activity.calendar_id},
            ))

        status = normalize_status(activity.raw_status)
        if status not in {"not_started", "in_progress", "complete", None}:
            diagnostics.append(CPMDiagnostic(
                "unsupported_activity_status", "Activity status is not handled by the CPM state policy.",
                CPMFindingSeverity.WARNING,
                activity_id=activity.activity_id,
                metadata={"status": activity.status},
            ))

        if normalize_status(activity.status) is not None:
            pass

        duration = activity.remaining_duration_hours if status == "in_progress" else activity.remaining_duration_hours
        if status in {"not_started", "in_progress"}:
            effective = duration if duration is not None else activity.original_duration_hours
            if effective is not None and effective < 0:
                fatal = True
                diagnostics.append(CPMDiagnostic(
                    "negative_duration", "Negative effective duration prevents CPM calculation.",
                    CPMFindingSeverity.ERROR,
                    activity_id=activity.activity_id,
                    metadata={"effective_duration_hours": effective},
                ))

        if activity.activity_type in {"level_of_effort", "TT_LOEP"}:
            diagnostics.append(CPMDiagnostic(
                "loe_not_supported", "Level-of-effort activities are excluded from this CPM pass.",
                CPMFindingSeverity.WARNING,
                activity_id=activity.activity_id,
            ))

    start_activities = graph.get_start_activities()
    finish_activities = graph.get_finish_activities()
    if not start_activities:
        fatal = True
        diagnostics.append(CPMDiagnostic(
            "no_start_activities", "No network start activities were found.",
            CPMFindingSeverity.ERROR,
        ))

    if not finish_activities:
        fatal = True
        diagnostics.append(CPMDiagnostic(
            "no_finish_activities", "No network finish activities were found.",
            CPMFindingSeverity.ERROR,
        ))

    return diagnostics, fatal
