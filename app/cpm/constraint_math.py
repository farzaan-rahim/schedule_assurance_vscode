from __future__ import annotations

from app.calendars.working_time import add_working_hours


def constraint_support(constraint_type: str | None) -> str:
    forward = {"START_ON_OR_AFTER", "START_ON", "MANDATORY_START", "AS_LATE_AS_POSSIBLE"}
    backward = {"START_ON_OR_BEFORE", "FINISH_ON_OR_BEFORE", "FINISH_ON", "MANDATORY_FINISH"}
    both = {"FINISH_ON_OR_AFTER"}
    if constraint_type in forward:
        return "FORWARD"
    if constraint_type in backward:
        return "BACKWARD"
    if constraint_type in both:
        return "BOTH"
    return "VALIDATION_ONLY_OR_UNSUPPORTED"


def forward_constraint(timestamp, constraint_type: str | None, constraint_date):
    if constraint_type in {"START_ON_OR_AFTER", "START_ON", "MANDATORY_START"}:
        return max(timestamp, constraint_date) if constraint_date else timestamp
    return timestamp


def backward_constraint(current_late_finish, constraint_type: str | None, constraint_date):
    if constraint_type in {"START_ON_OR_BEFORE", "FINISH_ON_OR_BEFORE", "FINISH_ON", "MANDATORY_FINISH"}:
        if constraint_date:
            return min(current_late_finish, constraint_date)
    return current_late_finish
