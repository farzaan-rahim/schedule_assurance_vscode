"""Read-only bounded navigation projections; no analytical calculations."""
from sqlalchemy import select,func,or_
from app.persistence.models.schema import ProjectRecord,ScheduleVersionRecord
from app.persistence.services.imports import dto,ProjectInfo,ScheduleVersionInfo

class NavigationRepository:
    def __init__(self,sessions):self.sessions=sessions
    def projects(self,offset=0,limit=50,search='',*,sort='',descending=False):
        with self.sessions() as s:
            predicate=or_(ProjectRecord.project_code.icontains(search,autoescape=True),ProjectRecord.project_name.icontains(search,autoescape=True))
            total=s.scalar(select(func.count()).select_from(ProjectRecord).where(predicate))
            columns={k:getattr(ProjectRecord,k) for k in ('project_code','project_name','active','created_at')}
            column=columns.get(sort,ProjectRecord.project_code)
            order=column.desc() if descending else column.asc()
            rows=s.scalars(select(ProjectRecord).where(predicate).order_by(order.nulls_last(),ProjectRecord.id).offset(offset).limit(limit))
            return tuple(dto(ProjectInfo,r) for r in rows),total
    def versions(self,project_id,offset=0,limit=50,*,sort='',descending=False):
        with self.sessions() as s:
            predicate=ScheduleVersionRecord.project_id==project_id
            total=s.scalar(select(func.count()).select_from(ScheduleVersionRecord).where(predicate))
            columns={k:getattr(ScheduleVersionRecord,k) for k in ('label','version_type','data_date','imported_at','source_filename','activity_count','relationship_count','wbs_count','calendar_count','resource_count','import_status')}
            column=columns.get(sort,ScheduleVersionRecord.imported_at)
            order=column.desc() if descending or not sort else column.asc()
            rows=s.scalars(select(ScheduleVersionRecord).where(predicate).order_by(order.nulls_last(),ScheduleVersionRecord.id).offset(offset).limit(limit))
            return tuple(dto(ScheduleVersionInfo,r) for r in rows),total
