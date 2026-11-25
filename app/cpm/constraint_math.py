from __future__ import annotations

from app.calendars.working_time import (
    next_working_time, previous_working_time,
    start_for_finish_not_before, finish_for_start_not_after,
)

SUPPORTED_CONSTRAINTS = frozenset({
    "START_ON_OR_AFTER", "FINISH_ON_OR_AFTER",
    "START_ON_OR_BEFORE", "FINISH_ON_OR_BEFORE",
})


def forward_constraint_requirement(kind, stamp, calendar, duration):
    if kind == "START_ON_OR_AFTER":
        return next_working_time(calendar, stamp) if duration else stamp
    if kind == "FINISH_ON_OR_AFTER":
        return start_for_finish_not_before(calendar, stamp, duration)
    return None


def backward_constraint_requirement(kind, stamp, calendar, duration):
    if kind == "FINISH_ON_OR_BEFORE":
        return previous_working_time(calendar, stamp) if duration else stamp
    if kind == "START_ON_OR_BEFORE":
        return finish_for_start_not_after(calendar, stamp, duration)
    return None


def constraint_support(constraint_type: str | None) -> str:
    if constraint_type in {"START_ON_OR_AFTER", "FINISH_ON_OR_AFTER"}:
        return "FORWARD"
    if constraint_type in {"START_ON_OR_BEFORE", "FINISH_ON_OR_BEFORE"}:
        return "BACKWARD"
    return "VALIDATION_ONLY_OR_UNSUPPORTED"
