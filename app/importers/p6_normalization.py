from __future__ import annotations


def normalize_status(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    upper = cleaned.upper()
    mapping = {
        "TK_COMPLETE": "complete",
        "COMPLETE": "complete",
        "COMPLETED": "complete",
        "TK_ACTIVE": "in_progress",
        "ACTIVE": "in_progress",
        "IN PROGRESS": "in_progress",
        "INPROGRESS": "in_progress",
        "TK_NOTSTART": "not_started",
        "NOT STARTED": "not_started",
        "NOTSTART": "not_started",
    }
    return mapping.get(upper, cleaned.casefold())


def normalize_activity_type(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    upper = cleaned.upper()
    mapping = {
        "TT_STARTMILE": "start_milestone",
        "START MILESTONE": "start_milestone",
        "STARTMILESTONE": "start_milestone",
        "TT_FINMILE": "finish_milestone",
        "FINISH MILESTONE": "finish_milestone",
        "TT_MILE": "milestone",
        "MILESTONE": "milestone",
        "TT_TASK": "task",
        "TASK": "task",
        "TT_LOEP": "level_of_effort",
        "TT_LOE": "level_of_effort",
        "TT_WBS": "wbs_summary",
        "WBS_SUMMARY": "wbs_summary",
        "LEVEL OF EFFORT": "level_of_effort",
    }
    return mapping.get(upper, cleaned.casefold())


def normalize_milestone_type(raw_value: str | None) -> str | None:
    return normalize_activity_type(raw_value)


def normalize_relationship_type(raw_value: str | None) -> str:
    if raw_value is None:
        return ""
    upper = raw_value.strip().upper()
    mapping = {
        "PR_FS": "FS",
        "PR_SS": "SS",
        "PR_FF": "FF",
        "PR_SF": "SF",
        "FS": "FS",
        "SS": "SS",
        "FF": "FF",
        "SF": "SF",
    }
    return mapping.get(upper, upper)


def normalize_constraint_type(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    upper = raw_value.strip().upper()
    mapping = {
        "CS_MSO": "MANDATORY_START",
        "CS_MFO": "MANDATORY_FINISH",
        "CS_SNET": "START_ON_OR_AFTER",
        "CS_SNLT": "START_ON_OR_BEFORE",
        "CS_FNET": "FINISH_ON_OR_AFTER",
        "CS_FNLT": "FINISH_ON_OR_BEFORE",
        "CS_ALAP": "AS_LATE_AS_POSSIBLE",
        "CS_MSOA": "START_ON_OR_AFTER",
        "CS_MEOB": "FINISH_ON_OR_BEFORE",
        "CS_MEOA": "FINISH_ON_OR_AFTER",
        "CS_MSOB": "START_ON_OR_BEFORE",
        "CS_MFOB": "MUST_FINISH_ON",
    }
    return mapping.get(upper, upper)
