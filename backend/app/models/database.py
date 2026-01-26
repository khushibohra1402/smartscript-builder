"""
Database Models - SQLite with SQLAlchemy
Implements RBAC and Project-Level Isolation per SRS Section 3.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from uuid import uuid4

from app.config import settings


Base = declarative_base()


class UserRole(str, Enum):
    """RBAC Roles per SRS Section 3."""
    ADMIN = "admin"           # Read/Write/Config - Cross-Project Visibility
    DEVELOPER = "developer"   # Read/Write Scripts - Only assigned Project folders
    QA_VIEWER = "qa_viewer"   # Read/Execute Only - Only assigned Project folders


class ExecutionStatus(str, Enum):
    """Execution status per SRS Section 7."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class DeviceType(str, Enum):
    """Device types for automation."""
    WEB = "web"
    MOBILE = "mobile"


class Platform(str, Enum):
    """Supported platforms."""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    ANDROID = "android"
    IOS = "ios"


class TestType(str, Enum):
    """Test categories."""
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    SMOKE = "smoke"
    INTEGRATION = "integration"


# ============================================================================
# User & RBAC Models
# ============================================================================

class User(Base):
    """User model with role-based access control."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.QA_VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_assignments = relationship("ProjectAssignment", back_populates="user")
    executions = relationship("Execution", back_populates="user")


class ProjectAssignment(Base):
    """Maps users to projects for data isolation."""
    __tablename__ = "project_assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    can_write = Column(Boolean, default=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="project_assignments")
    project = relationship("Project", back_populates="assignments")


# ============================================================================
# Project Models
# ============================================================================

class Project(Base):
    """Project with custom enterprise library configuration."""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    library_path = Column(String(500), nullable=False)  # Path to enterprise_lib folder
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # RAG Index metadata
    faiss_index_path = Column(String(500))
    last_indexed_at = Column(DateTime)
    
    # Relationships
    assignments = relationship("ProjectAssignment", back_populates="project")
    test_cases = relationship("TestCase", back_populates="project")
    executions = relationship("Execution", back_populates="project")


# ============================================================================
# Test Case Models
# ============================================================================

class TestCase(Base):
    """Generated test case with script code."""
    __tablename__ = "test_cases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)  # Natural language input from user
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    platform = Column(SQLEnum(Platform), nullable=False)
    test_type = Column(SQLEnum(TestType), nullable=False)
    
    # Generated script
    script_code = Column(Text)  # Python code generated by Ollama
    script_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    project = relationship("Project", back_populates="test_cases")
    executions = relationship("Execution", back_populates="test_case")


# ============================================================================
# Execution Models (Per SRS Section 7 Schema)
# ============================================================================

class Execution(Base):
    """Execution result matching SRS Section 7 JSON schema."""
    __tablename__ = "executions"
    
    # execution_id: uuid
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Relationships
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # status: PASS | FAIL | WARNING
    status = Column(SQLEnum(ExecutionStatus), nullable=False, default=ExecutionStatus.PENDING)
    
    # metrics
    total_duration = Column(Float)  # seconds
    avg_response_time = Column(Float)  # seconds
    step_success_rate = Column(Float)  # percentage (0-100)
    
    # artifacts
    video_path = Column(String(500))
    screenshot_failure = Column(String(500))
    
    # ai_analysis
    ai_analysis = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="executions")
    project = relationship("Project", back_populates="executions")
    user = relationship("User", back_populates="executions")
    steps = relationship("ExecutionStep", back_populates="execution", order_by="ExecutionStep.order")


class ExecutionStep(Base):
    """Individual step in an execution (per SRS Section 7)."""
    __tablename__ = "execution_steps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False)
    order = Column(Integer, nullable=False)
    
    # Step data per SRS schema
    action = Column(String(500), nullable=False)
    result = Column(Boolean, nullable=False)
    latency = Column(Float)  # milliseconds
    error = Column(Text)  # string | null
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    execution = relationship("Execution", back_populates="steps")


# ============================================================================
# Device Registry
# ============================================================================

class Device(Base):
    """Registered devices for MTK Connect."""
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(200), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    platform = Column(SQLEnum(Platform), nullable=False)
    
    # Connection info
    device_id = Column(String(200))  # ADB device ID or browser path
    host = Column(String(200))
    port = Column(Integer)
    
    # Status
    status = Column(String(50), default="offline")  # ready, busy, offline
    last_seen = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Database Setup
# ============================================================================

def get_database_url() -> str:
    """Get SQLite database URL."""
    return f"sqlite+aiosqlite:///{settings.DATABASE_PATH}"


async def init_database():
    """Initialize the database and create all tables."""
    from app.config import ensure_directories
    ensure_directories()
    
    engine = create_async_engine(get_database_url(), echo=settings.DEBUG)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def get_session() -> AsyncSession:
    """Get an async database session."""
    engine = create_async_engine(get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
