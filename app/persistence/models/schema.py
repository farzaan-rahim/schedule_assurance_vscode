from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, CheckConstraint, DateTime, Double, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.persistence.base import Base, UUIDPrimaryKey, utcnow


class ProjectRecord(UUIDPrimaryKey,Base):
    __tablename__='projects'
    project_code: Mapped[str]=mapped_column(Text,nullable=False,unique=True)
    project_name: Mapped[str]=mapped_column(Text,nullable=False)
    description: Mapped[str | None]=mapped_column(Text)
    active: Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default='true')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=utcnow,server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow,server_default=func.now())


class ScheduleVersionRecord(UUIDPrimaryKey,Base):
    __tablename__='schedule_versions'
    project_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('projects.id'),nullable=False,index=True)
    label: Mapped[str]=mapped_column(Text,nullable=False)
    version_type: Mapped[str]=mapped_column(String(16),nullable=False)
    source_filename: Mapped[str]=mapped_column(Text,nullable=False)
    source_sha256: Mapped[str]=mapped_column(String(64),nullable=False)
    source_project_id: Mapped[str]=mapped_column(Text,nullable=False)
    source_project_code: Mapped[str]=mapped_column(Text,nullable=False)
    source_project_name: Mapped[str]=mapped_column(Text,nullable=False)
    data_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    source_planned_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    source_planned_finished: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    imported_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=utcnow,server_default=func.now())
    import_status: Mapped[str]=mapped_column(String(16),nullable=False,default='IMPORTING')
    activity_count: Mapped[int]=mapped_column(Integer,nullable=False)
    relationship_count: Mapped[int]=mapped_column(Integer,nullable=False)
    wbs_count: Mapped[int]=mapped_column(Integer,nullable=False)
    calendar_count: Mapped[int]=mapped_column(Integer,nullable=False)
    resource_count: Mapped[int]=mapped_column(Integer,nullable=False)
    resource_assignment_count: Mapped[int]=mapped_column(Integer,nullable=False)
    __table_args__=(UniqueConstraint('project_id','source_sha256',name='uq_versions_project_sha256'),
        CheckConstraint("version_type IN ('BASELINE','UPDATE','CURRENT','SNAPSHOT')",name='version_type'),
        CheckConstraint("import_status IN ('IMPORTING','SUCCEEDED','FAILED')",name='import_status'),
        CheckConstraint("source_sha256 ~ '^[0-9a-f]{64}$'",name='source_sha256'))


class SourceFileRecord(UUIDPrimaryKey,Base):
    __tablename__='source_files'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,unique=True)
    original_filename: Mapped[str]=mapped_column(Text,nullable=False)
    storage_filename: Mapped[str]=mapped_column(Text,nullable=False,unique=True)
    media_type: Mapped[str]=mapped_column(Text,nullable=False)
    byte_size: Mapped[int]=mapped_column(Integer,nullable=False)
    sha256: Mapped[str]=mapped_column(String(64),nullable=False)
    relative_path: Mapped[str]=mapped_column(Text,nullable=False,unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=utcnow,server_default=func.now())
    __table_args__=(CheckConstraint('byte_size > 0',name='positive_size'),
        CheckConstraint("relative_path !~ '(^/|[\\\\:]|(^|/)\\.\\.(/|$))'",name='relative_path'))


class WBSRecord(UUIDPrimaryKey,Base):
    __tablename__='wbs'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_wbs_id: Mapped[str]=mapped_column(Text,nullable=False)
    source_parent_wbs_id: Mapped[str | None]=mapped_column(Text)
    wbs_code: Mapped[str | None]=mapped_column(Text)
    wbs_name: Mapped[str | None]=mapped_column(Text)
    stable_path: Mapped[str | None]=mapped_column(Text)
    parent_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_wbs_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_wbs_order'),
        UniqueConstraint('schedule_version_id','source_wbs_id',name='uq_wbs_source_id'),
        ForeignKeyConstraint(['schedule_version_id','parent_db_id'],['wbs.schedule_version_id','wbs.id'],name='fk_wbs_parent_db_id',deferrable=True,initially='DEFERRED'),
    )


