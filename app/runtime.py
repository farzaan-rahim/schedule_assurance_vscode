"""Read-only, password-safe local readiness diagnostics. No schema changes."""
import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass,field,asdict
from datetime import datetime,timezone
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse,RedirectResponse
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from app.persistence.settings import PersistenceSettings,PROJECT_ROOT


@dataclass(frozen=True)
class RuntimeStatus:
    status: str
    message: str
    database_configured: bool | None
    database_reachable: bool | None=None
    migrations_current: bool | None=None
    ui_available: bool=True
    setup_url: str='/setup'
    checked_at: datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    @property
    def ready(self):return self.status=='READY'
    def payload(self):return jsonable_encoder(dict(asdict(self),ready=self.ready))


def inspect_runtime(settings=None,*,engine_factory=None,expected_heads=None):
    """A short diagnostic connection, not the application's cached engine.

    Exception text and connection URLs never appear in status messages/logs.
    SELECT and Alembic revision inspection only; migrations are never run here.
    """
    try:settings=settings or PersistenceSettings()
    except Exception:
        return RuntimeStatus('INVALID_CONFIGURATION','Database configuration is invalid. Check SA_DATABASE_URL in the repository .env; see Local setup.',False)
    if settings.database_url is None:
        return RuntimeStatus('UNCONFIGURED','PostgreSQL is not configured. Add SA_DATABASE_URL to the repository .env, then recheck setup.',False)
    engine=None
    try:
        factory=engine_factory or create_engine
        url=make_url(settings.database_url.get_secret_value()).set(drivername='postgresql+psycopg')
        engine=factory(url,poolclass=NullPool,hide_parameters=True,
            connect_args={'prepare_threshold':None,'connect_timeout':3})
        with engine.connect() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '3000ms'"))
            connection.execute(text('SELECT 1'))
            try:
                current=set(MigrationContext.configure(connection).get_current_heads())
                expected=set(expected_heads if expected_heads is not None else ScriptDirectory.from_config(Config(str(PROJECT_ROOT/'alembic.ini'))).get_heads())
            except Exception:
                return RuntimeStatus('MIGRATIONS_UNKNOWN','Database reachable; migration status could not be verified. Check database permissions and run alembic current.',True,True,None)
            if current!=expected or not current:
                return RuntimeStatus('MIGRATIONS_REQUIRED','Database reachable; migrations are not current. From the repository root run: alembic upgrade head.',True,True,False)
            return RuntimeStatus('READY','PostgreSQL is reachable and migrations are current.',True,True,True)
    except Exception:
        return RuntimeStatus('DATABASE_UNAVAILABLE','Database is configured but unavailable. Start PostgreSQL and check credentials, host and port; see Local setup.',True,False,None)
    finally:
        if engine is not None:
            try:engine.dispose()
            except Exception:logging.getLogger(__name__).warning('Runtime diagnostic connection cleanup could not complete.')


SETUP_HTML=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Schedule Assurance - Local setup</title>
<style>body{font:16px/1.6 Segoe UI,Arial,sans-serif;background:#f3f6fa;color:#172c45;margin:auto;padding:32px;max-width:980px}main{background:white;padding:32px;border-radius:12px;border:1px solid #dce4ee}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f8;padding:16px;border-radius:6px}a{color:#225f9b}a:focus-visible{outline:3px solid #2869a8;outline-offset:4px}</style></head>
<body><main><a href="/ui/">Return to workspace</a><h1>Local runtime setup</h1><p>The UI can run without PostgreSQL. Projects, imports and stored analyses require a configured, reachable database with current migrations.</p>
<ol><li>Open a terminal in the repository root and activate the virtual environment:<pre>.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt</pre></li>
<li>Configure the repository <code>.env</code> using <code>.env.example</code>. Do not overwrite existing credentials. The Compose example uses port 5433; a native PostgreSQL installation commonly uses 5432. Use the actual database, role and port.</li>
<li>Start local PostgreSQL. With Docker Desktop running and the Compose variables configured:<pre>docker compose up -d postgres</pre>Alternatively start your installed PostgreSQL service and create/select the database and role.</li>
<li>Apply migrations explicitly:<pre>alembic upgrade head
alembic current</pre></li>
<li>Start the application:<pre>python -m uvicorn app.main:app --reload</pre></li>
<li>Open <a href="/ui/">the workspace</a>, then Recheck setup. Full startup and the controlled planner UAT workflow are documented in README.md.</li></ol>
<p><a href="/docs">API documentation</a> | <a href="/redoc">ReDoc</a> | <a href="/openapi.json">OpenAPI JSON</a> | <a href="/api/runtime?refresh=true">Runtime diagnostics</a></p>
<p>No connection string, password or automatic schema changes are exposed by runtime diagnostics.</p></main></body></html>"""


def install_runtime(app):
    original=app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(application):
        state=await asyncio.to_thread(inspect_runtime)
        application.state.runtime_status=state
        logger=logging.getLogger(__name__)
        if not logger.hasHandlers():
            handler=logging.StreamHandler();handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'));logger.addHandler(handler);logger.setLevel(logging.INFO)
        logger.info('Runtime: UI available; database configured=%s reachable=%s migrations_current=%s state=%s',
            state.database_configured,state.database_reachable,state.migrations_current,state.status)
        async with original(application) as context:yield context
    app.router.lifespan_context=lifespan
    @app.get('/api/runtime',tags=['System'])
    async def runtime_status(request:Request,refresh:bool=False):
        state=getattr(request.app.state,'runtime_status',None)
        if refresh or state is None:
            state=await asyncio.to_thread(inspect_runtime);request.app.state.runtime_status=state
        return state.payload()
    @app.get('/ui/docs',include_in_schema=False)
    async def legacy_docs():return RedirectResponse('/docs',status_code=307)
    @app.get('/setup',include_in_schema=False,response_class=HTMLResponse)
    async def local_setup():return HTMLResponse(SETUP_HTML)
