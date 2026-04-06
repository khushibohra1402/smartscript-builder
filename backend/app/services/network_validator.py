"""
Network Validator Service
Validates STB network device connectivity and subnet membership.
"""

import asyncio
import socket
import ipaddress
from typing import Dict, List, Optional, Tuple
from loguru import logger


class NetworkValidator:
    """Validates that STB hardware devices are reachable and on the same subnet."""

    @staticmethod
    def detect_local_ip() -> str:
        """Detect the laptop's local IP address."""
        try:
            # Connect to a non-routable address to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("10.254.254.254", 1))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    async def validate_network_device(ip: str, timeout: float = 3.0) -> bool:
        """Check if a device is reachable via TCP connect or ICMP ping."""
        # Try common ports first (HTTP 80, RedRat default, etc.)
        for port in [80, 443, 8080]:
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                return True
            except Exception:
                continue

        # Fall back to system ping
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", str(int(timeout)), ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
            return proc.returncode == 0
        except Exception:
            return False

    @staticmethod
    def check_same_subnet(ip1: str, ip2: str, prefix_length: int = 24) -> bool:
        """Check if two IP addresses are on the same /24 subnet."""
        try:
            net = ipaddress.ip_network(f"{ip1}/{prefix_length}", strict=False)
            return ipaddress.ip_address(ip2) in net
        except (ValueError, TypeError):
            return False

    async def validate_stb_network(
        self,
        stb_ip: str,
        rcu_ip: str,
        smart_plug_ip: Optional[str] = None,
    ) -> Dict:
        """
        Validate all STB network devices.
        Returns structured result with per-device status.
        """
        local_ip = self.detect_local_ip()
        issues: List[str] = []
        devices: Dict[str, str] = {}

        # Validate STB
        stb_reachable = await self.validate_network_device(stb_ip)
        if not stb_reachable:
            issues.append("STB device not reachable on network")
            devices["stb"] = "unreachable"
        elif not self.check_same_subnet(local_ip, stb_ip):
            issues.append("STB not on same network as host machine")
            devices["stb"] = "subnet_mismatch"
        else:
            devices["stb"] = "reachable"

        # Validate RCU
        rcu_reachable = await self.validate_network_device(rcu_ip)
        if not rcu_reachable:
            issues.append("RCU device not reachable")
            devices["rcu"] = "unreachable"
        elif not self.check_same_subnet(local_ip, rcu_ip):
            issues.append("RCU not on same network as host machine")
            devices["rcu"] = "subnet_mismatch"
        else:
            devices["rcu"] = "reachable"

        # Validate Smart Plug (optional)
        if smart_plug_ip:
            plug_reachable = await self.validate_network_device(smart_plug_ip)
            if not plug_reachable:
                issues.append("Smart plug connection failed")
                devices["smart_plug"] = "unreachable"
            elif not self.check_same_subnet(local_ip, smart_plug_ip):
                issues.append("Devices must be on same network as host machine")
                devices["smart_plug"] = "subnet_mismatch"
            else:
                devices["smart_plug"] = "reachable"

        return {
            "status": "failed" if issues else "success",
            "local_ip": local_ip,
            "devices": devices,
            "issues": issues if issues else None,
        }


# Global instance
network_validator = NetworkValidator()
