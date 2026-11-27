"""Isolated NiceGUI event/client scenario, called by pytest in a subprocess."""
import asyncio
from nicegui.testing.user_simulation import user_simulation
from nicegui import ui
from nicegui.elements.upload_files import SmallFileUpload
from tests.test_analysis_anchors import controlled_xer
from app.ui.pages import PlannerUI
from app.runtime import RuntimeStatus
from tests.ui_helpers import memory_service

async def scenario():
    controllers=[];service=memory_service()
    def root():controllers.append(PlannerUI(service,runtime_probe=lambda:RuntimeStatus('READY','Controlled runtime ready',True,True,True)).build())
    async with user_simulation(root) as user:
        await user.open('/')
        await user.should_see('Open Projects')
        await asyncio.sleep(.2)
        ctrl=controllers[0]
        ctrl.project_select.set_value(str(ctrl.service.catalog.project.id))
        for _ in range(300):
            if ctrl.state.version_id is not None and not ctrl.state.busy:break
            await asyncio.sleep(.01)
        assert ctrl.state.project_id==ctrl.service.catalog.project.id and ctrl.state.version_id is not None
        await user.should_see('Controlled UI Project')
        await ctrl.navigate('Schedule Health')
        user.find('Analyze Health').click()
        await user.should_see('Generic health score')
        await asyncio.sleep(.2)
        await ctrl.navigate('DCMA');user.find('Run DCMA').click()
        await user.should_see('Critical Path Test')
        await user.should_see('Critical Path Length Index')
        await asyncio.sleep(.5)
        await ctrl.navigate('CPM / Paths')
        await user.should_see('Analysis Anchor does not establish contractual completion authority. No milestone is selected automatically.')
        assert ctrl.state.analysis_anchor_id is None
        user.find('Analysis Anchor internal ID').type('5')
        user.find('Run CPM').click()
        await user.should_see('Application Calculated Controlling Paths')
        await asyncio.sleep(.5)
        assert ctrl.analysis is not None
        await ctrl.navigate('Change Analysis')
        ctrl.state.source_version_id=ctrl.service.catalog.versions[0].id
        user.find('Source / Baseline Version').elements.pop().set_value(str(ctrl.state.source_version_id))
        user.find('Run comparison').click()
        await user.should_see('Change section')
        await asyncio.sleep(.3)
        await ctrl.navigate('Reports');user.find('Preview report metadata').click()
        await user.should_see('Report sections')
        await asyncio.sleep(.2)
        download=asyncio.create_task(user.download.next(timeout=5))
        user.find('Export forensic Excel').click()
        response=await download
        assert response.content[:2]==b'PK'
        await asyncio.sleep(.2)
        await ctrl.investigate({'activity_id':'0'})
        await user.should_see('Activity investigation')
        await user.should_see('Imported P6')
        await user.should_see('Application Calculated')
        user.find(kind=ui.button,content='Close').click()
        await asyncio.sleep(.1)
        await ctrl.navigate('Milestones');user.find('View Milestones').click()
        await user.should_see('Total Milestones')
        await asyncio.sleep(.3)
        await ctrl.navigate('Diagnostics')
        await user.should_see('Category')
        await asyncio.sleep(.2)
        await ctrl.navigate('Schedule Versions')
        upload=next(iter(user.find(ui.upload).elements))
        await upload.handle_uploads([SmallFileUpload('test.xer','application/octet-stream',controlled_xer())])
        await user.should_see('Project match confirmed')
        assert not ctrl.import_panel.import_button.enabled
        user.find('Schedule Version label').type('Imported through UI')
        await upload.handle_uploads([SmallFileUpload('bad.xer','application/octet-stream',b'not a schedule')])
        await user.should_see('Preflight failed')
        await asyncio.sleep(.3)
        await user.should_see('Application error')
        await upload.handle_uploads([SmallFileUpload('new.xer','application/octet-stream',controlled_xer())])
        await user.should_see('Project match confirmed')
        user.find(marker='confirm-xer-import').click()
        await asyncio.sleep(.5)
        assert ctrl.service.catalog.get_version(ctrl.state.version_id).label=='Imported through UI'
        await user.should_not_see('Application error')
        user.find(kind=ui.button,content='Projects').click()
        await user.should_see('Project directory')
        await asyncio.sleep(.2)
        user.find(marker='table-projects').trigger('request',{'pagination':{'page':1,'rowsPerPage':100,'sortBy':'project_code','descending':True}})
        await asyncio.sleep(.2)
        assert ctrl.state.query('projects').limit==100 and ctrl.state.query('projects').descending
        user.find('Activity ID / name / text').type('NO_MATCH')
        user.find('Apply filters').click()
        await asyncio.sleep(.2)
        assert not next(iter(user.find(marker='table-projects').elements)).rows
        # Re-select through the server-paged directory, including UUID decoding.
        next(iter(user.find('Activity ID / name / text').elements)).set_value('')
        user.find('Apply filters').click()
        await asyncio.sleep(.2)
        directory=next(iter(user.find(marker='table-projects').elements))
        user.find(marker='table-projects').trigger('selection',{'rows':[directory.rows[0]],'added':True})
        await asyncio.sleep(.3)
        assert ctrl.state.project_id==service.catalog.project.id
        # An application/server failure remains visible, not an empty-success state.
        from fastapi import HTTPException
        def unavailable():raise HTTPException(503,'Controlled database unavailable')
        await ctrl.fetch(unavailable,label='Testing server error')
        await user.should_see('Controlled database unavailable')
        current_version=ctrl.state.version_id;saved_query=ctrl.state.query('projects')
        await user.open('/')
        for _ in range(300):
            if len(controllers)>1 and controllers[-1].state.version_id==current_version and not controllers[-1].state.busy:break
            await asyncio.sleep(.01)
        assert controllers[-1].state.version_id==current_version
        assert controllers[-1].state.query('projects')==saved_query
        print('UI_SCENARIO_PASSED')

if __name__=='__main__':asyncio.run(scenario())
