"""
Pydantic Schemas - API Request/Response Models
Implements strict JSON schemas per SRS Section 7.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums (matching database models)
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    QA_VIEWER = "qa_viewer"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class DeviceType(str, Enum):
    WEB = "web"
    MOBILE = "mobile"


class Platform(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    ANDROID = "android"
    IOS = "ios"


class TestType(str, Enum):
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    SMOKE = "smoke"
    INTEGRATION = "integration"


class DeviceStatus(str, Enum):
    READY = "ready"
    BUSY = "busy"
    OFFLINE = "offline"


# ============================================================================
# Project Schemas
# ============================================================================

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    library_path: str = Field(..., min_length=1)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    library_path: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    last_indexed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Test Configuration Schemas (SRS Section 5.1)
# ============================================================================

class TestConfigurationRequest(BaseModel):
    """Test configuration for script generation."""
    project_id: str
    device_type: DeviceType
    platform: Platform
    test_type: TestType
    test_case_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)  # Natural language input


class DeviceValidationRequest(BaseModel):
    """Request to validate device connection via MTK Connect."""
    device_type: DeviceType
    platform: Platform
    device_id: Optional[str] = None


class DeviceValidationResponse(BaseModel):
    """Response from device validation."""
    is_valid: bool
    device_type: DeviceType
    platform: Platform
    device_id: Optional[str] = None
    message: str
    details: Optional[dict] = None


# ============================================================================
# Script Generation Schemas (RAG Engine)
# ============================================================================

class ScriptGenerationRequest(BaseModel):
    """Request for AI script generation."""
    project_id: str
    description: str = Field(..., min_length=10)
    device_type: DeviceType
    platform: Platform
    test_type: TestType


class ScriptGenerationResponse(BaseModel):
    """Response with generated script."""
    script_code: str
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    rag_context_used: List[str] = []  # Library methods injected into prompt
    generation_time_ms: float


# ============================================================================
# Test Case Schemas
# ============================================================================

class TestCaseCreate(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    device_type: DeviceType
    platform: Platform
    test_type: TestType
    script_code: str


class TestCaseResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    device_type: DeviceType
    platform: Platform
    test_type: TestType
    script_code: Optional[str] = None
    script_validated: bool
    validation_errors: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Execution Schemas (SRS Section 7 - STRICT)
# ============================================================================

class ExecutionStepSchema(BaseModel):
    """Single step in execution - per SRS Section 7."""
    action: str
    result: bool
    latency: float  # milliseconds
    error: Optional[str] = None


class ExecutionMetrics(BaseModel):
    """Metrics block - per SRS Section 7."""
    total_duration: float  # seconds
    avg_response_time: float  # seconds
    step_success_rate: float  # percentage (0-100)


class ExecutionArtifacts(BaseModel):
    """Artifacts block - per SRS Section 7."""
    video_path: str
    screenshot_failure: Optional[str] = None


class ExecutionResultSchema(BaseModel):
    """
    Complete execution result - EXACTLY per SRS Section 7.
    
    {
      "execution_id": "uuid",
      "status": "PASS | FAIL | WARNING",
      "metrics": {...},
      "steps": [...],
      "artifacts": {...},
      "ai_analysis": "string"
    }
    """
    execution_id: str
    status: ExecutionStatus
    test_name: str
    project_name: str
    metrics: ExecutionMetrics
    steps: List[ExecutionStepSchema]
    artifacts: ExecutionArtifacts
    ai_analysis: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutionRequest(BaseModel):
    """Request to execute a test case."""
    test_case_id: str
    device_id: Optional[str] = None  # For mobile


class ExecutionListItem(BaseModel):
    """Summary item for execution history."""
    execution_id: str
    test_name: str
    project_name: str
    status: ExecutionStatus
    total_duration: Optional[float] = None
    step_success_rate: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Device Schemas
# ============================================================================

class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: DeviceType
    platform: Platform
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# WebSocket Schemas (Real-time Updates)
# ============================================================================

class WebSocketMessage(BaseModel):
    """WebSocket message for real-time execution updates."""
    type: str  # "step_complete", "execution_complete", "error"
    execution_id: str
    data: dict


class StepUpdateMessage(BaseModel):
    """Real-time step update."""
    step_number: int
    action: str
    result: bool
    latency: float
    error: Optional[str] = None


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
