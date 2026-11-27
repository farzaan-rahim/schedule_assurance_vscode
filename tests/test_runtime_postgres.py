import pytest
from sqlalchemy import text
from tests.conftest_postgres import pg
from app.runtime import inspect_runtime
from app.persistence.settings import PersistenceSettings

pytestmark=pytest.mark.postgres


def check(pg,**kwargs):
    settings=PersistenceSettings(database_url='postgresql://unused/test',_env_file=None)
    return inspect_runtime(settings,engine_factory=lambda *a,**k:pg.engine,**kwargs)


def test_current_migrations_are_ready_and_read_only(pg):
    before=pg.engine.connect()
    before.close()
    result=check(pg)
    assert result.ready and result.database_configured and result.database_reachable and result.migrations_current
    assert 'postgresql://' not in str(result.payload())


def test_empty_schema_requires_migration_and_is_not_database_unavailable(pg):
    pg.migration('downgrade','base')
    result=check(pg)
    assert result.status=='MIGRATIONS_REQUIRED' and result.database_reachable is True
    assert result.migrations_current is False
    # Diagnostics did not run an upgrade or create application tables.
    with pg.engine.connect() as c:assert c.scalar(text("SELECT to_regclass('activities')")) is None


def test_revision_mismatch_is_distinct_from_connection_failure(pg):
    result=check(pg,expected_heads=('a-deliberately-different-revision',))
    assert result.status=='MIGRATIONS_REQUIRED' and result.database_reachable is True



def test_migration_inspection_error_preserves_reachability(pg,monkeypatch):
    from app import runtime
    def unavailable(*args,**kwargs):raise RuntimeError('Controlled schema inspection failure')
    monkeypatch.setattr(runtime.MigrationContext,'configure',unavailable)
    result=check(pg)
    assert result.status=='MIGRATIONS_UNKNOWN' and result.database_reachable is True
    assert result.migrations_current is None
