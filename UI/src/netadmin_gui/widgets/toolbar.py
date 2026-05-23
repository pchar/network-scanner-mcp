"""
Toolbar - Scan controls and configuration.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QCheckBox, QGroupBox, QFormLayout, QLineEdit, QMessageBox,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, Qt


class Toolbar(QWidget):
    """Main toolbar with scan controls and configuration."""

    scan_requested = Signal(dict)
    toggle_continuous = Signal(bool)
    clean_requested = Signal()
    auto_detect_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setStyleSheet("background: #f6f6f6; border-bottom: 1px solid #d0d0d0;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        # ── Start/Stop Toggle ──
        self.btn_toggle = QPushButton("Start")
        self.btn_toggle.setFixedWidth(70)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.clicked.connect(self._on_toggle)
        self._is_running = False
        self._apply_button_style(self.btn_toggle, start=True)
        layout.addWidget(self.btn_toggle)

        # ── One-shot Scan ──
        self.btn_scan = QPushButton("Scan Now")
        self.btn_scan.setFixedWidth(100)
        self.btn_scan.clicked.connect(self._on_scan)
        self._apply_button_style(self.btn_scan, start=False)
        layout.addWidget(self.btn_scan)

        layout.addSpacing(10)

        # ── Config ──
        config_group = QGroupBox("Config")
        config_group.setStyleSheet(
            "QGroupBox { font-size: 11px; color: #555; "
            "border: 1px solid #d8d8d8; border-radius: 5px; "
            "margin-top: 8px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }"
        )
        config_layout = QFormLayout()
        config_layout.setSpacing(3)
        config_layout.setLabelAlignment(Qt.AlignRight)

        group_style = (
            "font-size: 11px; padding: 3px 6px; "
            "border: 1px solid #c0c0c0; border-radius: 3px; background: #fff;"
        )
        combo_style = (
            "font-size: 11px; padding: 3px 6px; "
            "border: 1px solid #c0c0c0; border-radius: 3px; background: #fff; min-width: 80px;"
        )

        self.cb_interface = QComboBox()
        self.cb_interface.addItems(["en0"])
        self.cb_interface.setStyleSheet(combo_style)
        config_layout.addRow("Interface:", self.cb_interface)

        det_layout = QHBoxLayout()
        self.btn_detect = QPushButton("Auto")
        self.btn_detect.setFixedWidth(35)
        self.btn_detect.setStyleSheet("font-size: 10px; padding: 2px 4px; "
                                       "border: 1px solid #c0c0c0; border-radius: 3px; background: #e8e8e8;")
        self.btn_detect.clicked.connect(self._on_auto_detect)
        det_layout.addWidget(self.btn_detect)
        det_layout.addWidget(QLabel("Subnet:"), 0, Qt.AlignRight)
        det_layout.addSpacing(4)
        self.le_subnet = QLineEdit("172.30.200.0/24")
        self.le_subnet.setStyleSheet(group_style + " font-family: Menlo, monospace;")
        self.le_subnet.setFixedWidth(140)
        det_layout.addWidget(self.le_subnet)
        config_layout.addRow("", det_layout)

        self.cb_depth = QComboBox()
        self.cb_depth.addItems(["Quick (ARP)", "Full (ARP+DNS+Ports)"])
        self.cb_depth.setStyleSheet(combo_style)
        config_layout.addRow("Depth:", self.cb_depth)

        self.cb_resolve = QCheckBox("Resolve DNS")
        config_layout.addRow("", self.cb_resolve)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        layout.addSpacing(10)

        # ── Interval ──
        interval_group = QGroupBox("Interval")
        interval_group.setStyleSheet(
            "QGroupBox { font-size: 11px; color: #555; "
            "border: 1px solid #d8d8d8; border-radius: 5px; "
            "margin-top: 8px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }"
        )
        interval_layout = QHBoxLayout()

        self.cb_interval = QComboBox()
        self.cb_interval.addItems(["Off", "30s", "1m", "5m", "15m"])
        self.cb_interval.setStyleSheet(combo_style)
        interval_layout.addWidget(self.cb_interval)
        self.cb_interval.currentTextChanged.connect(self._update_interval)
        self._current_interval = 0

        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)

        layout.addSpacing(8)

        # ── Clean ──
        self.btn_clean = QPushButton("Clean")
        self.btn_clean.setStyleSheet(
            "font-size: 11px; padding: 3px 8px; "
            "border: 1px solid #c0c0c0; border-radius: 3px; background: #fff; color: #c0392b;"
        )
        self.btn_clean.clicked.connect(self._on_clean)
        self.btn_clean.setEnabled(False)
        layout.addWidget(self.btn_clean)

        # ── Stats ──
        self.lbl_stats = QLabel("Devices: 0  |  Offline: 0  |  New: 0")
        self.lbl_stats.setStyleSheet("font-family: Menlo, monospace; font-size: 11px; color: #666;")
        layout.addWidget(self.lbl_stats, stretch=1)

    def _apply_button_style(self, btn, start=False):
        """Apply a visible button style with solid background colors."""
        if start:
            bg = "background: #3a7bd5;"
            fg = "color: #ffffff;"
        else:
            bg = "background: #4a90d9;"
            fg = "color: #ffffff;"

        btn.setStyleSheet(
            f"QPushButton {{ "
            f"padding: 5px 14px; "
            f"border: 1px solid #2d6ab8; "
            f"border-radius: 5px; "
            f"{bg}"
            f"{fg}"
            f"font-size: 12px; "
            f"font-weight: bold; "
            f"}} "
            f"QPushButton:hover {{ {bg.replace('#3a7bd5', '#5ba3e0').replace('#4a90d9', '#6aa3e0')}; }} "
            f"QPushButton:pressed {{ background: #2d5aa0; }} "
            f"QPushButton:disabled {{ background: #d0d0d0; color: #aaa; border-color: #c0c0c0; }}"
        )

    def _on_toggle(self):
        self._is_running = not self._is_running
        if self._is_running:
            self.btn_toggle.setText("Stop")
            self.btn_toggle.setStyleSheet(
                "QPushButton { "
                "padding: 5px 14px; "
                "border: 1px solid #a93226; "
                "border-radius: 5px; "
                "background: #e74c3c; "
                "color: #ffffff; "
                "font-size: 12px; "
                "font-weight: bold; "
                "} "
                "QPushButton:hover { background: #f06060; } "
                "QPushButton:pressed { background: #c0392b; }"
            )
        else:
            self.btn_toggle.setText("Start")
            self.btn_toggle.setStyleSheet(
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
                "QPushButton:pressed { background: #2d5aa0; }"
            )

        self.toggle_continuous.emit(self._is_running)
        if self._is_running:
            self._on_scan()
        else:
            self.btn_scan.setEnabled(True)

    def _on_scan(self):
        config = self.get_config()
        self.scan_requested.emit(config)

    def _on_auto_detect(self):
        self.lbl_stats.setText("Detecting subnet...")
        self.auto_detect_requested.emit(self.cb_interface.currentText())

    def _on_clean(self):
        reply = QMessageBox.question(
            self, "Confirm Cleanup",
            "This will permanently remove all unreachable devices.\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.clean_requested.emit()

    def get_config(self):
        scan_type_text = self.cb_depth.currentText()
        return {
            "subnet": self.le_subnet.text().strip(),
            "interface": self.cb_interface.currentText(),
            "scan_depth": "full" if "Full" in scan_type_text else "quick",
            "auto_resolve": self.cb_resolve.isChecked(),
            "interval": self._current_interval,
        }

    def _update_interval(self, text):
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
        self.lbl_stats.setText(
            f"Devices: {total}  |  Offline: {offline}  |  New: {new_count}"
        )

    def set_offline_count(self, count):
        if count > 0:
            self.btn_clean.setText(f"Clean ({count} offline)")
            self.btn_clean.setEnabled(True)
        else:
            self.btn_clean.setText("Clean")
            self.btn_clean.setEnabled(False)

    def set_scan_button_enabled(self, enabled):
        self.btn_scan.setEnabled(enabled)

    def update_interface_list(self, interfaces):
        self.cb_interface.clear()
        self.cb_interface.addItems(interfaces)
