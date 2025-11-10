"""
Main window for the Torchlight Infinite Price Tracker.
"""

import logging
import time
from typing import Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent

from ..constants import (
    APP_TITLE,
    FILTER_ASHES,
    FILTER_COMPASS,
    FILTER_CURRENCY,
    FILTER_GLOW,
    FILTER_OTHERS,
    ITEM_TYPES,
    UI_COLORS,
    UI_DEFAULT_WINDOW_HEIGHT,
    UI_DEFAULT_WINDOW_WIDTH,
    UI_LISTBOX_HEIGHT,
    UI_MIN_WINDOW_HEIGHT,
    UI_MIN_WINDOW_WIDTH,
    calculate_price_with_tax,
    get_price_freshness_indicator,
)
from ..config_manager import ConfigManager
from ..file_manager import FileManager
from ..inventory_tracker import InventoryTracker
from ..statistics_tracker import StatisticsTracker
from .excel_exporter import ExcelExporter
from .styles import get_stylesheet
from .widgets import StatsCard, ControlCard, DropsCard
from .dialogs import DropsDetailDialog, SettingsDialog

logger = logging.getLogger(__name__)


class TrackerMainWindow(QMainWindow):
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
        Initialize the tracker main window.

        Args:
            config_manager: Configuration manager instance
            file_manager: File manager instance
            inventory_tracker: Inventory tracker instance
            statistics_tracker: Statistics tracker instance
            log_file_path: Path to the game log file
        """
        super().__init__()

        self.config_manager = config_manager
        self.file_manager = file_manager
        self.inventory_tracker = inventory_tracker
        self.statistics_tracker = statistics_tracker
        self.log_file_path = log_file_path
        self.excel_exporter = ExcelExporter(file_manager, config_manager)

        self.app_running = True
        self.show_all = False
        self.current_show_types = ITEM_TYPES.copy()

        # Initialize color palette
        self.colors = UI_COLORS

        self._setup_window()
        self._apply_stylesheet()
        self._create_widgets()
        self._create_dialogs()
        self._create_tray_icon()
        self._load_window_geometry()

    def _setup_window(self) -> None:
        """Setup the main window properties."""
        self.setWindowTitle(APP_TITLE)
        self.setWindowFlags(Qt.Window)

        # Make window resizable with minimum size constraints
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setMinimumSize(UI_MIN_WINDOW_WIDTH, UI_MIN_WINDOW_HEIGHT)
        self.resize(UI_DEFAULT_WINDOW_WIDTH, UI_DEFAULT_WINDOW_HEIGHT)

    def _apply_stylesheet(self) -> None:
        """Apply Qt Style Sheet for modern dark theme."""
        stylesheet = get_stylesheet(self.colors)
        self.setStyleSheet(stylesheet)

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        central_widget = self.centralWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Stats card
        self.stats_card = StatsCard(self.colors)
        main_layout.addWidget(self.stats_card)

        # Control panel
        self.control_card = ControlCard(
            self.colors,
            self.start_initialization,
            self.debug_log_format,
            self.export_drops_to_excel,
            self.show_settings_window
        )
        main_layout.addWidget(self.control_card)

        # Drops card
        self.drops_card = DropsCard(
            ITEM_TYPES,
            FILTER_CURRENCY,
            FILTER_ASHES,
            FILTER_COMPASS,
            FILTER_GLOW,
            FILTER_OTHERS,
            UI_LISTBOX_HEIGHT,
            self.change_states,
            self.set_filter
        )
        main_layout.addWidget(self.drops_card)

    def _create_dialogs(self) -> None:
        """Create dialog windows."""
        self.drops_dialog = DropsDetailDialog(
            self,
            ITEM_TYPES,
            FILTER_CURRENCY,
            FILTER_ASHES,
            FILTER_COMPASS,
            FILTER_GLOW,
            FILTER_OTHERS,
            self.change_states,
            self.set_filter
        )

        self.settings_dialog = SettingsDialog(
            self,
            self.config_manager,
            self.change_tax,
            self.reset_tracking
        )

    def _create_tray_icon(self) -> None:
        """Create the system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

        logger.info("System tray icon created")

    def _load_window_geometry(self) -> None:
        """Load saved window geometry from config."""
        config = self.config_manager.get()
        if config.window_x is not None and config.window_y is not None:
            if config.window_width is not None and config.window_height is not None:
                self.setGeometry(config.window_x, config.window_y,
                                config.window_width, config.window_height)
                logger.info(f"Loaded window geometry: {config.window_x},{config.window_y} "
                           f"{config.window_width}x{config.window_height}")

    def _save_window_geometry(self) -> None:
        """Save window geometry to config."""
        if not self.isMaximized() and not self.isMinimized():
            geometry = self.geometry()
            self.config_manager.update_window_geometry(
                geometry.x(), geometry.y(),
                geometry.width(), geometry.height()
            )

    # Event handlers
    def start_initialization(self) -> None:
        """Start the inventory initialization process."""
        if self.inventory_tracker.start_initialization():
            self.control_card.set_initialization_waiting()

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
            item_count: Number of unique items initialized
        """
        self.control_card.set_initialization_complete(item_count)

    def closeEvent(self, event: QCloseEvent) -> None:
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

            # Hide tray icon
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()

            # Close child dialogs
            try:
                self.drops_dialog.close()
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"Error closing drops dialog: {e}")

            try:
                self.settings_dialog.close()
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"Error closing settings dialog: {e}")

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
            self.stats_card.reset_stats()
            self.drops_card.inner_panel_drop_listbox.clear()

            QMessageBox.information(
                self,
                "Reset Complete",
                "Statistics have been reset. Inventory initialization preserved."
            )

    def change_tax(self, value: int) -> None:
        """
        Change the tax setting.

        Args:
            value: 0 for no tax, 1 for tax enabled
        """
        self.config_manager.update_tax(value)
        logger.info(f"Tax setting changed to: {'Enabled' if value else 'Disabled'}")

    def change_states(self) -> None:
        """Toggle between current map and all drops view."""
        self.show_all = not self.show_all

        # Update button texts
        self.drops_card.set_view_mode(self.show_all)
        self.drops_dialog.update_toggle_text(self.show_all)

        self.reshow()

    def set_filter(self, item_types: list) -> None:
        """
        Set the item type filter.

        Args:
            item_types: List of item types to display
        """
        self.current_show_types = item_types
        self.drops_card.set_filter_active(item_types)
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
        else:
            stats = self.statistics_tracker.get_current_map_stats()

        # Update labels
        current_map_stats = self.statistics_tracker.get_current_map_stats()
        total_stats = self.statistics_tracker.get_total_stats()

        # Prepare drop items with their values for sorting
        drop_items = []
        for item_id, count in stats['drops'].items():
            if item_id not in full_table:
                continue

            item_data = full_table[item_id]
            item_name = item_data.get("name", item_id)
            item_type = item_data.get("type", "Unknown")

            if item_type not in self.current_show_types:
                continue

            # Determine status based on last update time using helper
            now = time.time()
            last_update = item_data.get("last_update", 0)
            status = get_price_freshness_indicator(last_update, now)

            # Calculate price with tax if applicable using centralized function
            base_price = item_data.get("price", 0)
            item_price = calculate_price_with_tax(base_price, item_id, self.config_manager.is_tax_enabled())

            total_value = round(count * item_price, 2)
            drop_items.append((total_value, f"{status} {item_name} x{count} [{total_value}]"))

        # Sort by total value (descending - highest first)
        drop_items.sort(key=lambda x: x[0], reverse=True)

        # Update drop listbox
        self.drops_card.inner_panel_drop_listbox.clear()
        for _, item_text in drop_items:
            self.drops_card.inner_panel_drop_listbox.addItem(item_text)

    def update_display(self) -> None:
        """Update the time and income displays."""
        if self.statistics_tracker.is_in_map:
            current_stats = self.statistics_tracker.get_current_map_stats()
            self.stats_card.update_current_map_stats(
                current_stats['duration'],
                current_stats['income'],
                current_stats['income_per_minute']
            )

        total_stats = self.statistics_tracker.get_total_stats()
        self.stats_card.update_total_stats(
            total_stats['duration'],
            total_stats['income'],
            total_stats['income_per_minute'],
            total_stats['map_count']
        )

    def show_from_tray(self) -> None:
        """Show window from tray."""
        self.show()
        self.activateWindow()
        self.raise_()

    def on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()

    def quit_application(self) -> None:
        """Quit the application."""
        self.app_running = False
        QApplication.quit()

    def changeEvent(self, event) -> None:
        """Handle window state changes."""
        if event.type() == event.WindowStateChange:
            if self.isMinimized():
                # Minimize to tray
                QTimer.singleShot(0, self.hide)
                self.tray_icon.showMessage(
                    "Torchlight Price Tracker",
                    "Application minimized to tray",
                    QSystemTrayIcon.Information,
                    2000
                )
        super().changeEvent(event)

    def moveEvent(self, event) -> None:
        """Handle window move event."""
        super().moveEvent(event)
        self._save_window_geometry()

    def resizeEvent(self, event) -> None:
        """Handle window resize event."""
        super().resizeEvent(event)
        self._save_window_geometry()

    def export_drops_to_excel(self) -> None:
        """Export drops to an Excel file sorted by item category."""
        try:
            stats = self.statistics_tracker.get_total_stats()
            export_type = "All Drops"

            if not stats['drops']:
                QMessageBox.information(
                    self,
                    "No Drops",
                    "There are no drops to export."
                )
                return

            # Prompt user for save location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"torchlight_drops_{timestamp}.xlsx"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                default_filename,
                "Excel Files (*.xlsx)"
            )

            if not file_path:
                return  # User cancelled

            # Export using ExcelExporter
            result = self.excel_exporter.export_to_file(file_path, stats, export_type)

            # Build success message
            success_msg = f"Drops have been exported to:\n{result['file_path']}\n\n"
            success_msg += f"Total items: {result['total_items']}\n"
            success_msg += f"Time elapsed: {result['time_str']}\n"
            if result['map_count'] is not None:
                success_msg += f"Map count: {result['map_count']}\n"
            success_msg += f"Total FE: {result['total_fe']}\n"
            success_msg += f"FE/Hour: {result['fe_per_hour']}"

            QMessageBox.information(
                self,
                "Export Successful",
                success_msg
            )
            logger.info(f"Drops exported to: {file_path}")

        except Exception as e:
            logger.error(f"Error exporting drops to Excel: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting:\n{str(e)}"
            )