class CalendarRecord(UUIDPrimaryKey,Base):
    __tablename__='calendars'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_calendar_id: Mapped[str]=mapped_column(Text,nullable=False)
    calendar_name: Mapped[str | None]=mapped_column(Text)
    project_id: Mapped[str | None]=mapped_column(Text)
    default_flag: Mapped[bool | None]=mapped_column(Boolean)
    last_change_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    calendar_type: Mapped[str | None]=mapped_column(Text)
    hours_per_day: Mapped[float | None]=mapped_column(Double)
    hours_per_week: Mapped[float | None]=mapped_column(Double)
    hours_per_month: Mapped[float | None]=mapped_column(Double)
    hours_per_year: Mapped[float | None]=mapped_column(Double)
    resource_private: Mapped[bool | None]=mapped_column(Boolean)
    raw_clndr_data: Mapped[str | None]=mapped_column(Text)
    source_base_calendar_id: Mapped[str | None]=mapped_column(Text)
    base_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    working_pattern: Mapped[dict | list | None]=mapped_column(JSONB)
    exceptions: Mapped[dict | list | None]=mapped_column(JSONB)
    diagnostics: Mapped[dict | list | None]=mapped_column(JSONB)
    domain_calendar_kind: Mapped[str]=mapped_column(Text,nullable=False)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_calendars_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_calendars_order'),
        UniqueConstraint('schedule_version_id','source_calendar_id',name='uq_calendars_source_id'),
        ForeignKeyConstraint(['schedule_version_id','base_db_id'],['calendars.schedule_version_id','calendars.id'],name='fk_calendars_base_db_id',deferrable=True,initially='DEFERRED'),
    )


class ActivityRecord(UUIDPrimaryKey,Base):
    __tablename__='activities'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_task_id: Mapped[str]=mapped_column(Text,nullable=False)
    activity_code: Mapped[str | None]=mapped_column(Text)
    activity_name: Mapped[str | None]=mapped_column(Text)
    activity_type: Mapped[str | None]=mapped_column(Text)
    status: Mapped[str | None]=mapped_column(Text)
    raw_activity_type: Mapped[str | None]=mapped_column(Text)
    raw_status: Mapped[str | None]=mapped_column(Text)
    primary_constraint_type: Mapped[str | None]=mapped_column(Text)
    primary_constraint_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    secondary_constraint_type: Mapped[str | None]=mapped_column(Text)
    secondary_constraint_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    raw_primary_constraint_type: Mapped[str | None]=mapped_column(Text)
    raw_secondary_constraint_type: Mapped[str | None]=mapped_column(Text)
    planned_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    planned_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    actual_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    actual_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    original_duration_hours: Mapped[float | None]=mapped_column(Double)
    remaining_duration_hours: Mapped[float | None]=mapped_column(Double)
    total_float_hours: Mapped[float | None]=mapped_column(Double)
    free_float_hours: Mapped[float | None]=mapped_column(Double)
    percent_complete: Mapped[float | None]=mapped_column(Double)
    early_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    early_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    late_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    late_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    expected_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    remaining_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    remaining_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    duration_type: Mapped[str | None]=mapped_column(Text)
    suspend_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    resume_date: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    source_project_id: Mapped[str | None]=mapped_column(Text)
    source_wbs_id: Mapped[str | None]=mapped_column(Text)
    source_calendar_id: Mapped[str | None]=mapped_column(Text)
    wbs_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    calendar_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_activities_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_activities_order'),
        UniqueConstraint('schedule_version_id','source_task_id',name='uq_activities_source_id'),
        ForeignKeyConstraint(['schedule_version_id','wbs_db_id'],['wbs.schedule_version_id','wbs.id'],name='fk_activities_wbs_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','calendar_db_id'],['calendars.schedule_version_id','calendars.id'],name='fk_activities_calendar_db_id',deferrable=True,initially='DEFERRED'),
        Index('ix_activities_version_code','schedule_version_id','activity_code'),
    )


