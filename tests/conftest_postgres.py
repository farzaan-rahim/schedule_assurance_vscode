# Helpers imported by the PostgreSQL tests; never use a production/default DB URL.
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import os,re
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema,DropSchema
from app.persistence.services.storage import LocalSourceStorage
from app.persistence.services.imports import PersistedScheduleImportService,PersistenceCatalogService

ROOT=Path(__file__).resolve().parents[1]


@dataclass
class PostgresHarness:
    engine: object
    sessions: object
    storage: object
    schema: str

    @property
    def importer(self):return PersistedScheduleImportService(self.sessions,self.storage)
    @property
    def catalog(self):return PersistenceCatalogService(self.sessions)
    def migration(self,direction,target):
        config=Config(str(ROOT/'alembic.ini'))
        with self.engine.begin() as conn:
            config.attributes['connection']=conn
            getattr(command,direction)(config,target)


@pytest.fixture
def pg(tmp_path):
    url=os.environ.get('POSTGRES_TEST_DATABASE_URL')
    if not url:pytest.skip('Set POSTGRES_TEST_DATABASE_URL to an explicitly disposable PostgreSQL database.')
    parsed=make_url(url)
    if parsed.get_backend_name()!='postgresql':pytest.fail('postgres tests require actual PostgreSQL, not SQLite.')
    parsed=parsed.set(drivername='postgresql+psycopg');schema='sa_test_'+uuid4().hex
    assert re.fullmatch(r'sa_test_[0-9a-f]{32}',schema)
    admin=create_engine(parsed,connect_args={'prepare_threshold':None})
    with admin.begin() as c:c.execute(CreateSchema(schema))
    engine=create_engine(parsed,connect_args={'options':'-csearch_path='+schema,'prepare_threshold':None},pool_pre_ping=True)
    harness=PostgresHarness(engine,sessionmaker(engine,expire_on_commit=False),LocalSourceStorage(tmp_path/'sources'),schema)
    try:
        harness.migration('upgrade','head')
        yield harness
    finally:
        engine.dispose()
        with admin.begin() as c:c.execute(DropSchema(schema,cascade=True))
        admin.dispose()
