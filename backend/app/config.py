"""
Configuration Module - GenAI Automation Framework
Handles all environment and application configuration.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "GenAI Automation Framework"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Database (SQLite - Local)
    DATABASE_PATH: Path = Path("./data/automation.db")
    
    # Ollama (Local LLM)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:7b"  # or llama3:7b
    OLLAMA_TIMEOUT: int = 120  # seconds
    
    # RAG Engine
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: Path = Path("./data/faiss_index")
    
    # Projects & Storage
    PROJECTS_ROOT: Path = Path("./projects")
    ARTIFACTS_FOLDER: str = "artifacts"
    
    # MTK Connect
    MTK_CONNECT_HOST: str = "localhost"
    MTK_CONNECT_PORT: int = 5037  # ADB default
    MTK_CONNECT_TIMEOUT: int = 10
    
    # Automation
    PLAYWRIGHT_HEADLESS: bool = False
    APPIUM_HOST: str = "http://localhost:4723"
    
    # Security
    FORBIDDEN_IMPORTS: list[str] = Field(
        default=["os", "subprocess", "sys", "shutil", "pathlib", "socket", "requests"]
    )
    MAX_SCRIPT_SIZE: int = 50000  # bytes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def ensure_directories():
    """Create required directories if they don't exist."""
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
    settings.PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
