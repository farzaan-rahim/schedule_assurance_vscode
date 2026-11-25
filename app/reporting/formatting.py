from datetime import datetime, timezone
from enum import Enum
import json
from openpyxl.styles import Alignment, Font, PatternFill
from app.reporting.limits import ReportLimitError
from app.reporting.serialization import to_json_value

NAVY = "15384A"
TEAL = "167D8D"
PALE = "EDF4F7"
WHITE = "FFFFFF"
COLORS = {
    'ADDED':'D8EFDF','IMPROVED':'D8EFDF','RECOVERED':'D8EFDF',
    'REMOVED':'F7DBDC','DETERIORATED':'F7DBDC','BECAME_NEGATIVE':'F7DBDC',
    'CHANGED':'FFF0C2','DELAYED':'FFF0C2','WBS_MOVED':'FFF0C2',
    'TYPE_CHANGED':'FFF0C2','LAG_CHANGED':'FFF0C2','STATUS_CHANGED':'FFF0C2',
    'NOT_EVALUATED':'E5E7EB','BLOCKED':'E5E7EB','EXCLUDED':'E5E7EB','NOT_APPLICABLE':'E5E7EB',
}
NUMBER_FORMATS = {'date':'yyyy-mm-dd hh:mm','hours':'0.00','number':'0.00','percentage':'0.00%','integer':'0','text':'General','boolean':'General'}
BODY_FONT = Font(name='Calibri',size=11,color='15384A')
HEADER_FONT = Font(name='Calibri',size=11,bold=True,color=WHITE)
HEADER_FILL = PatternFill('solid',fgColor=TEAL)
BODY_ALIGNMENT = Alignment(vertical='top',wrap_text=True)
FILLS = {k:PatternFill('solid',fgColor=v) for k,v in COLORS.items()}


def excel_value(value):
    if isinstance(value, Enum):value=value.value
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, (dict,tuple,list)):
        value=json.dumps(to_json_value(value),ensure_ascii=False) if isinstance(value,dict) else '; '.join(str(to_json_value(v)) for v in value)
    if isinstance(value,str) and len(value)>32767:
        raise ReportLimitError('Excel cell exceeds 32,767 characters; use JSON detail instead. No text was truncated.')
    return value
