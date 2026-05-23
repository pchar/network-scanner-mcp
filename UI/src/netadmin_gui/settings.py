"""
Network Scanner GUI - Persistent Settings & Device Storage

Handles saving/loading device history between app sessions and
persistent settings (scan config, interface preferences).
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


# ─── Device Storage ────────────────────────────────────────────────────────


class DeviceStore:
    """Persistent storage for scanned devices. JSON file on disk."""

    def __init__(self, path: Optional[str] = None):
        if path is None:
            # macOS standard location: ~/Library/Application Support/
            app_dir = Path.home() / "Library" / "Application Support" / "Network Scanner"
            app_dir.mkdir(parents=True, exist_ok=True)
            path = str(app_dir / "devices.json")
        self.path = path

    def load(self) -> dict:
        """Load device history from disk. Returns {ip: device_dict}."""
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            return {}

    def save(self, devices: dict):
        """Save device history to disk."""
        try:
            with open(self.path, "w") as f:
                json.dump(devices, f, indent=2)
        except IOError as e:
            print(f"Failed to save devices: {e}")

    def get(self, key: str) -> Optional[dict]:
        """Get a single device by key."""
        devices = self.load()
        return devices.get(key)

    def get_all(self) -> dict:
        """Get all devices."""
        return self.load()

    def delete(self, key: str):
        """Delete a single device."""
        devices = self.load()
        devices.pop(key, None)
        self.save(devices)

    def delete_unreachable(self) -> int:
        """Delete all unreachable devices. Returns count deleted."""
        devices = self.load()
        to_remove = [k for k, v in devices.items() if v.get("status") == "unreachable"]
        for k in to_remove:
            del devices[k]
        self.save(devices)
        return len(to_remove)


# ─── Settings Storage ──────────────────────────────────────────────────────


class SettingsStore:
    """Persistent settings (scan config, app state)."""

    def __init__(self, path: Optional[str] = None):
        if path is None:
            app_dir = Path.home() / "Library" / "Application Support" / "Network Scanner"
            app_dir.mkdir(parents=True, exist_ok=True)
            path = str(app_dir / "settings.json")
        self.path = path

    def load(self) -> dict:
        """Load settings."""
        if not os.path.exists(self.path):
            return self._default_settings()
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            return self._default_settings()

    def save(self, settings: dict):
        """Save settings."""
        try:
            with open(self.path, "w") as f:
                json.dump(settings, f, indent=2)
        except IOError as e:
            print(f"Failed to save settings: {e}")

    def _default_settings(self) -> dict:
        return {
            "subnet": "172.30.200.0/24",
            "interface": "en0",
            "scan_depth": "quick",        # quick or full
            "auto_resolve": True,
            "interval": 0,                # 0 = off, else seconds
            "port_range": "common",       # common or specific
            "window_geometry": None,
            "window_state": None,
        }

    def get_all(self) -> dict:
        return self.load()


# ─── Status Computation ────────────────────────────────────────────────────


def compute_device_status(old_devices: dict, new_devices: list) -> dict:
    """
    Compare new scan results with existing history.
    Returns updated {ip: device_dict} with status computed.
    
    Status rules:
    - 'online'      = was seen before AND still reachable
    - 'unreachable' = was seen before but now gone
    - 'new'         = brand new (first time seen)
    """
    existing = {d["ip"]: d for d in new_devices}
    result = {}

    for ip, device in existing.items():
        if ip in old_devices:
            device["status"] = "online"
        else:
            device["status"] = "new"

    # Check for previously seen devices that are now gone
    for ip, old_device in old_devices.items():
        if ip not in existing:
            old_device["status"] = "unreachable"
            result[ip] = old_device

    # Merge new + remaining online devices
    for ip, device in existing.items():
        if ip not in result:
            result[ip] = device

    return result


def get_status_color(status: str) -> str:
    """Return CSS/Qt color for device status."""
    colors = {
        "online": "#27ae60",       # green
        "unreachable": "#e74c3c",  # red
        "new": "#95a5a6",          # grey
    }
    return colors.get(status, "#95a5a6")


def get_status_emoji(status: str) -> str:
    """Return emoji for device status."""
    emojis = {
        "online": "🟢",
        "unreachable": "🔴",
        "new": "⚪",
    }
    return emojis.get(status, "⚪")
