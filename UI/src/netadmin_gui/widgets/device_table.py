"""
Device Table - Main table view with status indicators.

Shows scanned devices with sortable columns and color-coded status:
  🟢 GREEN = device was present AND still reachable
  🔴 RED   = device was present but now unreachable (offline)
  ⚪ NEUTRAL = brand new device (first time seen)
"""
from PySide6.QtWidgets import (
    QTableWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QHeaderView, QApplication, QLabel
)
from PySide6.QtGui import QColor, QIcon, QKeyEvent
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel

# ─── Status Indicator Delegate ─────────────────────────────────────────────


class StatusDelegate:
    """Computes status colors and emojis."""

    @staticmethod
    def color(status):
        """Return QColor for status."""
        colors = {
            "online": QColor("#27ae60"),
            "unreachable": QColor("#e74c3c"),
            "new": QColor("#95a5a6"),
        }
        return colors.get(status, QColor("#95a5a6"))

    @staticmethod
    def emoji(status):
        """Return emoji string for status."""
        emojis = {
            "online": "●",
            "unreachable": "●",
            "new": "○",
        }
        return emojis.get(status, "○")

    @staticmethod
    def status_text(status):
        """Return human-readable status text."""
        texts = {
            "online": "Online",
            "unreachable": "Offline",
            "new": "New",
        }
        return texts.get(status, status)


# ─── Proxy Model for Sorting/Filtering ─────────────────────────────────────


class DeviceProxyModel(QSortFilterProxyModel):
    """Sorts and filters device data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_status = "all"

    def set_filter_status(self, status):
        self._filter_status = status
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if self._filter_status == "all":
            return True

        idx = self.sourceModel().index(source_row, 0, source_parent)
        # Status is in column 0 (status column)
        status = self.sourceModel().data(idx, Qt.DisplayRole)
        return status == self._filter_status


# ─── Device Table Widget ───────────────────────────────────────────────────


class DeviceTable(QWidget):
    """Main device table with status indicators, sorting, and filtering."""

    device_selected = Signal(dict)  # Emitted when a row is clicked
    device_double_clicked = Signal(dict)  # Emitted on double-click

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Filter bar ──
        filter_bar = QHBoxLayout()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search IP or hostname...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(self.search_input)

        # Status filter
        status_filter = QHBoxLayout()
        status_filter.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Online", "Offline", "New"])
        self.status_combo.currentTextChanged.connect(self._on_status_filter_changed)
        status_filter.addWidget(self.status_combo)
        filter_bar.addLayout(status_filter)
        filter_bar.addStretch()

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
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        # Sort by clicking headers
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._sort_column = 1
        self._sort_asc = True

        layout.addWidget(self.table)

        # ── Proxy model ──
        self.proxy = DeviceProxyModel()
        self.proxy.setSourceModel(self.table.model())

        # Connect row click
        self.table.itemClicked.connect(self._on_row_clicked)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)

    def _on_header_clicked(self, column):
        """Handle column header click for sorting."""
        if column == 0:  # Skip status column sorting
            return
        if self._sort_column == column:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_column = column
            self._sort_asc = True

        self.table.horizontalHeader().setSortIndicator(column, Qt.AscendingOrder if self._sort_asc else Qt.DescendingOrder)
        self.proxy.sort(column, Qt.AscendingOrder if self._sort_asc else Qt.DescendingOrder)

    def _on_search_changed(self, text):
        """Filter table by search text."""
        self.proxy.setFilterFixedString(text)

    def _on_status_filter_changed(self, status):
        """Filter by status."""
        status_map = {"All": "all", "Online": "online", "Offline": "unreachable", "New": "new"}
        self.proxy.set_filter_status(status_map.get(status, "all"))

    def _on_row_clicked(self, item):
        """Emit device_selected when a row is clicked."""
        row = item.row()
        device = self._get_device_from_row(row)
        if device:
            self.device_selected.emit(device)

    def _on_row_double_clicked(self, item):
        """Emit device_double_clicked when a row is double-clicked."""
        row = item.row()
        device = self._get_device_from_row(row)
        if device:
            self.device_double_clicked.emit(device)

    def _get_device_from_row(self, row):
        """Extract device dict from a table row."""
        try:
            status_item = self.table.item(row, 0)
            ip_item = self.table.item(row, 1)
            hostname_item = self.table.item(row, 2)
            mac_item = self.table.item(row, 3)
            vendor_item = self.table.item(row, 4)
            first_seen_item = self.table.item(row, 5)
            last_seen_item = self.table.item(row, 6)

            if not all([ip_item, mac_item]):
                return None

            return {
                "status": status_item.text(),
                "ip": ip_item.text(),
                "hostname": hostname_item.text() if hostname_item else "",
                "mac": mac_item.text(),
                "vendor": vendor_item.text() if vendor_item else "",
                "first_seen": first_seen_item.text() if first_seen_item else "",
                "last_seen": last_seen_item.text() if last_seen_item else "",
            }
        except Exception:
            return None

    def set_devices(self, devices):
        """
        Populate the table with device data.
        
        devices: dict of {ip: device_dict} with optional 'status' key.
        """
        self.table.setRowCount(0)

        for ip, device in devices.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            status = device.get("status", "new")
            color = StatusDelegate.color(status)

            # Status column — colored dot using text color
            dot = "●" if status != "new" else "◼"
            status_item = QTableWidgetItem(dot)
            status_item.setForeground(color)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setData(Qt.UserRole, status)  # Store raw status
            self.table.setItem(row, 0, status_item)

            # IP
            self.table.setItem(row, 1, QTableWidgetItem(device.get("ip", "")))

            # Hostname
            self.table.setItem(row, 2, QTableWidgetItem(device.get("hostname", "-")))

            # MAC
            self.table.setItem(row, 3, QTableWidgetItem(device.get("mac", "-")))

            # Vendor
            self.table.setItem(row, 4, QTableWidgetItem(device.get("vendor", "-")))

            # First seen
            self.table.setItem(row, 5, QTableWidgetItem(device.get("first_seen", "")))

            # Last seen
            self.table.setItem(row, 6, QTableWidgetItem(device.get("last_seen", "")))

        # Auto-resize columns to content
        for col in range(1, 7):
            self.table.resizeColumnToContents(col)

    def get_selected_device(self):
        """Get the currently selected device dict, or None."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self._get_device_from_row(current_row)

    def get_unreachable_count(self):
        """Count devices with unreachable status."""
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == "unreachable":
                count += 1
        return count
