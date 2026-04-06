"""
Configuration Manager Service
Manages per-project STB hardware configuration (configuration.json).
"""

import json
from pathlib import Path
from typing import Optional
from loguru import logger

from app.config import settings


DEFAULT_STB_CONFIG = {
    "stb": {
        "model": "G4",
        "type": "Production",
        "ip": ""
    },
    "rcu": {
        "type": "IRRX",
        "ip": ""
    },
    "smart_plug": {
        "enabled": False,
        "ip": ""
    },
    "capture_card": {
        "hdmi_index": 0
    }
}


class ConfigManager:
    """Manages per-project configuration.json files for STB hardware setup."""

    def _config_path(self, project_name: str) -> Path:
        return settings.PROJECTS_ROOT / project_name / "configuration.json"

    def load_project_config(self, project_name: str) -> dict:
        """Load project configuration. Returns defaults if file doesn't exist."""
        path = self._config_path(project_name)
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load config for {project_name}: {e}")
        return dict(DEFAULT_STB_CONFIG)

    def save_config(self, project_name: str, config: dict) -> Path:
        """Save configuration to project directory."""
        path = self._config_path(project_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved: {path}")
        return path

    def update_stb_config(
        self,
        project_name: str,
        stb_model: Optional[str] = None,
        stb_type: Optional[str] = None,
        stb_ip: Optional[str] = None,
        rcu_type: Optional[str] = None,
        rcu_ip: Optional[str] = None,
        smart_plug_enabled: Optional[bool] = None,
        smart_plug_ip: Optional[str] = None,
        hdmi_index: Optional[int] = None,
    ) -> dict:
        """Update STB-specific fields in the project configuration."""
        config = self.load_project_config(project_name)

        if stb_model is not None:
            config.setdefault("stb", {})["model"] = stb_model
        if stb_type is not None:
            config.setdefault("stb", {})["type"] = stb_type
        if stb_ip is not None:
            config.setdefault("stb", {})["ip"] = stb_ip
        if rcu_type is not None:
            config.setdefault("rcu", {})["type"] = rcu_type
        if rcu_ip is not None:
            config.setdefault("rcu", {})["ip"] = rcu_ip
        if smart_plug_enabled is not None:
            config.setdefault("smart_plug", {})["enabled"] = smart_plug_enabled
        if smart_plug_ip is not None:
            config.setdefault("smart_plug", {})["ip"] = smart_plug_ip
        if hdmi_index is not None:
            config.setdefault("capture_card", {})["hdmi_index"] = hdmi_index

        self.save_config(project_name, config)
        return config

    def get_environment_summary(self, project_name: str) -> str:
        """
        Return a human-readable summary of the STB environment
        for injection into LLM prompts.
        """
        config = self.load_project_config(project_name)
        stb = config.get("stb", {})
        rcu = config.get("rcu", {})
        plug = config.get("smart_plug", {})
        capture = config.get("capture_card", {})

        lines = [
            "Environment Configuration:",
            f"  STB Model: {stb.get('model', 'Unknown')}",
            f"  STB Type: {stb.get('type', 'Unknown')}",
            f"  STB IP: {stb.get('ip', 'Not set')}",
            f"  RCU Type: {rcu.get('type', 'Unknown')}",
            f"  RCU IP: {rcu.get('ip', 'Not set')}",
            f"  Smart Plug: {'Enabled' if plug.get('enabled') else 'Disabled'}",
        ]
        if plug.get("enabled"):
            lines.append(f"  Smart Plug IP: {plug.get('ip', 'Not set')}")
        lines.append(f"  HDMI Capture Index: {capture.get('hdmi_index', 0)}")
        return "\n".join(lines)


# Global instance
config_manager = ConfigManager()
