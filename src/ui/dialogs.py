"""
Dialog windows for the Torchlight Infinite Price Tracker.
"""

from typing import Callable, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox
)
from PyQt5.QtCore import Qt

from ..config_manager import ConfigManager


class DropsDetailDialog(QDialog):
    """Dialog for detailed drops filtering and viewing."""

    def __init__(
        self,
        parent,
        item_types: List[str],
        filter_currency: List[str],
        filter_ashes: List[str],
        filter_compass: List[str],
        filter_glow: List[str],
        filter_others: List[str],
        on_change_view: Callable[[], None],
        on_filter_change: Callable[[List[str]], None]
    ):
        """
        Initialize the drops detail dialog.

        Args:
            parent: Parent widget
            item_types: List of all item types
            filter_currency: Currency filter list
            filter_ashes: Embers filter list
            filter_compass: Compass filter list
            filter_glow: Memory filter list
            filter_others: Others filter list
            on_change_view: Callback for changing view
            on_filter_change: Callback for filter changes
        """
        super().__init__(parent)
        self.item_types = item_types
        self.filter_currency = filter_currency
        self.filter_ashes = filter_ashes
        self.filter_compass = filter_compass
        self.filter_glow = filter_glow
        self.filter_others = filter_others
        self.on_change_view = on_change_view
        self.on_filter_change = on_filter_change
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Drops Detail - FurTorch")
        self.setWindowFlags(Qt.Tool)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header card
        header_card = QFrame()
        header_card.setProperty("class", "card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(15, 15, 15, 15)

        header_label = QLabel("DROP FILTERS")
        header_label.setProperty("class", "status")
        header_layout.addWidget(header_label)

        self.button_toggle_all = QPushButton("Current: Current Map Drops (Click to toggle All Drops)")
        self.button_toggle_all.setCursor(Qt.PointingHandCursor)
        self.button_toggle_all.clicked.connect(self.on_change_view)
        header_layout.addWidget(self.button_toggle_all)

        layout.addWidget(header_card)

        # Filter buttons card
        filters_card = QFrame()
        filters_card.setProperty("class", "card")
        filters_layout = QVBoxLayout(filters_card)
        filters_layout.setContentsMargins(15, 15, 15, 15)

        filters_label = QLabel("ITEM CATEGORIES")
        filters_label.setProperty("class", "status")
        filters_layout.addWidget(filters_label)

        filter_items = [
            ("All Items", self.item_types),
            ("Currency", self.filter_currency),
            ("Embers", self.filter_ashes),
            ("Compass", self.filter_compass),
            ("Memory", self.filter_glow),
            ("Others", self.filter_others)
        ]

        for text, filter_type in filter_items:
            btn = QPushButton(text)
            btn.setProperty("class", "secondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, f=filter_type: self.on_filter_change(f))
            filters_layout.addWidget(btn)

        layout.addWidget(filters_card)

    def update_toggle_text(self, show_all: bool) -> None:
        """
        Update the toggle button text.

        Args:
            show_all: True if showing all drops, False if showing current map
        """
        if show_all:
            self.button_toggle_all.setText("Current: All Drops (Click to toggle Current Map Drops)")
        else:
            self.button_toggle_all.setText("Current: Current Map Drops (Click to toggle All Drops)")


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        on_tax_change: Callable[[int], None],
        on_reset_tracking: Callable[[], None]
    ):
        """
        Initialize the settings dialog.

        Args:
            parent: Parent widget
            config_manager: Configuration manager instance
            on_tax_change: Callback for tax setting changes
            on_reset_tracking: Callback for reset tracking button
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_tax_change = on_tax_change
        self.on_reset_tracking = on_reset_tracking
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Settings - FurTorch")
        self.setWindowFlags(Qt.Tool)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Tax settings card
        tax_card = QFrame()
        tax_card.setProperty("class", "card")
        tax_layout = QVBoxLayout(tax_card)
        tax_layout.setContentsMargins(15, 15, 15, 15)

        tax_title = QLabel("TAX SETTINGS")
        tax_title.setProperty("class", "status")
        tax_layout.addWidget(tax_title)

        tax_row = QHBoxLayout()
        label_tax = QLabel("Price Calculation:")
        tax_row.addWidget(label_tax)

        config = self.config_manager.get()
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["No tax", "Include tax"])
        self.tax_combo.setCurrentIndex(config.tax)
        self.tax_combo.currentIndexChanged.connect(self.on_tax_change)
        tax_row.addWidget(self.tax_combo)

        tax_layout.addLayout(tax_row)
        layout.addWidget(tax_card)

        # Actions card
        actions_card = QFrame()
        actions_card.setProperty("class", "card")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(15, 15, 15, 15)

        actions_title = QLabel("ACTIONS")
        actions_title.setProperty("class", "status")
        actions_layout.addWidget(actions_title)

        reset_button = QPushButton("Reset Statistics")
        reset_button.setProperty("class", "danger")
        reset_button.setCursor(Qt.PointingHandCursor)
        reset_button.clicked.connect(self.on_reset_tracking)
        actions_layout.addWidget(reset_button)

        layout.addWidget(actions_card)
