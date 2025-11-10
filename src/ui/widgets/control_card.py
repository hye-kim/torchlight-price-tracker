"""
Control panel card widget for the Torchlight Infinite Price Tracker.
"""

from typing import Callable, Dict
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt


class ControlCard(QFrame):
    """Widget containing initialization and action controls."""

    def __init__(
        self,
        colors: Dict[str, str],
        on_initialize: Callable[[], None],
        on_debug_log: Callable[[], None],
        on_export: Callable[[], None],
        on_settings: Callable[[], None]
    ):
        """
        Initialize the control card.

        Args:
            colors: Color palette dictionary for styling
            on_initialize: Callback for initialize button
            on_debug_log: Callback for debug log button
            on_export: Callback for export button
            on_settings: Callback for settings button
        """
        super().__init__()
        self.colors = colors
        self.on_initialize = on_initialize
        self.on_debug_log = on_debug_log
        self.on_export = on_export
        self.on_settings = on_settings
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI layout and widgets."""
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Initialization section
        init_label = QLabel("INITIALIZATION")
        init_label.setProperty("class", "status")
        layout.addWidget(init_label)

        init_row = QHBoxLayout()
        init_row.setSpacing(10)

        self.button_initialize = QPushButton("Initialize Tracker")
        self.button_initialize.setCursor(Qt.PointingHandCursor)
        self.button_initialize.clicked.connect(self.on_initialize)
        init_row.addWidget(self.button_initialize)

        self.label_initialize_status = QLabel("Not initialized")
        self.label_initialize_status.setProperty("class", "status")
        init_row.addWidget(self.label_initialize_status)
        init_row.addStretch()

        layout.addLayout(init_row)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.colors['border']}; max-height: 1px;")
        layout.addWidget(separator)

        # Actions section
        actions_label = QLabel("ACTIONS")
        actions_label.setProperty("class", "status")
        layout.addWidget(actions_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(5)

        button_log = QPushButton("🔍 Debug Log")
        button_log.setProperty("class", "secondary")
        button_log.setCursor(Qt.PointingHandCursor)
        button_log.clicked.connect(self.on_debug_log)
        button_row.addWidget(button_log)

        button_export = QPushButton("📊 Export")
        button_export.setProperty("class", "secondary")
        button_export.setCursor(Qt.PointingHandCursor)
        button_export.clicked.connect(self.on_export)
        button_row.addWidget(button_export)

        button_settings = QPushButton("⚙ Settings")
        button_settings.setProperty("class", "secondary")
        button_settings.setCursor(Qt.PointingHandCursor)
        button_settings.clicked.connect(self.on_settings)
        button_row.addWidget(button_settings)

        layout.addLayout(button_row)

    def set_initialization_waiting(self) -> None:
        """Set initialization status to waiting."""
        self.label_initialize_status.setText("Waiting for bag update...")
        self.label_initialize_status.setStyleSheet(f"color: {self.colors['warning']};")
        self.button_initialize.setEnabled(False)

    def set_initialization_complete(self, item_count: int) -> None:
        """
        Set initialization status to complete.

        Args:
            item_count: Number of items initialized
        """
        self.label_initialize_status.setText(f"✓ Initialized ({item_count} items)")
        self.label_initialize_status.setStyleSheet(f"color: {self.colors['success']};")
        self.button_initialize.setEnabled(True)
