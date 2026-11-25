from uuid import uuid4
from sqlalchemy import insert,select
from app.importers.models import ImportDiagnostic,ImportDiagnosticSeverity
from app.persistence.models import schema as orm
from app.persistence.mappers.schedule import dump_schedule,load_schedule,SPECS
from app.persistence.mappers.codec import encode_raw,decode_raw
from app.persistence.exceptions import PersistenceError

MODELS=tuple(spec[2] for spec in SPECS)+(orm.RelationshipRecord,orm.UnresolvedRelationshipRecord,orm.SchedulingOptionsRecord)


class ScheduleDataRepository:
    def __init__(self,session):self.session=session

    def persist(self,version_id,schedule):
        rows=dump_schedule(schedule,version_id)
        for model in MODELS:
            data=rows[model]
            for start in range(0,len(data),1000):
                self.session.execute(insert(model).execution_options(render_nulls=True),data[start:start+1000])
        self.session.flush()

    def load(self,version):
        if version.import_status!='SUCCEEDED':raise PersistenceError('Only successful immutable versions can be analyzed.')
        records={model:list(self.session.scalars(select(model).where(model.schedule_version_id==version.id).order_by(model.source_order))) for model in MODELS}
        return load_schedule(version,records)

    def persist_diagnostics(self,version_id,diagnostics):
        rows=[]
        for order,d in enumerate(diagnostics):
            related=str(d.raw_value) if d.field_name in {'task_id','task_code','pred_task_id','wbs_id','clndr_id','rsrc_id'} and isinstance(d.raw_value,str) else None
            rows.append(dict(id=uuid4(),schedule_version_id=version_id,source_order=order,severity=d.severity.value,code=d.code,message=d.message,
                table_name=d.table,field_name=d.field_name,related_source_id=related,raw_value=encode_raw(d.raw_value),details={'row_number':d.row_number}))
        if rows:self.session.execute(insert(orm.DiagnosticRecord),rows)

    def load_diagnostics(self,version_id):
        rows=self.session.scalars(select(orm.DiagnosticRecord).where(orm.DiagnosticRecord.schedule_version_id==version_id).order_by(orm.DiagnosticRecord.source_order))
        return tuple(ImportDiagnostic(r.code,r.message,ImportDiagnosticSeverity(r.severity),r.table_name,r.details.get('row_number'),r.field_name,decode_raw(r.raw_value)) for r in rows)
