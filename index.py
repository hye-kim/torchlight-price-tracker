"""
Torchlight Infinite Profit Tracker - PyQt5 Version

This is a refactored version using PyQt5 with better code organization, error handling,
type hints, logging, and thread safety.
"""

import logging
import time
import threading
from typing import Optional, Dict, Any
import ctypes
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QComboBox, QMessageBox, QDialog, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from src.constants import (
    APP_TITLE,
    ITEM_TYPES,
    FILTER_CURRENCY,
    FILTER_ASHES,
    FILTER_COMPASS,
    FILTER_GLOW,
    FILTER_OTHERS,
    UI_FONT_FAMILY,
    UI_FONT_SIZE_LARGE,
    UI_FONT_SIZE_MEDIUM,
    UI_LISTBOX_HEIGHT,
    UI_LISTBOX_WIDTH,
    STATUS_FRESH,
    STATUS_STALE,
    STATUS_OLD,
    TIME_FRESH_THRESHOLD,
    TIME_STALE_THRESHOLD,
    LOG_POLL_INTERVAL,
    EXCLUDED_ITEM_ID
)
from src.config_manager import ConfigManager
from src.file_manager import FileManager
from src.log_parser import LogParser
from src.inventory_tracker import InventoryTracker
from src.statistics_tracker import StatisticsTracker
from src.game_detector import GameDetector

# Setup logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tracker.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Set the StreamHandler to use UTF-8 encoding
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        handler.stream.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    initialization_complete = pyqtSignal(int)
    update_display = pyqtSignal()
    reshow_drops = pyqtSignal()


