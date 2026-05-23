"""
Toolbar - Scan controls and configuration.

Contains scan button, interval settings, subnet configuration,
interface selector, and the clean-unreachable button.
"""
from PySide6.QtWidgets import (
    QToolBar, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QCheckBox, QGroupBox, QFormLayout,
    QMessageBox,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal


class Toolbar(QToolBar):
    """Main toolbar with scan controls and configuration."""

    scan_requested = Signal(dict)  # Emits scan config dict
    clean_requested = Signal()     # Emits when clean button clicked

    def __init__(self, parent=None):
        super().__init__("Controls", parent)
        self.setFloatable(False)
        self.setMovable(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        # ── Scan Button (big, prominent) ──
        self.btn_scan = QPushButton("📡 Scan Network")
        self.btn_scan.setFont(QFont("Helvetica", 12, QFont.Bold))
        self.btn_scan.setFixedWidth(160)
        self.btn_scan.clicked.connect(self._on_scan)
        layout.addWidget(self.btn_scan)

        # Scan type dropdown
        self.cb_scan_type = QComboBox()
        self.cb_scan_type.addItems(["Quick (ARP)", "Full (ARP+DNS+Ports)"])
        layout.addWidget(self.cb_scan_type)

        layout.addSpacing(20)

        # ── Scan Config Group ──
        config_group = QGroupBox("Scan Config")
        config_layout = QFormLayout()

        # Subnet
        self.le_subnet = QLabel("172.30.200.0/24")
        self.le_subnet.setFont(QFont("Menlo", 10))
        config_layout.addRow("Subnet:", self.le_subnet)

        # Interface
        self.cb_interface = QComboBox()
        self.cb_interface.addItems(["en0"])  # Will be populated at runtime
        config_layout.addRow("Interface:", self.cb_interface)

        # Auto-resolve
        self.cb_resolve = QCheckBox("Resolve Hostnames")
        self.cb_resolve.setChecked(True)
        config_layout.addRow("", self.cb_resolve)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        layout.addSpacing(20)

        # ── Interval Group ──
        interval_group = QGroupBox("Auto-Scan")
        interval_layout = QHBoxLayout()

        self.cb_interval = QComboBox()
        self.cb_interval.addItems(["Off", "30s", "1m", "5m", "15m"])
        interval_layout.addWidget(self.cb_interval)
        self.cb_interval.currentTextChanged.connect(self._update_interval)
        self._current_interval = 0  # seconds

        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)

        layout.addSpacing(20)

        # ── Cleanup Button ──
        self.btn_clean = QPushButton("🗑 Clean Offline")
        self.btn_clean.setFont(QFont("Helvetica", 10))
        self.btn_clean.setStyleSheet("color: #e74c3c; border: 1px solid #e74c3c;")
        self.btn_clean.clicked.connect(self._on_clean)
        layout.addWidget(self.btn_clean)

        # ── Stats ──
        self.lbl_stats = QLabel("Devices: 0  |  Offline: 0  |  New: 0")
        self.lbl_stats.setFont(QFont("Menlo", 10))
        layout.addWidget(self.lbl_stats, stretch=1)
        layout.addStretch()

        self.setLayout(layout)

    def _on_scan(self):
        """Emit scan request with current config."""
        config = self.get_config()
        self.scan_requested.emit(config)

    def _on_clean(self):
        """Emit clean request after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Cleanup",
            "This will permanently remove all unreachable devices.\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.clean_requested.emit()

    def get_config(self):
        """Read current configuration from UI controls."""
        scan_type_text = self.cb_scan_type.currentText()
        return {
            "subnet": self.le_subnet.text(),
            "interface": self.cb_interface.currentText(),
            "scan_depth": "full" if "Full" in scan_type_text else "quick",
            "auto_resolve": self.cb_resolve.isChecked(),
            "interval": self._current_interval,
        }

    def _update_interval(self, text):
        """Parse interval text to seconds."""
        text = text.strip()
        if text == "Off" or text == "0":
            self._current_interval = 0
        elif text.endswith("s"):
            self._current_interval = int(text[:-1])
        elif text.endswith("m"):
            self._current_interval = int(text[:-1]) * 60
        else:
            self._current_interval = 0

    def set_device_counts(self, total, offline, new_count):
        """Update the stats label with current counts."""
        self.lbl_stats.setText(
            f"Devices: {total}  |  Offline: {offline}  |  New: {new_count}"
        )

    def set_offline_count(self, count):
        """Update the clean button with offline count."""
        if count > 0:
            self.btn_clean.setText(f"🗑 Clean ({count} offline)")
            self.btn_clean.setEnabled(True)
        else:
            self.btn_clean.setText("🗑 Clean Offline")
            self.btn_clean.setEnabled(False)

    def set_scan_button_enabled(self, enabled):
        """Enable/disable the scan button."""
        self.btn_scan.setEnabled(enabled)

    def update_interface_list(self, interfaces):
        """Update the interface dropdown with available interfaces."""
        self.cb_interface.clear()
        self.cb_interface.addItems(interfaces)
