# Network Scanner GUI

Native macOS network scanner application using PySide6 with in-process MCP tools.

## Quick Start

```bash
cd /Users/pch/MyProjects/Sandbox/network-scanner-mcp/ui
PYTHONPATH=../src python3 -m src.netadmin_gui
```

Or use the launcher:

```bash
chmod +x run.sh
./run.sh
```

## What It Does

- Scans your local network for devices using ARP (via the in-process MCP server)
- Persists device history between app restarts (saves to `~/Library/Application Support/Network Scanner/devices.json`)
- Tracks device status with color indicators:
  - 🟢 Green = device was present AND still reachable
  - 🔴 Red = device was present but now offline
  - ⚪ Grey = brand new device (first time seen)
- Automatically detects which devices are unreachable from previous scans
- Clean offline devices button to remove unreachable hosts

## Features

### Toolbar
- **Scan Network** - Start a new network scan (Quick or Full)
- **Interface selector** - Choose which network interface to scan (en0, en1, etc.)
- **Auto-scan** - Configure interval (Off, 30s, 1m, 5m, 15m) for continuous monitoring
- **Clean Offline** - Remove all devices that are now unreachable (with confirmation)

### Device Table
- Sortable columns: Status, IP, Hostname, MAC, Vendor, First Seen, Last Seen
- Search/filter by IP or hostname
- Status filter: All, Online, Offline, New
- Click a row to see detailed info in the sidebar
- Double-click for quick actions

### Device Detail Sidebar
- Full device information display
- Ping device
- Resolve hostname via reverse DNS
- Port scan capability

### Log Panel
- Color-coded log messages (INFO, WARN, ERROR, SUCCESS)
- Timestamped entries
- Toggle visibility with Ctrl+L

## Architecture

```
src/netadmin_gui/
├── main_window.py      # Main window, scan workflow, device storage
├── tools.py            # MCP tools import (scan_network, get_device_info, etc.)
├── scanner_worker.py   # Background workers (QRunnable) for non-blocking scans
├── settings.py         # Persistent JSON storage + status computation
├── widgets/
│   ├── device_table.py   # Table with colored status indicators
│   ├── device_detail.py  # Sidebar detail panel
│   ├── log_panel.py      # Debug output display
│   └── toolbar.py        # Scan controls
```

## Dependencies

- PySide6 (installed via pip)
- network-scanner-mcp (imported directly, no separate process)

## Data Storage

- **Device history**: `~/Library/Application Support/Network Scanner/devices.json`
- **Settings**: `~/Library/Application Support/Network Scanner/settings.json`

## Troubleshooting

If the app crashes on startup:
1. Make sure network-scanner-mcp is installed: `cd ../.. && pip3 install -e .`
2. Check that arp-scan is installed: `which arp-scan`
3. Clear old data: `rm ~/Library/Application\ Support/Network\ Scanner/devices.json`
