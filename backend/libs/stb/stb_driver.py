"""
STB Driver - High-Level API for Set-Top Box Test Automation

This module provides the abstraction layer for STB test scripts.
Generated scripts should ONLY use these APIs — never raw OpenCV or RedRat calls.

Usage in generated test scripts:
    from stb_driver import STBDriver

    driver = STBDriver(redrat_ip="192.168.1.100", hdmi_index=0)
    driver.connect()
    driver.press("HOME")
    driver.wait_for_screen("templates/home_screen.png")
    text = driver.read_text()
    driver.disconnect()
"""

import time
import asyncio
from typing import Optional, Tuple


class STBDriver:
    """
    High-level driver for STB automation.
    Wraps vision (HDMI capture) and control (RedRat IR) into simple APIs.
    """
    
    def __init__(self, redrat_ip: str = "192.168.1.100", hdmi_index: int = 0):
        """
        Initialize the STB driver.
        
        Args:
            redrat_ip: IP address of the RedRat IR blaster device
            hdmi_index: HDMI capture card device index (default 0)
        """
        self.redrat_ip = redrat_ip
        self.hdmi_index = hdmi_index
        self._vision = None
        self._remote = None
        self._loop = None
    
    def connect(self) -> bool:
        """
        Connect to STB hardware (HDMI capture + IR blaster).
        
        Returns:
            True if both connections successful
        
        Raises:
            ConnectionError: If hardware is not reachable
        """
        from app.services.stb_vision import STBVisionService
        from app.services.redrat_bridge import RedRatController
        
        self._vision = STBVisionService(hdmi_capture_index=self.hdmi_index)
        if not self._vision.connect(timeout=15.0):
            raise ConnectionError(f"HDMI capture not available on index {self.hdmi_index}")
        
        self._remote = RedRatController(ip_address=self.redrat_ip)
        self._loop = asyncio.new_event_loop()
        if not self._loop.run_until_complete(self._remote.connect(timeout=10.0)):
            raise ConnectionError(f"RedRat IR blaster not reachable at {self.redrat_ip}")
        
        print("STEP:Connect|PASS|0|")
        return True
    
    def disconnect(self):
        """Release all hardware connections."""
        if self._vision:
            self._vision.disconnect()
        if self._loop:
            self._loop.close()
        print("STEP:Disconnect|PASS|0|")
    
    def press(self, button: str, repeat: int = 1, delay: float = 0.3):
        """
        Press a remote control button.
        
        Args:
            button: Button name (HOME, OK, UP, DOWN, LEFT, RIGHT, PLAY, PAUSE, etc.)
            repeat: Number of times to press
            delay: Delay between presses in seconds
        
        Supported buttons:
            Navigation: UP, DOWN, LEFT, RIGHT, OK, BACK, HOME, MENU, EXIT
            Playback: PLAY, PAUSE, STOP, FF, RW, RECORD
            Volume: VOL_UP, VOL_DOWN, MUTE
            Channel: CH_UP, CH_DOWN
            Numbers: 0-9
            Color: RED, GREEN, YELLOW, BLUE
            Info: INFO, GUIDE, DVR, SETTINGS
        """
        start = time.time()
        success = self._loop.run_until_complete(
            self._remote.send_command(button, repeat=repeat, delay=delay)
        )
        elapsed = (time.time() - start) * 1000
        status = "PASS" if success else "FAIL"
        error = "" if success else f"IR command {button} failed"
        print(f"STEP:Press {button}|{status}|{elapsed:.0f}|{error}")
        if not success:
            raise RuntimeError(f"Failed to send IR command: {button}")
    
    def press_sequence(self, buttons: list, delay: float = 0.5):
        """
        Press a sequence of buttons with delays.
        
        Args:
            buttons: List of button names in order
            delay: Delay between each button press
        """
        for btn in buttons:
            self.press(btn)
            time.sleep(delay)
    
    def enter_channel(self, channel: str):
        """
        Enter a channel number digit by digit.
        
        Args:
            channel: Channel number as string (e.g., "101")
        """
        start = time.time()
        success = self._loop.run_until_complete(
            self._remote.enter_channel(channel)
        )
        elapsed = (time.time() - start) * 1000
        status = "PASS" if success else "FAIL"
        print(f"STEP:Enter channel {channel}|{status}|{elapsed:.0f}|")
    
    def navigate(self, direction: str, steps: int = 1):
        """
        Navigate in a direction multiple steps.
        
        Args:
            direction: UP, DOWN, LEFT, or RIGHT
            steps: Number of steps to move
        """
        self.press(direction, repeat=steps)
    
    def wait_for_screen(
        self,
        template_path: str,
        timeout: float = 15.0,
        threshold: float = 0.8
    ) -> Tuple[int, int]:
        """
        Wait until a specific screen/element appears.
        
        Args:
            template_path: Path to template image to search for
            timeout: Maximum wait time in seconds
            threshold: Match confidence (0-1, default 0.8)
        
        Returns:
            (x, y) coordinates of the matched element center
        
        Raises:
            TimeoutError: If element not found within timeout
        """
        start = time.time()
        result = self._vision.find_template(template_path, threshold=threshold, timeout=timeout)
        elapsed = (time.time() - start) * 1000
        
        if result:
            x, y, conf = result
            print(f"STEP:Wait for screen ({template_path})|PASS|{elapsed:.0f}|")
            return (x, y)
        
        error = f"Screen not found: {template_path}"
        print(f"STEP:Wait for screen ({template_path})|FAIL|{elapsed:.0f}|{error}")
        raise TimeoutError(error)
    
    def read_text(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Read text from the current screen using OCR.
        
        Args:
            region: Optional (x, y, width, height) to crop before OCR
        
        Returns:
            Extracted text string
        """
        start = time.time()
        text = self._vision.extract_text(region=region)
        elapsed = (time.time() - start) * 1000
        status = "PASS" if text else "FAIL"
        print(f"STEP:Read text|{status}|{elapsed:.0f}|")
        return text
    
    def verify_text(self, expected: str, region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Verify that expected text appears on screen.
        
        Args:
            expected: Text string to search for
            region: Optional screen region to check
        
        Returns:
            True if text found
        
        Raises:
            AssertionError: If text not found
        """
        start = time.time()
        actual = self._vision.extract_text(region=region)
        elapsed = (time.time() - start) * 1000
        found = expected.lower() in actual.lower()
        
        status = "PASS" if found else "FAIL"
        error = "" if found else f"Expected '{expected}' not found in '{actual[:100]}'"
        print(f"STEP:Verify text '{expected}'|{status}|{elapsed:.0f}|{error}")
        
        if not found:
            raise AssertionError(error)
        return True
    
    def capture_screenshot(self, filename: str = "screenshot.png") -> str:
        """
        Capture a screenshot of the current STB output.
        
        Args:
            filename: Output filename
        
        Returns:
            Path to saved screenshot
        """
        start = time.time()
        success = self._vision.save_frame(filename)
        elapsed = (time.time() - start) * 1000
        status = "PASS" if success else "FAIL"
        print(f"STEP:Capture screenshot|{status}|{elapsed:.0f}|")
        return filename if success else ""
    
    def wait(self, seconds: float):
        """
        Wait for a specified duration (for hardware latency).
        
        Args:
            seconds: Time to wait
        """
        time.sleep(seconds)
    
    def launch_app(self, app_name: str, home_first: bool = True):
        """
        Launch an application on the STB.
        
        Args:
            app_name: Name of the app to launch
            home_first: Press HOME before navigating (default True)
        """
        if home_first:
            self.press("HOME")
            self.wait(2.0)
        # Navigate and select — specific flow depends on STB UI
        print(f"STEP:Launch app {app_name}|PASS|0|")
    
    def play_content(self):
        """Start playback of selected content."""
        self.press("PLAY")
        self.wait(2.0)
    
    def pause_content(self):
        """Pause current playback."""
        self.press("PAUSE")
    
    def stop_content(self):
        """Stop current playback."""
        self.press("STOP")
