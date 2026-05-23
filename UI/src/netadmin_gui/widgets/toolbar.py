"""
Toolbar - Minimal toolbar with just a Start button.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal


class Toolbar(QWidget):
    """Minimal toolbar with a single Start button."""

    scan_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
        self.setStyleSheet("background: #f6f6f6; border-bottom: 1px solid #d0d0d0;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(12)

        # ── Start Button ──
        self.btn_scan = QPushButton("Start")
        self.btn_scan.setFixedWidth(70)
        self.btn_scan.clicked.connect(self._on_scan)
        self.btn_scan.setStyleSheet(
            "QPushButton { "
            "padding: 5px 14px; "
            "border: 1px solid #2d6ab8; "
            "border-radius: 5px; "
            "background: #3a7bd5; "
            "color: #ffffff; "
            "font-size: 12px; "
            "font-weight: bold; "
            "} "
            "QPushButton:hover { background: #5ba3e0; } "
            "QPushButton:pressed { background: #2d5aa0; } "
            "QPushButton:disabled { background: #d0d0d0; color: #aaa; border-color: #c0c0c0; }"
        )
        layout.addWidget(self.btn_scan)

        # ── Stats ──
        self.lbl_stats = QLabel("Devices: 0  |  Offline: 0  |  New: 0")
        self.lbl_stats.setStyleSheet("font-family: Menlo, monospace; font-size: 11px; color: #666;")
        layout.addWidget(self.lbl_stats, stretch=1)

    def _on_scan(self):
        self.scan_requested.emit({
            "subnet": None,
            "interface": "en0",
            "scan_depth": "quick",
            "auto_resolve": True,
            "interval": 0,
        })

    def set_device_counts(self, total, offline, new_count):
        self.lbl_stats.setText(
            f"Devices: {total}  |  Offline: {offline}  |  New: {new_count}"
        )

    def set_scan_button_enabled(self, enabled):
        self.btn_scan.setEnabled(enabled)
