"""
Executions API Router
Test execution and history management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from app.models.database import (
    Execution, 
    ExecutionStep, 
    TestCase, 
    Project,
    ExecutionStatus as DBExecutionStatus,
    get_session
)
from app.models.schemas import (
    ExecutionRequest,
    ExecutionResultSchema,
    ExecutionListItem,
    ExecutionStatus,
    StepUpdateMessage
)
from app.services.execution_service import execution_service

router = APIRouter(prefix="/executions", tags=["Executions"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[execution_id] = websocket
    
    def disconnect(self, execution_id: str):
        self.active_connections.pop(execution_id, None)
    
    async def send_update(self, execution_id: str, message: dict):
        if execution_id in self.active_connections:
            await self.active_connections[execution_id].send_json(message)


manager = ConnectionManager()


@router.post("/", response_model=ExecutionResultSchema)
async def execute_test(
    request: ExecutionRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Execute a test case.
    
    This endpoint starts the execution and waits for completion.
    For real-time updates, connect to the WebSocket endpoint.
    """
    # Get test case with project
    result = await session.execute(
        select(TestCase).where(TestCase.id == request.test_case_id)
    )
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    if not test_case.script_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test case has no script code"
        )
    
    # Get project
    result = await session.execute(
        select(Project).where(Project.id == test_case.project_id)
    )
    project = result.scalar_one_or_none()
    
    execution_id = str(uuid4())
    
    # Create database record
    db_execution = Execution(
        id=execution_id,
        test_case_id=test_case.id,
        project_id=test_case.project_id,
        status=DBExecutionStatus.RUNNING,
        started_at=datetime.utcnow()
    )
    session.add(db_execution)
    await session.commit()
    
    # Execute with optional WebSocket callback
    async def on_step_complete(step: StepUpdateMessage):
        await manager.send_update(execution_id, {
            "type": "step_complete",
            "data": step.model_dump()
        })
    
    # Run execution
    execution_result = await execution_service.execute(
        execution_id=execution_id,
        test_case_id=test_case.id,
        project_id=test_case.project_id,
        project_name=project.name if project else "Unknown",
        test_name=test_case.name,
        script_code=test_case.script_code,
        device_type=test_case.device_type,
        platform=test_case.platform.value,
        device_id=request.device_id,
        on_step_complete=on_step_complete
    )
    
    # Update database with results
    db_execution.status = DBExecutionStatus[execution_result.status.value]
    db_execution.completed_at = datetime.utcnow()
    db_execution.total_duration = execution_result.metrics.total_duration
    db_execution.avg_response_time = execution_result.metrics.avg_response_time
    db_execution.step_success_rate = execution_result.metrics.step_success_rate
    db_execution.video_path = execution_result.artifacts.video_path
    db_execution.screenshot_failure = execution_result.artifacts.screenshot_failure
    db_execution.ai_analysis = execution_result.ai_analysis
    
    # Save steps
    for i, step in enumerate(execution_result.steps):
        db_step = ExecutionStep(
            execution_id=execution_id,
            order=i,
            action=step.action,
            result=step.result,
            latency=step.latency,
            error=step.error
        )
        session.add(db_step)
    
    await session.commit()
    
    # Notify WebSocket of completion
    await manager.send_update(execution_id, {
        "type": "execution_complete",
        "data": execution_result.model_dump()
    })
    
    return execution_result


@router.websocket("/ws/{execution_id}")
async def execution_websocket(
    websocket: WebSocket,
    execution_id: str
):
    """WebSocket endpoint for real-time execution updates."""
    await manager.connect(execution_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(execution_id)


@router.get("/", response_model=List[ExecutionListItem])
async def list_executions(
    project_id: Optional[str] = None,
    status: Optional[ExecutionStatus] = None,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """List execution history with optional filters."""
    query = select(Execution).order_by(desc(Execution.created_at))
    
    if project_id:
        query = query.where(Execution.project_id == project_id)
    
    if status:
        query = query.where(Execution.status == DBExecutionStatus[status.value])
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    executions = result.scalars().all()
    
    # Build response with test and project names
    items = []
    for exe in executions:
        # Get test case name
        tc_result = await session.execute(
            select(TestCase.name).where(TestCase.id == exe.test_case_id)
        )
        test_name = tc_result.scalar_one_or_none() or "Unknown"
        
        # Get project name
        proj_result = await session.execute(
            select(Project.name).where(Project.id == exe.project_id)
        )
        project_name = proj_result.scalar_one_or_none() or "Unknown"
        
        items.append(ExecutionListItem(
            execution_id=exe.id,
            test_name=test_name,
            project_name=project_name,
            status=ExecutionStatus(exe.status.value),
            total_duration=exe.total_duration,
            step_success_rate=exe.step_success_rate,
            created_at=exe.created_at
        ))
    
    return items


@router.get("/{execution_id}", response_model=ExecutionResultSchema)
async def get_execution(
    execution_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific execution result."""
    result = await session.execute(
        select(Execution).where(Execution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Get steps
    steps_result = await session.execute(
        select(ExecutionStep)
        .where(ExecutionStep.execution_id == execution_id)
        .order_by(ExecutionStep.order)
    )
    steps = steps_result.scalars().all()
    
    # Get names
    tc_result = await session.execute(
        select(TestCase.name).where(TestCase.id == execution.test_case_id)
    )
    test_name = tc_result.scalar_one_or_none() or "Unknown"
    
    proj_result = await session.execute(
        select(Project.name).where(Project.id == execution.project_id)
    )
    project_name = proj_result.scalar_one_or_none() or "Unknown"
    
    from app.models.schemas import ExecutionStepSchema, ExecutionMetrics, ExecutionArtifacts
    
    return ExecutionResultSchema(
        execution_id=execution.id,
        status=ExecutionStatus(execution.status.value),
        test_name=test_name,
        project_name=project_name,
        metrics=ExecutionMetrics(
            total_duration=execution.total_duration or 0,
            avg_response_time=execution.avg_response_time or 0,
            step_success_rate=execution.step_success_rate or 0
        ),
        steps=[
            ExecutionStepSchema(
                action=s.action,
                result=s.result,
                latency=s.latency or 0,
                error=s.error
            ) for s in steps
        ],
        artifacts=ExecutionArtifacts(
            video_path=execution.video_path or "",
            screenshot_failure=execution.screenshot_failure
        ),
        ai_analysis=execution.ai_analysis or "",
        created_at=execution.created_at
    )


@router.get("/active/list")
async def list_active_executions():
    """Get currently running executions."""
    return execution_service.get_active_executions()
