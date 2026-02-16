"""
Projects API Router
CRUD operations for projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pathlib import Path

from app.models.database import Project, get_session
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.rag_engine import library_indexer

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """List all projects."""
    result = await session.execute(
        select(Project)
        .where(Project.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific project by ID."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new project."""
    # Ensure project directory exists (create if needed)
    from app.config import settings
    import os
    
    project_dir = os.path.join(str(settings.PROJECTS_ROOT), project.name.replace(" ", "_").lower())
    os.makedirs(project_dir, exist_ok=True)
    
    # Use provided library_path or default to project directory
    library_path = Path(project.library_path) if project.library_path else Path(project_dir)
    if project.library_path and not library_path.exists():
        # Create the library path if it doesn't exist
        library_path.mkdir(parents=True, exist_ok=True)
    
    db_project = Project(
        name=project.name,
        description=project.description,
        library_path=str(library_path)
    )
    
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    
    return db_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a project."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await session.commit()
    await session.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Soft delete a project."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.is_active = False
    await session.commit()


@router.post("/{project_id}/index")
async def index_project_library(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Index the project's enterprise library for RAG."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        index_result = await library_indexer.index_library(
            Path(project.library_path),
            project_id
        )
        
        # Update project with index metadata
        from datetime import datetime
        project.last_indexed_at = datetime.utcnow()
        project.faiss_index_path = str(index_result.get("faiss_index_path", ""))
        await session.commit()
        
        return index_result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
