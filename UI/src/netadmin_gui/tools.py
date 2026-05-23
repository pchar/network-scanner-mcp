"""
MCP Tools - Direct in-process MCP server integration.

Wraps the network-scanner-mcp tool functions for direct in-process calls.
"""
import sys
import os

# Add the project src to path so we can import MCP tools
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from network_scanner_mcp.server import (
        mcp,
        scan_network,
        get_device_info,
        get_network_topology,
        get_scanner_status,
        ping_device,
        resolve_device_hostname,
        mark_device_known,
        remove_device_known,
        get_device_history,
        get_unknown_devices,
        discover_services,
        scan_device_ports,
    )
    from network_scanner_mcp.alert_daemon import INTERFACE, DATA_DIR
except ImportError as e:
    raise RuntimeError(
        f"Cannot import MCP tools. Make sure network-scanner-mcp is installed. "
        f"Error: {e}"
    )

from datetime import datetime


# ─── Scanner Tools ──────────────────────────────────────────────────────────


class ScannerTools:
    """Wrapper for all MCP scanner tools."""

    @staticmethod
    def scan_network(subnet=None, resolve_names=True):
        """Run a full network scan."""
        return scan_network(subnet=subnet, resolve_names=resolve_names)

    @staticmethod
    def get_device_info(identifier):
        """Get info about a specific device."""
        return get_device_info(identifier)

    @staticmethod
    def get_network_topology():
        """Get full network topology."""
        return get_network_topology()

    @staticmethod
    def get_scanner_status():
        """Get scanner status."""
        return get_scanner_status()

    @staticmethod
    def ping_device(target, count=3):
        """Ping a device."""
        return ping_device(target=target, count=count)

    @staticmethod
    def resolve_device_hostname(target):
        """Resolve a hostname via reverse DNS."""
        return resolve_device_hostname(target=target)

    @staticmethod
    def mark_device_known(mac, label, device_type="trusted"):
        """Mark a device as known."""
        return mark_device_known(mac=mac, label=label, device_type=device_type)

    @staticmethod
    def remove_device_known(mac):
        """Remove a known device."""
        return remove_device_known(mac=mac)

    @staticmethod
    def get_device_history(mac=None):
        """Get device history."""
        return get_device_history(mac=mac)

    @staticmethod
    def get_unknown_devices():
        """Get unknown devices."""
        return get_unknown_devices()

    @staticmethod
    def discover_services():
        """Discover services on all known devices."""
        return discover_services()

    @staticmethod
    def scan_device_ports(target, ports=None, quick=True):
        """Scan ports on a device."""
        return scan_device_ports(target=target, ports=ports, quick=quick)


# ─── Interface Discovery ────────────────────────────────────────────────────


def get_available_interfaces():
    """Get list of available network interfaces on the system."""
    try:
        import netifaces
        ifaces = netifaces.interfaces()
        return ifaces
    except ImportError:
        return ["en0"]


def get_interface_info(interface_name):
    """Get IP and subnet info for an interface."""
    try:
        import netifaces
        addrs = netifaces.ifaddresses(interface_name)
        ipv4 = addrs.get(netifaces.AF_INET, [{}])[0]
        ipv6 = addrs.get(netifaces.AF_INET6, [{}])[0]
        return {
            "name": interface_name,
            "ip": ipv4.get("addr"),
            "netmask": ipv4.get("netmask"),
            "broadcast": ipv4.get("broadcast"),
            "family": "IPv6" if "inet6" in ipv6 else "IPv4",
        }
    except Exception:
        return {"name": interface_name}
