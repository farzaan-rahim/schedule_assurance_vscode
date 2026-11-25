from alembic import context
from app.persistence.base import Base
from app.persistence import models  # register independent ORM schema
from app.persistence.settings import PersistenceSettings
from app.persistence.session import engine_for_url
from app.persistence.exceptions import PersistenceNotConfigured

config=context.config
connection=config.attributes.get('connection')


def database_url():
    explicit=config.get_main_option('sqlalchemy.url')
    if explicit:return explicit
    settings=PersistenceSettings()
    if settings.database_url is None:raise PersistenceNotConfigured('Set SA_DATABASE_URL for Alembic.')
    return settings.database_url.get_secret_value()


def migrate(conn):
    context.configure(connection=conn,target_metadata=Base.metadata,compare_type=True)
    with context.begin_transaction():context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url(),target_metadata=Base.metadata,literal_binds=True,dialect_opts={'paramstyle':'named'})
    with context.begin_transaction():context.run_migrations()
elif connection is not None:
    migrate(connection)
else:
    with engine_for_url(database_url()).connect() as conn:migrate(conn)
