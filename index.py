"""
Torchlight Infinite Profit Tracker - Improved Version

This is a refactored version with better code organization, error handling,
type hints, logging, and thread safety.
"""

import sys
import os
import logging
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk, StringVar, Listbox, END
from typing import Optional, Dict, Any
import ctypes

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrackerApp(tk.Tk):
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

        self._setup_window()
        self._create_widgets()
        self._apply_config()

        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _setup_window(self) -> None:
        """Setup the main window properties."""
        self.title(APP_TITLE)

        # DPI awareness for Windows
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
            self.tk.call('tk', 'scaling', scale_factor / 75)
        except Exception as e:
            logger.warning(f"Could not set DPI awareness: {e}")

        self.resizable(False, False)
        self.attributes('-toolwindow', True)
        self.attributes('-topmost', True)

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main frames
        basic_frame = ttk.Frame(self)
        advanced_frame = ttk.Frame(self)
        basic_frame.pack(side="top", fill="both")
        advanced_frame.pack(side="top", fill="both")

        # Basic frame widgets (stats display)
        self.label_current_time = ttk.Label(
            basic_frame, text="Current: 0m00s",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE), anchor="w"
        )
        self.label_current_time.grid(row=0, column=0, padx=5, sticky="w")

        self.label_current_speed = ttk.Label(
            basic_frame, text="🔥 0 /min",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE)
        )
        self.label_current_speed.grid(row=0, column=1, padx=5, sticky="w")

        self.label_total_time = ttk.Label(
            basic_frame, text="Total: 0m00s",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE), anchor="w"
        )
        self.label_total_time.grid(row=1, column=0, padx=5, sticky="w")

        self.label_total_speed = ttk.Label(
            basic_frame, text="🔥 0 /min",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE)
        )
        self.label_total_speed.grid(row=1, column=1, padx=5, sticky="w")

        self.label_map_count = ttk.Label(
            basic_frame, text="🎫 0",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE)
        )
        self.label_map_count.grid(row=0, column=2, padx=5, sticky="w")

        self.label_current_earn = ttk.Label(
            basic_frame, text="🔥 0",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_LARGE)
        )
        self.label_current_earn.grid(row=1, column=2, padx=5, sticky="w")

        # Initialize button
        self.button_initialize = ttk.Button(
            basic_frame, text="Initialize",
            cursor="hand2", command=self.start_initialization
        )
        self.button_initialize.grid(row=0, column=3, padx=5, pady=5)

        self.label_initialize_status = ttk.Label(
            basic_frame, text="Not initialized",
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_MEDIUM)
        )
        self.label_initialize_status.grid(row=1, column=3, padx=5, pady=2)

        # Exit button
        button_exit = ttk.Button(
            basic_frame, text="Exit",
            cursor="hand2", command=self.exit_app
        )
        button_exit.grid(row=0, column=4, padx=5, pady=5)

        # Advanced frame widgets (drop list and controls)
        self.inner_pannel_drop_listbox = Listbox(
            advanced_frame,
            height=UI_LISTBOX_HEIGHT,
            width=UI_LISTBOX_WIDTH,
            font=(UI_FONT_FAMILY, UI_FONT_SIZE_MEDIUM)
        )
        self.inner_pannel_drop_listbox.insert(END, "Drops will be displayed here")
        self.inner_pannel_drop_listbox.grid(row=0, column=0, columnspan=6, sticky="nsew")

        inner_pannel_drop_scroll = ttk.Scrollbar(
            advanced_frame,
            command=self.inner_pannel_drop_listbox.yview,
            orient="vertical"
        )
        inner_pannel_drop_scroll.grid(row=0, column=6, sticky="ns")
        self.inner_pannel_drop_listbox.config(yscrollcommand=inner_pannel_drop_scroll.set)

        # Control buttons
        button_drops = ttk.Button(
            advanced_frame, text="Drops",
            cursor="hand2", width=7, command=self.show_drops_window
        )
        button_drops.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        button_log = ttk.Button(
            advanced_frame, text="Log",
            width=7, cursor="hand2", command=self.debug_log_format
        )
        button_log.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.words_short = StringVar()
        self.words_short.set("Current Map")
        button_change = ttk.Button(
            advanced_frame,
            textvariable=self.words_short,
            width=10, cursor="hand2", command=self.change_states
        )
        button_change.grid(row=1, column=3, pady=5)

        button_settings = ttk.Button(
            advanced_frame, text="Settings",
            cursor="hand2", width=7, command=self.show_settings_window
        )
        button_settings.grid(row=1, column=5, sticky="e", padx=5, pady=5)

        # Create popup windows
        self._create_drops_window()
        self._create_settings_window()

    def _create_drops_window(self) -> None:
        """Create the drops detail window."""
        self.inner_pannel_drop = tk.Toplevel(self)
        self.inner_pannel_drop.title("Drops")
        self.inner_pannel_drop.resizable(False, False)
        self.inner_pannel_drop.attributes('-toolwindow', True)
        self.inner_pannel_drop.attributes('-topmost', True)
        self.inner_pannel_drop.withdraw()

        # Toggle button
        self.words = StringVar()
        self.words.set("Current: Current Map Drops (Click to toggle All Drops)")
        inner_pannel_drop_show_all = ttk.Button(
            self.inner_pannel_drop,
            textvariable=self.words,
            width=30, cursor="hand2", command=self.change_states
        )
        inner_pannel_drop_show_all.grid(row=0, column=1)

        # Filter buttons
        button_all = ttk.Button(
            self.inner_pannel_drop, text="All",
            width=7, cursor="hand2", command=lambda: self.set_filter(ITEM_TYPES)
        )
        button_all.grid(row=0, column=0, padx=5, ipady=10)

        button_currency = ttk.Button(
            self.inner_pannel_drop, text="Currency",
            width=7, cursor="hand2", command=lambda: self.set_filter(FILTER_CURRENCY)
        )
        button_currency.grid(row=1, column=0, padx=5, ipady=10)

        button_ashes = ttk.Button(
            self.inner_pannel_drop, text="Ashes",
            width=7, cursor="hand2", command=lambda: self.set_filter(FILTER_ASHES)
        )
        button_ashes.grid(row=2, column=0, padx=5, ipady=10)

        button_compass = ttk.Button(
            self.inner_pannel_drop, text="Compass",
            width=7, cursor="hand2", command=lambda: self.set_filter(FILTER_COMPASS)
        )
        button_compass.grid(row=3, column=0, padx=5, ipady=10)

        button_glow = ttk.Button(
            self.inner_pannel_drop, text="Glow",
            width=7, cursor="hand2", command=lambda: self.set_filter(FILTER_GLOW)
        )
        button_glow.grid(row=4, column=0, padx=5, ipady=10)

        button_others = ttk.Button(
            self.inner_pannel_drop, text="Others",
            width=7, cursor="hand2", command=lambda: self.set_filter(FILTER_OTHERS)
        )
        button_others.grid(row=5, column=0, padx=5, ipady=10)

        self.inner_pannel_drop.protocol("WM_DELETE_WINDOW", self.inner_pannel_drop.withdraw)

    def _create_settings_window(self) -> None:
        """Create the settings window."""
        self.inner_pannel_settings = tk.Toplevel(self)
        self.inner_pannel_settings.title("Settings")
        self.inner_pannel_settings.resizable(False, False)
        self.inner_pannel_settings.attributes('-toolwindow', True)
        self.inner_pannel_settings.attributes('-topmost', True)
        self.inner_pannel_settings.withdraw()

        # Tax setting
        label_tax = ttk.Label(self.inner_pannel_settings, text="Tax:")
        label_tax.grid(row=0, column=0, padx=5, pady=5)

        config = self.config_manager.get()
        self.chose = ttk.Combobox(
            self.inner_pannel_settings,
            values=["No tax", "Include tax"],
            state="readonly"
        )
        self.chose.current(config.tax)
        self.chose.grid(row=0, column=1, padx=5, pady=5)
        self.chose.bind("<<ComboboxSelected>>", lambda e: self.change_tax(self.chose.current()))

        # Opacity setting
        label_opacity = ttk.Label(self.inner_pannel_settings, text="Opacity:")
        label_opacity.grid(row=1, column=0, padx=5, pady=5)

        self.scale_opacity = ttk.Scale(
            self.inner_pannel_settings,
            from_=0.1, to=1.0, orient=tk.HORIZONTAL,
            command=self.change_opacity
        )
        self.scale_opacity.grid(row=1, column=1, padx=5, pady=5)
        self.scale_opacity.set(config.opacity)

        # Reset button
        reset_button = ttk.Button(
            self.inner_pannel_settings,
            text="Reset Tracking",
            command=self.reset_tracking
        )
        reset_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

        self.inner_pannel_settings.protocol("WM_DELETE_WINDOW", self.inner_pannel_settings.withdraw)

    def _apply_config(self) -> None:
        """Apply configuration settings to the window."""
        config = self.config_manager.get()
        self.change_opacity(config.opacity)

    def start_initialization(self) -> None:
        """Start the inventory initialization process."""
        if self.inventory_tracker.start_initialization():
            self.label_initialize_status.config(
                text="Waiting for bag update...",
                foreground="blue"
            )
            self.button_initialize.config(state="disabled")

            messagebox.showinfo(
                "Initialization",
                "Click 'OK' and then sort your bag in-game by clicking the sort button.\n\n"
                "This will refresh your inventory and allow the tracker to initialize "
                "with the correct item counts."
            )
        else:
            messagebox.showinfo(
                "Initialization",
                "Initialization already in progress. Please wait."
            )

    def on_initialization_complete(self, item_count: int) -> None:
        """
        Called when initialization completes.

        Args:
            item_count: Number of unique items initialized.
        """
        self.label_initialize_status.config(
            text=f"Initialized {item_count} items",
            foreground="green"
        )
        self.button_initialize.config(state="normal")

    def exit_app(self) -> None:
        """Exit the application gracefully."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.app_running = False

            try:
                self.inner_pannel_drop.destroy()
            except:
                pass

            try:
                self.inner_pannel_settings.destroy()
            except:
                pass

            self.destroy()
            self.quit()

    def reset_tracking(self) -> None:
        """Reset all tracking data."""
        if messagebox.askyesno(
            "Reset Tracking",
            "Are you sure you want to reset all tracking data? "
            "This will clear all drop statistics."
        ):
            self.inventory_tracker.reset()
            self.statistics_tracker.reset()

            self.label_current_earn.config(text="🔥 0")
            self.label_map_count.config(text="🎫 0")
            self.inner_pannel_drop_listbox.delete(1, END)
            self.label_initialize_status.config(text="Not initialized")

            messagebox.showinfo("Reset Complete", "All tracking data has been reset.")

    def change_tax(self, value: int) -> None:
        """
        Change the tax setting.

        Args:
            value: 0 for no tax, 1 for tax enabled.
        """
        self.config_manager.update_tax(value)
        logger.info(f"Tax setting changed to: {'Enabled' if value else 'Disabled'}")

    def change_opacity(self, value: float) -> None:
        """
        Change window opacity.

        Args:
            value: Opacity value (0.1 to 1.0).
        """
        opacity = float(value)
        self.config_manager.update_opacity(opacity)

        self.attributes('-alpha', opacity)

        if hasattr(self, 'inner_pannel_drop') and self.inner_pannel_drop.winfo_exists():
            self.inner_pannel_drop.attributes('-alpha', opacity)

        if hasattr(self, 'inner_pannel_settings') and self.inner_pannel_settings.winfo_exists():
            self.inner_pannel_settings.attributes('-alpha', opacity)

    def change_states(self) -> None:
        """Toggle between current map and all drops view."""
        self.show_all = not self.show_all
        if not self.show_all:
            self.words.set("Current: Current Map Drops (Click to toggle All Drops)")
            self.words_short.set("Current Map")
        else:
            self.words.set("Current: All Drops (Click to toggle Current Map Drops)")
            self.words_short.set("All Drops")
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
        if self.inner_pannel_drop.state() == "withdrawn":
            self.inner_pannel_drop.deiconify()
        else:
            self.inner_pannel_drop.withdraw()

    def show_settings_window(self) -> None:
        """Toggle the settings window."""
        if self.inner_pannel_settings.state() == "withdrawn":
            self.inner_pannel_settings.deiconify()
        else:
            self.inner_pannel_settings.withdraw()

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

        messagebox.showinfo(
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
            self.label_current_earn.config(text=f"🔥 {round(stats['income'], 2)}")
        else:
            stats = self.statistics_tracker.get_current_map_stats()
            self.label_current_earn.config(text=f"🔥 {round(stats['income'], 2)}")

        total_stats = self.statistics_tracker.get_total_stats()
        self.label_map_count.config(text=f"🎫 {total_stats['map_count']}")

        # Update drop listbox
        self.inner_pannel_drop_listbox.delete(1, END)

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
            self.inner_pannel_drop_listbox.insert(
                END,
                f"{status} {item_name} x{count} [{total_value}]"
            )

    def update_display(self) -> None:
        """Update the time and income displays."""
        if self.statistics_tracker.is_in_map:
            current_stats = self.statistics_tracker.get_current_map_stats()
            duration = current_stats['duration']

            m = int(duration // 60)
            s = int(duration % 60)
            self.label_current_time.config(text=f"Current: {m}m{s}s")

            income_per_min = current_stats['income_per_minute']
            self.label_current_speed.config(text=f"🔥 {round(income_per_min, 2)} /min")

        total_stats = self.statistics_tracker.get_total_stats()
        duration = total_stats['duration']
        m = int(duration // 60)
        s = int(duration % 60)
        self.label_total_time.config(text=f"Total: {m}m{s}s")

        income_per_min = total_stats['income_per_minute']
        self.label_total_speed.config(text=f"🔥 {round(income_per_min, 2)} /min")


class LogMonitorThread(threading.Thread):
    """Thread for monitoring the game log file."""

    def __init__(
        self,
        app: TrackerApp,
        log_file_path: Optional[str],
        log_parser: LogParser,
        inventory_tracker: InventoryTracker,
        statistics_tracker: StatisticsTracker
    ):
        """
        Initialize the log monitor thread.

        Args:
            app: Main application instance.
            log_file_path: Path to the game log file.
            log_parser: Log parser instance.
            inventory_tracker: Inventory tracker instance.
            statistics_tracker: Statistics tracker instance.
        """
        super().__init__(daemon=True)
        self.app = app
        self.log_file_path = log_file_path
        self.log_parser = log_parser
        self.inventory_tracker = inventory_tracker
        self.statistics_tracker = statistics_tracker
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
                time.sleep(LOG_POLL_INTERVAL)

                if not self.app.app_running:
                    break

                if self.log_file:
                    text = self.log_file.read()
                    if text:
                        self._process_log_text(text)

                # Update display
                self.app.update_display()

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
                self.app.after(0, lambda: self.app.on_initialization_complete(item_count))

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
            self.app.after(0, self.app.reshow)

            # If not in map but got changes, assume we're in a map
            if not self.statistics_tracker.is_in_map:
                self.statistics_tracker.is_in_map = True


def main():
    """Main entry point for the application."""
    logger.info("=== Torchlight Infinite Price Tracker Starting ===")

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

    if not game_found:
        messagebox.showwarning(
            "Game Not Found",
            "Could not find Torchlight: Infinite game process or log file.\n\n"
            "The tool will continue running but won't be able to track drops "
            "until the game is started.\n\n"
            "Please make sure the game is running with logging enabled, "
            "then restart this tool."
        )

    # Create and run the application
    app = TrackerApp(
        config_manager,
        file_manager,
        inventory_tracker,
        statistics_tracker,
        log_file_path
    )

    # Start log monitoring thread
    monitor = LogMonitorThread(
        app,
        log_file_path,
        log_parser,
        inventory_tracker,
        statistics_tracker
    )
    monitor.start()

    # Run the application
    logger.info("Application started")
    app.mainloop()
    logger.info("Application shut down")


if __name__ == "__main__":
    main()
