"""
Torchlight Infinite Profit Tracker - Improved Version

This is a refactored version with better code organization, error handling,
type hints, logging, and thread safety.
"""

import logging
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk, StringVar, Listbox, END
from typing import Optional, Dict, Any
import ctypes

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

        # Apply modern theme
        self._apply_modern_theme()

    def _apply_modern_theme(self) -> None:
        """Apply modern color scheme and styling to the UI."""
        # Modern color palette
        self.colors = {
            'bg_primary': '#1e1e2e',      # Dark background
            'bg_secondary': '#2a2a3e',    # Slightly lighter background
            'bg_tertiary': '#363650',     # Card/section background
            'accent': '#8b5cf6',          # Purple accent
            'accent_hover': '#9d70f7',    # Lighter purple for hover
            'success': '#10b981',         # Green for success
            'warning': '#f59e0b',         # Orange for warning
            'error': '#ef4444',           # Red for error
            'text_primary': '#e2e8f0',    # Light text
            'text_secondary': '#94a3b8',  # Muted text
            'border': '#4a4a5e',          # Border color
        }

        # Configure main window background
        self.configure(bg=self.colors['bg_primary'])

        # Create custom ttk style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam as base theme for customization

        # Configure TFrame
        self.style.configure(
            'TFrame',
            background=self.colors['bg_primary']
        )

        # Configure Card Frame (for sections)
        self.style.configure(
            'Card.TFrame',
            background=self.colors['bg_tertiary'],
            relief='flat',
            borderwidth=0
        )

        # Configure TLabel
        self.style.configure(
            'TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_primary'],
            font=('Segoe UI', 11)
        )

        # Configure Header labels (larger stats)
        self.style.configure(
            'Header.TLabel',
            background=self.colors['bg_tertiary'],
            foreground=self.colors['text_primary'],
            font=('Segoe UI', 13, 'bold'),
            padding=5
        )

        # Configure Status labels
        self.style.configure(
            'Status.TLabel',
            background=self.colors['bg_tertiary'],
            foreground=self.colors['text_secondary'],
            font=('Segoe UI', 9)
        )

        # Configure TButton
        self.style.configure(
            'TButton',
            background=self.colors['accent'],
            foreground=self.colors['text_primary'],
            borderwidth=0,
            relief='flat',
            padding=(15, 8),
            font=('Segoe UI', 10, 'bold')
        )

        self.style.map('TButton',
            background=[('active', self.colors['accent_hover']),
                       ('pressed', self.colors['accent'])],
            foreground=[('active', self.colors['text_primary'])]
        )

        # Configure Secondary buttons
        self.style.configure(
            'Secondary.TButton',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            relief='flat',
            padding=(12, 6),
            font=('Segoe UI', 9)
        )

        self.style.map('Secondary.TButton',
            background=[('active', self.colors['bg_tertiary']),
                       ('pressed', self.colors['bg_secondary'])],
            bordercolor=[('focus', self.colors['accent'])]
        )

        # Configure Exit button (danger style)
        self.style.configure(
            'Danger.TButton',
            background=self.colors['error'],
            foreground=self.colors['text_primary'],
            borderwidth=0,
            relief='flat',
            padding=(15, 8),
            font=('Segoe UI', 10, 'bold')
        )

        self.style.map('Danger.TButton',
            background=[('active', '#dc2626'),
                       ('pressed', self.colors['error'])]
        )

        # Configure TScrollbar
        self.style.configure(
            'Vertical.TScrollbar',
            background=self.colors['bg_secondary'],
            troughcolor=self.colors['bg_primary'],
            borderwidth=0,
            arrowsize=12
        )

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main container with padding
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Stats card frame
        stats_card = ttk.Frame(main_container, style='Card.TFrame')
        stats_card.pack(fill="both", padx=0, pady=(0, 10))

        # Stats frame inside card
        stats_frame = ttk.Frame(stats_card, style='Card.TFrame')
        stats_frame.pack(fill="both", padx=15, pady=15)

        # Current map stats (row 0)
        current_label = ttk.Label(
            stats_frame, text="CURRENT MAP",
            style='Status.TLabel'
        )
        current_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))

        self.label_current_time = ttk.Label(
            stats_frame, text="⏱ 0m00s",
            style='Header.TLabel'
        )
        self.label_current_time.grid(row=1, column=0, padx=(0, 15), sticky="w")

        self.label_current_speed = ttk.Label(
            stats_frame, text="🔥 0 /min",
            style='Header.TLabel'
        )
        self.label_current_speed.grid(row=1, column=1, padx=(0, 15), sticky="w")

        self.label_map_count = ttk.Label(
            stats_frame, text="🎫 0 maps",
            style='Header.TLabel'
        )
        self.label_map_count.grid(row=1, column=2, sticky="w")

        # Separator
        separator1 = ttk.Frame(stats_frame, height=1, style='Card.TFrame')
        separator1.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        # Total stats (row 3)
        total_label = ttk.Label(
            stats_frame, text="TOTAL SESSION",
            style='Status.TLabel'
        )
        total_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 5))

        self.label_total_time = ttk.Label(
            stats_frame, text="⏱ 0m00s",
            style='Header.TLabel'
        )
        self.label_total_time.grid(row=4, column=0, padx=(0, 15), sticky="w")

        self.label_total_speed = ttk.Label(
            stats_frame, text="🔥 0 /min",
            style='Header.TLabel'
        )
        self.label_total_speed.grid(row=4, column=1, padx=(0, 15), sticky="w")

        self.label_current_earn = ttk.Label(
            stats_frame, text="🔥 0 total",
            style='Header.TLabel'
        )
        self.label_current_earn.grid(row=4, column=2, sticky="w")

        # Control panel frame
        control_frame = ttk.Frame(main_container, style='Card.TFrame')
        control_frame.pack(fill="both", padx=0, pady=(0, 10))

        # Control buttons inside card
        controls = ttk.Frame(control_frame, style='Card.TFrame')
        controls.pack(fill="both", padx=15, pady=15)

        # Initialize section
        init_label = ttk.Label(
            controls, text="INITIALIZATION",
            style='Status.TLabel'
        )
        init_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.button_initialize = ttk.Button(
            controls, text="Initialize Tracker",
            cursor="hand2", command=self.start_initialization
        )
        self.button_initialize.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        self.label_initialize_status = ttk.Label(
            controls, text="Not initialized",
            style='Status.TLabel'
        )
        self.label_initialize_status.grid(row=1, column=1, sticky="w")

        # Separator
        separator2 = ttk.Frame(controls, height=1, style='Card.TFrame')
        separator2.grid(row=2, column=0, columnspan=2, sticky="ew", pady=12)

        # Action buttons
        action_label = ttk.Label(
            controls, text="ACTIONS",
            style='Status.TLabel'
        )
        action_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        button_frame = ttk.Frame(controls, style='Card.TFrame')
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew")

        button_exit = ttk.Button(
            button_frame, text="Exit",
            style='Danger.TButton',
            cursor="hand2", command=self.exit_app
        )
        button_settings = ttk.Button(
            button_frame, text="⚙ Settings",
            style='Secondary.TButton',
            cursor="hand2", command=self.show_settings_window
        )
        button_settings.pack(side="right", padx=(5, 0))

        button_drops = ttk.Button(
            button_frame, text="📋 Drops Detail",
            style='Secondary.TButton',
            cursor="hand2", command=self.show_drops_window
        )
        button_drops.pack(side="right", padx=(5, 0))

        button_log = ttk.Button(
            button_frame, text="🔍 Debug Log",
            style='Secondary.TButton',
            cursor="hand2", command=self.debug_log_format
        )
        button_log.pack(side="left")

        # Drops card frame
        drops_card = ttk.Frame(main_container, style='Card.TFrame')
        drops_card.pack(fill="both", expand=True, padx=0, pady=0)

        # Drops header
        drops_header = ttk.Frame(drops_card, style='Card.TFrame')
        drops_header.pack(fill="x", padx=15, pady=(15, 10))

        drops_title = ttk.Label(
            drops_header, text="RECENT DROPS",
            style='Status.TLabel'
        )
        drops_title.pack(side="left")

        self.words_short = StringVar()
        self.words_short.set("Current Map")
        button_change = ttk.Button(
            drops_header,
            textvariable=self.words_short,
            style='Secondary.TButton',
            cursor="hand2", command=self.change_states
        )
        button_change.pack(side="right")

        # Drops list container
        drops_container = ttk.Frame(drops_card, style='Card.TFrame')
        drops_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Styled listbox
        self.inner_pannel_drop_listbox = Listbox(
            drops_container,
            height=UI_LISTBOX_HEIGHT,
            width=UI_LISTBOX_WIDTH,
            font=('Segoe UI', 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['text_primary'],
            borderwidth=0,
            highlightthickness=0,
            relief='flat'
        )
        self.inner_pannel_drop_listbox.insert(END, "Drops will be displayed here...")
        self.inner_pannel_drop_listbox.pack(side="left", fill="both", expand=True)

        inner_pannel_drop_scroll = ttk.Scrollbar(
            drops_container,
            command=self.inner_pannel_drop_listbox.yview,
            orient="vertical"
        )
        inner_pannel_drop_scroll.pack(side="right", fill="y")
        self.inner_pannel_drop_listbox.config(yscrollcommand=inner_pannel_drop_scroll.set)

        # Create popup windows
        self._create_drops_window()
        self._create_settings_window()

    def _create_drops_window(self) -> None:
        """Create the drops detail window."""
        self.inner_pannel_drop = tk.Toplevel(self)
        self.inner_pannel_drop.title("Drops Detail - FurTorch")
        self.inner_pannel_drop.resizable(False, False)
        self.inner_pannel_drop.attributes('-toolwindow', True)
        self.inner_pannel_drop.attributes('-topmost', True)
        self.inner_pannel_drop.configure(bg=self.colors['bg_primary'])
        self.inner_pannel_drop.withdraw()

        # Main container
        main_frame = ttk.Frame(self.inner_pannel_drop)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header section
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill="x", pady=(0, 15))

        header_content = ttk.Frame(header_frame, style='Card.TFrame')
        header_content.pack(fill="x", padx=15, pady=15)

        header_label = ttk.Label(
            header_content, text="DROP FILTERS",
            style='Status.TLabel'
        )
        header_label.pack(side="top", anchor="w", pady=(0, 10))

        # Toggle button
        self.words = StringVar()
        self.words.set("Current: Current Map Drops (Click to toggle All Drops)")
        inner_pannel_drop_show_all = ttk.Button(
            header_content,
            textvariable=self.words,
            cursor="hand2", command=self.change_states
        )
        inner_pannel_drop_show_all.pack(fill="x")

        # Filter buttons section
        filters_frame = ttk.Frame(main_frame, style='Card.TFrame')
        filters_frame.pack(fill="x", pady=0)

        filters_content = ttk.Frame(filters_frame, style='Card.TFrame')
        filters_content.pack(fill="x", padx=15, pady=15)

        filters_label = ttk.Label(
            filters_content, text="ITEM CATEGORIES",
            style='Status.TLabel'
        )
        filters_label.pack(side="top", anchor="w", pady=(0, 10))

        # Filter button container
        filter_buttons = ttk.Frame(filters_content, style='Card.TFrame')
        filter_buttons.pack(fill="x")

        filter_items = [
            ("All Items", ITEM_TYPES),
            ("Currency", FILTER_CURRENCY),
            ("Ashes", FILTER_ASHES),
            ("Compass", FILTER_COMPASS),
            ("Glow", FILTER_GLOW),
            ("Others", FILTER_OTHERS)
        ]

        for text, filter_type in filter_items:
            btn = ttk.Button(
                filter_buttons, text=text,
                style='Secondary.TButton',
                cursor="hand2",
                command=lambda f=filter_type: self.set_filter(f)
            )
            btn.pack(fill="x", pady=3)

        self.inner_pannel_drop.protocol("WM_DELETE_WINDOW", self.inner_pannel_drop.withdraw)

    def _create_settings_window(self) -> None:
        """Create the settings window."""
        self.inner_pannel_settings = tk.Toplevel(self)
        self.inner_pannel_settings.title("Settings - FurTorch")
        self.inner_pannel_settings.resizable(False, False)
        self.inner_pannel_settings.attributes('-toolwindow', True)
        self.inner_pannel_settings.attributes('-topmost', True)
        self.inner_pannel_settings.configure(bg=self.colors['bg_primary'])
        self.inner_pannel_settings.withdraw()

        # Main container
        main_frame = ttk.Frame(self.inner_pannel_settings)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Tax settings card
        tax_card = ttk.Frame(main_frame, style='Card.TFrame')
        tax_card.pack(fill="x", pady=(0, 15))

        tax_content = ttk.Frame(tax_card, style='Card.TFrame')
        tax_content.pack(fill="x", padx=15, pady=15)

        tax_title = ttk.Label(
            tax_content, text="TAX SETTINGS",
            style='Status.TLabel'
        )
        tax_title.pack(side="top", anchor="w", pady=(0, 10))

        tax_row = ttk.Frame(tax_content, style='Card.TFrame')
        tax_row.pack(fill="x")

        label_tax = ttk.Label(tax_row, text="Price Calculation:", style='TLabel')
        label_tax.pack(side="left", padx=(0, 10))

        config = self.config_manager.get()
        self.chose = ttk.Combobox(
            tax_row,
            values=["No tax", "Include tax"],
            state="readonly",
            width=15
        )
        self.chose.current(config.tax)
        self.chose.pack(side="left")
        self.chose.bind("<<ComboboxSelected>>", lambda e: self.change_tax(self.chose.current()))

        # Actions card
        actions_card = ttk.Frame(main_frame, style='Card.TFrame')
        actions_card.pack(fill="x", pady=0)

        actions_content = ttk.Frame(actions_card, style='Card.TFrame')
        actions_content.pack(fill="x", padx=15, pady=15)

        actions_title = ttk.Label(
            actions_content, text="ACTIONS",
            style='Status.TLabel'
        )
        actions_title.pack(side="top", anchor="w", pady=(0, 10))

        reset_button = ttk.Button(
            actions_content,
            text="Reset Statistics",
            style='Danger.TButton',
            cursor="hand2",
            command=self.reset_tracking
        )
        reset_button.pack(fill="x")

        self.inner_pannel_settings.protocol("WM_DELETE_WINDOW", self.inner_pannel_settings.withdraw)

    def start_initialization(self) -> None:
        """Start the inventory initialization process."""
        if self.inventory_tracker.start_initialization():
            self.label_initialize_status.config(
                text="Waiting for bag update...",
                foreground=self.colors['warning']
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
            text=f"✓ Initialized ({item_count} items)",
            foreground=self.colors['success']
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
        """Reset tracking statistics while preserving inventory initialization."""
        if messagebox.askyesno(
            "Reset Statistics",
            "Are you sure you want to reset all tracking statistics? "
            "This will clear all drop statistics and map counts.\n\n"
            "Your inventory initialization will be preserved."
        ):
            # Reset statistics only, preserve inventory state
            self.statistics_tracker.reset()

            # Update UI to show reset state
            self.label_current_earn.config(text="🔥 0 total")
            self.label_map_count.config(text="🎫 0 maps")
            self.inner_pannel_drop_listbox.delete(1, END)
            # Don't reset initialization status - preserve it

            messagebox.showinfo("Reset Complete", "Statistics have been reset. Inventory initialization preserved.")

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
            self.label_current_earn.config(text=f"🔥 {round(stats['income'], 2)} total")
        else:
            stats = self.statistics_tracker.get_current_map_stats()
            self.label_current_earn.config(text=f"🔥 {round(stats['income'], 2)} total")

        total_stats = self.statistics_tracker.get_total_stats()
        self.label_map_count.config(text=f"🎫 {total_stats['map_count']} maps")

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
            self.label_current_time.config(text=f"⏱ {m}m{s:02d}s")

            income_per_min = current_stats['income_per_minute']
            self.label_current_speed.config(text=f"🔥 {round(income_per_min, 2)} /min")

        total_stats = self.statistics_tracker.get_total_stats()
        duration = total_stats['duration']
        m = int(duration // 60)
        s = int(duration % 60)
        self.label_total_time.config(text=f"⏱ {m}m{s:02d}s")

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

    # Create and run the application
    app = TrackerApp(
        config_manager,
        file_manager,
        inventory_tracker,
        statistics_tracker,
        log_file_path
    )

    # Show game not found warning after app is created (deferred)
    if not game_found:
        logger.warning("Game not found - tracker will run without log monitoring")
        app.after(100, lambda: messagebox.showwarning(
            "Game Not Found",
            "Could not find Torchlight: Infinite game process or log file.\n\n"
            "The tool will continue running but won't be able to track drops "
            "until the game is started.\n\n"
            "Please make sure the game is running with logging enabled, "
            "then restart this tool."
        ))

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
