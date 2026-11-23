from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.activities import router as activities_router
from app.api.agent import router as agent_router
from app.api.analysis import router as analysis_router
from app.api.schedules import router as schedules_router
from app.api.schedule_versions import router as schedule_versions_router
from app.api.schedule_comparisons import router as schedule_comparisons_router
from app.api.tools import router as tools_router
from app.api.reports import router as reports_router
from app.api.project_discovery import router as project_discovery_router
from app.api.planning_context import router as planning_context_router
from app.api.activity_resolution import router as activity_resolution_router
from app.api.error_handlers import http_exception_handler
from app.api.error_handlers import validation_exception_handler
from app.api.error_handlers import unexpected_exception_handler
from app.config import Settings
from app.config import get_settings


def database_readiness() -> dict[str, Any]:
    from app.db.session import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"available": True, "required": True, "error": None}
    except Exception:
        return {
            "available": False,
            "required": True, #true
            "error": "Database connection unavailable.",
        }


def create_application(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()
    application = FastAPI(
        title="AI Planning Copilot API",
        description="API for importing and analysing Primavera P6 XER schedules.",
        version="0.4.0",
    )

    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, unexpected_exception_handler)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.parsed_cors_allowed_origins,
        allow_credentials=application_settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Authorization", "X-Request-ID"],
    )

    application.include_router(tools_router)
    application.include_router(schedules_router)
    application.include_router(activities_router)
    application.include_router(analysis_router)
    application.include_router(agent_router)
    application.include_router(schedule_versions_router)
    application.include_router(schedule_comparisons_router)
    application.include_router(reports_router)
    application.include_router(project_discovery_router)
    application.include_router(planning_context_router)
    application.include_router(activity_resolution_router)

    @application.get("/api/health", tags=["System"])
    def health_check() -> dict[str, Any]:
        database = database_readiness()
        return {
            "status": "healthy" if database["available"] else "degraded",
            "application": "AI Planning Copilot",
            "version": "0.4.0",
            "application_available": True,
            "database": database,
            "ai_provider_required": False,
        }

    return application


app = create_application()
