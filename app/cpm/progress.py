"""Narrow retained remaining-work requirements, with no source mutation."""
from dataclasses import dataclass
from datetime import datetime

from app.calendars.working_time import add_working_hours, working_hours_between
from app.cpm.relationship_math import forward_successor_requirement
from app.importers.p6_normalization import normalize_status


@dataclass(frozen=True)
class ProgressRequirement:
    timestamp: datetime | None
    expired_lag_hours: float
    remaining_lag_hours: float
    basis: str


def retained_requirement(relationship, predecessor, successor, predecessor_calendar,
                         successor_calendar, lag, *, source_predecessor, source_successor,
                         data_date, options):
    status = normalize_status(source_predecessor.raw_status or source_predecessor.status)
    if normalize_status(source_successor.raw_status or source_successor.status) == 'complete':
        return ProgressRequirement(None, 0.0, 0.0, 'HISTORICAL_ONLY')
    if relationship.relationship_type.upper() == 'SS' and status == 'in_progress':
        if lag < 0 or options.ss_lag_from_early_start is not True:
            raise ValueError('Progressed SS requires supported nonnegative Early Start lag policy.')
        elapsed = max(0.0, working_hours_between(predecessor_calendar, source_predecessor.actual_start, data_date))
        expired = min(lag, elapsed)
        remaining = lag - expired
        stamp = add_working_hours(predecessor_calendar, predecessor.calculated_early_start, remaining)
        return ProgressRequirement(stamp, expired, remaining, 'P6_SS_EARLY_START_EXPIRED_LAG')
    if relationship.relationship_type.upper() == 'SF' and status == 'in_progress':
        raise ValueError('Progressed SF endpoint semantics are not implemented.')
    stamp = forward_successor_requirement(relationship, predecessor, successor, predecessor_calendar, successor_calendar, lag)
    expired = 0.0
    if status == 'complete' and lag > 0:
        actual_endpoint = (source_predecessor.actual_start if relationship.relationship_type.upper() in {'SS', 'SF'}
                           else source_predecessor.actual_finish)
        expired = min(lag, max(0.0, working_hours_between(predecessor_calendar, actual_endpoint, data_date)))
    # Audit only: the absolute historical endpoint plus full lag above remains
    # the actual requirement; never replay the residual from a guessed date.
    return ProgressRequirement(stamp, expired, lag - expired, 'RETAINED_REMAINING_ENDPOINT')
