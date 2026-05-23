"""
Device Detail - Sidebar panel showing detailed info for selected device.
"""
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QLabel,
    QTextEdit, QPushButton, QHBoxLayout,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal


class DeviceDetail(QGroupBox):
    """Shows detailed information about the selected device."""

    ping_requested = Signal(str)     # Signal(ip)
    hostname_requested = Signal(str) # Signal(ip)
    portscan_requested = Signal(str) # Signal(ip)

    def __init__(self, parent=None):
        super().__init__("Device Details", parent)
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Basic Info ──
        info_group = QGroupBox("Information")
        info_layout = QFormLayout()
        info_layout.setSpacing(6)

        self.lbl_ip = QLabel("-")
        self.lbl_mac = QLabel("-")
        self.lbl_hostname = QLabel("-")
        self.lbl_vendor = QLabel("-")
        self.lbl_status = QLabel("-")
        self.lbl_first_seen = QLabel("-")
        self.lbl_last_seen = QLabel("-")
        self.lbl_known = QLabel("-")

        info_layout.addRow("IP:", self.lbl_ip)
        info_layout.addRow("MAC:", self.lbl_mac)
        info_layout.addRow("Hostname:", self.lbl_hostname)
        info_layout.addRow("Vendor:", self.lbl_vendor)
        info_layout.addRow("Status:", self.lbl_status)
        info_layout.addRow("First Seen:", self.lbl_first_seen)
        info_layout.addRow("Last Seen:", self.lbl_last_seen)
        info_layout.addRow("Known:", self.lbl_known)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ── Actions ──
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        self.btn_ping = QPushButton("Ping Device")
        self.btn_ping.clicked.connect(self._on_ping)
        actions_layout.addWidget(self.btn_ping)

        self.btn_hostname = QPushButton("Resolve Hostname")
        self.btn_hostname.clicked.connect(self._on_hostname)
        actions_layout.addWidget(self.btn_hostname)

        self.btn_portscan = QPushButton("Port Scan")
        self.btn_portscan.clicked.connect(self._on_portscan)
        actions_layout.addWidget(self.btn_portscan)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # ── Raw Data ──
        raw_group = QGroupBox("Raw Data")
        raw_layout = QVBoxLayout()
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Menlo", 8))
        self.raw_text.setMaximumHeight(150)
        raw_layout.addWidget(self.raw_text)
        raw_group.setLayout(raw_layout)
        layout.addWidget(raw_group)

        layout.addStretch()

    def set_device(self, device):
        """Populate the detail panel with device info."""
        if not device:
            self.lbl_ip.setText("-")
            self.lbl_mac.setText("-")
            self.lbl_hostname.setText("-")
            self.lbl_vendor.setText("-")
            self.lbl_status.setText("-")
            self.lbl_first_seen.setText("-")
            self.lbl_last_seen.setText("-")
            self.lbl_known.setText("-")
            self.raw_text.setPlainText("")
            return

        self.lbl_ip.setText(device.get("ip", "-"))
        self.lbl_mac.setText(device.get("mac", "-"))
        self.lbl_hostname.setText(device.get("hostname", "-") or "-")
        self.lbl_vendor.setText(device.get("vendor", "-"))
        self.lbl_first_seen.setText(device.get("first_seen", "-"))
        self.lbl_last_seen.setText(device.get("last_seen", "-"))
        self.lbl_known.setText(device.get("is_known", False) and "Yes" or "No")

        # Color code status
        status = device.get("status", "new")
        color_map = {
            "online": "#27ae60",
            "unreachable": "#e74c3c",
            "new": "#95a5a6",
        }
        color = color_map.get(status, "#95a5a6")
        self.lbl_status.setText(f'<span style="color:{color}">{status.upper()}</span>')

        # Build raw data display
        raw_lines = [
            f"IP:           {device.get('ip', '-')}",
            f"MAC:          {device.get('mac', '-')}",
            f"Hostname:     {device.get('hostname', '-') or '(none)'}",
            f"Vendor:       {device.get('vendor', '-')}",
            f"Status:       {status}",
            f"First Seen:   {device.get('first_seen', '-')}",
            f"Last Seen:    {device.get('last_seen', '-')}",
            f"Seen Count:   {device.get('seen_count', 0)}",
            f"Is Known:     {device.get('is_known', False)}",
            f"Is Cluster:   {device.get('is_cluster_node', False)}",
        ]
        self.raw_text.setPlainText("\n".join(raw_lines))

    def _on_ping(self):
        ip = self.lbl_ip.text()
        if ip and ip != "-":
            self.ping_requested.emit(ip)

    def _on_hostname(self):
        ip = self.lbl_ip.text()
        if ip and ip != "-":
            self.hostname_requested.emit(ip)

    def _on_portscan(self):
        ip = self.lbl_ip.text()
        if ip and ip != "-":
            self.portscan_requested.emit(ip)
