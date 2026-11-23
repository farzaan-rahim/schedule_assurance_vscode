from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class SerializableActivityResult:
    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=str))


@dataclass(frozen=True)
class ActivityMatch(SerializableActivityResult):
    activity_id: str
    activity_code: str
    activity_name: str
    wbs_code: str | None
    wbs_name: str | None
    status: str | None
    planned_start: datetime | None
    planned_finish: datetime | None
    total_float_hours: float | None
    is_critical: bool | None
    match_type: str
    match_score: int
    selection_number: int | None = None


@dataclass(frozen=True)
class ActivitySearchResult(SerializableActivityResult):
    query: str
    total_matches: int
    returned_matches: int
    items: tuple[ActivityMatch, ...]
    message: str


@dataclass(frozen=True)
class ActivityResolutionResult(SerializableActivityResult):
    resolved: bool
    ambiguous: bool
    not_found: bool
    activity: ActivityMatch | None
    candidates: tuple[ActivityMatch, ...]
    query: str
    total_matches: int
    returned_matches: int
    message: str


@dataclass(frozen=True)
class PendingActivitySelection(SerializableActivityResult):
    selection_id: str
    query: str
    candidates: tuple[ActivityMatch, ...]
    requested_operation: str
    operation_arguments: dict[str, Any]
    schedule_version_id: int
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class PendingSelectionResult(SerializableActivityResult):
    success: bool
    expired: bool
    no_pending_selection: bool
    selected_activity: ActivityMatch | None
    requested_operation: str | None
    operation_result: dict[str, Any] | None
    message: str
