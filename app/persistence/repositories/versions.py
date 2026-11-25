from uuid import uuid4
from sqlalchemy import select
from app.persistence.models.schema import ScheduleVersionRecord,SourceFileRecord
from app.persistence.exceptions import RecordNotFound


class ScheduleVersionRepository:
    def __init__(self,session):self.session=session

    def get(self,version_id):
        row=self.session.get(ScheduleVersionRecord,version_id)
        if row is None:raise RecordNotFound('Schedule version was not found.')
        return row

    def duplicate(self,project_id,digest):
        return self.session.scalar(select(ScheduleVersionRecord).where(ScheduleVersionRecord.project_id==project_id,ScheduleVersionRecord.source_sha256==digest))

    def list(self,project_id,offset=0,limit=100):
        return list(self.session.scalars(select(ScheduleVersionRecord).where(ScheduleVersionRecord.project_id==project_id)
            .order_by(ScheduleVersionRecord.imported_at,ScheduleVersionRecord.id).offset(offset).limit(limit)))

    def create_importing(self,version_id,project_id,schedule,source,label,version_type):
        p=schedule.project
        row=ScheduleVersionRecord(id=version_id,project_id=project_id,label=label,version_type=version_type,
            source_filename=source.original_filename,source_sha256=source.sha256,source_project_id=p.project_id,
            source_project_code=p.project_code,source_project_name=p.project_name,data_date=p.data_date,
            source_planned_start=p.planned_start,source_planned_finished=p.planned_finished,import_status='IMPORTING',
            activity_count=len(schedule.activities),relationship_count=len(schedule.relationships),wbs_count=len(schedule.wbs_nodes),
            calendar_count=len(schedule.calendars),resource_count=len(schedule.resources),resource_assignment_count=len(schedule.resource_assignments))
        self.session.add(row);self.session.flush();return row

    def add_source(self,source):
        row=SourceFileRecord(id=source.id,schedule_version_id=source.version_id,original_filename=source.original_filename,
            storage_filename=source.storage_filename,media_type=source.media_type,byte_size=source.byte_size,sha256=source.sha256,relative_path=source.relative_path)
        self.session.add(row);self.session.flush()

    def seal(self,version):
        version.import_status='SUCCEEDED';self.session.flush()
