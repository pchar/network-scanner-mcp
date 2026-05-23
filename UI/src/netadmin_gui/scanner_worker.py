"""
Scanner Worker - Background thread that calls MCP tools.

Uses QThread + QObject pattern so signals work correctly.
All MCP server functions are async, so we use asyncio.run() to execute them
synchronously within the worker thread.
"""
import asyncio
import json
from PySide6.QtCore import QThread, Signal, QObject


class ScanWorkerSignals(QObject):
    started = Signal(str)
    progress = Signal(int, str)
    completed = Signal(dict)
    error = Signal(str)


class PingWorkerSignals(QObject):
    result = Signal(str, dict)


class HostnameWorkerSignals(QObject):
    result = Signal(str, str)


def run_scan(config, signals):
    """Execute scan in a worker object."""
    import sys, os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from network_scanner_mcp.server import scan_network

        signals.started.emit("Starting network scan...")
        signals.progress.emit(10, "Initializing ARP scan...")

        subnet = config.get("subnet")
        resolve = config.get("auto_resolve", True)
        if subnet == "":
            subnet = None

        signals.progress.emit(30, f"Scanning {subnet or 'auto-detected subnet'}...")
        # server.scan_network is async and returns a JSON string
        raw = asyncio.run(scan_network(subnet=subnet, resolve_names=resolve))
        result = json.loads(raw) if isinstance(raw, str) else raw
        signals.progress.emit(70, "Processing results...")

        devices = {}
        if result and isinstance(result, dict):
            device_list = result.get("devices", [])
            for device in device_list:
                ip = device.get("ip", "")
                if ip:
                    devices[ip] = {
                        "ip": ip,
                        "mac": device.get("mac", ""),
                        "hostname": device.get("hostname") or "",
                        "vendor": device.get("vendor", "Unknown"),
                        "first_seen": device.get("first_seen", ""),
                        "last_seen": device.get("last_seen", ""),
                        "seen_count": device.get("seen_count", 1),
                        "is_known": False,
                        "is_cluster_node": False,
                        "ports": [],
                        "services": [],
                    }

        signals.progress.emit(100, f"Found {len(devices)} devices")
        signals.completed.emit(devices)

    except Exception as e:
        signals.error.emit(f"Scan failed: {str(e)}")
        import traceback
        traceback.print_exc()


def run_ping(target, count, signals):
    import sys, os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from network_scanner_mcp.server import ping_device
        # server.ping_device is async
        result = asyncio.run(ping_device(target=target, count=count))
        signals.result.emit(target, result)
    except Exception as e:
        signals.result.emit(target, {"success": False, "error": str(e)})


def run_hostname(target, signals):
    import sys, os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from network_scanner_mcp.server import resolve_device_hostname
        # server.resolve_device_hostname is async
        result = asyncio.run(resolve_device_hostname(target=target))
        hostname = result.get("hostname", "unknown") if isinstance(result, dict) else "unknown"
        signals.result.emit(target, hostname)
    except Exception as e:
        signals.result.emit(target, "error")
