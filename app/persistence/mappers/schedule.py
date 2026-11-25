from dataclasses import fields
from datetime import datetime
from uuid import uuid4
from app.models import schedule as domain
from app.models.scheduling_options import P6SchedulingOptions
from app.persistence.models import schema as orm
from app.persistence.mappers.codec import calendar_values,calendar_from_record
from app.persistence.exceptions import PersistenceError

# Mapping keys are domain names; ORM keys explicitly separate DB FKs/source identities.
SPECS=(
    ('wbs_nodes',domain.WBS,orm.WBSRecord,{'wbs_id':'source_wbs_id','parent_wbs_id':'source_parent_wbs_id'}),
    ('calendars',domain.Calendar,orm.CalendarRecord,{'calendar_id':'source_calendar_id','base_calendar_id':'source_base_calendar_id'}),
    ('activities',domain.Activity,orm.ActivityRecord,{'activity_id':'source_task_id','project_id':'source_project_id','wbs_id':'source_wbs_id','calendar_id':'source_calendar_id'}),
    ('resources',domain.Resource,orm.ResourceRecord,{'resource_id':'source_resource_id','parent_resource_id':'source_parent_resource_id','calendar_id':'source_calendar_id'}),
    ('resource_assignments',domain.ResourceAssignment,orm.ResourceAssignmentRecord,{'assignment_id':'source_assignment_id','activity_id':'source_activity_id','resource_id':'source_resource_id'}),
    ('activity_code_types',domain.ActivityCodeType,orm.ActivityCodeTypeRecord,{'activity_code_type_id':'source_type_id','wbs_id':'source_wbs_id'}),
    ('activity_code_values',domain.ActivityCodeValue,orm.ActivityCodeValueRecord,{'activity_code_id':'source_value_id','activity_code_type_id':'source_type_id','parent_activity_code_id':'source_parent_value_id'}),
    ('activity_code_assignments',domain.ActivityCodeAssignment,orm.ActivityCodeAssignmentRecord,{'activity_id':'source_activity_id','activity_code_type_id':'source_type_id','activity_code_id':'source_value_id'}),
    ('udf_definitions',domain.UDFDefinition,orm.UDFDefinitionRecord,{'udf_type_id':'source_udf_type_id'}),
    ('udf_values',domain.UDFValue,orm.UDFValueRecord,{'udf_type_id':'source_udf_type_id'}),
)
IDENTITY={'wbs_nodes':'wbs_id','calendars':'calendar_id','activities':'activity_id','resources':'resource_id',
    'resource_assignments':'assignment_id','activity_code_types':'activity_code_type_id','activity_code_values':'activity_code_id','udf_definitions':'udf_type_id'}
CALENDAR_SPECIAL={'weekly_pattern','exceptions','diagnostics'}


def _values(value,cls,rename,loading=False):
    result={}
    for f in fields(cls):
        if cls is domain.Calendar and f.name in CALENDAR_SPECIAL:continue
        key=rename.get(f.name,f.name)
        item=getattr(value,key if loading else f.name)
        if not loading and isinstance(item,datetime) and item.tzinfo is not None:
            raise PersistenceError('Imported scheduling dates require project-local naive datetime values; timezone is not discarded.')
        result[f.name if loading else key]=item
    return result


def stable_wbs_path(schedule,key):
    names=[];seen=set()
    while key:
        if key in seen:names.append('[cycle:'+key+']');break
        seen.add(key);node=schedule.wbs_nodes.get(key)
        if node is None:names.append('[unresolved:'+key+']');break
        names.append(node.wbs_code or node.wbs_name);key=node.parent_wbs_id
    return ' > '.join(reversed(names))


