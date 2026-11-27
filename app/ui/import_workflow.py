"""Two-stage, session-memory XER preflight and explicit persisted import."""
from dataclasses import dataclass
from nicegui import ui
from app.importers.preflight import XERPreflight


@dataclass
class ImportDraft:
    content: bytes | None=None
    filename: str=''
    preview: XERPreflight | None=None
    source_project_id: str | None=None
    label: str=''
    version_type: str='UPDATE'
    matching_application_project: object=None

    @property
    def project(self):
        return self.preview.select(self.source_project_id) if self.preview and self.source_project_id else None

    def clear_file(self):
        self.content=None;self.filename='';self.preview=None;self.source_project_id=None;self.matching_application_project=None


class XERImportPanel:
    def __init__(self,controller):
        self.ctrl=controller;self.draft=controller.import_draft;self.processing=False;self.existing=self.draft.matching_application_project

    def build(self):
        with ui.expansion('Import an XER schedule',icon='upload_file',value=not self.ctrl.versions or bool(self.draft.content)).classes('sa-card w-full'):
            ui.label('Inspect the XER first, then confirm the source project and import. Preflight saves no project, version or source file.').classes('sa-subtitle')
            self.label=ui.input('Schedule Version label',value=self.draft.label,on_change=self.label_changed).props('outlined').classes('w-80')
            ui.select(['BASELINE','UPDATE','CURRENT','SNAPSHOT'],value=self.draft.version_type,label='Version type',
                on_change=lambda e:setattr(self.draft,'version_type',e.value)).props('outlined').classes('w-64')
            self.progress=ui.label('Preflight ready' if self.draft.preview else 'Select an XER for preflight').props('role=status aria-live=polite')
            self.upload=ui.upload(label='Select .xer for preflight',on_upload=self.inspect,auto_upload=True,max_files=1,
                max_file_size=self.ctrl.backend().services.maximum_upload_bytes,on_rejected=self.reject).props('accept=.xer').classes('w-full')
            self.upload.on('removed',self.removed)
            self.source_select=ui.select({},label='Source P6 project',on_change=self.source_changed).props('outlined').classes('w-full')
            self.details=ui.column().classes('w-full gap-3')
            self.import_button=ui.button('Import confirmed XER',icon='save',on_click=self.final_import).props('no-caps').mark('confirm-xer-import')
            self.render_preview()
        return self

    def label_changed(self,e):
        self.draft.label=e.value or '';self.update_allowed()

    def selected_application_project(self):
        return next((p for p in self.ctrl.projects if p.id==self.ctrl.state.project_id),None)

    def update_allowed(self):
        p=self.draft.project
        allowed=bool(not self.processing and not self.ctrl.state.busy and self.draft.content and p and p.importable
            and p.matches(self.selected_application_project()) and self.draft.label.strip())
        self.import_button.set_enabled(allowed)

    def set_processing(self,value):
        self.processing=value;self.upload.set_enabled(not value);self.source_select.set_enabled(not value);self.update_allowed()

    def removed(self):
        if self.processing:return
        self.draft.clear_file();self.existing=None;self.progress.set_text('Select an XER for preflight');self.render_preview()

    def reject(self):
        self.removed();self.progress.set_text('Choose one .xer within the configured upload limit.')

    async def inspect(self,e):
        if self.processing or self.ctrl.state.busy:return
        self.draft.clear_file();self.existing=None;self.render_preview();self.set_processing(True)
        self.progress.set_text('Reading XER project metadata')
        try:
            content=bytearray();maximum=self.ctrl.backend().services.maximum_upload_bytes
            async for chunk in e.file.iterate():
                if len(content)+len(chunk)>maximum:
                    self.progress.set_text('Upload exceeds the configured size limit.');return
                content.extend(chunk)
            preview=await self.ctrl.fetch(lambda:self.ctrl.backend().preflight_xer(bytes(content),e.file.name),label='Inspecting XER projects')
            if preview is None:self.progress.set_text('Preflight failed | see diagnostics above');return
            self.draft.content=bytes(content);self.draft.filename=e.file.name;self.draft.preview=preview
            self.draft.source_project_id=preview.default_project_id
            await self.load_existing()
            self.progress.set_text('Preflight complete | nothing persisted')
        finally:
            self.set_processing(False);self.render_preview()

    async def load_existing(self):
        p=self.draft.project;self.existing=None
        if p and p.project_code:
            self.existing=await self.ctrl.fetch(lambda:self.ctrl.backend().matching_project(p),label='Finding matching application project')
        self.draft.matching_application_project=self.existing

    async def source_changed(self,e):
        if self.processing or (e.value or None)==self.draft.source_project_id:return
        self.draft.source_project_id=e.value or None
        self.set_processing(True)
        try:await self.load_existing()
        finally:self.set_processing(False);self.render_preview()

    def render_preview(self):
        self.details.clear();preview=self.draft.preview
        self.source_select.options={p.source_project_id:f'{p.project_code} | {p.project_name} | {p.activity_count} activities' for p in preview.projects} if preview else {}
        self.source_select.value=self.draft.source_project_id;self.source_select.update()
        self.source_select.set_visibility(bool(preview))
        with self.details:
            if preview:
                ui.label('Detected P6 projects').classes('text-lg')
                ui.table(columns=[dict(name=k,label=t,field=k,align='left') for k,t in [('project_code','P6 Project Code'),('project_name','P6 Project Name'),('source_project_id','Source P6 Project ID'),('activity_count','Activities')]],
                    rows=[dict(project_code=p.project_code,project_name=p.project_name,source_project_id=p.source_project_id,activity_count=p.activity_count) for p in preview.projects],row_key='source_project_id',pagination=10).classes('sa-table')
                p=self.draft.project
                if p is None:
                    self.ctrl.note('Multiple source projects detected. Choose a source P6 project explicitly; no dominant project is selected.')
                else:
                    self.ctrl.values({'P6 Project Code':p.project_code,'P6 Project Name':p.project_name,'Source P6 Project ID':p.source_project_id,
                        'Data Date':p.data_date,'Activity count':p.activity_count,'Relationship count':p.relationship_count,'WBS count':p.wbs_count})
                    selected=self.selected_application_project()
                    if not p.importable:self.ctrl.note('This source project has no importable activities or project code.')
                    if p.matches(selected):
                        ui.label('Project match confirmed').classes('sa-note').props('role=status')
                    else:
                        ui.label('Selected application project code: '+(selected.project_code if selected else 'None selected')).classes('sa-note')
                        ui.label('XER project code: '+p.project_code).classes('sa-note')
                        ui.label('Import is disabled until the selected application project matches the XER project code.')
                        ui.button('Choose matching project',on_click=self.choose_matching).props('outline no-caps')
                        if self.existing is not None:
                            ui.label('A project with this exact code already exists.')
                            ui.button('Use existing project',on_click=lambda:self.activate(self.existing)).props('no-caps')
                        else:
                            ui.input('Project Code from XER',value=p.project_code).props('outlined readonly').classes('w-full')
                            self.project_name=ui.input('Application Project Name',value=p.project_name).props('outlined').classes('w-full')
                            ui.button('Create project from XER',on_click=self.create_project).props('no-caps').set_enabled(p.importable)
        self.update_allowed()

    async def activate(self,project):
        if project is None:return
        if not any(p.id==project.id for p in self.ctrl.projects):self.ctrl.projects.append(project)
        await self.ctrl.choose_project(project.id)

    async def choose_matching(self):
        if self.processing or self.ctrl.state.busy:return
        await self.load_existing()
        if self.existing is not None:await self.activate(self.existing)
        else:await self.ctrl.navigate('Projects')

    async def create_project(self):
        if self.processing or self.ctrl.state.busy:return
        p=self.draft.project
        if p is None:return
        self.set_processing(True)
        try:
            project=await self.ctrl.fetch(lambda:self.ctrl.backend().create_project_from_xer(p,self.project_name.value),label='Creating project from XER')
        finally:self.set_processing(False)
        if project is not None:await self.activate(project)

    async def final_import(self):
        if self.processing or self.ctrl.state.busy:return
        self.update_allowed()
        if not self.import_button.enabled:return
        self.set_processing(True);self.progress.set_text('Importing | parsing, mapping and persistence')
        project_id=self.ctrl.state.project_id
        try:
            result=await self.ctrl.fetch(lambda:self.ctrl.backend().import_xer(project_id,self.draft.content,self.draft.filename,self.draft.label,self.draft.version_type,
                source_project_id=self.draft.source_project_id),label='Importing confirmed XER')
            self.progress.set_text('Complete' if result else 'Import failed | see diagnostics above')
        finally:self.set_processing(False)
        if result:
            self.draft.clear_file();self.ctrl.state.version_id=None;await self.ctrl.choose_project(project_id)
