"""Session-scoped orchestration of existing application services, never formulas."""
from collections import OrderedDict
from dataclasses import asdict,replace
from datetime import datetime
from app.api.persistence import get_persistence_services
from app.persistence.repositories.navigation import NavigationRepository
from app.persistence.exceptions import ImportRejected,RecordNotFound
from app.milestones.service import MilestoneAnalysisService
from app.graph.schedule_graph import ScheduleGraph
from app.cpm.analysis_anchors import AnalysisAnchorConfig,analysis_anchor_catalog
from app.comparison.wbs import wbs_path,WBSHierarchyError
from app.reporting.serialization import to_json_value
from app.ui.presentation import record,page_rows,report_record


class PlannerService:
    def __init__(self,services=None):
        self.services=services or get_persistence_services()
        self.catalog=self.services.catalog
        self.navigation=NavigationRepository(self.catalog.sessions)
        self.cache=OrderedDict()
    def cached(self,key,build):
        if key not in self.cache:self.cache[key]=build()
        self.cache.move_to_end(key)
        while len(self.cache)>8:self.cache.popitem(last=False)
        return self.cache[key]
    def clear(self):self.cache.clear()
    def projects(self,q):return self.navigation.projects(q.offset,q.limit,q.search,sort=q.sort,descending=q.descending)
    def versions(self,project_id,q):return self.navigation.versions(project_id,q.offset,q.limit,sort=q.sort,descending=q.descending)
    def create_project(self,code,name,description):return self.catalog.create_project(code,name,description)
    def schedule(self,version_id):return self.cached(('schedule',version_id),lambda:self.catalog.load_version(version_id))[1]
    def health(self,version_id):return self.cached(('health',version_id),lambda:self.services.analyses.health(version_id))
    def dcma(self,version_id):return self.cached(('dcma',version_id),lambda:self.services.analyses.dcma(version_id))
    def milestones(self,version_id,baseline_id=None):
        def build():
            if baseline_id:return self.services.analyses.milestones(baseline_id,version_id)
            s=self.schedule(version_id);return MilestoneAnalysisService().analyze(s,ScheduleGraph(s))
        return self.cached(('milestones',version_id,baseline_id),build)
    def overview(self,version_id):
        h=self.health(version_id);d=self.dcma(version_id);m=self.milestones(version_id)
        return dict(health_score=h.score,health_rating=h.rating,dcma_score=d.overall_score.score,dcma_rating=d.overall_score.rating,
            milestone_count=m.summary.total_milestones)
    def preflight_xer(self,content,filename):
        from app.persistence.services.storage import LocalSourceStorage
        from app.importers.preflight import preflight_xer
        LocalSourceStorage('.',self.services.maximum_upload_bytes).validate(content,filename)
        return preflight_xer(content)

    def matching_project(self,preview):
        return self.catalog.find_project_by_code(preview.project_code)

    def create_project_from_xer(self,preview,name):
        if not preview.importable:raise ImportRejected('Selected source project has no importable activities or identity.')
        existing=self.matching_project(preview)
        if existing is not None:return existing
        try:return self.catalog.create_project(preview.project_code,name)
        except ImportRejected:
            # Concurrent creation remains protected by the existing unique code constraint.
            existing=self.matching_project(preview)
            if existing is not None:return existing
            raise

    def import_xer(self,project_id,content,filename,label,version_type,*,source_project_id=None):
        result=self.services.importer.import_bytes(content,filename,label=label,version_type=version_type,project_id=project_id,**({"source_project_id":source_project_id} if source_project_id is not None else {}))
        self.clear();return result
    def anchor_selection(self,key,mode='CALIBRATION',finish='',*,activity_code=None):
        if not key and not activity_code:raise ValueError('Select an explicit Analysis Anchor first.')
        stamp=datetime.fromisoformat(finish) if mode=='INDEPENDENT' and finish else None
        return AnalysisAnchorConfig(analysis_anchor_internal_id=key or None,analysis_anchor_activity_code=activity_code or None,mode=mode,required_finish=stamp,selected_by='Planner UI')
    def anchors(self,version_id):
        def build():
            s=self.schedule(version_id);return analysis_anchor_catalog(s,ScheduleGraph(s))
        return self.cached(('anchors',version_id),build)
    def anchor_analysis(self,version_id,selection):
        return self.cached(('anchor',version_id,selection),lambda:self.services.analyses.analyze_anchor(version_id,selection))
    def report(self,source_id,target_id,selection=None):
        if not source_id or not target_id:raise ValueError('Select both source and target versions.')
        return self.cached(('report',source_id,target_id,selection),lambda:self.services.analyses.forensic(source_id,target_id,analysis_selection=selection))
    def export(self,source_id,target_id,selection=None):return self.services.analyses.excel(self.report(source_id,target_id,selection))
    def report_page(self,report,key,query):
        section=report.section(key)
        payload=page_rows(section.rows,query,projector=report_record)
        for row in payload['rows']:
            row['_version_id']=report.metadata.current.version_id if row.get('current_internal_task_id') else report.metadata.baseline.version_id
        return dict(section_key=key,title=section.title,availability=section.availability,message=section.message,
            diagnostics=section.diagnostics,columns=section.columns,**payload)
    def wbs(self,s,a):
        try:return wbs_path(s,a.wbs_id)
        except WBSHierarchyError as exc:return 'UNRESOLVED: '+str(exc)
    def activity_detail(self,version_id,activity_id,analysis=None,*,by_code=False):
        s=self.schedule(version_id)
        matches=s.get_activities_by_code(activity_id) if by_code else []
        if by_code and len(matches)!=1:raise RecordNotFound('Activity code is missing or ambiguous; use an internal task identity.')
        a=matches[0] if by_code else s.activities_by_id.get(activity_id)
        if a is not None:activity_id=a.activity_id
        if a is None:raise RecordNotFound('Activity not found in selected version; inspect the source version for removed activities.')
        def relationship(r):
            p=s.activities.get(r.predecessor_activity_id);q=s.activities.get(r.successor_activity_id)
            return dict(relationship_id=r.relationship_id,predecessor=p.activity_code if p else r.predecessor_activity_id,
                successor=q.activity_code if q else r.successor_activity_id,relationship_type=r.relationship_type,lag_hours=r.lag_hours)
        calc=next((r for r in analysis.cpm_result.activity_results if r.activity_id==activity_id),None) if analysis else None
        return dict(identity=dict(internal_task_id=a.activity_id,activity_id=a.activity_code,name=a.activity_name,wbs_path=self.wbs(s,a),
            activity_type=a.activity_type,status=a.status,calendar=s.calendars.get(a.calendar_id).calendar_name if a.calendar_id in s.calendars else None),
            imported=record(a),application_calculated={k:v for k,v in record(calc).items() if not k.startswith('imported_')} if calc else None,
            analysis_anchor=analysis.anchor if analysis else None,
            application_availability='NOT_EVALUATED' if calc is None else dict(early=calc.early_date_status,late=calc.late_date_status,float=calc.float_status),
            predecessors=[relationship(r) for r in s.relationships if r.successor_activity_id==activity_id],
            successors=[relationship(r) for r in s.relationships if r.predecessor_activity_id==activity_id],
            health_findings=[issue for rule in self.health(version_id).rule_results for issue in rule.issues if issue.activity_code==a.activity_code],
            dcma_findings=[f for metric in self.dcma(version_id).metric_results for f in metric.findings if f.activity_id==a.activity_id or not f.activity_id and f.activity_code==a.activity_code],
            resource_assignments=s.get_resource_assignments(activity_id),
            milestone=next((m for m in self.milestones(version_id).milestones if m.activity_id==activity_id),None),
            finding_scope_note='Findings retain service detail limits; issue counts may exceed returned findings. Duplicate visible codes can make code-only health findings ambiguous.')
    def diagnostics(self,version_id,analysis=None):
        rows=[dict(record(d),category='IMPORT',severity=getattr(d.severity,'value',d.severity)) for d in self.catalog.diagnostics(version_id)]
        if analysis:
            rows.extend(dict(record(d),category='CPM',severity=getattr(d.severity,'value',d.severity)) for d in analysis.diagnostics)
            rows.extend(dict(activity_id=d.activity_id,category='DIRECTIONAL_AVAILABILITY',severity='WARNING',code=d.late_status,
                message='; '.join(d.reason_codes),status=d.late_status) for d in analysis.activity_dispositions if d.reason_codes)
        else:
            s=self.schedule(version_id)
            from app.cpm.config import CPMConfig
            forward=self.cached(('forward',version_id),lambda:self.services.analyses.cpm(version_id,CPMConfig(component_calculation_policy='DIRECTIONAL_FORWARD',progress_scheduling_policy='P6_RETAINED_LOGIC')))
            rows.extend(dict(record(d),category='CPM_FORWARD',severity=getattr(d.severity,'value',d.severity)) for d in forward.diagnostics)
        return rows


    def dcma_finding_rows(self,version_id,metric):
        s=self.schedule(version_id)
        graph=self.cached(('graph',version_id),lambda:ScheduleGraph(s))
        rows=[]
        for finding in metric.findings:
            row=record(finding).copy();a=s.activities.get(finding.activity_id)
            if a:
                row.update(status=a.status,activity_type=a.activity_type,
                    predecessor_count=len(graph.predecessor_relationships.get(a.activity_id,())),
                    successor_count=len(graph.successor_relationships.get(a.activity_id,())))
            for direction in ('predecessor','successor'):
                endpoint=s.activities.get(getattr(finding,direction+'_activity_id'))
                row[direction+'_activity_code']=endpoint.activity_code if endpoint else None
                row[direction+'_activity_name']=endpoint.activity_name if endpoint else None
            row['threshold']=metric.threshold;rows.append(row)
        return rows


    def analysis_rows(self,analysis):
        # Reuse the existing comparison engine for ES/EF variance; never subtract
        # dates or implement comparison arithmetic in presentation code.
        from app.cpm.comparison import compare_activities
        from app.ui.presentation import selected_analysis_rows
        comparisons,_=compare_activities(analysis.cpm_result.schedule,analysis.cpm_result.activity_results,analysis.cpm_result.calculation_config)
        rows=selected_analysis_rows(analysis,comparisons)
        s=analysis.cpm_result.schedule
        for row in rows:
            a=s.activities.get(row['activity_id'])
            if a:row['wbs_path']=self.wbs(s,a)
        return rows


    def milestone_rows(self,version_id,result):
        from app.milestones.analysis import preferred_planned_date
        s=self.schedule(version_id)
        comparisons={c.current_activity.activity_id:c for c in result.comparisons if c.current_activity is not None}
        ambiguous={c.activity_code for c in result.comparisons if c.movement.value=='AMBIGUOUS'}
        rows=[]
        for m in result.milestones:
            c=comparisons.get(m.activity_id);a=s.activities.get(m.activity_id)
            row=record(m).copy()
            row.update(_version_id=str(version_id),planned_date=preferred_planned_date(a,m.classification) if a else None,
                baseline_date=c.baseline_planned_date if c else None,
                movement=c.movement if c else 'AMBIGUOUS' if m.activity_code in ambiguous else None,
                movement_hours=c.planned_date_variance_hours if c else None)
            rows.append(row)
        return rows
