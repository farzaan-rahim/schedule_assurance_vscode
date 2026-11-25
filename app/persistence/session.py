from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.persistence.exceptions import PersistenceNotConfigured
from app.persistence.settings import PersistenceSettings


@lru_cache(maxsize=8)
def engine_for_url(url):
    parsed=make_url(url)
    if parsed.drivername not in {'postgresql','postgresql+psycopg'}:
        raise ValueError('Persistence requires PostgreSQL/psycopg 3.')
    return create_engine(parsed.set(drivername='postgresql+psycopg'),pool_pre_ping=True,
                         connect_args={'prepare_threshold':None})


def session_factory(settings=None):
    settings=settings or PersistenceSettings()
    if settings.database_url is None:raise PersistenceNotConfigured('Set SA_DATABASE_URL to enable persistence.')
    return sessionmaker(engine_for_url(settings.database_url.get_secret_value()),expire_on_commit=False)
