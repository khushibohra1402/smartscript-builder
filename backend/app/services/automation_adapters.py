"""
Automation Adapters - Playwright (Web) and Appium (Mobile)
Implements SRS Tier 3: The Automation Adapters.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.config import settings
from app.models.schemas import (
    ExecutionStatus, 
    ExecutionStepSchema, 
    ExecutionMetrics,
    ExecutionArtifacts,
    Platform,
    DeviceType
)


class BaseAutomationAdapter(ABC):
    """Abstract base class for automation adapters."""
    
    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Initialize the automation session."""
        pass
    
    @abstractmethod
    async def execute_script(
        self, 
        script_code: str,
        artifacts_dir: Path
    ) -> Dict[str, Any]:
        """Execute the generated test script."""
        pass
    
    @abstractmethod
    async def teardown(self) -> None:
        """Clean up the automation session."""
        pass


class PlaywrightAdapter(BaseAutomationAdapter):
    """
    Playwright adapter for web automation.
    Handles Chrome, Firefox, and Safari.
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.steps: List[ExecutionStepSchema] = []
        self.video_path: Optional[str] = None
    
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Initialize Playwright browser."""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            platform = config.get("platform", Platform.CHROME)
            headless = config.get("headless", settings.PLAYWRIGHT_HEADLESS)
            artifacts_dir = config.get("artifacts_dir")
            
            # Select browser
            if platform == Platform.CHROME:
                browser_type = self.playwright.chromium
            elif platform == Platform.FIREFOX:
                browser_type = self.playwright.firefox
            elif platform == Platform.SAFARI:
                browser_type = self.playwright.webkit
            else:
                browser_type = self.playwright.chromium
            
            self.browser = await browser_type.launch(headless=headless)
            
            # Create context with video recording
            context_options = {
                "viewport": {"width": 1920, "height": 1080}
            }
            
            if artifacts_dir:
                context_options["record_video_dir"] = str(artifacts_dir)
                context_options["record_video_size"] = {"width": 1280, "height": 720}
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            logger.info(f"Playwright {platform.value} browser initialized")
            return True
        
        except Exception as e:
            logger.error(f"Playwright setup failed: {e}")
            return False
    
    async def execute_script(
        self,
        script_code: str,
        artifacts_dir: Path
    ) -> Dict[str, Any]:
        """
        Execute a Python test script with Playwright.
        Captures steps, timing, and handles errors.
        """
        self.steps = []
        start_time = time.time()
        status = ExecutionStatus.PASS
        error_message = None
        screenshot_failure = None
        
        try:
            # Create a namespace for script execution
            namespace = {
                "page": self.page,
                "context": self.context,
                "browser": self.browser,
                "asyncio": asyncio,
                "steps": self.steps,
                "logger": logger
            }
            
            # Execute the script
            exec(compile(script_code, "<generated_script>", "exec"), namespace)
            
            # If there's a test class, instantiate and run it
            for name, obj in namespace.items():
                if isinstance(obj, type) and name.startswith("Test"):
                    instance = obj()
                    
                    # Setup
                    if hasattr(instance, "setup"):
                        step_start = time.time()
                        try:
                            await self._run_method(instance.setup)
                            self._add_step("Setup", True, time.time() - step_start)
                        except Exception as e:
                            self._add_step("Setup", False, time.time() - step_start, str(e))
                            raise
                    
                    # Run test methods
                    for method_name in dir(instance):
                        if method_name.startswith("test_"):
                            method = getattr(instance, method_name)
                            step_start = time.time()
                            try:
                                await self._run_method(method)
                                self._add_step(method_name, True, time.time() - step_start)
                            except Exception as e:
                                self._add_step(method_name, False, time.time() - step_start, str(e))
                                status = ExecutionStatus.FAIL
                                error_message = str(e)
                                
                                # Capture failure screenshot
                                screenshot_path = artifacts_dir / "failure_screenshot.png"
                                await self.page.screenshot(path=str(screenshot_path))
                                screenshot_failure = str(screenshot_path)
                    
                    # Teardown
                    if hasattr(instance, "teardown"):
                        step_start = time.time()
                        try:
                            await self._run_method(instance.teardown)
                            self._add_step("Teardown", True, time.time() - step_start)
                        except Exception as e:
                            self._add_step("Teardown", False, time.time() - step_start, str(e))
        
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            status = ExecutionStatus.FAIL
            error_message = str(e)
            
            # Capture failure screenshot
            try:
                screenshot_path = artifacts_dir / "failure_screenshot.png"
                await self.page.screenshot(path=str(screenshot_path))
                screenshot_failure = str(screenshot_path)
            except:
                pass
        
        # Get video path
        video_path = None
        if self.page.video:
            try:
                video_path = await self.page.video.path()
            except:
                pass
        
        total_duration = time.time() - start_time
        successful_steps = sum(1 for s in self.steps if s.result)
        
        return {
            "status": status,
            "metrics": ExecutionMetrics(
                total_duration=total_duration,
                avg_response_time=sum(s.latency for s in self.steps) / max(len(self.steps), 1) / 1000,
                step_success_rate=(successful_steps / max(len(self.steps), 1)) * 100
            ),
            "steps": self.steps,
            "artifacts": ExecutionArtifacts(
                video_path=video_path or "",
                screenshot_failure=screenshot_failure
            ),
            "error": error_message
        }
    
    async def _run_method(self, method):
        """Run a method, handling both sync and async."""
        if asyncio.iscoroutinefunction(method):
            await method()
        else:
            method()
    
    def _add_step(
        self, 
        action: str, 
        result: bool, 
        latency: float, 
        error: Optional[str] = None
    ):
        """Add an execution step."""
        self.steps.append(ExecutionStepSchema(
            action=action,
            result=result,
            latency=latency * 1000,  # Convert to ms
            error=error
        ))
    
    async def teardown(self) -> None:
        """Clean up Playwright resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
            logger.info("Playwright teardown complete")
        except Exception as e:
            logger.error(f"Playwright teardown error: {e}")


class AppiumAdapter(BaseAutomationAdapter):
    """
    Appium adapter for mobile automation.
    Handles Android and iOS devices.
    """
    
    def __init__(self):
        self.driver = None
        self.steps: List[ExecutionStepSchema] = []
    
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Initialize Appium driver."""
        try:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options
            from appium.options.ios import XCUITestOptions
            
            platform = config.get("platform", Platform.ANDROID)
            device_id = config.get("device_id")
            
            if platform == Platform.ANDROID:
                options = UiAutomator2Options()
                options.platform_name = "Android"
                options.device_name = device_id or "Android Emulator"
                options.automation_name = "UiAutomator2"
                
                # Add app path if provided
                if "app_path" in config:
                    options.app = config["app_path"]
            
            elif platform == Platform.IOS:
                options = XCUITestOptions()
                options.platform_name = "iOS"
                options.device_name = device_id or "iPhone Simulator"
                options.automation_name = "XCUITest"
                
                if "app_path" in config:
                    options.app = config["app_path"]
            
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            self.driver = webdriver.Remote(
                settings.APPIUM_HOST,
                options=options
            )
            
            logger.info(f"Appium {platform.value} driver initialized")
            return True
        
        except Exception as e:
            logger.error(f"Appium setup failed: {e}")
            return False
    
    async def execute_script(
        self,
        script_code: str,
        artifacts_dir: Path
    ) -> Dict[str, Any]:
        """Execute a mobile test script with Appium."""
        self.steps = []
        start_time = time.time()
        status = ExecutionStatus.PASS
        error_message = None
        screenshot_failure = None
        
        try:
            namespace = {
                "driver": self.driver,
                "steps": self.steps,
                "logger": logger
            }
            
            exec(compile(script_code, "<generated_script>", "exec"), namespace)
            
            # Similar pattern to Playwright - find and run test class
            for name, obj in namespace.items():
                if isinstance(obj, type) and name.startswith("Test"):
                    instance = obj()
                    
                    if hasattr(instance, "setup"):
                        step_start = time.time()
                        try:
                            instance.setup()
                            self._add_step("Setup", True, time.time() - step_start)
                        except Exception as e:
                            self._add_step("Setup", False, time.time() - step_start, str(e))
                            raise
                    
                    for method_name in dir(instance):
                        if method_name.startswith("test_"):
                            method = getattr(instance, method_name)
                            step_start = time.time()
                            try:
                                method()
                                self._add_step(method_name, True, time.time() - step_start)
                            except Exception as e:
                                self._add_step(method_name, False, time.time() - step_start, str(e))
                                status = ExecutionStatus.FAIL
                                error_message = str(e)
                                
                                screenshot_path = artifacts_dir / "failure_screenshot.png"
                                self.driver.save_screenshot(str(screenshot_path))
                                screenshot_failure = str(screenshot_path)
                    
                    if hasattr(instance, "teardown"):
                        step_start = time.time()
                        try:
                            instance.teardown()
                            self._add_step("Teardown", True, time.time() - step_start)
                        except Exception as e:
                            self._add_step("Teardown", False, time.time() - step_start, str(e))
        
        except Exception as e:
            logger.error(f"Appium execution failed: {e}")
            status = ExecutionStatus.FAIL
            error_message = str(e)
        
        total_duration = time.time() - start_time
        successful_steps = sum(1 for s in self.steps if s.result)
        
        return {
            "status": status,
            "metrics": ExecutionMetrics(
                total_duration=total_duration,
                avg_response_time=sum(s.latency for s in self.steps) / max(len(self.steps), 1) / 1000,
                step_success_rate=(successful_steps / max(len(self.steps), 1)) * 100
            ),
            "steps": self.steps,
            "artifacts": ExecutionArtifacts(
                video_path="",  # Appium video recording requires separate setup
                screenshot_failure=screenshot_failure
            ),
            "error": error_message
        }
    
    def _add_step(
        self,
        action: str,
        result: bool,
        latency: float,
        error: Optional[str] = None
    ):
        """Add an execution step."""
        self.steps.append(ExecutionStepSchema(
            action=action,
            result=result,
            latency=latency * 1000,
            error=error
        ))
    
    async def teardown(self) -> None:
        """Clean up Appium driver."""
        try:
            if self.driver:
                self.driver.quit()
            logger.info("Appium teardown complete")
        except Exception as e:
            logger.error(f"Appium teardown error: {e}")