class TrackerApp(QMainWindow):
    """Main application window for the Torchlight Infinite Price Tracker."""

    def __init__(
        self,
        config_manager: ConfigManager,
        file_manager: FileManager,
        inventory_tracker: InventoryTracker,
        statistics_tracker: StatisticsTracker,
        log_file_path: Optional[str]
    ):
        """
        Initialize the tracker application.

        Args:
            config_manager: Configuration manager instance.
            file_manager: File manager instance.
            inventory_tracker: Inventory tracker instance.
            statistics_tracker: Statistics tracker instance.
            log_file_path: Path to the game log file.
        """
        super().__init__()

        self.config_manager = config_manager
        self.file_manager = file_manager
        self.inventory_tracker = inventory_tracker
        self.statistics_tracker = statistics_tracker
        self.log_file_path = log_file_path

        self.app_running = True
        self.show_all = False
        self.current_show_types = ITEM_TYPES.copy()

        # Worker signals for thread-safe UI updates
        self.signals = WorkerSignals()
        self.signals.initialization_complete.connect(self.on_initialization_complete)
        self.signals.update_display.connect(self.update_display)
        self.signals.reshow_drops.connect(self.reshow)

        # Initialize color palette
        self.colors = {
            'bg_primary': '#1e1e2e',
            'bg_secondary': '#2a2a3e',
            'bg_tertiary': '#363650',
            'accent': '#8b5cf6',
            'accent_hover': '#9d70f7',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'text_primary': '#e2e8f0',
            'text_secondary': '#94a3b8',
            'border': '#4a4a5e',
        }

        self._setup_window()
        self._apply_stylesheet()
        self._create_widgets()

        # Create dialog windows
        self._create_drops_window()
        self._create_settings_window()

    def _setup_window(self) -> None:
        """Setup the main window properties."""
        self.setWindowTitle(APP_TITLE)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        # Set fixed size (non-resizable)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

    def _apply_stylesheet(self) -> None:
        """Apply Qt Style Sheet for modern dark theme."""
        stylesheet = f"""
            QMainWindow {{
                background-color: {self.colors['bg_primary']};
            }}

            QWidget {{
                background-color: {self.colors['bg_primary']};
                color: {self.colors['text_primary']};
                font-family: 'Segoe UI';
                font-size: 11pt;
            }}

            QFrame.card {{
                background-color: {self.colors['bg_tertiary']};
                border-radius: 8px;
                padding: 15px;
            }}

            QLabel {{
                color: {self.colors['text_primary']};
                background-color: transparent;
            }}

            QLabel.header {{
                font-size: 13pt;
                font-weight: bold;
                color: {self.colors['text_primary']};
                padding: 5px;
            }}

            QLabel.status {{
                font-size: 9pt;
                color: {self.colors['text_secondary']};
            }}

            QPushButton {{
                background-color: {self.colors['accent']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 10pt;
            }}

            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}

            QPushButton:pressed {{
                background-color: {self.colors['accent']};
            }}

            QPushButton.secondary {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: normal;
            }}

            QPushButton.secondary:hover {{
                background-color: {self.colors['bg_tertiary']};
            }}

            QPushButton.danger {{
                background-color: {self.colors['error']};
                color: {self.colors['text_primary']};
            }}

            QPushButton.danger:hover {{
                background-color: #dc2626;
            }}

            QPushButton:disabled {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_secondary']};
            }}

            QListWidget {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 5px;
                font-size: 10pt;
            }}

            QListWidget::item {{
                padding: 5px;
            }}

            QListWidget::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['text_primary']};
            }}

            QComboBox {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 150px;
            }}

            QComboBox:hover {{
                border-color: {self.colors['accent']};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                selection-background-color: {self.colors['accent']};
                border: 1px solid {self.colors['border']};
            }}

            QDialog {{
                background-color: {self.colors['bg_primary']};
            }}
        """
        self.setStyleSheet(stylesheet)

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        central_widget = self.centralWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Stats card
        stats_card = self._create_stats_card()
        main_layout.addWidget(stats_card)

        # Control panel
        control_card = self._create_control_card()
        main_layout.addWidget(control_card)

        # Drops card
        drops_card = self._create_drops_card()
        main_layout.addWidget(drops_card)

    def _create_stats_card(self) -> QFrame:
        """Create the statistics display card."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

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

        self.label_map_count = QLabel("🎫 0 maps")
        self.label_map_count.setProperty("class", "header")
        current_grid.addWidget(self.label_map_count, 0, 2)

        layout.addLayout(current_grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.colors['border']}; max-height: 1px;")
        layout.addWidget(separator)

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

        self.label_current_earn = QLabel("🔥 0 total")
        self.label_current_earn.setProperty("class", "header")
        total_grid.addWidget(self.label_current_earn, 0, 2)

        layout.addLayout(total_grid)

        return card

    def _create_control_card(self) -> QFrame:
        """Create the control panel card."""
        card = QFrame()
        card.setProperty("class", "card")

        layout = QVBoxLayout(card)
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
        self.button_initialize.clicked.connect(self.start_initialization)
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
        button_log.clicked.connect(self.debug_log_format)
        button_row.addWidget(button_log)

        button_drops = QPushButton("📋 Drops Detail")
        button_drops.setProperty("class", "secondary")
        button_drops.setCursor(Qt.PointingHandCursor)
        button_drops.clicked.connect(self.show_drops_window)
        button_row.addWidget(button_drops)

        button_settings = QPushButton("⚙ Settings")
        button_settings.setProperty("class", "secondary")
        button_settings.setCursor(Qt.PointingHandCursor)
        button_settings.clicked.connect(self.show_settings_window)
        button_row.addWidget(button_settings)

        layout.addLayout(button_row)

        return card

    def _create_drops_card(self) -> QFrame:
        """Create the drops display card."""
        card = QFrame()
        card.setProperty("class", "card")

        layout = QVBoxLayout(card)
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
        self.button_change.clicked.connect(self.change_states)
        header_layout.addWidget(self.button_change)

        layout.addLayout(header_layout)

        # Drops list
        self.inner_pannel_drop_listbox = QListWidget()
        self.inner_pannel_drop_listbox.setMinimumHeight(UI_LISTBOX_HEIGHT * 20)  # Approximate height
        self.inner_pannel_drop_listbox.addItem("Drops will be displayed here...")
        layout.addWidget(self.inner_pannel_drop_listbox)

        return card

    def _create_drops_window(self) -> None:
        """Create the drops detail dialog."""
        self.drops_dialog = QDialog(self)
        self.drops_dialog.setWindowTitle("Drops Detail - FurTorch")
        self.drops_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.drops_dialog.setModal(False)

        layout = QVBoxLayout(self.drops_dialog)
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
        self.button_toggle_all.clicked.connect(self.change_states)
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
            ("All Items", ITEM_TYPES),
            ("Currency", FILTER_CURRENCY),
            ("Embers", FILTER_ASHES),
            ("Compass", FILTER_COMPASS),
            ("Memory", FILTER_GLOW),
            ("Others", FILTER_OTHERS)
        ]

        for text, filter_type in filter_items:
            btn = QPushButton(text)
            btn.setProperty("class", "secondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, f=filter_type: self.set_filter(f))
            filters_layout.addWidget(btn)

        layout.addWidget(filters_card)

    def _create_settings_window(self) -> None:
        """Create the settings dialog."""
        self.settings_dialog = QDialog(self)
        self.settings_dialog.setWindowTitle("Settings - FurTorch")
        self.settings_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.settings_dialog.setModal(False)

        layout = QVBoxLayout(self.settings_dialog)
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
        self.tax_combo.currentIndexChanged.connect(self.change_tax)
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
        reset_button.clicked.connect(self.reset_tracking)
        actions_layout.addWidget(reset_button)

        layout.addWidget(actions_card)

    def start_initialization(self) -> None:
        """Start the inventory initialization process."""
        if self.inventory_tracker.start_initialization():
            self.label_initialize_status.setText("Waiting for bag update...")
            self.label_initialize_status.setStyleSheet(f"color: {self.colors['warning']};")
            self.button_initialize.setEnabled(False)

            QMessageBox.information(
                self,
                "Initialization",
                "Click 'OK' and then sort your bag in-game by clicking the sort button.\n\n"
                "This will refresh your inventory and allow the tracker to initialize "
                "with the correct item counts."
            )
        else:
            QMessageBox.information(
                self,
                "Initialization",
                "Initialization already in progress. Please wait."
            )

    def on_initialization_complete(self, item_count: int) -> None:
        """
        Called when initialization completes.

        Args:
            item_count: Number of unique items initialized.
        """
        self.label_initialize_status.setText(f"✓ Initialized ({item_count} items)")
        self.label_initialize_status.setStyleSheet(f"color: {self.colors['success']};")
        self.button_initialize.setEnabled(True)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Signal the app to stop
            self.app_running = False

            # Close child dialogs
            try:
                self.drops_dialog.close()
            except:
                pass

            try:
                self.settings_dialog.close()
            except:
                pass

            # Accept the event and quit the application
            event.accept()
            QApplication.quit()
        else:
            event.ignore()

    def reset_tracking(self) -> None:
        """Reset tracking statistics while preserving inventory initialization."""
        reply = QMessageBox.question(
            self,
            "Reset Statistics",
            "Are you sure you want to reset all tracking statistics? "
            "This will clear all drop statistics and map counts.\n\n"
            "Your inventory initialization will be preserved.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.statistics_tracker.reset()

            # Update UI
            self.label_current_earn.setText("🔥 0 total")
            self.label_map_count.setText("🎫 0 maps")
            self.inner_pannel_drop_listbox.clear()

            QMessageBox.information(
                self,
                "Reset Complete",
                "Statistics have been reset. Inventory initialization preserved."
            )

    def change_tax(self, value: int) -> None:
        """
        Change the tax setting.

        Args:
            value: 0 for no tax, 1 for tax enabled.
        """
        self.config_manager.update_tax(value)
        logger.info(f"Tax setting changed to: {'Enabled' if value else 'Disabled'}")

    def change_states(self) -> None:
        """Toggle between current map and all drops view."""
        self.show_all = not self.show_all
        if not self.show_all:
            self.button_toggle_all.setText("Current: Current Map Drops (Click to toggle All Drops)")
            self.button_change.setText("Current Map")
        else:
            self.button_toggle_all.setText("Current: All Drops (Click to toggle Current Map Drops)")
            self.button_change.setText("All Drops")
        self.reshow()

    def set_filter(self, item_types: list) -> None:
        """
        Set the item type filter.

        Args:
            item_types: List of item types to display.
        """
        self.current_show_types = item_types
        self.reshow()

    def show_drops_window(self) -> None:
        """Toggle the drops detail window."""
        if self.drops_dialog.isVisible():
            self.drops_dialog.hide()
        else:
            self.drops_dialog.show()

    def show_settings_window(self) -> None:
        """Toggle the settings window."""
        if self.settings_dialog.isVisible():
            self.settings_dialog.hide()
        else:
            self.settings_dialog.show()

    def debug_log_format(self) -> None:
        """Print debug information about current state."""
        logger.info("=== DEBUG INFO ===")
        logger.info(f"Bag initialized: {self.inventory_tracker.bag_initialized}")
        logger.info(f"Initialization complete: {self.inventory_tracker.initialization_complete}")

        bag_summary = self.inventory_tracker.get_bag_state_summary()
        logger.info(f"Total items tracked: {len(bag_summary)}")

        full_table = self.file_manager.load_full_table()
        for item_id, total in bag_summary.items():
            name = full_table.get(item_id, {}).get("name", f"Unknown (ID: {item_id})")
            logger.info(f"  {name}: {total}")

        QMessageBox.information(
            self,
            "Debug Information",
            f"Debug information has been logged.\n\n"
            f"Bag initialized: {self.inventory_tracker.bag_initialized}\n"
            f"Initialization complete: {self.inventory_tracker.initialization_complete}\n"
            f"Total items tracked: {len(bag_summary)}"
        )

    def reshow(self) -> None:
        """Refresh the drop display."""
        full_table = self.file_manager.load_full_table()

        # Get appropriate drop list
        if self.show_all:
            stats = self.statistics_tracker.get_total_stats()
            self.label_current_earn.setText(f"🔥 {round(stats['income'], 2)} total")
        else:
            stats = self.statistics_tracker.get_current_map_stats()
            self.label_current_earn.setText(f"🔥 {round(stats['income'], 2)} total")

        total_stats = self.statistics_tracker.get_total_stats()
        self.label_map_count.setText(f"🎫 {total_stats['map_count']} maps")

        # Update drop listbox
        self.inner_pannel_drop_listbox.clear()

        for item_id, count in stats['drops'].items():
            if item_id not in full_table:
                continue

            item_data = full_table[item_id]
            item_name = item_data.get("name", item_id)
            item_type = item_data.get("type", "Unknown")

            if item_type not in self.current_show_types:
                continue

            # Determine status based on last update time
            now = time.time()
            last_update = item_data.get("last_update", 0)
            time_passed = now - last_update

            if time_passed < TIME_FRESH_THRESHOLD:
                status = STATUS_FRESH
            elif time_passed < TIME_STALE_THRESHOLD:
                status = STATUS_STALE
            else:
                status = STATUS_OLD

            # Calculate price with tax if applicable
            item_price = item_data.get("price", 0)
            if self.config_manager.is_tax_enabled() and item_id != EXCLUDED_ITEM_ID:
                item_price = item_price * 0.875

            total_value = round(count * item_price, 2)
            self.inner_pannel_drop_listbox.addItem(
                f"{status} {item_name} x{count} [{total_value}]"
            )

    def update_display(self) -> None:
        """Update the time and income displays."""
        if self.statistics_tracker.is_in_map:
            current_stats = self.statistics_tracker.get_current_map_stats()
            duration = current_stats['duration']

            m = int(duration // 60)
            s = int(duration % 60)
            self.label_current_time.setText(f"⏱ {m}m{s:02d}s")

            income_per_min = current_stats['income_per_minute']
            self.label_current_speed.setText(f"🔥 {round(income_per_min, 2)} /min")

        total_stats = self.statistics_tracker.get_total_stats()
        duration = total_stats['duration']
        m = int(duration // 60)
        s = int(duration % 60)
        self.label_total_time.setText(f"⏱ {m}m{s:02d}s")

        income_per_min = total_stats['income_per_minute']
        self.label_total_speed.setText(f"🔥 {round(income_per_min, 2)} /min")


class LogMonitorThread(threading.Thread):
    """Thread for monitoring the game log file."""

    def __init__(
        self,
        app: TrackerApp,
        log_file_path: Optional[str],
        log_parser: LogParser,
        inventory_tracker: InventoryTracker,
        statistics_tracker: StatisticsTracker,
        signals: WorkerSignals
    ):
        """
        Initialize the log monitor thread.

        Args:
            app: Main application instance.
            log_file_path: Path to the game log file.
            log_parser: Log parser instance.
            inventory_tracker: Inventory tracker instance.
            statistics_tracker: Statistics tracker instance.
            signals: Worker signals for thread-safe UI updates.
        """
        super().__init__(daemon=True)
        self.app = app
        self.log_file_path = log_file_path
        self.log_parser = log_parser
        self.inventory_tracker = inventory_tracker
        self.statistics_tracker = statistics_tracker
        self.signals = signals
        self.log_file = None

    def run(self) -> None:
        """Run the log monitoring loop."""
        if self.log_file_path:
            try:
                self.log_file = open(self.log_file_path, "r", encoding="utf-8")
                self.log_file.seek(0, 2)  # Seek to end
                logger.info("Log file opened successfully")
            except IOError as e:
                logger.error(f"Could not open log file: {e}")
                self.log_file = None
        else:
            logger.warning("No log file path provided")

        while self.app.app_running:
            try:
                # Sleep in smaller chunks to be more responsive to shutdown
                for _ in range(int(LOG_POLL_INTERVAL * 10)):
                    if not self.app.app_running:
                        break
                    time.sleep(0.1)

                if not self.app.app_running:
                    break

                if self.log_file:
                    text = self.log_file.read()
                    if text:
                        self._process_log_text(text)

                # Update display via signal
                self.signals.update_display.emit()

            except Exception as e:
                logger.error(f"Error in log monitor thread: {e}", exc_info=True)

        if self.log_file:
            self.log_file.close()
            logger.info("Log file closed")

    def _process_log_text(self, text: str) -> None:
        """
        Process new log text.

        Args:
            text: New log text to process.
        """
        # Update prices
        self.log_parser.update_prices_in_table(text)

        # Check for initialization completion
        if self.inventory_tracker.awaiting_initialization:
            success, item_count = self.inventory_tracker.process_initialization(text)
            if success:
                self.signals.initialization_complete.emit(item_count)

        # Detect map changes
        entering_map, exiting_map = self.log_parser.detect_map_change(text)

        if entering_map:
            self.statistics_tracker.enter_map()
            self.inventory_tracker.reset_map_baseline()

        if exiting_map:
            self.statistics_tracker.exit_map()

        # Detect item changes
        changes = self.inventory_tracker.scan_for_changes(text)
        if changes:
            self.statistics_tracker.process_item_changes(changes)
            self.signals.reshow_drops.emit()

            # If not in map but got changes, assume we're in a map
            if not self.statistics_tracker.is_in_map:
                self.statistics_tracker.is_in_map = True


def main():
    """Main entry point for the application."""
    logger.info("=== Torchlight Infinite Price Tracker Starting (PyQt5) ===")

    # Create QApplication
    app = QApplication(sys.argv)

    # Initialize managers
    config_manager = ConfigManager()
    file_manager = FileManager()

    # Initialize data files
    file_manager.ensure_file_exists("config.json", {"opacity": 1.0, "tax": 0, "user": ""})
    file_manager.ensure_file_exists("translation_mapping.json", {})
    file_manager.initialize_full_table_from_en_table()

    # Initialize core components
    log_parser = LogParser(file_manager)
    inventory_tracker = InventoryTracker(log_parser)
    statistics_tracker = StatisticsTracker(file_manager, config_manager)

    # Detect game and log file
    game_detector = GameDetector()
    game_found, log_file_path = game_detector.detect_game()

    # Create and run the application
    tracker_app = TrackerApp(
        config_manager,
        file_manager,
        inventory_tracker,
        statistics_tracker,
        log_file_path
    )

    # Show game not found warning after app is created
    if not game_found:
        logger.warning("Game not found - tracker will run without log monitoring")
        QTimer.singleShot(100, lambda: QMessageBox.warning(
            tracker_app,
            "Game Not Found",
            "Could not find Torchlight: Infinite game process or log file.\n\n"
            "The tool will continue running but won't be able to track drops "
            "until the game is started.\n\n"
            "Please make sure the game is running with logging enabled, "
            "then restart this tool."
        ))

    # Start log monitoring thread
    monitor = LogMonitorThread(
        tracker_app,
        log_file_path,
        log_parser,
        inventory_tracker,
        statistics_tracker,
        tracker_app.signals
    )
    monitor.start()

    # Show the window
    tracker_app.show()

    # Run the application
    logger.info("Application started")
    exit_code = app.exec_()
    logger.info("Application shut down")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
