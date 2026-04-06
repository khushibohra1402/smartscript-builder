"""
Devices API Router
Device validation and management via MTK Connect + Network Validator.
"""

from fastapi import APIRouter
from typing import List, Optional

from app.models.schemas import (
    DeviceValidationRequest, 
    DeviceValidationResponse,
    DeviceResponse,
    STBNetworkValidationRequest,
    DeviceType
)
from app.services.mtk_connect import mtk_connect
from app.services.network_validator import network_validator

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/validate", response_model=DeviceValidationResponse)
async def validate_device(request: DeviceValidationRequest):
    """
    Validate device connection before test execution.
    
    - Web: Checks if browser binary exists
    - Mobile: Checks if device is connected via ADB/MTK Connect
    - STB: Delegates to network validation
    """
    if request.device_type == DeviceType.STB:
        # For STB, do a basic ping check on the provided device_id (IP)
        if request.device_id:
            reachable = await network_validator.validate_network_device(request.device_id)
            return DeviceValidationResponse(
                is_valid=reachable,
                device_type=request.device_type,
                platform=request.platform,
                device_id=request.device_id,
                message="STB device is reachable" if reachable else "STB device not reachable on network",
            )
        return DeviceValidationResponse(
            is_valid=False,
            device_type=request.device_type,
            platform=request.platform,
            message="STB IP address required for validation",
        )
    return await mtk_connect.validate_device(request)


@router.post("/validate-stb-network")
async def validate_stb_network(request: STBNetworkValidationRequest):
    """
    Validate all STB network devices (STB, RCU, Smart Plug).
    Checks reachability and subnet membership.
    """
    return await network_validator.validate_stb_network(
        stb_ip=request.stb_ip,
        rcu_ip=request.rcu_ip,
        smart_plug_ip=request.smart_plug_ip,
    )


@router.get("/", response_model=List[dict])
async def list_connected_devices():
    """List all connected devices (Android and iOS)."""
    return await mtk_connect.list_devices()
