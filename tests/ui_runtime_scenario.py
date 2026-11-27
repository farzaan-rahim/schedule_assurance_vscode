"""Runtime presentation UAT: server-side NiceGUI events, not viewport claims."""
import asyncio,threading
from nicegui import ui
from nicegui.testing.user_simulation import user_simulation
from app.runtime import RuntimeStatus
from app.ui.pages import PlannerUI
from app.ui.state import NAVIGATION
from app.ui.presentation import page_rows
from tests.ui_helpers import memory_service

async def scenario():
    controllers=[];service=memory_service()
    status=[RuntimeStatus('UNCONFIGURED','PostgreSQL is not configured. Controlled setup instruction.',False)]
    def root():controllers.append(PlannerUI(service,runtime_probe=lambda:status[0]).build())
    async with user_simulation(root) as user:
        await user.open('/')
        for _ in range(300):
            if controllers[0].runtime_status is not None:break
            await asyncio.sleep(.01)
        ctrl=controllers[0]
        assert ctrl.task_label.text=='Setup required' and not ctrl.failed
        assert not ctrl.project_select.enabled and not ctrl.version_select.enabled
        links=[e for e in user.client.elements.values() if e.tag=='a']
        assert any(e._props.get('href')=='/docs' for e in links)
        assert all(not e._props.get('href','').startswith('/ui/docs') for e in links)
        for title,_ in NAVIGATION:
            user.find(kind=ui.button,content=title).click()
            await asyncio.sleep(.02)
            assert ctrl.state.page==title
            assert not ctrl.failed and ctrl.runtime_status.ui_available
        await user.should_not_see('Create project')
        ctrl.toggle_navigation();assert not ctrl.drawer.value and ctrl.menu_button._props['aria-expanded']=='false'
        ctrl.toggle_navigation();assert ctrl.drawer.value and ctrl.menu_button._props['aria-expanded']=='true'
        for state,label in [
            (RuntimeStatus('DATABASE_UNAVAILABLE','Configured database unavailable',True,False,None),'Database unavailable'),
            (RuntimeStatus('MIGRATIONS_REQUIRED','Run alembic upgrade head',True,True,False),'Migrations required')]:
            status[0]=state;await ctrl.recheck()
            assert ctrl.task_label.text==label and not ctrl.failed and not ctrl.project_select.enabled
        status[0]=RuntimeStatus('READY','Controlled database ready',True,True,True)
        await ctrl.recheck()
        assert ctrl.project_select.enabled and ctrl.state.project_id is None
        await ctrl.navigate('Schedule Health')
        await user.should_see('Select a project to view schedule health.')
        service.catalog.versions=[];service.catalog.schedules={}
        await ctrl.choose_project(service.catalog.project.id)
        await user.should_see('No Schedule Version selected.')
        await ctrl.navigate('Schedule Versions')
        await user.should_see('Schedule Version label')
        started=threading.Event();complete=threading.Event()
        def actual_work():started.set();complete.wait(timeout=5);return 'done'
        task=asyncio.create_task(ctrl.fetch(actual_work,label='Rendering Excel workbook'))
        for _ in range(100):
            if started.is_set():break
            await asyncio.sleep(.01)
        assert ctrl.spinner.visible and ctrl.task_label.text=='Rendering Excel workbook'
        assert not ctrl.project_select.enabled
        complete.set();assert await task=='done'
        rows=[dict(activity_id='UAT_LONG_ACTIVITY_ID_WITH_MULTIPLE_SEGMENTS_'+str(i),description='Long imported description '+('utility corridor handover '*25),
            wbs_path='ROOT > CORRIDOR > AREA > PACKAGE > STRUCTURES > HANDOVER',date='2026-01-05 08:00',duration_hours=10.5,
            total_float_hours=-2.25,availability='NOT_EVALUATED') for i in range(250)]
        ctrl.content.clear()
        with ctrl.content:ctrl.table('uat',lambda q:page_rows(rows,q),title='Synthetic presentation records',filters=True)
        await asyncio.sleep(.15)
        table=next(iter(user.find(marker='table-uat').elements))
        for size in (50,100,200):
            user.find(marker='table-uat').trigger('request',{'pagination':{'page':1,'rowsPerPage':size,'sortBy':'activity_id','descending':False}})
            await asyncio.sleep(.15)
            assert len(table.rows)==size and table.pagination['rowsNumber']==250
            assert table.rows[0]['total_float_hours']==-2.25 and table.rows[0]['availability']=='NOT_EVALUATED'
        assert table._props['tabindex']=='0' or table._props['tabindex']==0
        assert table._props['aria-label']=='Synthetic presentation records'
        print('RUNTIME_UI_SCENARIO_PASSED')

if __name__=='__main__':asyncio.run(scenario())
