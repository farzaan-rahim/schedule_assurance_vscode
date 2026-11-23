from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import model_validator
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
DEFAULT_CORS_ALLOWED_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173"
)


class DatabaseConfigurationError(RuntimeError):
    """Raised when required database configuration is missing."""


class ModelSettings(BaseSettings):
    ai_active_provider: str | None = Field(default=None, validation_alias="AI_ACTIVE_PROVIDER")
    ai_active_model: str | None = Field(default=None, validation_alias="AI_ACTIVE_MODEL")
    ai_allow_local_models: bool = Field(default=True, validation_alias="AI_ALLOW_LOCAL_MODELS")
    ai_local_model_roots: str = Field(default="..", validation_alias="AI_LOCAL_MODEL_ROOTS")
    ai_local_device: str = Field(default="cpu", validation_alias="AI_LOCAL_DEVICE")
    ai_local_min_free_memory_gb: float = Field(default=4.0, ge=1, validation_alias="AI_LOCAL_MIN_FREE_MEMORY_GB")
    ai_local_max_context: int = Field(default=4096, ge=512, le=131072, validation_alias="AI_LOCAL_MAX_CONTEXT")
    ai_provider: str | None = Field(
        default=None,
        validation_alias="AI_PROVIDER",
    )
    ai_model: str | None = Field(
        default=None,
        min_length=1,
        validation_alias="AI_MODEL",
    )
    ai_fallback_enabled: bool = Field(
        default=True,
        validation_alias="AI_FALLBACK_ENABLED",
    )
    ai_explanation_enabled: bool = Field(
        default=False,
        validation_alias="AI_EXPLANATION_ENABLED",
    )
    ai_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        le=3600,
        validation_alias="AI_TIMEOUT_SECONDS",
    )
    ai_request_timeout_seconds: float = Field(
        default=600,
        gt=0,
        le=3600,
        validation_alias="AI_REQUEST_TIMEOUT_SECONDS",
    )
    ai_tool_workflow_timeout_seconds: float = Field(
        default=900,
        gt=0,
        le=3600,
        validation_alias="AI_TOOL_WORKFLOW_TIMEOUT_SECONDS",
    )
    ai_max_empty_response_retries: int = Field(
        default=1,
        ge=0,
        le=2,
        validation_alias="AI_MAX_EMPTY_RESPONSE_RETRIES",
    )
    ai_max_tool_repair_attempts: int = Field(
        default=1,
        ge=0,
        le=2,
        validation_alias="AI_MAX_TOOL_REPAIR_ATTEMPTS",
    )
    ai_temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
        validation_alias="AI_TEMPERATURE",
    )
    ai_max_output_tokens: int | None = Field(
        default=None,
        ge=16,
        le=8192,
        validation_alias="AI_MAX_OUTPUT_TOKENS",
    )
    ai_thinking_enabled: bool | None = Field(
        default=None,
        validation_alias="AI_THINKING_ENABLED",
    )
    ai_debug_timing: bool | None = Field(
        default=None,
        validation_alias="AI_DEBUG_TIMING",
    )
    planning_agent_model_provider: str = Field(
        default="ollama",
        validation_alias="PLANNING_AGENT_MODEL_PROVIDER",
    )
    ollama_model: str = Field(
        default="qwen3:8b",
        min_length=1,
        validation_alias="OLLAMA_MODEL",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        min_length=1,
        validation_alias="OLLAMA_BASE_URL",
    )
    ollama_keep_alive: str = Field(
        default="30m",
        min_length=1,
        validation_alias="OLLAMA_KEEP_ALIVE",
    )
    ollama_temperature: float = Field(
        default=0,
        ge=0,
        le=2,
        validation_alias="OLLAMA_TEMPERATURE",
    )
    ollama_enable_thinking: bool = Field(
        default=False,
        validation_alias="OLLAMA_ENABLE_THINKING",
    )
    ollama_max_output_tokens: int = Field(
        default=256,
        ge=16,
        le=8192,
        validation_alias="OLLAMA_MAX_OUTPUT_TOKENS",
    )
    ollama_benchmark_timeout_seconds: float = Field(
        default=120,
        gt=0,
        le=600,
        validation_alias="OLLAMA_BENCHMARK_TIMEOUT_SECONDS",
    )
    azure_openai_endpoint: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_ENDPOINT",
    )
    azure_openai_deployment_name: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME",
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_ai_provider(self) -> str:
        if not self.ai_fallback_enabled:
            return "disabled"
        return (self.ai_active_provider or self.ai_provider or self.planning_agent_model_provider).strip().casefold()

    @property
    def resolved_ai_model(self) -> str:
        return (self.ai_active_model or self.ai_model or self.ollama_model).strip()

    @property
    def parsed_ai_local_model_roots(self) -> list[Path]:
        roots = []
        for item in self.ai_local_model_roots.split(","):
            value = item.strip()
            if value:
                path = Path(value)
                roots.append((path if path.is_absolute() else BACKEND_DIRECTORY / path).resolve())
        return list(dict.fromkeys(roots))

    @property
    def resolved_ai_timeout_seconds(self) -> float:
        return self.ai_timeout_seconds or self.ai_request_timeout_seconds

    @property
    def resolved_ai_temperature(self) -> float:
        return self.ollama_temperature if self.ai_temperature is None else self.ai_temperature

    @property
    def resolved_ai_max_output_tokens(self) -> int:
        return self.ollama_max_output_tokens if self.ai_max_output_tokens is None else self.ai_max_output_tokens

    @property
    def resolved_ai_thinking_enabled(self) -> bool:
        return self.ollama_enable_thinking if self.ai_thinking_enabled is None else self.ai_thinking_enabled


