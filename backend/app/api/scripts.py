"""
Script Generation API Router
AI-powered test script generation with RAG.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.models.database import Project, TestCase, get_session
from app.models.schemas import (
    ScriptGenerationRequest,
    ScriptGenerationResponse,
    TestCaseCreate,
    TestCaseResponse
)
from app.services.script_generator import script_generator

router = APIRouter(prefix="/scripts", tags=["Script Generation"])


@router.post("/generate", response_model=ScriptGenerationResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Generate a test script from natural language description.
    
    Uses the RAG engine to:
    1. Retrieve relevant library methods
    2. Build a context-aware prompt
    3. Generate code via Ollama
    4. Validate with code guardrail
    """
    # Get project to retrieve library path
    result = await session.execute(
        select(Project).where(Project.id == request.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Generate script
    library_path = Path(project.library_path) if project.library_path else None
    response = await script_generator.generate(request, library_path)
    
    return response


@router.post("/save", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def save_test_case(
    test_case: TestCaseCreate,
    session: AsyncSession = Depends(get_session)
):
    """Save a generated script as a test case."""
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == test_case.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validate script before saving
    from app.services.rag_engine import code_guardrail
    is_valid, errors = code_guardrail.validate(test_case.script_code)
    
    db_test_case = TestCase(
        project_id=test_case.project_id,
        name=test_case.name,
        description=test_case.description,
        device_type=test_case.device_type,
        platform=test_case.platform,
        test_type=test_case.test_type,
        script_code=test_case.script_code,
        script_validated=is_valid,
        validation_errors=errors if errors else None
    )
    
    session.add(db_test_case)
    await session.commit()
    await session.refresh(db_test_case)
    
    return db_test_case


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific test case."""
    result = await session.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    return test_case


@router.post("/analyze-failure")
async def analyze_failure(error_traceback: str):
    """
    Use AI to translate technical errors to user-friendly messages.
    Implements SRS Section 5.2: AI Failure Analyst.
    """
    analysis = await script_generator.analyze_failure(error_traceback)
    return {"analysis": analysis}
