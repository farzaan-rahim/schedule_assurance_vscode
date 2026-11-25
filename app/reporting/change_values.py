"""Presentation variances only; no scheduling or analysis-engine calls."""
from datetime import datetime
from app.comparison.activity_diff import elapsed_hours, numeric_variance
from app.reporting.models import Availability, ChangeClassification as C, ChangeValue


def change_value(baseline, current, unit=None, *, comparable=True, direction=None):
    if not comparable or baseline is None or current is None:
        return ChangeValue(baseline, current, unit=unit, availability=Availability.NOT_APPLICABLE,
                           diagnostics=("Both unambiguously matched values are required for a variance.",))
    variance = None
    if isinstance(baseline, datetime) and isinstance(current, datetime):
        try:
            variance = elapsed_hours(baseline, current)
        except TypeError:
            return ChangeValue(baseline, current, unit=unit, availability=Availability.BLOCKED,
                               diagnostics=("Mixed aware/naive dates cannot be compared.",))
    elif isinstance(baseline, (int, float)) and not isinstance(baseline, bool) and isinstance(current, (int, float)) and not isinstance(current, bool):
        variance = numeric_variance(baseline, current)
    classification = C.UNCHANGED if baseline == current else C.CHANGED
    if variance is not None and variance != 0:
        if direction == "date":
            classification = C.DELAYED if variance > 0 else C.IMPROVED
        elif direction == "float":
            classification = (C.BECAME_NEGATIVE if baseline >= 0 > current else
                              C.RECOVERED if baseline < 0 <= current else
                              C.DETERIORATED if variance < 0 else C.IMPROVED)
        elif direction == "duration":
            classification = C.DETERIORATED if variance > 0 else C.IMPROVED
    percentage = variance / baseline if variance is not None and isinstance(baseline, (int, float)) and baseline > 0 else None
    notes = () if percentage is not None or not isinstance(baseline, (int, float)) or isinstance(baseline, bool) else ("Percentage requires a positive baseline denominator.",)
    return ChangeValue(baseline, current, variance, percentage, unit, classification,
                       Availability.AVAILABLE, diagnostics=notes)
