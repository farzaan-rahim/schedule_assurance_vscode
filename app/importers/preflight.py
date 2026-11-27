"""Read-only XER identity/count scan. No schedule mapping, graph, database or file storage."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO,TextIOWrapper
from app.importers.xer_parser import XERParser
from app.importers.schedule_mapper import ScheduleMapper


@dataclass(frozen=True)
class XERProjectPreview:
    source_project_id: str
    project_code: str
    project_name: str
    data_date: datetime | None
    activity_count: int
    relationship_count: int
    wbs_count: int

    @property
    def importable(self):
        return bool(self.source_project_id and self.project_code and self.activity_count)

    def matches(self,project):
        return project is not None and project.project_code==self.project_code


@dataclass(frozen=True)
class XERPreflight:
    projects: tuple[XERProjectPreview,...]

    @property
    def default_project_id(self):
        return self.projects[0].source_project_id if len(self.projects)==1 else None

    def select(self,source_project_id):
        matches=[p for p in self.projects if p.source_project_id==source_project_id]
        if len(matches)!=1:
            raise ValueError('Choose one unambiguous source P6 project before importing.')
        return matches[0]


class _MetadataParser(XERParser):
    CORE_TABLES={'PROJECT','TASK','TASKPRED','PROJWBS'}


def _metadata_rows(content):
    with TextIOWrapper(BytesIO(content),encoding='utf-8',errors='replace') as stream:
        yield from _MetadataParser().iter_rows(stream)


def preflight_xer(content: bytes) -> XERPreflight:
    projects=[];tasks=Counter();relationships=Counter();wbs=Counter();owners={};unscoped_relationships=[];roots={}
    for table,row in _metadata_rows(content):
        project_id=row.get('proj_id','').strip()
        if table=='PROJECT':projects.append(row)
        elif table=='TASK':
            tasks[project_id]+=1
            owners[row.get('task_id','')]=project_id
        elif table=='TASKPRED':
            if project_id:relationships[project_id]+=1
            else:unscoped_relationships.append(row.get('task_id',''))
        elif table=='PROJWBS':
            wbs[project_id]+=1
            if row.get('proj_node_flag')=='Y':
                roots[project_id]=row.get('wbs_name','').strip()
            elif not row.get('parent_wbs_id','').strip():
                roots.setdefault(project_id,row.get('wbs_name','').strip())
    if not projects:raise ValueError('XER preflight found no PROJECT rows. Select a valid P6 XER file.')
    for task_id in unscoped_relationships:relationships[owners.get(task_id,'')]+=1
    previews=[];mapper=ScheduleMapper()
    for row in projects:
        p=mapper._map_project([row])
        name=row.get('proj_name','').strip() or roots.get(p.project_id) or p.project_name
        previews.append(XERProjectPreview(p.project_id,p.project_code,name,p.data_date,tasks[p.project_id],
            relationships[p.project_id],wbs[p.project_id]+(wbs[''] if len(projects)==1 and p.project_id else 0)))
    ids=[p.source_project_id for p in previews]
    if any(not key for key in ids) or len(ids)!=len(set(ids)):
        raise ValueError('XER PROJECT identities are missing or duplicated; source selection is ambiguous.')
    return XERPreflight(tuple(previews))
