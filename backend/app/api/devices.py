"""
Devices API Router
Device validation and management via MTK Connect.
"""

from fastapi import APIRouter, Depends
from typing import List

from app.models.schemas import (
    DeviceValidationRequest, 
    DeviceValidationResponse,
    DeviceResponse
)
from app.services.mtk_connect import mtk_connect

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/validate", response_model=DeviceValidationResponse)
async def validate_device(request: DeviceValidationRequest):
    """
    Validate device connection before test execution.
    
    - Web: Checks if browser binary exists
    - Mobile: Checks if device is connected via ADB/MTK Connect
    """
    return await mtk_connect.validate_device(request)


@router.get("/", response_model=List[dict])
async def list_connected_devices():
    """List all connected devices (Android and iOS)."""
    return await mtk_connect.list_devices()