class Settings(ModelSettings):
    database_url: str = Field(
        min_length=1,
        validation_alias="DATABASE_URL",
    )
    planning_context_ttl_minutes: int = Field(
        default=480,
        ge=1,
        validation_alias="PLANNING_CONTEXT_TTL_MINUTES",
    )
    pending_activity_selection_ttl_minutes: int = Field(
        default=30,
        ge=1,
        validation_alias="PENDING_ACTIVITY_SELECTION_TTL_MINUTES",
    )
    activity_search_default_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        validation_alias="ACTIVITY_SEARCH_DEFAULT_LIMIT",
    )
    activity_search_max_limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        validation_alias="ACTIVITY_SEARCH_MAX_LIMIT",
    )
    agent_max_tool_iterations: int = Field(
        default=6,
        ge=1,
        le=20,
        validation_alias="AGENT_MAX_TOOL_ITERATIONS",
    )
    agent_request_timeout_seconds: float = Field(
        default=600,
        gt=0,
        le=3600,
        validation_alias="AGENT_REQUEST_TIMEOUT_SECONDS",
    )
    agent_include_debug_timing: bool = Field(
        default=False,
        validation_alias="AGENT_INCLUDE_DEBUG_TIMING",
    )
    enable_deterministic_fast_path: bool = Field(
        default=True,
        validation_alias="ENABLE_DETERMINISTIC_FAST_PATH",
    )
    cors_allowed_origins: str = Field(
        default=DEFAULT_CORS_ALLOWED_ORIGINS,
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        validation_alias="CORS_ALLOW_CREDENTIALS",
    )
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def parsed_cors_allowed_origins(self) -> list[str]:
        origins = [
            item.strip()
            for item in self.cors_allowed_origins.split(",")
            if item.strip()
        ]
        if not origins:
            return DEFAULT_CORS_ALLOWED_ORIGINS.split(",")
        return list(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_cors_credentials(self):
        if self.cors_allow_credentials and "*" in self.parsed_cors_allowed_origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS cannot contain '*' when "
                "CORS_ALLOW_CREDENTIALS is true."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        missing_database_url = any(
            item["type"] == "missing" and item["loc"] == ("DATABASE_URL",)
            for item in error.errors()
        )
        if not missing_database_url:
            messages = "; ".join(item["msg"] for item in error.errors())
            raise DatabaseConfigurationError(
                f"Application configuration is invalid: {messages}"
            ) from error
        raise DatabaseConfigurationError(
            "DATABASE_URL is required. Add it to backend/.env "
            "using the postgresql+psycopg URL format."
        ) from error


@lru_cache
def get_model_settings() -> ModelSettings:
    return ModelSettings()
