from pathlib import Path
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


PROJECT_ROOT=Path(__file__).resolve().parents[2]


class PersistenceSettings(BaseSettings):
    model_config=SettingsConfigDict(env_prefix='SA_',env_file=PROJECT_ROOT/'.env',extra='ignore')
    database_url: SecretStr | None=None
    storage_root: Path=Path('var/source-files')
    maximum_upload_bytes: int=100*1024*1024

    @field_validator('database_url')
    @classmethod
    def postgres_only(cls,value):
        if value is not None:
            try:
                url=make_url(value.get_secret_value())
            except ArgumentError as exc:
                raise ValueError('Use a valid PostgreSQL connection URL.') from exc
            if url.drivername not in {'postgresql','postgresql+psycopg'}:
                raise ValueError('Use a PostgreSQL URL with psycopg 3.')
        return value

    @field_validator('maximum_upload_bytes')
    @classmethod
    def positive_limit(cls,value):
        if value<1:raise ValueError('Upload limit must be positive.')
        return value
