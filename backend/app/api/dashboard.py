"""
 Dashboard API Router
 Aggregated statistics for the dashboard.
"""
 
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional
 
from app.models.database import (
     Execution,
     ExecutionStatus as DBExecutionStatus,
     get_session
 )
from pydantic import BaseModel
 
 
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
 
 
class DashboardStats(BaseModel):
     """Dashboard statistics response."""
     total_executions: int
     pass_rate: float
     failed_tests: int
     avg_duration: float
     # Trends (compared to previous period)
     executions_trend: float
     pass_rate_trend: float
     failed_tests_trend: float
     duration_trend: float
 
 
@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
     days: int = 30,
     session: AsyncSession = Depends(get_session)
 ):
     """
     Get aggregated dashboard statistics.
     
     Calculates metrics for the specified period and compares to the previous period.
     """
     now = datetime.utcnow()
     current_period_start = now - timedelta(days=days)
     previous_period_start = current_period_start - timedelta(days=days)
     
     # Current period stats
     current_stats = await _get_period_stats(session, current_period_start, now)
     
     # Previous period stats (for trends)
     previous_stats = await _get_period_stats(session, previous_period_start, current_period_start)
     
     # Calculate trends
     executions_trend = _calculate_trend(current_stats["total"], previous_stats["total"])
     pass_rate_trend = _calculate_trend(current_stats["pass_rate"], previous_stats["pass_rate"])
     failed_trend = _calculate_trend(current_stats["failed"], previous_stats["failed"])
     duration_trend = _calculate_trend(current_stats["avg_duration"], previous_stats["avg_duration"])
     
     return DashboardStats(
         total_executions=current_stats["total"],
         pass_rate=round(current_stats["pass_rate"], 1),
         failed_tests=current_stats["failed"],
         avg_duration=round(current_stats["avg_duration"], 1),
         executions_trend=round(executions_trend, 1),
         pass_rate_trend=round(pass_rate_trend, 1),
         failed_tests_trend=round(failed_trend, 1),
         duration_trend=round(duration_trend, 1),
     )
 
 
async def _get_period_stats(
     session: AsyncSession,
     start: datetime,
     end: datetime
 ) -> dict:
     """Calculate stats for a specific time period."""
     
     # Total executions
     total_result = await session.execute(
         select(func.count(Execution.id)).where(
             Execution.created_at >= start,
             Execution.created_at < end
         )
     )
     total = total_result.scalar() or 0
     
     # Passed executions
     passed_result = await session.execute(
         select(func.count(Execution.id)).where(
             Execution.created_at >= start,
             Execution.created_at < end,
             Execution.status == DBExecutionStatus.PASS
         )
     )
     passed = passed_result.scalar() or 0
     
     # Failed executions
     failed_result = await session.execute(
         select(func.count(Execution.id)).where(
             Execution.created_at >= start,
             Execution.created_at < end,
             Execution.status == DBExecutionStatus.FAIL
         )
     )
     failed = failed_result.scalar() or 0
     
     # Average duration
     duration_result = await session.execute(
         select(func.avg(Execution.total_duration)).where(
             Execution.created_at >= start,
             Execution.created_at < end,
             Execution.total_duration.isnot(None)
         )
     )
     avg_duration = duration_result.scalar() or 0
     
     # Calculate pass rate
     pass_rate = (passed / total * 100) if total > 0 else 0
     
     return {
         "total": total,
         "passed": passed,
         "failed": failed,
         "pass_rate": pass_rate,
         "avg_duration": avg_duration,
     }
 
 
def _calculate_trend(current: float, previous: float) -> float:
     """Calculate percentage change between periods."""
     if previous == 0:
         return 100 if current > 0 else 0
     return ((current - previous) / previous) * 100