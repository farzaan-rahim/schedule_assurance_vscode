from __future__ import annotations

from app.dcma.models import DCMAStatus


def percentage_status(
    percentage: float,
    warning_pct: float,
    fail_pct: float,
) -> DCMAStatus:
    if fail_pct <= 0:
        if percentage > 0:
            return DCMAStatus.FAIL
    elif percentage >= fail_pct:
        return DCMAStatus.FAIL

    if warning_pct <= 0:
        if percentage > 0:
            return DCMAStatus.WARNING
    elif percentage >= warning_pct:
        return DCMAStatus.WARNING
    return DCMAStatus.PASS


def finding_percentage(finding_count: int, eligible_count: int) -> float:
    if eligible_count <= 0:
        return 0.0
    return round(100.0 * finding_count / eligible_count, 2)
