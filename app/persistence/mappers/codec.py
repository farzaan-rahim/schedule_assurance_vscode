"""Closed, lossless codecs; no pickle or dynamic class loading."""
from datetime import date,datetime,time
from enum import Enum
from math import isfinite
from app.calendars.models import (P6Calendar,WeeklyWorkPattern,WorkDay,WorkPeriod,CalendarException,CalendarDiagnostic,CalendarDiagnosticSeverity)
from app.models.schedule import Calendar
from app.persistence.exceptions import PersistenceError


def encode_raw(value):
    if value is None:return {'t':'none'}
    if isinstance(value,Enum):raise PersistenceError('Unsupported raw diagnostic enum; store its explicit source value.')
    if isinstance(value,datetime):return {'t':'datetime','v':value.isoformat()}
    if isinstance(value,date):return {'t':'date','v':value.isoformat()}
    if isinstance(value,time):return {'t':'time','v':value.isoformat()}
    if isinstance(value,bool):return {'t':'bool','v':value}
    if isinstance(value,int):return {'t':'int','v':value}
    if isinstance(value,float):return {'t':'float','v':repr(value)}
    if isinstance(value,str):return {'t':'str','v':value}
    if isinstance(value,dict):return {'t':'dict','v':[[encode_raw(k),encode_raw(v)] for k,v in value.items()]}
    if isinstance(value,(tuple,list)):return {'t':'tuple' if isinstance(value,tuple) else 'list','v':[encode_raw(v) for v in value]}
    raise PersistenceError('Unsupported raw diagnostic value; lossless encoding is required.')


def decode_raw(value):
    if value is None:return None
    kind=value['t'];v=value.get('v')
    if kind=='none':return None
    if kind=='datetime':return datetime.fromisoformat(v)
    if kind=='date':return date.fromisoformat(v)
    if kind=='time':return time.fromisoformat(v)
    if kind=='float':return float(v)
    if kind in {'str','bool','int'}:return v
    if kind=='dict':return {decode_raw(k):decode_raw(item) for k,item in v}
    if kind=='tuple':return tuple(decode_raw(x) for x in v)
    if kind=='list':return [decode_raw(x) for x in v]
    raise PersistenceError('Unknown stored diagnostic encoding.')


def periods(values):return [{'start':p.start.isoformat(),'finish':p.finish.isoformat()} for p in values]
def read_periods(values):return tuple(WorkPeriod(time.fromisoformat(p['start']),time.fromisoformat(p['finish'])) for p in values)


def calendar_values(calendar):
    if type(calendar) not in {Calendar,P6Calendar}:raise PersistenceError('Unsupported canonical calendar class.')
    return dict(domain_calendar_kind='P6Calendar' if type(calendar) is P6Calendar else 'Calendar',
        working_pattern=None if calendar.weekly_pattern is None else [{'weekday':d.weekday,'working':d.working,'periods':periods(d.periods)} for d in calendar.weekly_pattern.days],
        exceptions=[{'date':e.exception_date.isoformat(),'working':e.working,'periods':periods(e.periods)} for e in calendar.exceptions],
        diagnostics=[{'code':d.code,'message':d.message,'severity':d.severity.value,'calendar_id':d.calendar_id,'raw_value':encode_raw(d.raw_value)} for d in calendar.diagnostics])


def calendar_from_record(record,values):
    kind={'Calendar':Calendar,'P6Calendar':P6Calendar}.get(record.domain_calendar_kind)
    if kind is None:raise PersistenceError('Unknown stored calendar representation.')
    values.update(weekly_pattern=None if record.working_pattern is None else WeeklyWorkPattern(tuple(WorkDay(d['weekday'],d['working'],read_periods(d['periods'])) for d in record.working_pattern)),
        exceptions=tuple(CalendarException(date.fromisoformat(d['date']),d['working'],read_periods(d['periods'])) for d in record.exceptions),
        diagnostics=tuple(CalendarDiagnostic(d['code'],d['message'],CalendarDiagnosticSeverity(d['severity']),d['calendar_id'],decode_raw(d['raw_value'])) for d in record.diagnostics))
    return kind(**values)
