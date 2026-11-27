from fastapi.responses import RedirectResponse
from nicegui import ui
from app.ui.pages import PlannerUI


def install_ui(app):
    @ui.page('/')
    async def workspace():
        PlannerUI().build()
    @app.get('/',include_in_schema=False)
    def homepage():return RedirectResponse('/ui/')
    ui.run_with(app,mount_path='/ui',title='Schedule Assurance',show_welcome_message=False,reconnect_timeout=15)
