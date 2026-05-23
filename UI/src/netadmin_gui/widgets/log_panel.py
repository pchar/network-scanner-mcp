"""
Log Panel - Debug/Info output display.

Shows scan progress, device status changes, and error messages.
"""
from PySide6.QtWidgets import (
    QGroupBox, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Signal, Qt


class LogPanel(QGroupBox):
    """Log/Debug output panel with color-coded messages."""

    def __init__(self, parent=None):
        super().__init__("Log", parent)
        self.setMinimumHeight(150)
        self.setMaximumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Top bar with clear button
        top_bar = QHBoxLayout()
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedSize(80, 24)
        self.btn_clear.clicked.connect(self.clear_log)
        top_bar.addWidget(self.btn_clear)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Log text area
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Menlo", 9))
        self.log_text.setMaximumBlockCount(500)
        layout.addWidget(self.log_text)

    def log(self, message: str, level: str = "INFO"):
        """Add a message to the log with color coding."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        
        colors = {
            "INFO": "#cccccc",
            "WARN": "#f39c12",
            "ERROR": "#e74c3c",
            "SUCCESS": "#27ae60",
        }
        color = colors.get(level, "#cccccc")

        # Use HTML for coloring
        html = f'<span style="color:{color}">{timestamp} [{level:5s}] {message}</span>\n'
        self.log_text.appendHtml(html)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """Clear all log messages."""
        self.log_text.clear()

    def log_info(self, message):
        self.log(message, "INFO")

    def log_warn(self, message):
        self.log(message, "WARN")

    def log_error(self, message):
        self.log(message, "ERROR")

    def log_success(self, message):
        self.log(message, "SUCCESS")
