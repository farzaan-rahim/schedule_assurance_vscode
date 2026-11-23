from __future__ import annotations

from app.calendars.models import CalendarDiagnostic, CalendarDiagnosticSeverity
from dataclasses import replace


def resolve_calendar_inheritance(calendars: dict[str, object]) -> tuple[dict[str, object], list[CalendarDiagnostic]]:
    diagnostics: list[CalendarDiagnostic] = []

    for calendar_id, calendar in calendars.items():
        base_id = getattr(calendar, "base_calendar_id", None)
        if base_id and base_id not in calendars:
            diagnostics.append(CalendarDiagnostic(
                code="missing_base_calendar",
                message="Calendar references a missing base calendar.",
                severity=CalendarDiagnosticSeverity.WARNING,
                calendar_id=calendar_id,
                raw_value=base_id,
            ))

        visited: set[str] = set()
        current_id: str | None = calendar_id
        while current_id:
            if current_id in visited:
                diagnostics.append(CalendarDiagnostic(
                    code="circular_calendar_inheritance",
                    message="Circular calendar inheritance detected.",
                    severity=CalendarDiagnosticSeverity.ERROR,
                    calendar_id=calendar_id,
                    raw_value=current_id,
                ))
                break
            visited.add(current_id)
            current = calendars.get(current_id)
            if current is None:
                break
            current_id = getattr(current, "base_calendar_id", None)

    for calendar_id, calendar in list(calendars.items()):
        base_id = getattr(calendar, "base_calendar_id", None)
        if not base_id or base_id not in calendars:
            continue
        base = calendars[base_id]
        if getattr(calendar, "weekly_pattern", None) is None:
            exceptions = getattr(calendar, "exceptions", ())
            if not exceptions:
                exceptions = getattr(base, "exceptions", ())
            calendars[calendar_id] = replace(
                calendar,
                weekly_pattern=getattr(base, "weekly_pattern", None),
                exceptions=exceptions,
            )

    return calendars, diagnostics