class RelationshipRecord(UUIDPrimaryKey,Base):
    __tablename__='relationships'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_relationship_id: Mapped[str | None]=mapped_column(Text)
    source_predecessor_id: Mapped[str | None]=mapped_column(Text)
    source_successor_id: Mapped[str | None]=mapped_column(Text)
    relationship_type: Mapped[str | None]=mapped_column(Text)
    raw_relationship_type: Mapped[str | None]=mapped_column(Text)
    lag_hours: Mapped[float]=mapped_column(Double,nullable=False)
    predecessor_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    successor_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_relationships_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_relationships_order'),
        ForeignKeyConstraint(['schedule_version_id','predecessor_db_id'],['activities.schedule_version_id','activities.id'],name='fk_relationships_predecessor_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','successor_db_id'],['activities.schedule_version_id','activities.id'],name='fk_relationships_successor_db_id',deferrable=True,initially='DEFERRED'),
        CheckConstraint('predecessor_db_id IS NOT NULL AND successor_db_id IS NOT NULL',name='resolved_endpoints'),
    )


class UnresolvedRelationshipRecord(UUIDPrimaryKey,Base):
    __tablename__='unresolved_relationships'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_relationship_id: Mapped[str | None]=mapped_column(Text)
    source_predecessor_id: Mapped[str | None]=mapped_column(Text)
    source_successor_id: Mapped[str | None]=mapped_column(Text)
    relationship_type: Mapped[str | None]=mapped_column(Text)
    raw_relationship_type: Mapped[str | None]=mapped_column(Text)
    lag_hours: Mapped[float]=mapped_column(Double,nullable=False)
    predecessor_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    successor_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_unresolved_relationships_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_unresolved_relationships_order'),
        ForeignKeyConstraint(['schedule_version_id','predecessor_db_id'],['activities.schedule_version_id','activities.id'],name='fk_unresolved_relationships_predecessor_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','successor_db_id'],['activities.schedule_version_id','activities.id'],name='fk_unresolved_relationships_successor_db_id',deferrable=True,initially='DEFERRED'),
        CheckConstraint('predecessor_db_id IS NULL OR successor_db_id IS NULL',name='unresolved_endpoint'),
    )


class ResourceRecord(UUIDPrimaryKey,Base):
    __tablename__='resources'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_resource_id: Mapped[str]=mapped_column(Text,nullable=False)
    resource_code: Mapped[str | None]=mapped_column(Text)
    resource_name: Mapped[str | None]=mapped_column(Text)
    resource_type: Mapped[str | None]=mapped_column(Text)
    active_flag: Mapped[str | None]=mapped_column(Text)
    employee_id: Mapped[str | None]=mapped_column(Text)
    email: Mapped[str | None]=mapped_column(Text)
    role_id: Mapped[str | None]=mapped_column(Text)
    cost_qty_type: Mapped[str | None]=mapped_column(Text)
    unit_id: Mapped[str | None]=mapped_column(Text)
    location_id: Mapped[str | None]=mapped_column(Text)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_parent_resource_id: Mapped[str | None]=mapped_column(Text)
    source_calendar_id: Mapped[str | None]=mapped_column(Text)
    parent_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    calendar_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_resources_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_resources_order'),
        UniqueConstraint('schedule_version_id','source_resource_id',name='uq_resources_source_id'),
        ForeignKeyConstraint(['schedule_version_id','parent_db_id'],['resources.schedule_version_id','resources.id'],name='fk_resources_parent_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','calendar_db_id'],['calendars.schedule_version_id','calendars.id'],name='fk_resources_calendar_db_id',deferrable=True,initially='DEFERRED'),
    )


