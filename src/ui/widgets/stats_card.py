"""
Statistics display card widget for the Torchlight Infinite Price Tracker.
"""

from typing import Dict
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QLabel


class StatsCard(QFrame):
    """Widget displaying game statistics (map count, time, income, etc.)."""

    def __init__(self, colors: Dict[str, str]):
        """
        Initialize the statistics card.

        Args:
            colors: Color palette dictionary for styling
        """
        super().__init__()
        self.colors = colors
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI layout and widgets."""
        self.setProperty("class", "card")
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Map count at the top
        map_count_label = QLabel("MAP COUNT")
        map_count_label.setProperty("class", "status")
        layout.addWidget(map_count_label)

        self.label_map_count = QLabel("🎫 0 maps")
        self.label_map_count.setProperty("class", "header")
        layout.addWidget(self.label_map_count)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet(f"background-color: {self.colors['border']}; max-height: 1px;")
        layout.addWidget(separator1)

        # Current map stats
        current_label = QLabel("CURRENT MAP")
        current_label.setProperty("class", "status")
        layout.addWidget(current_label)

        current_grid = QGridLayout()
        current_grid.setSpacing(15)

        self.label_current_time = QLabel("⏱ 0m00s")
        self.label_current_time.setProperty("class", "header")
        current_grid.addWidget(self.label_current_time, 0, 0)

        self.label_current_speed = QLabel("🔥 0 /min")
        self.label_current_speed.setProperty("class", "header")
        current_grid.addWidget(self.label_current_speed, 0, 1)

        self.label_current_map_fe = QLabel("🔥 0 FE")
        self.label_current_map_fe.setProperty("class", "header")
        current_grid.addWidget(self.label_current_map_fe, 0, 2)

        layout.addLayout(current_grid)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet(f"background-color: {self.colors['border']}; max-height: 1px;")
        layout.addWidget(separator2)

        # Total stats
        total_label = QLabel("TOTAL SESSION")
        total_label.setProperty("class", "status")
        layout.addWidget(total_label)

        total_grid = QGridLayout()
        total_grid.setSpacing(15)

        self.label_total_time = QLabel("⏱ 0m00s")
        self.label_total_time.setProperty("class", "header")
        total_grid.addWidget(self.label_total_time, 0, 0)

        self.label_total_speed = QLabel("🔥 0 /min")
        self.label_total_speed.setProperty("class", "header")
        total_grid.addWidget(self.label_total_speed, 0, 1)

        self.label_total_fe = QLabel("🔥 0 FE")
        self.label_total_fe.setProperty("class", "header")
        total_grid.addWidget(self.label_total_fe, 0, 2)

        layout.addLayout(total_grid)

    def update_current_map_stats(self, duration: float, income: float, income_per_min: float) -> None:
        """
        Update current map statistics display.

        Args:
            duration: Map duration in seconds
            income: Total FE earned in current map
            income_per_min: Income per minute rate
        """
        m = int(duration // 60)
        s = int(duration % 60)
        self.label_current_time.setText(f"⏱ {m}m{s:02d}s")
        self.label_current_speed.setText(f"🔥 {round(income_per_min, 2)} /min")
        self.label_current_map_fe.setText(f"🔥 {round(income, 2)} FE")

    def update_total_stats(self, duration: float, income: float, income_per_min: float, map_count: int) -> None:
        """
        Update total session statistics display.

        Args:
            duration: Total session duration in seconds
            income: Total FE earned in session
            income_per_min: Average income per minute rate
            map_count: Number of maps completed
        """
        m = int(duration // 60)
        s = int(duration % 60)
        self.label_total_time.setText(f"⏱ {m}m{s:02d}s")
        self.label_total_speed.setText(f"🔥 {round(income_per_min, 2)} /min")
        self.label_total_fe.setText(f"🔥 {round(income, 2)} FE")
        self.label_map_count.setText(f"🎫 {map_count} maps")

    def reset_stats(self) -> None:
        """Reset all statistics displays to zero."""
        self.label_total_fe.setText("🔥 0 FE")
        self.label_current_map_fe.setText("🔥 0 FE")
        self.label_map_count.setText("🎫 0 maps")
        self.label_current_time.setText("⏱ 0m00s")
        self.label_current_speed.setText("🔥 0 /min")
        self.label_total_time.setText("⏱ 0m00s")
        self.label_total_speed.setText("🔥 0 /min")
