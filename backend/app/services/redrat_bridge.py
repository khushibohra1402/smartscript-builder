"""
RedRat IR Blaster Bridge - Remote Control for STB
Sends IR commands to Set-Top Box hardware via RedRat device.
"""

import time
import asyncio
from typing import Optional, Dict, List
from loguru import logger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# Standard IR command set for STB remotes
STB_COMMANDS = [
    "POWER", "HOME", "MENU", "BACK", "EXIT",
    "UP", "DOWN", "LEFT", "RIGHT", "OK", "SELECT",
    "PLAY", "PAUSE", "STOP", "FF", "RW", "RECORD",
    "VOL_UP", "VOL_DOWN", "MUTE",
    "CH_UP", "CH_DOWN",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "RED", "GREEN", "YELLOW", "BLUE",
    "INFO", "GUIDE", "DVR", "SETTINGS",
]


class RedRatController:
    """
    Controls a Set-Top Box via RedRat IR Blaster.
    
    Communication is HTTP-based, sending IR signal names 
    to the RedRat device which transmits the corresponding IR code.
    """
    
    def __init__(self, ip_address: str, port: int = 80):
        self.ip_address = ip_address
        self.port = port
        self.base_url = f"http://{ip_address}:{port}"
        self._connected = False
        self._command_delay = 0.3  # seconds between commands
    
    async def connect(self, timeout: float = 10.0) -> bool:
        """
        Verify connectivity to the RedRat device.
        
        Returns:
            True if device is reachable
        """
        if not HTTPX_AVAILABLE:
            logger.error("httpx not installed. Run: pip install httpx")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self.base_url}/status")
                if response.status_code == 200:
                    self._connected = True
                    logger.info(f"RedRat connected at {self.base_url}")
                    return True
                    
                # Some RedRat devices respond on different endpoints
                response = await client.get(f"{self.base_url}/")
                if response.status_code in (200, 204):
                    self._connected = True
                    logger.info(f"RedRat connected at {self.base_url} (root endpoint)")
                    return True
                    
        except httpx.ConnectError:
            logger.error(f"RedRat not reachable at {self.base_url}")
        except httpx.TimeoutException:
            logger.error(f"RedRat connection timed out at {self.base_url}")
        except Exception as e:
            logger.error(f"RedRat connection failed: {e}")
        
        self._connected = False
        return False
    
    async def send_command(
        self,
        command_name: str,
        repeat: int = 1,
        delay: Optional[float] = None
    ) -> bool:
        """
        Send an IR command to the STB.
        
        Args:
            command_name: IR signal name (e.g., "HOME", "OK", "PLAY")
            repeat: Number of times to send the command
            delay: Custom delay between repeated commands
            
        Returns:
            True if command was sent successfully
        """
        cmd = command_name.upper()
        if cmd not in STB_COMMANDS:
            logger.warning(f"Unknown IR command: {cmd} (sending anyway)")
        
        inter_delay = delay or self._command_delay
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                for i in range(repeat):
                    response = await client.post(
                        f"{self.base_url}/send",
                        json={"signal": cmd}
                    )
                    
                    if response.status_code not in (200, 204):
                        logger.error(f"IR command '{cmd}' failed: HTTP {response.status_code}")
                        return False
                    
                    logger.debug(f"IR sent: {cmd} ({i+1}/{repeat})")
                    
                    if i < repeat - 1:
                        await asyncio.sleep(inter_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send IR command '{cmd}': {e}")
            return False
    
    async def send_sequence(
        self,
        commands: List[str],
        delay: Optional[float] = None
    ) -> bool:
        """
        Send a sequence of IR commands with delays.
        
        Args:
            commands: List of command names in order
            delay: Delay between each command
            
        Returns:
            True if all commands sent successfully
        """
        inter_delay = delay or self._command_delay
        
        for cmd in commands:
            success = await self.send_command(cmd)
            if not success:
                logger.error(f"Sequence failed at command: {cmd}")
                return False
            await asyncio.sleep(inter_delay)
        
        return True
    
    async def navigate(self, direction: str, steps: int = 1) -> bool:
        """Navigate in a direction (UP/DOWN/LEFT/RIGHT) multiple steps."""
        direction = direction.upper()
        if direction not in ("UP", "DOWN", "LEFT", "RIGHT"):
            logger.error(f"Invalid direction: {direction}")
            return False
        return await self.send_command(direction, repeat=steps)
    
    async def enter_channel(self, channel_number: str) -> bool:
        """Enter a channel number digit by digit."""
        for digit in str(channel_number):
            if digit not in "0123456789":
                continue
            success = await self.send_command(digit)
            if not success:
                return False
            await asyncio.sleep(0.2)
        return True
    
    def is_connected(self) -> bool:
        return self._connected
    
    def set_command_delay(self, delay: float):
        """Set delay between IR commands (seconds)."""
        self._command_delay = max(0.1, delay)
