"""
Main Window - The main application window.

Ties together the toolbar, device table, detail sidebar, and log panel.
Handles the scan workflow: load old data → run scan → compare → update UI.
"""
import sys
import os
import json
from datetime import datetime

# Add project src to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMessageBox, QMenuBar, QMenu,
    QApplication, QStyleFactory,
)
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from PySide6.QtCore import Qt, QTimer

from .widgets.device_table import DeviceTable
from .widgets.device_detail import DeviceDetail
from .widgets.log_panel import LogPanel
from .widgets.toolbar import Toolbar
from .settings import DeviceStore, SettingsStore, compute_device_status, get_status_emoji
from .scanner_worker import ScanWorkerSignals, PingWorkerSignals, HostnameWorkerSignals, run_scan, run_ping, run_hostname
from . import tools as scanner_tools

from PySide6.QtCore import QThread


class MainWindow(QMainWindow):
    """Main application window for the Network Scanner."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Scanner")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # ── Persistent storage ──
        self.device_store = DeviceStore()
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()

        # ── State ──
        self.devices = {}           # {ip: device_dict} with status
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self._on_timer_scan)

        # ── Build UI ──
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central_widget()
        self._load_initial_devices()
        self._apply_interface_config()

    def _build_menu_bar(self):
        """Create the macOS-style menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        scan_action = file_menu.addAction("Scan Network...")
        scan_action.setShortcut("Ctrl+S")
        scan_action.triggered.connect(self._on_scan)
        file_menu.addSeparator()
        clean_action = file_menu.addAction("Clean Offline Devices")
        clean_action.setShortcut("Ctrl+Shift+Del")
        clean_action.triggered.connect(self._on_clean)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Quit")
        exit_action.setShortcut("Cmd+Q")
        exit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu("View")
        toggle_log = view_menu.addAction("Toggle Log Panel")
        toggle_log.setShortcut("Ctrl+L")
        toggle_log.triggered.connect(self._toggle_log)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About Network Scanner")
        about_action.triggered.connect(self._show_about)

    def _build_toolbar(self):
        """Create the toolbar widget."""
        self.toolbar = Toolbar()

        # Connect toolbar signals
        self.toolbar.scan_requested.connect(self._on_scan)
        self.toolbar.toggle_continuous.connect(self._on_toggle_continuous)
        self.toolbar.clean_requested.connect(self._on_clean)
        self.toolbar.auto_detect_requested.connect(self._on_auto_detect_subnet)

    def _build_central_widget(self):
        """Build the central widget with split panes."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ── Toolbar at top ──
        main_layout.addWidget(self.toolbar)

        # ── Splitter: Table + Detail Sidebar ──
        splitter = QSplitter(Qt.Horizontal)

        # Device table (left, expands)
        self.device_table = DeviceTable()
        self.device_table.device_selected.connect(self._on_device_selected)
        self.device_table.device_double_clicked.connect(self._on_device_double_clicked)
        splitter.addWidget(self.device_table)

        # Device detail (right, fixed width)
        self.device_detail = DeviceDetail()
        self.device_detail.ping_requested.connect(self._on_ping)
        self.device_detail.hostname_requested.connect(self._on_hostname)
        self.device_detail.portscan_requested.connect(self._on_portscan)
        splitter.addWidget(self.device_detail)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([800, 300])

        main_layout.addWidget(splitter)

        # ── Log Panel (bottom, collapsible) ──
        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

    def _load_initial_devices(self):
        """Load previously saved devices on startup."""
        old_devices = self.device_store.load()
        if old_devices:
            self.devices = old_devices
            self.device_table.set_devices(self.devices)
            self._update_counts()
            self.log_panel.log_success(f"Loaded {len(old_devices)} devices from previous session")
        else:
            self.log_panel.log_info("No previous scan data found. Run a scan to begin.")

    def _apply_interface_config(self):
        """Populate interface list from system."""
        try:
            interfaces = scanner_tools.get_available_interfaces()
            self.toolbar.update_interface_list(interfaces)
        except Exception:
            pass

    # ── Scan Workflow ──────────────────────────────────────────────────────

    def _on_scan(self):
        """Start a network scan."""
        if self.toolbar.btn_scan.isEnabled():
            self._execute_scan()

    def _execute_scan(self):
        """Execute the scan using a background thread."""
        config = self.toolbar.get_config()

        # Save current settings
        self.settings["subnet"] = config["subnet"]
        self.settings["scan_depth"] = config["scan_depth"]
        self.settings["auto_resolve"] = config["auto_resolve"]
        self.settings_store.save(self.settings)

        # Disable controls during scan
        self.toolbar.set_scan_button_enabled(False)
        self.log_panel.log_info(f"Starting scan: interface={config['interface']}, resolve={config['auto_resolve']}")

        # Create thread + signals (QObject pattern — signals work correctly)
        self._scan_thread = QThread()
        signals = ScanWorkerSignals()

        # Connect signals BEFORE moving to thread
        signals.started.connect(self.log_panel.log_info)
        signals.progress.connect(self._on_scan_progress)
        signals.completed.connect(self._on_scan_complete)
        signals.error.connect(self._on_scan_error)

        # Connect thread started → run scan
        def _do_scan():
            run_scan(config, signals)

        self._scan_thread.started.connect(_do_scan)
        # When thread finishes, clean up thread
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        # Re-enable buttons when done
        def _on_done():
            self.toolbar.set_scan_button_enabled(True)
            if self._is_continuous:
                # Schedule next scan based on interval
                interval = self.settings.get("interval", 0)
                if interval > 0:
                    self._scan_timer.start(interval * 1000)
        self._scan_thread.finished.connect(_on_done)

        self._scan_thread.start()

    def _on_scan_progress(self, percent, message):
        """Handle scan progress updates."""
        self.log_panel.log_info(message)

    def _on_scan_complete(self, new_devices):
        """Process scan completion and update the UI."""
        self.log_panel.log_success(f"Scan complete: {len(new_devices)} devices found")

        # Compute status for each device
        self.devices = compute_device_status(self.devices, new_devices)

        # Log status changes
        for ip, device in self.devices.items():
            status = device.get("status", "new")
            if status == "unreachable":
                hostname = device.get("hostname", ip)
                self.log_panel.log_warn(f"[RED] {ip} ({hostname}) — previously online, now OFFLINE")
            elif status == "online":
                self.log_panel.log_success(f"[GREEN] {ip} — confirmed online")
            elif status == "new":
                self.log_panel.log_info(f"[NEW] {ip} — newly discovered")

        # Update UI
        self.device_table.set_devices(self.devices)
        self._update_counts()

        # Save to disk
        self.device_store.save(self.devices)

        # Re-enable scan button
        self.toolbar.set_scan_button_enabled(True)

        # Update interval timer
        interval = self.settings.get("interval", 0)
        if interval > 0:
            self.scan_timer.start(interval * 1000)

    def _on_scan_error(self, error_msg):
        """Handle scan errors."""
        self.log_panel.log_error(f"Scan error: {error_msg}")
        self.toolbar.set_scan_button_enabled(True)

    def _on_timer_scan(self):
        """Auto-scan triggered by timer."""
        self.log_panel.log_info("Auto-scan triggered by timer")
        self._execute_scan()

    def _update_counts(self):
        """Update the stats label with current counts."""
        total = len(self.devices)
        offline = sum(1 for d in self.devices.values() if d.get("status") == "unreachable")
        new_count = sum(1 for d in self.devices.values() if d.get("status") == "new")
        self.toolbar.set_device_counts(total, offline, new_count)
        self.toolbar.set_offline_count(offline)

    # ── Cleanup ────────────────────────────────────────────────────────────

    def _on_clean(self):
        """Remove all unreachable devices."""
        unreachable = [ip for ip, d in self.devices.items() if d.get("status") == "unreachable"]
        if not unreachable:
            self.log_panel.log_info("No offline devices to clean")
            return

        count = len(unreachable)
        reply = QMessageBox.question(
            self, "Clean Offline Devices",
            f"Delete {count} offline device(s)?\n\n"
            f"{', '.join(unreachable[:5])}" + ("..." if len(unreachable) > 5 else ""),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            for ip in unreachable:
                del self.devices[ip]
            self.device_store.save(self.devices)
            self.device_table.set_devices(self.devices)
            self._update_counts()
            self.log_panel.log_success(f"Deleted {count} offline device(s)")

    # ── Device Selection ───────────────────────────────────────────────────

    def _on_device_selected(self, device):
        """Handle device row selection."""
        self.device_detail.set_device(device)

    def _on_device_double_clicked(self, device):
        """Handle device row double-click."""
        status = device.get("status", "new")
        if status == "unreachable":
            self.log_panel.log_warn(f"Device {device['ip']} is offline")
        else:
            self.log_panel.log_info(f"Selected {device['ip']}")

    # ── Device Actions ─────────────────────────────────────────────────────

    def _on_ping(self, target_ip):
        """Ping a selected device."""
        self.log_panel.log_info(f"Pinging {target_ip}...")
        thread = QThread()
        signals = PingWorkerSignals()
        signals.result.connect(self._on_ping_result)
        signals.result.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        signals.result.connect(signals.deleteLater)
        thread.started.connect(lambda: run_ping(target_ip, 3, signals))
        thread.start()

    def _on_ping_result(self, ip, result):
        """Handle ping result."""
        success = result.get("success", False) if isinstance(result, dict) else False
        if success:
            self.log_panel.log_success(f"{ip} is reachable")
        else:
            self.log_panel.log_warn(f"{ip} is unreachable")

    def _on_hostname(self, target_ip):
        """Resolve hostname for a device."""
        self.log_panel.log_info(f"Resolving hostname for {target_ip}...")
        thread = QThread()
        signals = HostnameWorkerSignals()
        signals.result.connect(self._on_hostname_result)
        signals.result.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        signals.result.connect(signals.deleteLater)
        thread.started.connect(lambda: run_hostname(target_ip, signals))
        thread.start()

    def _on_hostname_result(self, ip, hostname):
        """Handle hostname resolution result."""
        self.log_panel.log_info(f"{ip} → {hostname}")

    def _on_portscan(self, target_ip):
        """Start port scan on a device."""
        self.log_panel.log_info(f"Port scanning {target_ip}...")
        self.log_panel.log_info("Port scanning requires additional tool implementation")

    # ── Continuous Scan Control ────────────────────────────────────────────

    def _on_toggle_continuous(self, running):
        """Handle start/stop continuous scan toggle."""
        if running:
            self.log_panel.log_info("Continuous scanning STARTED")
        else:
            self.scan_timer.stop()
            self.log_panel.log_info("Continuous scanning STOPPED")

    def _on_auto_detect_subnet(self, interface):
        """Auto-detect the subnet for the given interface."""
        self.log_panel.log_info(f"Auto-detecting subnet on {interface}...")
        try:
            import netifaces
            addrs = netifaces.ifaddresses(interface)
            ipv4 = addrs.get(netifaces.AF_INET, [])
            if ipv4:
                addr = ipv4[0]['addr']
                netmask = ipv4[0]['netmask']
                import ipaddress
                iface = ipaddress.IPv4Interface(f"{addr}/{netmask}")
                network = iface.network
                subnet = str(network)
                self.toolbar.le_subnet.setText(subnet)
                self.log_panel.log_success(f"Detected subnet: {subnet}")
            else:
                self.log_panel.log_warn(f"No IPv4 address found on {interface}")
        except Exception as e:
            self.log_panel.log_error(f"Auto-detect failed: {e}")

    # ── UI Helpers ─────────────────────────────────────────────────────────

    def _toggle_log(self):
        """Toggle log panel visibility."""
        visible = not self.log_panel.isVisible()
        self.log_panel.setVisible(visible)
        self.log_panel.log_info(f"Log panel {'shown' if visible else 'hidden'}")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Network Scanner",
            "Network Scanner\n\n"
            "A macOS native network discovery tool.\n"
            "Uses in-process MCP tools for network scanning.\n\n"
            f"PySide6 {QApplication.platform_name()}"
        )

    def closeEvent(self, event):
        """Save state on app close."""
        if self.devices:
            self.device_store.save(self.devices)
            self.log_panel.log_info("Saved device data before closing")
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Network Scanner")
    app.setOrganizationName("Network Scanner")
    app.setStyle("Fusion")  # Cross-platform consistent look

    # Dark mode preference
    try:
        # Try to set dark style
        dark_palette = app.style().standardPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        app.setPalette(dark_palette)
    except Exception:
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
