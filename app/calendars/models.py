from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class WorkPeriod:
    start: time
    finish: time


@dataclass(frozen=True)
class WorkDay:
    weekday: int
    working: bool
    periods: tuple[WorkPeriod, ...] = ()


@dataclass(frozen=True)
class CalendarException:
    exception_date: date
    working: bool
    periods: tuple[WorkPeriod, ...] = ()


class CalendarDiagnosticSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CalendarDiagnostic:
    code: str
    message: str
    severity: CalendarDiagnosticSeverity
    calendar_id: str | None = None
    raw_value: Any | None = None


@dataclass(frozen=True)
class WeeklyWorkPattern:
    days: tuple[WorkDay, ...]


@dataclass
class P6Calendar:
    calendar_id: str
    calendar_name: str
    project_id: str | None = None
    default_flag: bool = False
    base_calendar_id: str | None = None
    last_change_date: datetime | None = None
    calendar_type: str | None = None
    hours_per_day: float | None = None
    hours_per_week: float | None = None
    hours_per_month: float | None = None
    hours_per_year: float | None = None
    resource_private: bool | None = None
    raw_clndr_data: str | None = None
    weekly_pattern: WeeklyWorkPattern | None = None
    exceptions: tuple[CalendarException, ...] = ()
    diagnostics: tuple[CalendarDiagnostic, ...] = ()
