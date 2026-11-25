from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.persistence.models.schema import ProjectRecord
from app.persistence.exceptions import RecordNotFound


class ProjectRepository:
    def __init__(self,session):self.session=session

    def get(self,project_id):
        row=self.session.get(ProjectRecord,project_id)
        if row is None:raise RecordNotFound('Project was not found.')
        return row

    def by_code(self,code):
        return self.session.scalar(select(ProjectRecord).where(ProjectRecord.project_code==code))

    def create(self,code,name,description=None,active=True):
        row=ProjectRecord(id=uuid4(),project_code=code,project_name=name,description=description,active=active)
        self.session.add(row);self.session.flush();return row

    def resolve_source(self,project):
        statement=insert(ProjectRecord).values(id=uuid4(),project_code=project.project_code,project_name=project.project_name,active=True)
        self.session.execute(statement.on_conflict_do_nothing(index_elements=[ProjectRecord.project_code]))
        return self.by_code(project.project_code)

    def list(self,offset=0,limit=100):
        return list(self.session.scalars(select(ProjectRecord).order_by(ProjectRecord.created_at,ProjectRecord.id).offset(offset).limit(limit)))
