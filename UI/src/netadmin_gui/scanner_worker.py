"""
Scanner Worker - Background thread that calls MCP tools.

Runs network scans, device lookups, and other operations in a background
thread so the UI never freezes. Uses QRunnable + QThreadPool.
"""
from PySide6.QtCore import QRunnable, Signal, QThreadPool
from PySide6.QtGui import QFont


class ScannerWorker(QRunnable):
    """Runs a network scan in a background thread."""

    started = Signal(str)       # (message)
    progress = Signal(int, str) # (percentage, message)
    completed = Signal(dict)    # (devices dict)
    error = Signal(str)         # (error message)

    def __init__(self, config):
        super().__init__()
        self.setAutoDelete(True)
        self.config = config

    def run(self):
        """Execute the network scan."""
        import sys
        import os
        # Add project path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            from network_scanner_mcp.server import scan_network

            self.started.emit("Starting network scan...")
            self.progress.emit(10, "Initializing ARP scan...")

            # Parse config
            subnet = self.config.get("subnet")
            resolve = self.config.get("auto_resolve", True)

            if subnet == "":
                subnet = None

            self.progress.emit(30, f"Scanning {subnet or 'auto-detected subnet'}...")

            # Execute scan
            result = scan_network(subnet=subnet, resolve_names=resolve)

            self.progress.emit(70, "Processing results...")

            # Extract devices from result
            devices = {}
            if result and isinstance(result, dict):
                device_list = result.get("devices", [])
                new_list = result.get("new_devices", [])

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

            self.progress.emit(100, f"Found {len(devices)} devices")
            self.completed.emit(devices)

        except Exception as e:
            self.error.emit(f"Scan failed: {str(e)}")
            import traceback
            traceback.print_exc()


class PingWorker(QRunnable):
    """Ping a single device."""

    result = Signal(str, dict)  # (ip, result_dict)

    def __init__(self, target, count=3):
        super().__init__()
        self.setAutoDelete(True)
        self.target = target
        self.count = count

    def run(self):
        import sys, os
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            from network_scanner_mcp.server import ping_device
            result = ping_device(target=self.target, count=self.count)
            self.result.emit(self.target, result)
        except Exception as e:
            self.result.emit(self.target, {"success": False, "error": str(e)})


class HostnameWorker(QRunnable):
    """Resolve a device hostname."""

    result = Signal(str, str)  # (ip, hostname)

    def __init__(self, target):
        super().__init__()
        self.setAutoDelete(True)
        self.target = target

    def run(self):
        import sys, os
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            from network_scanner_mcp.server import resolve_device_hostname
            result = resolve_device_hostname(target=self.target)
            hostname = result.get("hostname", "unknown") if isinstance(result, dict) else "unknown"
            self.result.emit(self.target, hostname)
        except Exception as e:
            self.result.emit(self.target, "error")
