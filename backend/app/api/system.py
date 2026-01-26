"""
System API Router
Health checks and system status.
"""

from fastapi import APIRouter
from datetime import datetime

from app.config import settings
from app.services.ollama_client import ollama_client

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/status")
async def system_status():
    """Get detailed system status including Ollama availability."""
    ollama_healthy = await ollama_client.check_health()
    ollama_models = await ollama_client.list_models() if ollama_healthy else []
    
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        },
        "ollama": {
            "healthy": ollama_healthy,
            "host": settings.OLLAMA_HOST,
            "configured_model": settings.OLLAMA_MODEL,
            "available_models": ollama_models
        },
        "database": {
            "path": str(settings.DATABASE_PATH),
            "type": "SQLite"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/config")
async def get_config():
    """Get non-sensitive configuration values."""
    return {
        "ollama_host": settings.OLLAMA_HOST,
        "ollama_model": settings.OLLAMA_MODEL,
        "projects_root": str(settings.PROJECTS_ROOT),
        "playwright_headless": settings.PLAYWRIGHT_HEADLESS,
        "appium_host": settings.APPIUM_HOST
    }
