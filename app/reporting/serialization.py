from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
import json


def to_json_value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if is_dataclass(value):
        return {f.name: to_json_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(k): to_json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_json_value(v) for v in value]
    return value


def serialize_report(report, *, offset=0, limit=None):
    if offset < 0 or (limit is not None and limit < 1):
        raise ValueError("Pagination requires offset >= 0 and limit >= 1.")
    sections = []
    for section in report.sections:
        # Avoid copying entire datasets before slicing a preview page.
        data = {f.name: to_json_value(getattr(section, f.name)) for f in fields(section) if f.name != 'rows'}
        rows = section.rows[offset:None if limit is None else offset + limit]
        data['rows'] = to_json_value(rows)
        data['pagination'] = dict(offset=offset, limit=limit, returned=len(rows), total=section.count)
        data['truncated'] = section.truncated
        data['has_more'] = offset + len(rows) < len(section.rows)
        sections.append(data)
    return dict(schema_version=report.schema_version, metadata=to_json_value(report.metadata), sections=sections)


def report_json(report, **kwargs):
    return json.dumps(serialize_report(report, **kwargs), ensure_ascii=False, allow_nan=False)
