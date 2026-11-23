from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.graph.schedule_graph import ScheduleGraph

from app.models.schedule import Schedule


class ImportDiagnosticSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True)
class ImportDiagnostic:
    code: str
    message: str
    severity: ImportDiagnosticSeverity
    table: str | None = None
    row_number: int | None = None
    field_name: str | None = None
    raw_value: Any | None = None


@dataclass
class ImportStatistics:
    activities: int = 0
    relationships: int = 0
    wbs_nodes: int = 0
    calendars: int = 0
    duplicate_activity_codes: int = 0
    invalid_references: int = 0
    parsing_warnings: int = 0
    resources: int = 0
    resource_assignments: int = 0
    activity_code_types: int = 0
    activity_code_values: int = 0
    activity_code_assignments: int = 0
    udf_definitions: int = 0
    udf_values: int = 0


@dataclass
class ScheduleImportResult:
    schedule: Schedule | None
    graph: ScheduleGraph | None
    statistics: ImportStatistics
    diagnostics: list[ImportDiagnostic] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.schedule is not None and not any(
            diagnostic.severity == ImportDiagnosticSeverity.FATAL
            for diagnostic in self.diagnostics
        )
