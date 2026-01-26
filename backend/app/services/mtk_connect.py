"""
MTK Connect Service - Device Bridge Integration
Handles device validation and connection management.
Implements SRS Section 5.1: Device Validation.
"""

import asyncio
import subprocess
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger

from app.config import settings
from app.models.schemas import DeviceValidationRequest, DeviceValidationResponse, DeviceType, Platform


class MTKConnectService:
    """
    Service for communicating with MTK Connect / ADB.
    Validates device connections before test execution.
    """
    
    def __init__(self):
        self.host = settings.MTK_CONNECT_HOST
        self.port = settings.MTK_CONNECT_PORT
        self.timeout = settings.MTK_CONNECT_TIMEOUT
    
    async def validate_device(self, request: DeviceValidationRequest) -> DeviceValidationResponse:
        """
        Validate device connection based on type.
        
        - Web: Check if browser binary exists
        - Mobile: Check if device is connected via ADB
        """
        if request.device_type == DeviceType.WEB:
            return await self._validate_web_browser(request.platform)
        else:
            return await self._validate_mobile_device(request.platform, request.device_id)
    
    async def _validate_web_browser(self, platform: Platform) -> DeviceValidationResponse:
        """Check if the specified browser is available."""
        browser_paths = {
            Platform.CHROME: [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ],
            Platform.FIREFOX: [
                "/usr/bin/firefox",
                "/Applications/Firefox.app/Contents/MacOS/firefox",
                "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
            ],
            Platform.SAFARI: [
                "/Applications/Safari.app/Contents/MacOS/Safari"
            ]
        }
        
        paths = browser_paths.get(platform, [])
        
        # Check if any path exists
        import os
        for path in paths:
            if os.path.exists(path):
                return DeviceValidationResponse(
                    is_valid=True,
                    device_type=DeviceType.WEB,
                    platform=platform,
                    message=f"{platform.value.title()} browser is ready",
                    details={"browser_path": path}
                )
        
        # Try using 'which' on Unix or 'where' on Windows
        try:
            result = await asyncio.create_subprocess_exec(
                "which" if os.name != "nt" else "where",
                platform.value,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=5)
            
            if result.returncode == 0 and stdout:
                return DeviceValidationResponse(
                    is_valid=True,
                    device_type=DeviceType.WEB,
                    platform=platform,
                    message=f"{platform.value.title()} browser is ready",
                    details={"browser_path": stdout.decode().strip()}
                )
        except Exception as e:
            logger.debug(f"Browser lookup failed: {e}")
        
        return DeviceValidationResponse(
            is_valid=False,
            device_type=DeviceType.WEB,
            platform=platform,
            message=f"{platform.value.title()} browser not found",
            details={"searched_paths": paths}
        )
    
    async def _validate_mobile_device(
        self, 
        platform: Platform, 
        device_id: Optional[str]
    ) -> DeviceValidationResponse:
        """Check if mobile device is connected via ADB/MTK Connect."""
        
        if platform == Platform.ANDROID:
            return await self._check_adb_device(device_id)
        elif platform == Platform.IOS:
            return await self._check_ios_device(device_id)
        
        return DeviceValidationResponse(
            is_valid=False,
            device_type=DeviceType.MOBILE,
            platform=platform,
            message=f"Unsupported mobile platform: {platform.value}"
        )
    
    async def _check_adb_device(self, device_id: Optional[str]) -> DeviceValidationResponse:
        """Check Android device via ADB."""
        try:
            # Run 'adb devices'
            result = await asyncio.create_subprocess_exec(
                "adb", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                return DeviceValidationResponse(
                    is_valid=False,
                    device_type=DeviceType.MOBILE,
                    platform=Platform.ANDROID,
                    message="ADB not available or not running",
                    details={"error": stderr.decode()}
                )
            
            # Parse device list
            output = stdout.decode()
            lines = output.strip().split('\n')[1:]  # Skip header
            devices = []
            
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 2 and parts[1] == 'device':
                    devices.append(parts[0])
            
            if not devices:
                return DeviceValidationResponse(
                    is_valid=False,
                    device_type=DeviceType.MOBILE,
                    platform=Platform.ANDROID,
                    message="No Android devices connected",
                    details={"adb_output": output}
                )
            
            # Check specific device or use first available
            target_device = device_id if device_id in devices else devices[0]
            
            return DeviceValidationResponse(
                is_valid=True,
                device_type=DeviceType.MOBILE,
                platform=Platform.ANDROID,
                device_id=target_device,
                message=f"Android device ready: {target_device}",
                details={"available_devices": devices}
            )
        
        except asyncio.TimeoutError:
            return DeviceValidationResponse(
                is_valid=False,
                device_type=DeviceType.MOBILE,
                platform=Platform.ANDROID,
                message="ADB connection timed out"
            )
        except FileNotFoundError:
            return DeviceValidationResponse(
                is_valid=False,
                device_type=DeviceType.MOBILE,
                platform=Platform.ANDROID,
                message="ADB not installed or not in PATH"
            )
        except Exception as e:
            logger.error(f"ADB check failed: {e}")
            return DeviceValidationResponse(
                is_valid=False,
                device_type=DeviceType.MOBILE,
                platform=Platform.ANDROID,
                message=f"Device check failed: {str(e)}"
            )
    
    async def _check_ios_device(self, device_id: Optional[str]) -> DeviceValidationResponse:
        """Check iOS device (requires libimobiledevice)."""
        try:
            # Try using idevice_id from libimobiledevice
            result = await asyncio.create_subprocess_exec(
                "idevice_id", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                return DeviceValidationResponse(
                    is_valid=False,
                    device_type=DeviceType.MOBILE,
                    platform=Platform.IOS,
                    message="libimobiledevice not available",
                    details={"error": stderr.decode()}
                )
            
            devices = [d.strip() for d in stdout.decode().strip().split('\n') if d.strip()]
            
            if not devices:
                return DeviceValidationResponse(
                    is_valid=False,
                    device_type=DeviceType.MOBILE,
                    platform=Platform.IOS,
                    message="No iOS devices connected"
                )
            
            target_device = device_id if device_id in devices else devices[0]
            
            return DeviceValidationResponse(
                is_valid=True,
                device_type=DeviceType.MOBILE,
                platform=Platform.IOS,
                device_id=target_device,
                message=f"iOS device ready: {target_device[:8]}...",
                details={"available_devices": devices}
            )
        
        except FileNotFoundError:
            return DeviceValidationResponse(
                is_valid=False,
                device_type=DeviceType.MOBILE,
                platform=Platform.IOS,
                message="libimobiledevice not installed"
            )
        except Exception as e:
            logger.error(f"iOS device check failed: {e}")
            return DeviceValidationResponse(
                is_valid=False,
                device_type=DeviceType.MOBILE,
                platform=Platform.IOS,
                message=f"Device check failed: {str(e)}"
            )
    
    async def list_devices(self) -> List[Dict]:
        """List all connected devices (both Android and iOS)."""
        devices = []
        
        # Check Android devices
        android_result = await self._check_adb_device(None)
        if android_result.is_valid and android_result.details:
            for dev_id in android_result.details.get("available_devices", []):
                devices.append({
                    "id": dev_id,
                    "type": "mobile",
                    "platform": "android",
                    "status": "ready"
                })
        
        # Check iOS devices
        ios_result = await self._check_ios_device(None)
        if ios_result.is_valid and ios_result.details:
            for dev_id in ios_result.details.get("available_devices", []):
                devices.append({
                    "id": dev_id,
                    "type": "mobile",
                    "platform": "ios",
                    "status": "ready"
                })
        
        return devices


# Global instance
mtk_connect = MTKConnectService()
