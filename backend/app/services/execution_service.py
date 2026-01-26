"""
Execution Service - Test Execution Orchestration
Handles the complete execution lifecycle with real-time updates.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Awaitable
from uuid import uuid4
from loguru import logger

from app.config import settings
from app.models.schemas import (
    ExecutionRequest,
    ExecutionResultSchema,
    ExecutionStatus,
    ExecutionMetrics,
    ExecutionArtifacts,
    ExecutionStepSchema,
    StepUpdateMessage,
    DeviceType
)
from app.services.automation_adapters import get_adapter, BaseAutomationAdapter
from app.services.script_generator import script_generator


class ExecutionService:
    """
    Orchestrates test execution with:
    - Real-time WebSocket updates
    - Artifact management
    - AI failure analysis
    """
    
    def __init__(self):
        self.active_executions: dict = {}
    
    async def execute(
        self,
        execution_id: str,
        test_case_id: str,
        project_id: str,
        project_name: str,
        test_name: str,
        script_code: str,
        device_type: DeviceType,
        platform: str,
        device_id: Optional[str] = None,
        on_step_complete: Optional[Callable[[StepUpdateMessage], Awaitable[None]]] = None
    ) -> ExecutionResultSchema:
        """
        Execute a test case and return the result.
        
        Args:
            execution_id: Unique execution identifier
            test_case_id: The test case being executed
            project_id: Parent project ID
            project_name: Project name for result display
            test_name: Test case name
            script_code: Generated Python script
            device_type: Web or Mobile
            platform: Specific platform (chrome, android, etc.)
            device_id: Device ID for mobile tests
            on_step_complete: Callback for real-time updates
        """
        # Create artifacts directory
        artifacts_dir = (
            settings.PROJECTS_ROOT / 
            project_name / 
            settings.ARTIFACTS_FOLDER / 
            execution_id
        )
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active execution
        self.active_executions[execution_id] = {
            "status": ExecutionStatus.RUNNING,
            "started_at": datetime.utcnow()
        }
        
        # Get appropriate adapter
        adapter = get_adapter(device_type)
        
        try:
            # Setup automation
            setup_success = await adapter.setup({
                "platform": platform,
                "device_id": device_id,
                "artifacts_dir": artifacts_dir,
                "headless": settings.PLAYWRIGHT_HEADLESS
            })
            
            if not setup_success:
                return self._create_error_result(
                    execution_id=execution_id,
                    test_name=test_name,
                    project_name=project_name,
                    error="Failed to initialize automation adapter"
                )
            
            # Execute script
            result = await adapter.execute_script(script_code, artifacts_dir)
            
            # Send step updates via callback
            if on_step_complete and result.get("steps"):
                for i, step in enumerate(result["steps"]):
                    await on_step_complete(StepUpdateMessage(
                        step_number=i + 1,
                        action=step.action,
                        result=step.result,
                        latency=step.latency,
                        error=step.error
                    ))
            
            # Generate AI analysis if failed
            ai_analysis = ""
            if result["status"] == ExecutionStatus.FAIL and result.get("error"):
                ai_analysis = await script_generator.analyze_failure(result["error"])
            elif result["status"] == ExecutionStatus.PASS:
                step_count = len(result.get("steps", []))
                duration = result["metrics"].total_duration
                ai_analysis = f"All {step_count} steps completed successfully in {duration:.1f}s."
            
            # Build final result
            execution_result = ExecutionResultSchema(
                execution_id=execution_id,
                status=result["status"],
                test_name=test_name,
                project_name=project_name,
                metrics=result["metrics"],
                steps=result.get("steps", []),
                artifacts=result["artifacts"],
                ai_analysis=ai_analysis,
                created_at=datetime.utcnow()
            )
            
            return execution_result
        
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}")
            return self._create_error_result(
                execution_id=execution_id,
                test_name=test_name,
                project_name=project_name,
                error=str(e)
            )
        
        finally:
            # Cleanup
            await adapter.teardown()
            self.active_executions.pop(execution_id, None)
    
    def _create_error_result(
        self,
        execution_id: str,
        test_name: str,
        project_name: str,
        error: str
    ) -> ExecutionResultSchema:
        """Create an error result when execution fails to start."""
        return ExecutionResultSchema(
            execution_id=execution_id,
            status=ExecutionStatus.FAIL,
            test_name=test_name,
            project_name=project_name,
            metrics=ExecutionMetrics(
                total_duration=0,
                avg_response_time=0,
                step_success_rate=0
            ),
            steps=[ExecutionStepSchema(
                action="Initialization",
                result=False,
                latency=0,
                error=error
            )],
            artifacts=ExecutionArtifacts(
                video_path="",
                screenshot_failure=None
            ),
            ai_analysis=f"Execution failed to start: {error}",
            created_at=datetime.utcnow()
        )
    
    def get_active_executions(self) -> list:
        """Get list of currently running executions."""
        return [
            {
                "execution_id": eid,
                "status": data["status"].value,
                "started_at": data["started_at"].isoformat()
            }
            for eid, data in self.active_executions.items()
        ]


# Global instance
execution_service = ExecutionService()