class STBAdapter(BaseAutomationAdapter):
    """
    STB Adapter for Set-Top Box automation.
    Combines HDMI vision capture + RedRat IR control.
    """
    
    def __init__(self):
        self.vision = None
        self.remote = None
        self.steps: List[ExecutionStepSchema] = []
        self.artifacts_dir: Optional[Path] = None
    
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Initialize STB hardware connections."""
        try:
            from app.services.stb_vision import STBVisionService
            from app.services.redrat_bridge import RedRatController
            
            hdmi_index = config.get("hdmi_capture_index", 0)
            redrat_ip = config.get("redrat_ip", "192.168.1.100")
            self.artifacts_dir = config.get("artifacts_dir")
            
            # Connect HDMI capture
            self.vision = STBVisionService(hdmi_capture_index=hdmi_index)
            vision_ok = self.vision.connect(timeout=15.0)
            if not vision_ok:
                logger.error("HDMI capture connection failed")
                return False
            
            # Connect RedRat IR blaster
            self.remote = RedRatController(ip_address=redrat_ip)
            remote_ok = await self.remote.connect(timeout=10.0)
            if not remote_ok:
                logger.error("RedRat IR blaster connection failed")
                return False
            
            logger.info("STB adapter initialized (vision + IR)")
            return True
        
        except Exception as e:
            logger.error(f"STB setup failed: {e}")
            return False
    
    async def execute_script(
        self,
        script_code: str,
        artifacts_dir: Path
    ) -> Dict[str, Any]:
        """Execute an STB test script via subprocess with log capture."""
        import subprocess
        import tempfile
        
        self.steps = []
        self.artifacts_dir = artifacts_dir
        start_time = time.time()
        status = ExecutionStatus.PASS
        error_message = None
        screenshot_failure = None
        
        # Write script to temp file
        script_file = artifacts_dir / "test_script.py"
        script_file.write_text(script_code)
        
        try:
            proc = subprocess.Popen(
                ["python", str(script_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(artifacts_dir)
            )
            
            stdout, stderr = proc.communicate(timeout=300)
            
            # Parse step results from stdout (convention: lines starting with STEP:)
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("STEP:"):
                    parts = line[5:].split("|")
                    if len(parts) >= 3:
                        action = parts[0].strip()
                        result = parts[1].strip().upper() == "PASS"
                        latency = float(parts[2].strip()) if parts[2].strip() else 0
                        err = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
                        self._add_step(action, result, latency / 1000, err)
                        if not result:
                            status = ExecutionStatus.FAIL
            
            if proc.returncode != 0:
                status = ExecutionStatus.FAIL
                error_message = stderr or f"Script exited with code {proc.returncode}"
                
                # Capture failure frame
                if self.vision and self.vision.is_connected():
                    fail_path = str(artifacts_dir / f"failure_{int(time.time())}.png")
                    self.vision.save_frame(fail_path)
                    screenshot_failure = fail_path
            
            if not self.steps:
                self._add_step(
                    "Script Execution",
                    status == ExecutionStatus.PASS,
                    time.time() - start_time
                )
        
        except subprocess.TimeoutExpired:
            proc.kill()
            status = ExecutionStatus.FAIL
            error_message = "Script execution timed out (300s)"
            self._add_step("Execution", False, 300, error_message)
        
        except Exception as e:
            logger.error(f"STB execution failed: {e}")
            status = ExecutionStatus.FAIL
            error_message = str(e)
            self._add_step("Execution", False, time.time() - start_time, str(e))
        
        total_duration = time.time() - start_time
        successful_steps = sum(1 for s in self.steps if s.result)
        
        return {
            "status": status,
            "metrics": ExecutionMetrics(
                total_duration=total_duration,
                avg_response_time=sum(s.latency for s in self.steps) / max(len(self.steps), 1) / 1000,
                step_success_rate=(successful_steps / max(len(self.steps), 1)) * 100
            ),
            "steps": self.steps,
            "artifacts": ExecutionArtifacts(
                video_path="",
                screenshot_failure=screenshot_failure
            ),
            "error": error_message
        }
    
    def _add_step(self, action: str, result: bool, latency: float, error: Optional[str] = None):
        self.steps.append(ExecutionStepSchema(
            action=action,
            result=result,
            latency=latency * 1000,
            error=error
        ))
    
    async def teardown(self) -> None:
        """Release STB hardware resources."""
        try:
            if self.vision:
                self.vision.disconnect()
            logger.info("STB adapter teardown complete")
        except Exception as e:
            logger.error(f"STB teardown error: {e}")


def get_adapter(device_type: DeviceType) -> BaseAutomationAdapter:
    """Factory function to get the appropriate adapter."""
    if device_type == DeviceType.WEB:
        return PlaywrightAdapter()
    elif device_type == DeviceType.STB:
        return STBAdapter()
    else:
        return AppiumAdapter()