class ResourceAssignmentRecord(UUIDPrimaryKey,Base):
    __tablename__='resource_assignments'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_assignment_id: Mapped[str]=mapped_column(Text,nullable=False)
    role_id: Mapped[str | None]=mapped_column(Text)
    account_id: Mapped[str | None]=mapped_column(Text)
    remain_quantity: Mapped[float | None]=mapped_column(Double)
    target_quantity: Mapped[float | None]=mapped_column(Double)
    actual_regular_quantity: Mapped[float | None]=mapped_column(Double)
    actual_overtime_quantity: Mapped[float | None]=mapped_column(Double)
    planned_cost: Mapped[float | None]=mapped_column(Double)
    actual_regular_cost: Mapped[float | None]=mapped_column(Double)
    actual_overtime_cost: Mapped[float | None]=mapped_column(Double)
    remaining_cost: Mapped[float | None]=mapped_column(Double)
    planned_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    planned_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    actual_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    actual_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    remaining_start: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    remaining_finish: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    cost_per_quantity: Mapped[float | None]=mapped_column(Double)
    cost_quantity_type: Mapped[str | None]=mapped_column(Text)
    rate_type: Mapped[str | None]=mapped_column(Text)
    resource_type: Mapped[str | None]=mapped_column(Text)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_activity_id: Mapped[str | None]=mapped_column(Text)
    source_resource_id: Mapped[str | None]=mapped_column(Text)
    activity_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    resource_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_resource_assignments_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_resource_assignments_order'),
        UniqueConstraint('schedule_version_id','source_assignment_id',name='uq_resource_assignments_source_id'),
        ForeignKeyConstraint(['schedule_version_id','activity_db_id'],['activities.schedule_version_id','activities.id'],name='fk_resource_assignments_activity_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','resource_db_id'],['resources.schedule_version_id','resources.id'],name='fk_resource_assignments_resource_db_id',deferrable=True,initially='DEFERRED'),
    )


class ActivityCodeTypeRecord(UUIDPrimaryKey,Base):
    __tablename__='activity_code_types'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_type_id: Mapped[str]=mapped_column(Text,nullable=False)
    name: Mapped[str | None]=mapped_column(Text)
    scope: Mapped[str | None]=mapped_column(Text)
    project_id: Mapped[str | None]=mapped_column(Text)
    sequence: Mapped[int | None]=mapped_column(Integer)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_wbs_id: Mapped[str | None]=mapped_column(Text)
    wbs_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_activity_code_types_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_activity_code_types_order'),
        UniqueConstraint('schedule_version_id','source_type_id',name='uq_activity_code_types_source_id'),
        ForeignKeyConstraint(['schedule_version_id','wbs_db_id'],['wbs.schedule_version_id','wbs.id'],name='fk_activity_code_types_wbs_db_id',deferrable=True,initially='DEFERRED'),
    )


class ActivityCodeValueRecord(UUIDPrimaryKey,Base):
    __tablename__='activity_code_values'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_value_id: Mapped[str]=mapped_column(Text,nullable=False)
    name: Mapped[str | None]=mapped_column(Text)
    short_name: Mapped[str | None]=mapped_column(Text)
    sequence: Mapped[int | None]=mapped_column(Integer)
    color: Mapped[str | None]=mapped_column(Text)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_type_id: Mapped[str | None]=mapped_column(Text)
    source_parent_value_id: Mapped[str | None]=mapped_column(Text)
    type_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    parent_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_activity_code_values_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_activity_code_values_order'),
        UniqueConstraint('schedule_version_id','source_value_id',name='uq_activity_code_values_source_id'),
        ForeignKeyConstraint(['schedule_version_id','type_db_id'],['activity_code_types.schedule_version_id','activity_code_types.id'],name='fk_activity_code_values_type_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','parent_db_id'],['activity_code_values.schedule_version_id','activity_code_values.id'],name='fk_activity_code_values_parent_db_id',deferrable=True,initially='DEFERRED'),
    )


class ActivityCodeAssignmentRecord(UUIDPrimaryKey,Base):
    __tablename__='activity_code_assignments'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    project_id: Mapped[str | None]=mapped_column(Text)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_activity_id: Mapped[str | None]=mapped_column(Text)
    source_type_id: Mapped[str | None]=mapped_column(Text)
    source_value_id: Mapped[str | None]=mapped_column(Text)
    activity_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    type_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    value_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_activity_code_assignments_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_activity_code_assignments_order'),
        ForeignKeyConstraint(['schedule_version_id','activity_db_id'],['activities.schedule_version_id','activities.id'],name='fk_activity_code_assignments_activity_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','type_db_id'],['activity_code_types.schedule_version_id','activity_code_types.id'],name='fk_activity_code_assignments_type_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','value_db_id'],['activity_code_values.schedule_version_id','activity_code_values.id'],name='fk_activity_code_assignments_value_db_id',deferrable=True,initially='DEFERRED'),
    )


