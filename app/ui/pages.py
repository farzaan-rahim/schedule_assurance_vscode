"""NiceGUI presentation. All domain values come from PlannerService."""
import asyncio
from dataclasses import replace
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from nicegui import ui,app as nicegui_app,context
from sqlalchemy.exc import SQLAlchemyError
from app.persistence.exceptions import PersistenceError,ImportRejected
from app.cpm.analysis_anchors import AnchorSelectionError
from app.reporting.excel_renderer import FILENAME,MEDIA_TYPE
from app.reporting.serialization import to_json_value
from app.ui.state import NAVIGATION,SessionState,TableQuery
from app.runtime import inspect_runtime,RuntimeStatus
from app.ui.service import PlannerService
from app.ui.import_workflow import ImportDraft,XERImportPanel
from app.ui.presentation import page_rows,record,report_record,text,metric_evidence,STATUS_COLORS,selected_analysis_rows

class PlannerUI:
    def __init__(self,service=None,*,runtime_probe=None):
        self.state=SessionState();self.import_draft=ImportDraft();self.failed=False;self.service=service;self.operation_lock=asyncio.Lock();self.projects=[];self.versions=[];self.version_count=0
        self.analysis=None;self.analysis_version=None;self.report=None;self.overview_data={};self.nav_buttons={}
        self.runtime_probe=runtime_probe or inspect_runtime;self.runtime_status=None;self.setup_checking=False;self.service_injected=service is not None
    def backend(self):
        if self.service is None:self.service=PlannerService()
        return self.service
    def build(self):
        ui.colors(primary='#2869a8',secondary='#183958',positive='#23734d',warning='#9c650b',negative='#b53636')
        ui.add_css(Path(__file__).with_name('styles.css').read_text())
        with ui.left_drawer(value=True).classes('sa-drawer').props('id=sa-navigation width=246 breakpoint=900') as self.drawer:
            with ui.row().classes('items-center gap-3 mb-5 px-3'):
                ui.avatar('schema',color='primary',text_color='white',size='36px')
                with ui.column().classes('gap-0'):
                    ui.label('Schedule Assurance').classes('sa-brand')
                    ui.label('PROJECT CONTROLS').classes('text-xs text-slate-400 tracking-widest')
            ui.separator().props('dark');ui.label('WORKSPACE').classes('sa-kicker')
            with ui.column().classes('sa-nav-list').props('role=navigation aria-label="Main navigation"'):
                for title,icon in NAVIGATION:
                    self.nav_buttons[title]=ui.button(title,icon=icon,on_click=lambda t=title:self.navigate(t)).props('flat no-caps align=left').classes('sa-nav')
            ui.space();ui.label('Evidence before conclusions').classes('text-xs text-slate-400 px-3')
            ui.label('Immutable schedule versions').classes('text-xs text-slate-400 px-3')
        with ui.header().classes('sa-header items-center gap-4'):
            self.menu_button=ui.button(icon='menu',on_click=self.toggle_navigation).props('flat round aria-label="Toggle navigation" aria-controls=sa-navigation aria-expanded=true')
            self.drawer.on_value_change(lambda e:self.menu_button.props('aria-expanded='+str(bool(e.value)).lower()))
            self.project_select=ui.select({},label='Project',on_change=self.project_changed).props('outlined dense options-dense').classes('w-64')
            self.version_select=ui.select({},label='Active Schedule Version',on_change=self.version_changed).props('outlined dense options-dense').classes('w-72')
            ui.space();ui.badge('IMPORTED + CALCULATED',color='grey-2',text_color='primary').classes('text-xs p-2')
            self.root_link('API','/docs','Swagger API documentation')
            self.root_link('Local setup','/setup','Local startup instructions')
        with ui.column().classes('sa-content'):
            with ui.row().classes('w-full items-center'):
                self.heading=ui.label('Project overview').classes('sa-title').props('id=sa-view-title role=heading aria-level=1');ui.space()
                self.spinner=ui.spinner(size='20px').props('role=progressbar aria-label="Operation in progress"');self.spinner.set_visibility(False)
                self.task_label=ui.label('Checking startup').classes('sa-subtitle').props('role=status aria-live=polite')
            with ui.row().classes('w-full items-center gap-3'):
                ui.badge('UI available',color='positive')
                self.database_badge=ui.badge('Checking database',color='grey-7')
                self.runtime_message=ui.label('Checking local runtime configuration.').classes('sa-subtitle').props('role=status aria-live=polite')
                self.recheck_button=ui.button('Recheck setup',icon='refresh',on_click=self.recheck).props('flat no-caps')
            self.banner=ui.column().classes('w-full');self.content=ui.column().classes('w-full gap-5').props('role=main aria-labelledby=sa-view-title')
        self.apply_control_state();self.render();ui.timer(.05,self.start,once=True)
        return self
    async def fetch(self,work,*,label='Loading',clear_error=True):
        if self.setup_checking or self.runtime_status is None:return None
        if not self.runtime_ready:self.render();return None
        await self.operation_lock.acquire()
        self.state.busy=True;self.project_select.disable();self.version_select.disable();self.spinner.set_visibility(True);self.task_label.set_text(label)
        if clear_error:self.banner.clear();self.failed=False
        try:
            result=await asyncio.to_thread(work);self.task_label.set_text('Failed' if self.failed else 'Complete');return result
        except (HTTPException,PersistenceError,AnchorSelectionError,ValueError,SQLAlchemyError,OSError) as exc:
            message=str(exc.detail) if isinstance(exc,HTTPException) else str(exc) if isinstance(exc,(PersistenceError,AnchorSelectionError,ValueError)) else 'The server could not complete this operation. Check database availability and retry.'
            self.failed=True;self.task_label.set_text('Failed')
            with self.banner:
                ui.label('Application error | '+message).classes('sa-error w-full').props('role=alert')
                if isinstance(exc,ImportRejected) and exc.diagnostics:self.local_records(exc.diagnostics,'Import diagnostics')
            return None
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Planner UI operation failed')
            self.failed=True;self.task_label.set_text('Failed')
            with self.banner:ui.label('Application error | Unexpected server response. Retry or consult server diagnostics.').classes('sa-error w-full').props('role=alert')
            return None
        finally:self.state.busy=False;self.spinner.set_visibility(False);self.apply_control_state();self.operation_lock.release()
    async def start(self):
        await context.client.connected()
        saved=nicegui_app.storage.tab.get('schedule_assurance_state')
        if isinstance(saved,SessionState):self.state=replace(saved,filters=dict(saved.filters),busy=False)
        nicegui_app.storage.tab['schedule_assurance_state']=self.state
        await self.check_setup()
        if not self.runtime_ready:self.render();return
        data=await self.fetch(lambda:self.backend().projects(TableQuery()),label='Loading projects')
        if data is not None:
            self.projects=list(data[0])
            if self.state.project_id:await self.choose_project(self.state.project_id)
            else:self.sync_context();self.render()
    @property
    def runtime_ready(self):return self.runtime_status is not None and self.runtime_status.ready
    def toggle_navigation(self):
        self.drawer.toggle()
        self.menu_button.props('aria-expanded='+str(bool(self.drawer.value)).lower())
    def root_link(self,label,path,accessible_name=None):
        # ui.link prefixes the NiceGUI mount; these routes belong to parent FastAPI.
        with ui.element('a').props(f'href="{path}" aria-label="{accessible_name or label}"').classes('sa-root-link text-sm'):
            ui.label(label)
    def apply_control_state(self):
        if not hasattr(self,'project_select'):return
        self.project_select.set_enabled(self.runtime_ready and not self.setup_checking and not self.state.busy and bool(self.projects))
        self.version_select.set_enabled(self.runtime_ready and not self.setup_checking and not self.state.busy and bool(self.state.project_id) and bool(self.versions))
    async def check_setup(self):
        self.setup_checking=True;self.apply_control_state()
        self.spinner.set_visibility(True);self.recheck_button.disable();self.task_label.set_text('Checking setup')
        try:
            try:self.runtime_status=await asyncio.to_thread(self.runtime_probe)
            except Exception:self.runtime_status=RuntimeStatus('DIAGNOSTICS_UNAVAILABLE','Runtime diagnostics are unavailable. Retry setup or check server logs.',None)
            labels={'READY':'Database ready','UNCONFIGURED':'Setup required','INVALID_CONFIGURATION':'Configuration invalid',
                'DATABASE_UNAVAILABLE':'Database unavailable','MIGRATIONS_REQUIRED':'Migrations required','MIGRATIONS_UNKNOWN':'Migration status unknown','DIAGNOSTICS_UNAVAILABLE':'Diagnostics unavailable'}
            label=labels[self.runtime_status.status]
            self.database_badge.set_text(label);self.database_badge.props('color=positive' if self.runtime_ready else 'color=grey-7')
            self.runtime_message.set_text(self.runtime_status.message)
            self.task_label.set_text('Ready' if self.runtime_ready else label)
        finally:self.setup_checking=False;self.spinner.set_visibility(False);self.recheck_button.enable();self.apply_control_state()
    async def recheck(self):
        if self.state.busy or self.setup_checking:return
        if self.service is not None and not self.service_injected:self.service.clear();self.service=None
        self.analysis=None;self.analysis_version=None;self.banner.clear();self.failed=False
        await self.check_setup()
        if self.runtime_ready:
            data=await self.fetch(lambda:self.backend().projects(TableQuery()),label='Loading projects')
            if data is not None:
                self.projects=list(data[0])
                if self.state.project_id:await self.choose_project(self.state.project_id)
                else:self.sync_context()
        self.apply_control_state();self.render()
    def empty_panel(self,panel,message):
        with panel:ui.label(message).classes('sa-empty').props('role=status')
    def sync_context(self):
        self.project_select.options={str(p.id):p.project_code+' | '+p.project_name for p in self.projects}
        self.project_select.value=str(self.state.project_id) if self.state.project_id else None;self.project_select.update()
        self.version_select.options={str(v.id):v.label+' | '+v.version_type for v in self.versions}
        self.version_select.value=str(self.state.version_id) if self.state.version_id else None;self.version_select.update();self.apply_control_state()
    async def project_changed(self,e):
        if not e.value or self.state.busy:return
        key=UUID(str(e.value))
        if key!=self.state.project_id:await self.choose_project(key)
    async def choose_project(self,key):
        if self.state.busy:return
        self.state.select_project(key);self.analysis=None;self.report=None;self.overview_data={}
        selected=self.state.version_id
        result=await self.fetch(lambda:self.backend().versions(key,TableQuery(limit=200)),label='Loading schedule versions')
        if result is not None:
            self.versions=list(result[0]);self.version_count=result[1]
            for identity in (selected,self.state.source_version_id,self.state.target_version_id):
                if identity and not any(v.id==identity for v in self.versions):
                    extra=await self.fetch(lambda k=identity:self.backend().catalog.get_version(k),label='Restoring selected version')
                    if extra is not None and extra.project_id==key:self.versions.append(extra)
            if self.versions:self.state.select_version(selected or self.versions[0].id)
            if not any(p.id==key for p in self.projects):self.projects.append(await asyncio.to_thread(self.backend().catalog.get_project,key))
            self.sync_context();self.render()
    async def version_changed(self,e):
        if not e.value or self.state.busy:return
        key=UUID(str(e.value))
        if key!=self.state.version_id:self.state.select_version(key);self.analysis=None;self.analysis_version=None;self.render()
    async def navigate(self,title):
        if self.state.busy:ui.notify('Wait for the current operation to complete.');return
        self.state.navigate(title);self.render()
    def note(self,message):ui.label(message).classes('sa-note w-full')
    def badge(self,status):ui.badge(text(status),color=STATUS_COLORS.get(text(status),'primary')).classes('px-2 py-1')
    def values(self,data):
        with ui.element('div').classes('sa-detail-grid'):
            for key,value in data.items():
                with ui.column().classes('gap-1'):
                    ui.label(key.replace('_',' ').title()).classes('text-xs text-slate-500')
                    ui.label(text(value)).classes('text-sm whitespace-pre-wrap')
    def stats(self,data):
        with ui.row().classes('w-full gap-4'):
            for label,value in data.items():
                with ui.card().classes('sa-card sa-stat'):
                    ui.label(label).classes('sa-subtitle');ui.label(text(value)).classes('sa-stat-value')
    def local_records(self,rows,title='',columns=None):
        return self.table('local-'+title,lambda q:page_rows(rows,q),title=title,columns=columns)
    def table(self,key,provider,*,title='',columns=None,pick=None,filters=False):
        q=self.state.query(key);controls={}
        if title:ui.label(title).classes('text-lg font-semibold mt-2')
        with ui.row().classes('w-full gap-3 items-end'):
            controls['search']=ui.input('Activity ID / name / text',value=q.search).props('outlined dense clearable').classes('sa-filter')
            if filters:
                for k,label in [('wbs','WBS contains'),('status','Status'),('activity_type','Activity type'),('classification','Classification'),('severity','Severity'),('category','Category')]:
                    controls[k]=ui.input(label,value=getattr(q,k)).props('outlined dense clearable').classes('sa-filter')
            apply=ui.button('Apply filters',icon='filter_list').props('outline no-caps')
        count=ui.label('Loading records...').classes('sa-subtitle')
        table=ui.table(rows=[],columns=[],row_key='_row_key',selection='single' if pick else None,
            pagination={'page':1,'rowsPerPage':q.limit,'rowsNumber':0}).classes('sa-table').props('flat bordered wrap-cells tabindex=0 role=region :rows-per-page-options="[50,100,200]"')
        table.props('aria-label="'+(title or self.state.page+' records')+'"')
        table.mark('table-'+key)
        for field in ('classification','availability','status'):
            table.add_slot('body-cell-'+field,'''<q-td :props="props"><q-badge :color="({PASS:'positive',WARNING:'warning',FAIL:'negative',BLOCKED:'negative',NOT_EVALUATED:'grey-7',NOT_APPLICABLE:'grey-7',AVAILABLE:'positive',ADDED:'positive',REMOVED:'negative',DELAYED:'warning',DETERIORATED:'negative',BECAME_NEGATIVE:'negative',CHANGED:'warning',TYPE_CHANGED:'warning',LAG_CHANGED:'warning',WBS_MOVED:'warning',STATUS_CHANGED:'warning',RECOVERED:'positive',IMPROVED:'positive'})[props.value] || 'grey-7'">{{ props.value }}</q-badge></q-td>''')
        original={}
        async def refresh(query=None):
            if table.is_deleted:return
            query=query or self.state.query(key)
            data=await self.fetch(lambda:provider(query),label='Loading '+(title or 'records'),clear_error=False)
            if table.is_deleted:return
            if data is None:
                count.set_text('Application error | records unavailable');table.rows=[];table.update();return
            if data['total'] and not data.get('rows') and query.offset:
                await refresh(replace(query,offset=0));return
            self.state.filters[key]=query;records=data.get('rows',[]);original.clear();original.update({r['_row_key']:r for r in records})
            wanted=columns or ([(c.key,c.title) for c in data['columns']] if data.get('columns') else [(k,k.replace('_',' ').title()) for r in records[:1] for k in r if not k.startswith('_')])
            if not wanted:wanted=[('message','Status')]
            table.columns=[dict(name=k,label=t,field=k,sortable=True,align='left') for k,t in wanted]
            types={c.key:c.data_type for c in data.get('columns',())}
            def cell(k,v):
                if types.get(k)=='percentage' and isinstance(v,(int,float)):return format(v,'.2%')
                return text(v) if isinstance(v,(dict,list,tuple)) or v is None else v
            table.rows=[{k:cell(k,v) for k,v in r.items()} for r in records]
            table.pagination={'page':query.offset//query.limit+1,'rowsPerPage':query.limit,'rowsNumber':data['total'],'sortBy':query.sort or None,'descending':query.descending}
            table.selected=[];table.update()
            count.set_text(f"{data['total']:,} records | showing {len(records)} | server-side page | availability: {text(data.get('availability','AVAILABLE'))}")
            if not records:count.set_text('No data | '+text(data.get('message') or 'No records match these filters.'))
        async def filtered():await refresh(replace(self.state.query(key),offset=0,**{k:c.value or '' for k,c in controls.items()}))
        async def requested(e):
            p=e.args.get('pagination',{});size=p.get('rowsPerPage',50)
            if size not in (50,100,200):size=50
            await refresh(replace(self.state.query(key),offset=max(0,p.get('page',1)-1)*size,limit=size,sort=p.get('sortBy') or '',descending=bool(p.get('descending'))))
        async def selected(e):
            if e.selection and pick:await pick(original[e.selection[0]['_row_key']])
        apply.on_click(filtered);controls['search'].on('keydown.enter',filtered);table.on('request',requested)
        if pick:table.on_select(selected)
        ui.timer(.02,refresh,once=True);return table
    def render(self):
        for title,b in self.nav_buttons.items():b.classes(remove='sa-nav-active',add='sa-nav-active' if title==self.state.page else '')
        self.heading.set_text('Project overview' if self.state.page=='Overview' else self.state.page);self.content.clear()
        with self.content:
            if self.runtime_status is None or self.setup_checking:
                self.note('Checking local startup configuration. The UI is available; database controls will be enabled when ready.');return
            if self.runtime_status is not None and not self.runtime_ready:
                self.note(self.runtime_status.message)
                ui.label(self.empty_message()).classes('sa-empty').props('role=status')
                self.root_link('Open local setup instructions','/setup')
                return
            if self.state.page=='Projects':self.projects_page();return
            if self.state.page=='Schedule Versions':self.versions_page();return
            if not self.state.project_id:
                self.note(self.empty_message())
                ui.button('Open Projects',icon='folder_open',on_click=lambda:self.navigate('Projects')).props('no-caps');return
            if not self.state.version_id:
                self.note('No Schedule Version selected. Import or select a version in Schedule Versions to use '+self.state.page+'.')
                ui.button('Open Schedule Versions',on_click=lambda:self.navigate('Schedule Versions')).props('no-caps');return
            {'Overview':self.overview_page,'Schedule Health':self.health_page,'DCMA':self.dcma_page,'Change Analysis':self.changes_page,
                'Milestones':self.milestones_page,'CPM / Paths':self.cpm_page,'Diagnostics':self.diagnostics_page,'Reports':self.reports_page}[self.state.page]()
    def empty_message(self):
        messages={'Overview':'Select a project to view its schedule overview.',
            'Projects':'Configure PostgreSQL to create or select projects.',
            'Schedule Versions':'Select a project to view or import schedule versions.',
            'Schedule Health':'Select a project to view schedule health.',
            'DCMA':'Select a project to run a DCMA-style assessment.',
            'Change Analysis':'Select a project and two Schedule Versions to compare.',
            'Milestones':'Select a project to review milestones.',
            'CPM / Paths':'Select a project and Schedule Version, then choose an explicit Analysis Anchor.',
            'Diagnostics':'Select a project to inspect import and calculation diagnostics.',
            'Reports':'Select a project and source/target versions to generate a report.'}
        return messages[self.state.page]
    def projects_page(self):
        self.note('Projects contain immutable schedule versions. Multiple baselines are supported.')
        with ui.expansion('Create a project',icon='add_circle',value=True).classes('sa-card w-full'):
            code=ui.input('Project code').props('outlined');name=ui.input('Project name').props('outlined');description=ui.input('Description (optional)').props('outlined')
            async def create():
                result=await self.fetch(lambda:self.backend().create_project(code.value,name.value,description.value or None),label='Creating project')
                if result:self.projects.append(result);await self.choose_project(result.id);self.state.page='Schedule Versions';self.render()
            ui.button('Create project',on_click=create).props('no-caps')
        def provider(q):
            rows,total=self.backend().projects(q)
            return dict(rows=[dict(jsonable_encoder(r),_row_key=str(r.id)) for r in rows],total=total)
        async def pick(row):await self.choose_project(UUID(str(row['id'])));await self.navigate('Overview')
        self.table('projects',provider,title='Project directory',columns=[('project_code','Project Code'),('project_name','Project Name'),('active','Active'),('created_at','Created')],pick=pick)
    def overview_page(self):
        p=next((p for p in self.projects if p.id==self.state.project_id),None);latest=self.versions[0] if self.versions else None
        with ui.card().classes('sa-card w-full'):
            self.values(dict(project_code=p.project_code if p else None,project_name=p.project_name if p else None,
                latest_schedule_version=latest.label if latest else None,latest_data_date=latest.data_date if latest else None,schedule_versions=self.version_count,
                current_analysis_baseline=next((v.label for v in self.versions if v.id==self.state.source_version_id),'Not selected'),
                current_analysis_update=next((v.label for v in self.versions if v.id==self.state.target_version_id),'Not selected')))
        self.stats({'Latest activities':latest.activity_count if latest else None,'Latest relationships':latest.relationship_count if latest else None,
            'Latest milestones':self.overview_data.get('milestone_count'),'Latest health score':self.overview_data.get('health_score'),'Latest DCMA score':self.overview_data.get('dcma_score')})
        self.note('Scores are Not evaluated until analysis runs. Generic health and DCMA are independent assessments; no combined score is created.')
        async def analyze():
            result=await self.fetch(lambda:self.backend().overview(latest.id),label='Analyzing latest imported version')
            if result is not None:self.overview_data=result;self.render()
        with ui.row():
            ui.button('Analyze latest schedule',icon='analytics',on_click=analyze).props('no-caps')
            ui.button('Version history',icon='history',on_click=lambda:self.navigate('Schedule Versions')).props('outline no-caps')
    def versions_page(self):
        self.note('Choose a version to analyze. Imported values are retained; successful versions are immutable. Imports require a Project code matching the P6 export.')
        self.import_panel=XERImportPanel(self).build()
        if not self.state.project_id:
            self.note('Select an XER to detect its project, or select an existing application project.')
            return
        def provider(q):
            rows,total=self.backend().versions(self.state.project_id,q)
            return dict(rows=[dict(jsonable_encoder(v),_row_key=str(v.id)) for v in rows],total=total)
        async def pick(row):
            key=UUID(str(row['id']));info=await self.fetch(lambda:self.backend().catalog.get_version(key),label='Selecting version')
            if info is None:return
            if not any(v.id==key for v in self.versions):self.versions.append(info)
            self.state.select_version(key);self.analysis=None;self.sync_context();ui.notify('Active version: '+row['label'])
        self.table('versions',provider,title='Version history | select a row to activate',columns=[(k,t) for k,t in [('label','Version'),('version_type','Type'),('data_date','Data Date'),('imported_at','Imported'),('source_filename','Original File'),('activity_count','Activities'),('relationship_count','Relationships'),('wbs_count','WBS'),('calendar_count','Calendars'),('resource_count','Resources'),('import_status','Status')]],pick=pick)
        with ui.row():
            for title in ('Schedule Health','DCMA','Milestones','CPM / Paths','Change Analysis','Reports'):
                ui.button(title,on_click=lambda t=title:self.navigate(t)).props('outline no-caps')
        ui.button('View import diagnostics',on_click=lambda:self.navigate('Diagnostics')).props('flat no-caps')
    async def investigate(self,row):
        key=row.get('current_internal_task_id') or row.get('internal_task_id') or row.get('activity_id')
        version=self.state.target_version_id if row.get('current_internal_task_id') else self.state.source_version_id if row.get('baseline_internal_task_id') else self.state.version_id
        if row.get('_version_id'):version=UUID(str(row['_version_id']))
        by_code=not bool(key)
        key=key or row.get('activity_code')
        if not key:return
        analysis=self.analysis if self.analysis_version==version else None
        result=await self.fetch(lambda:self.backend().activity_detail(version,key,analysis,by_code=by_code),label='Loading activity investigation')
        if result:
            with self.content,ui.dialog().props('maximized') as dialog,ui.card().classes('sa-card sa-dialog w-full'):
                dialog.on('hide',dialog.delete)
                with ui.row().classes('w-full items-center'):
                    ui.label('Activity investigation').classes('sa-title');ui.space();ui.button('Close',icon='close',on_click=dialog.close).props('flat')
                self.values(result['identity']);self.note(result['finding_scope_note'])
                comparison_context={k:row[k] for k in ('baseline_wbs','current_wbs','baseline_calendar','current_calendar','baseline_value','current_value','variance','percentage','classification','provenance') if k in row}
                if comparison_context:
                    with ui.expansion('Comparison context',value=True).classes('w-full'):self.values(comparison_context)
                for name,data in [('Imported P6',result['imported']),('Application Calculated',result['application_calculated'])]:
                    with ui.expansion(name,value=True).classes('w-full'):
                        if data:self.values(data)
                        else:self.badge('NOT_EVALUATED');ui.label('Run selected-anchor analysis to inspect calculated values. Imported values are not substituted.')
                self.values({'calculation_availability':result['application_availability'],'analysis_anchor':result['analysis_anchor']})
                for name,key in [('Predecessors','predecessors'),('Successors','successors'),('Health findings','health_findings'),('DCMA findings','dcma_findings'),('Resource assignments','resource_assignments')]:self.local_records(result[key],name)
                with ui.expansion('Milestone status').classes('w-full'):self.values(record(result['milestone']) if result['milestone'] else {'availability':'NOT_APPLICABLE'})
            dialog.open()
    def health_page(self):
        async def run():
            result=await self.fetch(lambda:self.backend().health(self.state.version_id),label='Analyzing schedule health')
            if result is None:return
            panel.clear()
            with panel:
                self.stats({'Generic health score':result.score,'Rating':result.rating,'Total findings':result.total_issues,'Critical':result.critical_issues,'Warnings':result.warning_issues})
                async def rule(row):
                    selected=next(r for r in result.rule_results if r.rule_id==row['rule_id'])
                    with ui.dialog() as d,ui.card().classes('sa-card w-full').style('min-width:85vw'):
                        ui.label(selected.rule_name).classes('text-xl');ui.label(f'Returned {selected.returned_count} of {selected.issue_count} findings; service detail limits are preserved.')
                        self.table('health-rule-'+selected.rule_id,lambda q:page_rows(selected.issues,q),title='Health rule findings',pick=self.investigate);ui.button('Close',on_click=d.close)
                    d.open()
                self.table('health-rules',lambda q:page_rows([dict(rule_id=r.rule_id,rule_name=r.rule_name,eligible_population=None,issue_count=r.issue_count,severity=r.severity,status='ISSUES_IDENTIFIED' if r.issue_count else 'NO_FINDINGS') for r in result.rule_results],q),title='Rules | select to investigate',pick=rule)
        self.note('Generic Schedule Health | independent from the DCMA-style assessment.')
        ui.button('Analyze Health',icon='monitor_heart',on_click=run).props('no-caps');panel=ui.column().classes('w-full gap-4')
        self.empty_panel(panel,'No health analysis run. Choose Analyze Health to evaluate this version.')
    def dcma_page(self):
        async def run():
            result=await self.fetch(lambda:self.backend().dcma(self.state.version_id),label='Running DCMA-style assessment')
            if result is None:return
            panel.clear()
            with panel:
                self.stats({'DCMA score':result.overall_score.score,'Rating':result.overall_score.rating,'Evaluated metrics':result.metrics_evaluated,'Not evaluated / applicable':result.metrics_not_evaluated})
                for m in result.metric_results:
                    with ui.expansion(m.metric_name,icon='fact_check').classes('sa-card w-full'):
                        self.badge(m.status)
                        self.values(dict(eligible_population=m.eligible_count,excluded_population=m.excluded_count,finding_count=m.finding_count,percentage=m.finding_percentage,threshold=m.threshold,
                            interpretation=m.threshold_interpretation,calculation_notes=m.calculation_notes,limitations=m.limitations,exclusion_reasons=m.exclusion_reasons))
                        if m.metric_id in {'critical_path_test','cpli'}:
                            self.values(metric_evidence(m));ui.label('Application defaults are not official DCMA limits. CPT FAIL does not prove defective scheduling logic.').classes('sa-subtitle')
                        if m.status.value=='NOT_EVALUATED' and m.details.get('source_cpm_result'):
                            source=m.details['source_cpm_result']
                            self.table('dcma-source-'+m.metric_id,lambda q,rows=source.get('diagnostics',()):page_rows(rows,q),title='Calculation diagnostics',filters=True)
                        self.note(f'Returned {len(m.findings)} of {m.finding_count} findings. Service detail limits apply.')
                        self.table('dcma-'+m.metric_id,lambda q,metric=m:page_rows(self.backend().dcma_finding_rows(self.state.version_id,metric),q),title=m.metric_name+' findings',filters=True,pick=self.investigate)
        self.note('PASS | WARNING | FAIL | NOT_EVALUATED | NOT_APPLICABLE are distinct states. Missing values are never shown as zero.')
        ui.button('Run DCMA',icon='fact_check',on_click=run).props('no-caps');panel=ui.column().classes('w-full gap-4')
        self.empty_panel(panel,'No DCMA assessment run. Choose Run DCMA to see metric availability and evidence.')
    def comparison_controls(self):
        options={str(v.id):v.label+' | '+v.version_type for v in self.versions}
        with ui.row().classes('w-full items-end'):
            source=ui.select(options,value=str(self.state.source_version_id) if self.state.source_version_id else None,label='Source / Baseline Version').props('outlined').classes('w-80')
            target=ui.select(options,value=str(self.state.target_version_id) if self.state.target_version_id else None,label='Target / Current Version').props('outlined').classes('w-80')
        source.on_value_change(lambda e:setattr(self.state,'source_version_id',UUID(e.value) if e.value else None))
        target.on_value_change(lambda e:setattr(self.state,'target_version_id',UUID(e.value) if e.value else None))
        return source,target
    def changes_page(self):
        self.comparison_controls()
        async def run():
            result=await self.fetch(lambda:self.backend().report(self.state.source_version_id,self.state.target_version_id),label='Building forensic comparison')
            if result is None:return
            self.report=result;panel.clear()
            with panel:
                self.values(record(result.metadata));self.note('Values and classifications come from ForensicChangeReport. Imported and calculated values remain separate.')
                options={s.key:s.title for s in result.sections};options['wbs_movement']='WBS Movement (activity change category)'
                global_search=ui.input('Global Activity ID / name',value=self.state.global_search).props('outlined clearable').classes('w-96')
                global_search.on_value_change(lambda e:setattr(self.state,'global_search',e.value or ''))
                section=ui.select(options,value='summary',label='Change section').props('outlined').classes('w-96');body=ui.column().classes('w-full')
                def show():
                    body.clear();key=section.value
                    with body:
                        if key=='wbs_movement':
                            rows=[r for r in result.section('activities').rows if 'wbs' in ' '.join(map(str,r.cells.get('change_categories',()))).casefold()]
                            self.table('changes-wbs',lambda q:page_rows(rows,replace(q,search=self.state.global_search or q.search),projector=report_record),filters=True,pick=self.investigate);return
                        s=result.section(key);self.badge(s.availability)
                        if s.message:ui.label(s.message)
                        if s.diagnostics:self.note(text(s.diagnostics))
                        self.table('changes-'+key,lambda q:self.backend().report_page(result,key,replace(q,search=self.state.global_search or q.search)),filters=True,pick=self.investigate)
                def apply_global():
                    for key,q in list(self.state.filters.items()):
                        if key.startswith('changes-'):self.state.filters[key]=replace(q,offset=0)
                    show()
                section.on_value_change(show);global_search.on('keydown.enter',apply_global);show()
        ui.button('Run comparison',icon='compare_arrows',on_click=run).props('no-caps');panel=ui.column().classes('w-full gap-4')
        self.empty_panel(panel,'No comparison run. Select source and target Schedule Versions, then Run comparison.')
    def milestones_page(self):
        self.note('Milestone movement uses the selected source baseline when available; dates are not recalculated in this screen.')
        self.comparison_controls()
        async def run():
            result=await self.fetch(lambda:self.backend().milestones(self.state.target_version_id or self.state.version_id,self.state.source_version_id),label='Analyzing milestones')
            if result is None:return
            panel.clear()
            with panel:
                self.values(record(result.summary));rows=self.backend().milestone_rows(self.state.target_version_id or self.state.version_id,result)
                flag=ui.select(['All','DELAYED','IMPROVED','negative_float','critical','overdue','completed'],value='All',label='Milestone filter').props('outlined').classes('w-64');body=ui.column().classes('w-full')
                def show():
                    body.clear()
                    with body:
                        selected=[r for r in rows if flag.value=='All' or text(r.get('movement'))==flag.value or r.get(flag.value) is True]
                        self.table('milestones-'+flag.value,lambda q:page_rows(selected,q),filters=True,pick=self.investigate,
                            columns=[('activity_code','Activity ID'),('activity_name','Milestone'),('classification','Type'),('status','Status'),('wbs_path','WBS'),('planned_date','Planned Milestone Date'),('baseline_date','Baseline Date'),('movement','Movement'),('movement_hours','Movement (elapsed h)'),('total_float_hours','Imported TF (h)'),('critical','Imported Critical Proxy'),('overdue','Overdue')])
                        self.local_records(result.findings,'Milestone health findings')
                        self.local_records([dict(anchor_activity_code=code,**record(driver)) for code,drivers in result.candidate_drivers.items() for driver in drivers],'Candidate milestone drivers')
                flag.on_value_change(show);show()
        ui.button('View Milestones',icon='flag',on_click=run).props('no-caps');panel=ui.column().classes('w-full gap-4')
        self.empty_panel(panel,'No milestone analysis run. Choose View Milestones to load this version.')
    def cpm_page(self):
        self.note('Analysis Anchor does not establish contractual completion authority. No milestone is selected automatically.')
        anchor=ui.input('Analysis Anchor internal ID',value=self.state.analysis_anchor_id or '').props('outlined').classes('w-80')
        code=ui.input('Analysis Anchor Activity ID / code (optional)',value=self.state.analysis_anchor_code or '').props('outlined').classes('w-96')
        code.on_value_change(lambda e:setattr(self.state,'analysis_anchor_code',e.value or None))
        mode=ui.select(['CALIBRATION','INDEPENDENT'],value=self.state.analysis_mode,label='Analysis mode').props('outlined').classes('w-64')
        finish=ui.input('INDEPENDENT required finish | YYYY-MM-DD HH:MM',value=self.state.required_finish).props('outlined').classes('w-96')
        anchor.on_value_change(lambda e:setattr(self.state,'analysis_anchor_id',e.value or None));mode.on_value_change(lambda e:setattr(self.state,'analysis_mode',e.value));finish.on_value_change(lambda e:setattr(self.state,'required_finish',e.value or ''))
        async def candidates():
            result=await self.fetch(lambda:self.backend().anchors(self.state.version_id),label='Loading candidate evidence')
            if result:
                candidates_panel.clear()
                with candidates_panel:
                    self.badge(result['completion_authority_status'])
                    async def choose(row):anchor.set_value(row['activity_id']);code.set_value(row['activity_code']);ui.notify('Selected Analysis Anchor: '+row['activity_code'])
                    self.table('anchor-candidates',lambda q:page_rows(result['candidates'],q),title='Candidate milestones | select explicitly',pick=choose,
                        columns=[('activity_code','Activity ID'),('activity_id','Internal ID'),('activity_name','Milestone'),('wbs_path','WBS'),('imported_early_finish','Imported Finish'),('evidence_class','Evidence'),('suitable_for_calibration','Calibration Suitability'),('suitability_diagnostics','Diagnostics')])
        async def run():
            self.analysis=None;self.analysis_version=None;analysis_panel.clear()
            def work():
                result=self.backend().anchor_analysis(self.state.version_id,self.backend().anchor_selection(anchor.value,mode.value,finish.value,activity_code=code.value))
                return result,self.backend().analysis_rows(result)
            loaded=await self.fetch(work,label='Running selected-anchor CPM')
            if loaded is None:return
            result,rows=loaded
            self.analysis=result;self.analysis_version=self.state.version_id;analysis_panel.clear()
            with analysis_panel:
                self.values(record(result.anchor));self.values(result.summary);self.badge(result.anchor.contractual_authority_status)
                self.local_records(result.diagnostics,'CPM diagnostics')
                cols=[('activity_code','Activity ID'),('activity_name','Name'),('wbs_path','WBS'),('status','Status'),('activity_type','Activity Type')]
                for name,title in [('early_start','ES'),('early_finish','EF'),('late_start','LS'),('late_finish','LF'),('total_float_hours','TF'),('free_float_hours','FF')]:cols.extend([('imported_'+name,'Imported '+title),('calculated_'+name,'Calculated '+title)])
                cols.extend([('early_start_variance_hours','ES variance (elapsed h)'),('early_finish_variance_hours','EF variance (elapsed h)'),('total_float_variance_hours','TF variance (h)'),('late_start_variance_hours','LS variance (elapsed h)'),('late_finish_variance_hours','LF variance (elapsed h)'),('free_float_variance_hours','FF variance (h)'),('es_availability','ES Availability'),('ef_availability','EF Availability'),('ls_availability','LS Availability'),('lf_availability','LF Availability'),('total_float_availability','TF Availability'),('free_float_availability','FF Availability'),('availability','Disposition'),('diagnostics','Diagnostics')])
                self.table('cpm-activities',lambda q:page_rows(rows,q),columns=cols,filters=True,pick=self.investigate)
                self.local_records(result.activity_dispositions,'Directional activity availability');self.local_records(result.relationship_dispositions,'Directional relationship availability')
                ui.label('Application Calculated Controlling Paths').classes('text-xl font-semibold');self.note('Connected application-calculated controlling paths | not P6 Longest Path.')
                s=result.cpm_result.schedule;by_id={r.activity_id:r for r in result.cpm_result.activity_results}
                for path in result.cpm_result.critical_paths:
                    with ui.expansion(path.path_id+' | rank '+str(path.rank)).classes('sa-card w-full'):
                        self.values({k:v for k,v in record(path).items() if k not in {'relationships','activity_ids','activity_codes','diagnostics','constraint_causes'}})
                        path_rows=[]
                        for index,key in enumerate(path.activity_ids):
                            r=by_id[key];raw=s.activities[key];rel=path.relationships[index-1] if index else None
                            path_rows.append(dict(sequence=index+1,activity_id=key,activity_code=r.activity_code,name=r.activity_name,wbs_path=self.backend().wbs(s,raw),duration_hours=r.effective_duration_hours,
                                relationship_type=rel.relationship_type if rel else None,lag_hours=rel.lag_hours if rel else None,ES=r.calculated_early_start,EF=r.calculated_early_finish,LS=r.calculated_late_start,LF=r.calculated_late_finish,TF=r.calculated_total_float_hours))
                        self.table('path-'+path.path_id,lambda q,data=path_rows:page_rows(data,q),pick=self.investigate)
                self.local_records(result.blocked_boundaries,'Blocked path boundaries')
        with ui.row():
            ui.button('Browse candidate anchors',icon='search',on_click=candidates).props('outline no-caps')
            ui.button('Run CPM',icon='account_tree',on_click=run).props('no-caps')
        candidates_panel=ui.column().classes('w-full');analysis_panel=ui.column().classes('w-full gap-4')
        self.empty_panel(analysis_panel,'No CPM analysis run. Select an explicit Analysis Anchor and choose Run CPM.')
        self.note('CPT and CPLI are assessed separately on the DCMA screen. Selected-anchor CPM does not imply they are evaluable.')
    def diagnostics_page(self):
        self.note('Import diagnostics and forward/selected-anchor availability. Expected Finish, LOE and progress limitations remain explicit.')
        self.table('diagnostics',lambda q:page_rows(self.backend().diagnostics(self.state.version_id,self.analysis if self.analysis_version==self.state.version_id else None),q),filters=True,
            columns=[('severity','Severity'),('category','Category'),('code','Code'),('activity_id','Internal Activity ID'),('message','Message'),('table','Source Table'),('field_name','Field')])
    def reports_page(self):
        self.comparison_controls();use=ui.checkbox('Include explicitly selected Analysis Anchor',value=False)
        self.note('Forensic report uses the existing report builder and Excel renderer. Unavailable calculated values remain unavailable.')
        self.values(dict(completion_authority_status='NOT_ESTABLISHED',selected_analysis_anchor=self.state.analysis_anchor_id))
        def selection():return self.backend().anchor_selection(self.state.analysis_anchor_id,self.state.analysis_mode,self.state.required_finish,activity_code=self.state.analysis_anchor_code) if use.value else None
        async def preview():
            result=await self.fetch(lambda:self.backend().report(self.state.source_version_id,self.state.target_version_id,selection()),label='Preparing report metadata')
            if result:
                metadata.clear()
                with metadata:self.values(record(result.metadata));self.local_records([dict(section=s.title,count=s.count,availability=s.availability,message=s.message,diagnostics=s.diagnostics) for s in result.sections],'Report sections')
        async def export():
            result=await self.fetch(lambda:self.backend().export(self.state.source_version_id,self.state.target_version_id,selection()),label='Rendering Excel workbook')
            if result:ui.download(result,filename=FILENAME,media_type=MEDIA_TYPE)
        with ui.row():
            ui.button('Preview report metadata',icon='description',on_click=preview).props('outline no-caps')
            ui.button('Export forensic Excel',icon='download',on_click=export).props('no-caps')
        metadata=ui.column().classes('w-full gap-4')
        self.empty_panel(metadata,'No report prepared. Select versions and preview report metadata before export.')
