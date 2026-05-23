"""
Device Table - Main table view with status indicators and sorting.

Uses QTableWidget with custom sortByColumn() — no custom model needed.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal


def status_color(status):
    return {
        "online": QColor("#27ae60"),
        "unreachable": QColor("#e74c3c"),
        "new": QColor("#95a5a6"),
    }.get(status, QColor("#95a5a6"))


# ─── Device Table Widget ────────────────────────────────────────────────────


class DeviceTable(QWidget):
    device_selected = Signal(dict)
    device_double_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Filter bar ──
        filter_bar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search IP or hostname...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._filter)
        filter_bar.addWidget(self.search_input)

        status_filter = QHBoxLayout()
        status_filter.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Online", "Offline", "New"])
        self.status_combo.currentTextChanged.connect(self._filter)
        status_filter.addWidget(self.status_combo)
        filter_bar.addLayout(status_filter)
        filter_bar.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(filter_bar)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Status", "IP", "Hostname", "MAC", "Vendor", "First Seen", "Last Seen"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        # Show sort arrows; custom handler toggles direction on click
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().setSortIndicator(1, Qt.AscendingOrder)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_sorted)

        # Row click
        self.table.itemClicked.connect(self._on_row_clicked)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)

        layout.addWidget(self.table)

    def _on_header_sorted(self, column):
        """Toggle sort direction on header click."""
        if column == 0:
            return
        header = self.table.horizontalHeader()
        current = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()
        if current == column:
            order = Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            order = Qt.AscendingOrder
        self.table.sortByColumn(column, order)
        header.setSortIndicator(column, order)

    def _filter(self):
        """Hide rows that don't match search/status filters."""
        search = self.search_input.text().lower()
        status = self.status_combo.currentText().lower()

        for row in range(self.table.rowCount()):
            item_ip = self.table.item(row, 1)
            item_host = self.table.item(row, 2)
            item_status = self.table.item(row, 0)

            if item_status is None:
                continue

            ip_text = item_ip.text().lower() if item_ip else ""
            host_text = item_host.text().lower() if item_host else ""

            row_status = item_status.data(Qt.UserRole) or ""
            if status != "all" and row_status != status:
                self.table.setRowHidden(row, True)
                continue

            if search and search not in ip_text and search not in host_text:
                self.table.setRowHidden(row, True)
                continue

            self.table.setRowHidden(row, False)

    def _on_row_clicked(self, item):
        row = item.row()
        device = self._get_device_from_row(row)
        if device:
            self.device_selected.emit(device)

    def _on_row_double_clicked(self, item):
        row = item.row()
        device = self._get_device_from_row(row)
        if device:
            self.device_double_clicked.emit(device)

    def _get_device_from_row(self, row):
        try:
            status_item = self.table.item(row, 0)
            ip_item = self.table.item(row, 1)
            if not ip_item:
                return None
            device = ip_item.data(Qt.UserRole)
            if not device:
                return None
            device = dict(device)
            if status_item:
                device["status"] = status_item.data(Qt.UserRole) or "new"
            return device
        except Exception:
            return None

    def set_devices(self, devices):
        """Populate the table. devices: dict of {ip: device_dict}."""
        # Disable auto-sort while populating
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for ip, device in devices.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            status = device.get("status", "new")
            color = status_color(status)

            # Status column
            dot = "●" if status != "new" else "○"
            status_item = QTableWidgetItem(dot)
            status_item.setForeground(color)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setData(Qt.UserRole, status)
            self.table.setItem(row, 0, status_item)

            # IP — store full device in UserRole for click retrieval
            ip_item = QTableWidgetItem(device.get("ip", ""))
            ip_item.setData(Qt.UserRole, dict(device))
            self.table.setItem(row, 1, ip_item)

            self.table.setItem(row, 2, QTableWidgetItem(device.get("hostname", "-")))
            self.table.setItem(row, 3, QTableWidgetItem(device.get("mac", "-")))
            self.table.setItem(row, 4, QTableWidgetItem(device.get("vendor", "-")))
            self.table.setItem(row, 5, QTableWidgetItem(device.get("first_seen", "")))
            self.table.setItem(row, 6, QTableWidgetItem(device.get("last_seen", "")))

        # Restore sorting and re-apply the current sort indicator
        self.table.setSortingEnabled(True)
        header = self.table.horizontalHeader()
        col = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()
        if col >= 0:
            self.table.sortByColumn(col, order)

        # Apply current filters
        self._filter()

    def get_selected_device(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self._get_device_from_row(row)

    def get_unreachable_count(self):
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == "unreachable":
                count += 1
        return count
