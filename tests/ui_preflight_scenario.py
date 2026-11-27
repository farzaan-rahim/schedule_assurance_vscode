"""Proprietary-free NiceGUI preflight event scenario, isolated from other clients."""
import asyncio
from nicegui import ui
from nicegui.testing.user_simulation import user_simulation
from nicegui.elements.upload_files import SmallFileUpload
from app.ui.pages import PlannerUI
from app.runtime import RuntimeStatus
from tests.ui_helpers import memory_service
from tests.test_analysis_anchors import controlled_xer
from tests.test_xer_preflight import multi_xer


async def settle(ctrl):
    for _ in range(300):
        if not ctrl.state.busy and not ctrl.import_panel.processing:break
        await asyncio.sleep(.01)
    await asyncio.sleep(.05)


async def scenario():
    controllers=[];service=memory_service()
    def root():controllers.append(PlannerUI(service,runtime_probe=lambda:RuntimeStatus('READY','Ready',True,True,True)).build())
    async with user_simulation(root) as user:
        await user.open('/')
        await user.should_see('Open Projects')
        ctrl=controllers[0]
        await ctrl.navigate('Schedule Versions')
        await user.should_see('Select .xer for preflight')
        assert ctrl.state.project_id is None
        initial_versions=len(service.catalog.versions)
        await ctrl.import_panel.upload.handle_uploads([SmallFileUpload('single.xer','application/octet-stream',controlled_xer())])
        await user.should_see('Use existing project')
        assert len(service.catalog.versions)==initial_versions and len(service.catalog.projects)==1
        assert not ctrl.import_panel.import_button.enabled
        user.find(kind=ui.button,content='Use existing project').click()
        await user.should_see('Project match confirmed');await settle(ctrl)
        user.find('Schedule Version label').type('Preflight update')
        await settle(ctrl)
        assert ctrl.import_panel.import_button.enabled

        # Switch to an unrelated application project; preserve the staged source.
        unrelated=service.catalog.create_project('TEST','Unrelated test project')
        ctrl.projects.append(unrelated);await ctrl.choose_project(unrelated.id)
        await user.should_see('Selected application project code: TEST')
        await user.should_see('XER project code: P1')
        assert not ctrl.import_panel.import_button.enabled
        await ctrl.import_panel.final_import()  # Button/handler guard blocks premature persistence.
        assert len(service.catalog.versions)==initial_versions
        user.find(kind=ui.button,content='Choose matching project').click()
        await user.should_see('Project match confirmed');await settle(ctrl)
        assert ctrl.state.project_id==service.catalog.project.id

        # Every project is visible; choosing the smaller project is deliberate.
        await ctrl.import_panel.upload.handle_uploads([SmallFileUpload('multi.xer','application/octet-stream',multi_xer())])
        await user.should_see('Multiple source projects detected.')
        assert ctrl.import_draft.source_project_id is None and not ctrl.import_panel.import_button.enabled
        assert len(service.catalog.projects)==2 and len(service.catalog.versions)==initial_versions
        ctrl.import_panel.source_select.set_value('20')
        await user.should_see('Create project from XER');await settle(ctrl)
        code=next(iter(user.find('Project Code from XER').elements))
        assert code.value=='BETA' and code._props['readonly']
        name=next(iter(user.find('Application Project Name').elements))
        assert name.value=='Beta project'
        name.set_value('Planner editable project name')
        user.find(kind=ui.button,content='Create project from XER').click()
        await user.should_see('Project match confirmed');await settle(ctrl)
        project=service.catalog.get_project(ctrl.state.project_id)
        assert project.project_code=='BETA' and project.project_name=='Planner editable project name'
        assert len(service.catalog.projects)==3 and len(service.catalog.versions)==initial_versions
        user.find(marker='confirm-xer-import').click()
        for _ in range(300):
            if len(service.catalog.versions)>initial_versions:break
            await asyncio.sleep(.01)
        await settle(ctrl)
        assert len(service.catalog.versions)==initial_versions+1
        imported=service.catalog.schedules[ctrl.state.version_id]
        assert imported.project.project_code=='BETA' and list(imported.activities)==['3']

        # A replacement file must invalidate the old approval, even on error.
        await ctrl.import_panel.upload.handle_uploads([SmallFileUpload('single.xer','application/octet-stream',controlled_xer())])
        await user.should_see('XER project code: P1');await settle(ctrl)
        assert ctrl.import_draft.preview is not None
        await ctrl.import_panel.upload.handle_uploads([SmallFileUpload('invalid.xer','application/octet-stream',b'not an XER')])
        await user.should_see('Preflight failed');await settle(ctrl)
        assert ctrl.import_draft.content is None and not ctrl.import_panel.import_button.enabled
        assert len(service.catalog.versions)==initial_versions+1
    print('PREFLIGHT_UI_PASSED')


if __name__=='__main__':asyncio.run(scenario())
