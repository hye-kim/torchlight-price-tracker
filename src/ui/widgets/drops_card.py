"""
Drops display card widget for the Torchlight Infinite Price Tracker.
"""

from typing import Callable, Dict, List
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget
from PyQt5.QtCore import Qt


class DropsCard(QFrame):
    """Widget displaying recent drops with filtering functionality."""

    def __init__(
        self,
        item_types: List[str],
        filter_currency: List[str],
        filter_ashes: List[str],
        filter_compass: List[str],
        filter_glow: List[str],
        filter_others: List[str],
        listbox_height: int,
        on_change_view: Callable[[], None],
        on_filter_change: Callable[[List[str]], None]
    ):
        """
        Initialize the drops card.

        Args:
            item_types: List of all item types
            filter_currency: Currency filter list
            filter_ashes: Embers filter list
            filter_compass: Compass filter list
            filter_glow: Memory filter list
            filter_others: Others filter list
            listbox_height: Height multiplier for listbox
            on_change_view: Callback for changing view (current map / all drops)
            on_filter_change: Callback for filter changes
        """
        super().__init__()
        self.item_types = item_types
        self.filter_currency = filter_currency
        self.filter_ashes = filter_ashes
        self.filter_compass = filter_compass
        self.filter_glow = filter_glow
        self.filter_others = filter_others
        self.listbox_height = listbox_height
        self.on_change_view = on_change_view
        self.on_filter_change = on_filter_change
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI layout and widgets."""
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        drops_title = QLabel("RECENT DROPS")
        drops_title.setProperty("class", "status")
        header_layout.addWidget(drops_title)

        header_layout.addStretch()

        self.button_change = QPushButton("Current Map")
        self.button_change.setProperty("class", "secondary")
        self.button_change.setCursor(Qt.PointingHandCursor)
        self.button_change.clicked.connect(self.on_change_view)
        header_layout.addWidget(self.button_change)

        layout.addLayout(header_layout)

        # Filter buttons
        filters_label = QLabel("FILTERS")
        filters_label.setProperty("class", "status")
        layout.addWidget(filters_label)

        # First row of filter buttons
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(5)

        self.btn_filter_all = QPushButton("All")
        self.btn_filter_all.setProperty("class", "filter-active")
        self.btn_filter_all.setCursor(Qt.PointingHandCursor)
        self.btn_filter_all.clicked.connect(lambda: self.on_filter_change(self.item_types))
        filter_row1.addWidget(self.btn_filter_all)

        self.btn_filter_currency = QPushButton("Currency")
        self.btn_filter_currency.setProperty("class", "secondary")
        self.btn_filter_currency.setCursor(Qt.PointingHandCursor)
        self.btn_filter_currency.clicked.connect(lambda: self.on_filter_change(self.filter_currency))
        filter_row1.addWidget(self.btn_filter_currency)

        self.btn_filter_embers = QPushButton("Embers")
        self.btn_filter_embers.setProperty("class", "secondary")
        self.btn_filter_embers.setCursor(Qt.PointingHandCursor)
        self.btn_filter_embers.clicked.connect(lambda: self.on_filter_change(self.filter_ashes))
        filter_row1.addWidget(self.btn_filter_embers)

        layout.addLayout(filter_row1)

        # Second row of filter buttons
        filter_row2 = QHBoxLayout()
        filter_row2.setSpacing(5)

        self.btn_filter_compass = QPushButton("Compass")
        self.btn_filter_compass.setProperty("class", "secondary")
        self.btn_filter_compass.setCursor(Qt.PointingHandCursor)
        self.btn_filter_compass.clicked.connect(lambda: self.on_filter_change(self.filter_compass))
        filter_row2.addWidget(self.btn_filter_compass)

        self.btn_filter_memory = QPushButton("Memory")
        self.btn_filter_memory.setProperty("class", "secondary")
        self.btn_filter_memory.setCursor(Qt.PointingHandCursor)
        self.btn_filter_memory.clicked.connect(lambda: self.on_filter_change(self.filter_glow))
        filter_row2.addWidget(self.btn_filter_memory)

        self.btn_filter_others = QPushButton("Others")
        self.btn_filter_others.setProperty("class", "secondary")
        self.btn_filter_others.setCursor(Qt.PointingHandCursor)
        self.btn_filter_others.clicked.connect(lambda: self.on_filter_change(self.filter_others))
        filter_row2.addWidget(self.btn_filter_others)

        layout.addLayout(filter_row2)

        # Store filter buttons for easy access
        self.filter_buttons = {
            tuple(self.item_types): self.btn_filter_all,
            tuple(self.filter_currency): self.btn_filter_currency,
            tuple(self.filter_ashes): self.btn_filter_embers,
            tuple(self.filter_compass): self.btn_filter_compass,
            tuple(self.filter_glow): self.btn_filter_memory,
            tuple(self.filter_others): self.btn_filter_others,
        }

        # Drops list
        self.inner_panel_drop_listbox = QListWidget()
        self.inner_panel_drop_listbox.setMinimumHeight(self.listbox_height * 20)  # Approximate height
        self.inner_panel_drop_listbox.addItem("Drops will be displayed here...")
        layout.addWidget(self.inner_panel_drop_listbox)

    def set_filter_active(self, item_types: List[str]) -> None:
        """
        Update filter button styling to show active filter.

        Args:
            item_types: List of item types to mark as active
        """
        filter_key = tuple(item_types)
        for key, button in self.filter_buttons.items():
            if key == filter_key:
                button.setProperty("class", "filter-active")
            else:
                button.setProperty("class", "secondary")
            # Force style update
            button.style().unpolish(button)
            button.style().polish(button)

    def set_view_mode(self, show_all: bool) -> None:
        """
        Update the view mode button text.

        Args:
            show_all: True if showing all drops, False if showing current map
        """
        if show_all:
            self.button_change.setText("All Drops")
        else:
            self.button_change.setText("Current Map")
