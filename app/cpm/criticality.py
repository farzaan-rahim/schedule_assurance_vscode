from __future__ import annotations


def classify_criticality(total_float_hours: float | None, critical_threshold: float, near_threshold: float) -> tuple[bool, bool]:
    if total_float_hours is None:
        return False, False
    critical = total_float_hours <= critical_threshold
    near = not critical and total_float_hours <= near_threshold
    return critical, near