class UDFDefinitionRecord(UUIDPrimaryKey,Base):
    __tablename__='udf_definitions'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_udf_type_id: Mapped[str]=mapped_column(Text,nullable=False)
    table_name: Mapped[str | None]=mapped_column(Text)
    name: Mapped[str | None]=mapped_column(Text)
    label: Mapped[str | None]=mapped_column(Text)
    data_type: Mapped[str | None]=mapped_column(Text)
    sequence: Mapped[int | None]=mapped_column(Integer)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_udf_definitions_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_udf_definitions_order'),
        UniqueConstraint('schedule_version_id','source_udf_type_id',name='uq_udf_definitions_source_id'),
    )


class UDFValueRecord(UUIDPrimaryKey,Base):
    __tablename__='udf_values'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    foreign_object_id: Mapped[str | None]=mapped_column(Text)
    subject_table: Mapped[str | None]=mapped_column(Text)
    raw_string_value: Mapped[str | None]=mapped_column(Text)
    text_value: Mapped[str | None]=mapped_column(Text)
    numeric_value: Mapped[float | None]=mapped_column(Double)
    date_value: Mapped[datetime | None]=mapped_column(DateTime(timezone=False))
    code_value: Mapped[str | None]=mapped_column(Text)
    raw: Mapped[dict]=mapped_column(JSONB,nullable=False)
    source_udf_type_id: Mapped[str | None]=mapped_column(Text)
    definition_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    activity_db_id: Mapped[UUID | None]=mapped_column(Uuid)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_udf_values_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_udf_values_order'),
        ForeignKeyConstraint(['schedule_version_id','definition_db_id'],['udf_definitions.schedule_version_id','udf_definitions.id'],name='fk_udf_values_definition_db_id',deferrable=True,initially='DEFERRED'),
        ForeignKeyConstraint(['schedule_version_id','activity_db_id'],['activities.schedule_version_id','activities.id'],name='fk_udf_values_activity_db_id',deferrable=True,initially='DEFERRED'),
        CheckConstraint("activity_db_id IS NULL OR upper(subject_table)='TASK'",name='task_subject_link'),
    )


class SchedulingOptionsRecord(UUIDPrimaryKey,Base):
    __tablename__='scheduling_options'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    source_project_id: Mapped[str | None]=mapped_column(Text)
    retained_logic: Mapped[bool | None]=mapped_column(Boolean)
    progress_override: Mapped[bool | None]=mapped_column(Boolean)
    ss_lag_from_early_start: Mapped[bool | None]=mapped_column(Boolean)
    use_expected_finish: Mapped[bool | None]=mapped_column(Boolean)
    set_planned_to_forecast: Mapped[bool | None]=mapped_column(Boolean)
    lag_calendar_policy: Mapped[str | None]=mapped_column(Text)
    external_relationship_policy: Mapped[str | None]=mapped_column(Text)
    raw_fields: Mapped[list]=mapped_column(JSONB,nullable=False)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_scheduling_options_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_scheduling_options_order'),
        UniqueConstraint('schedule_version_id',name='uq_scheduling_options_version'),
    )


class DiagnosticRecord(UUIDPrimaryKey,Base):
    __tablename__='import_diagnostics'
    schedule_version_id: Mapped[UUID]=mapped_column(Uuid,ForeignKey('schedule_versions.id',ondelete='CASCADE'),nullable=False,index=True)
    source_order: Mapped[int]=mapped_column(Integer,nullable=False)
    severity: Mapped[str | None]=mapped_column(Text)
    code: Mapped[str | None]=mapped_column(Text)
    message: Mapped[str | None]=mapped_column(Text)
    table_name: Mapped[str | None]=mapped_column(Text)
    field_name: Mapped[str | None]=mapped_column(Text)
    related_source_id: Mapped[str | None]=mapped_column(Text)
    raw_value: Mapped[dict | None]=mapped_column(JSONB)
    details: Mapped[dict]=mapped_column(JSONB,nullable=False)
    __table_args__=(
        UniqueConstraint('schedule_version_id','id',name='uq_import_diagnostics_version_id'),
        UniqueConstraint('schedule_version_id','source_order',name='uq_import_diagnostics_order'),
    )