def dump_schedule(schedule,version_id):
    rows={};identities={};collections={}
    for attr,cls,model,rename in SPECS:
        value=getattr(schedule,attr);items=list(value.values()) if isinstance(value,dict) else list(value)
        collections[attr]=items
        identities[attr]={getattr(item,IDENTITY[attr]):uuid4() for item in items} if attr in IDENTITY else {}
    for attr,cls,model,rename in SPECS:
        records=[]
        for order,item in enumerate(collections[attr]):
            data=_values(item,cls,rename)
            data.update(id=identities[attr][getattr(item,IDENTITY[attr])] if attr in IDENTITY else uuid4(),schedule_version_id=version_id,source_order=order)
            if attr=='wbs_nodes':data.update(parent_db_id=identities['wbs_nodes'].get(item.parent_wbs_id),stable_path=stable_wbs_path(schedule,item.wbs_id))
            elif attr=='calendars':data.update(**calendar_values(item),base_db_id=identities['calendars'].get(item.base_calendar_id))
            elif attr=='activities':data.update(wbs_db_id=identities['wbs_nodes'].get(item.wbs_id),calendar_db_id=identities['calendars'].get(item.calendar_id))
            elif attr=='resources':data.update(parent_db_id=identities['resources'].get(item.parent_resource_id),calendar_db_id=identities['calendars'].get(item.calendar_id))
            elif attr=='resource_assignments':data.update(activity_db_id=identities['activities'].get(item.activity_id),resource_db_id=identities['resources'].get(item.resource_id))
            elif attr=='activity_code_types':data['wbs_db_id']=identities['wbs_nodes'].get(item.wbs_id)
            elif attr=='activity_code_values':data.update(type_db_id=identities['activity_code_types'].get(item.activity_code_type_id),parent_db_id=identities['activity_code_values'].get(item.parent_activity_code_id))
            elif attr=='activity_code_assignments':data.update(activity_db_id=identities['activities'].get(item.activity_id),type_db_id=identities['activity_code_types'].get(item.activity_code_type_id),value_db_id=identities['activity_code_values'].get(item.activity_code_id))
            elif attr=='udf_values':data.update(definition_db_id=identities['udf_definitions'].get(item.udf_type_id),activity_db_id=identities['activities'].get(item.foreign_object_id) if item.subject_table.upper()=='TASK' else None)
            records.append(data)
        rows[model]=records
    rows[orm.RelationshipRecord]=[];rows[orm.UnresolvedRelationshipRecord]=[]
    for order,r in enumerate(schedule.relationships):
        p=identities['activities'].get(r.predecessor_activity_id);q=identities['activities'].get(r.successor_activity_id)
        model=orm.RelationshipRecord if p and q else orm.UnresolvedRelationshipRecord
        rows[model].append(dict(id=uuid4(),schedule_version_id=version_id,source_order=order,source_relationship_id=r.relationship_id,
            source_predecessor_id=r.predecessor_activity_id,source_successor_id=r.successor_activity_id,predecessor_db_id=p,successor_db_id=q,
            relationship_type=r.relationship_type,raw_relationship_type=r.raw_relationship_type,lag_hours=r.lag_hours))
    rows[orm.SchedulingOptionsRecord]=[]
    if schedule.scheduling_options:
        o=schedule.scheduling_options
        rows[orm.SchedulingOptionsRecord]=[dict(id=uuid4(),schedule_version_id=version_id,source_order=0,source_project_id=o.project_id,
            **{f.name:getattr(o,f.name) for f in fields(o) if f.name not in {'project_id','raw_fields'}},raw_fields=[list(pair) for pair in o.raw_fields])]
    return rows


def load_schedule(version,records):
    s=domain.Schedule(project=domain.Project(version.source_project_id,version.source_project_code,version.source_project_name,
        version.data_date,version.source_planned_start,version.source_planned_finished))
    for attr,cls,model,rename in SPECS:
        items=[]
        for row in records.get(model,()):
            data=_values(row,cls,rename,loading=True)
            items.append(calendar_from_record(row,data) if cls is domain.Calendar else cls(**data))
        setattr(s,attr,{getattr(item,IDENTITY[attr]):item for item in items} if attr in IDENTITY else items)
    relationships=sorted([*records.get(orm.RelationshipRecord,()),*records.get(orm.UnresolvedRelationshipRecord,())],key=lambda r:r.source_order)
    s.relationships=[domain.Relationship(r.source_relationship_id,r.source_predecessor_id,r.source_successor_id,r.relationship_type,r.lag_hours,r.raw_relationship_type) for r in relationships]
    opts=records.get(orm.SchedulingOptionsRecord,())
    if opts:
        row=opts[0]
        s.scheduling_options=P6SchedulingOptions(row.source_project_id,**{f.name:getattr(row,f.name) for f in fields(P6SchedulingOptions) if f.name not in {'project_id','raw_fields'}},raw_fields=tuple(tuple(pair) for pair in row.raw_fields))
    s.rebuild_activity_indexes();s.rebuild_optional_indexes()
    return s
