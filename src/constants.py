"""
Constants used throughout the Torchlight Infinite Price Tracker application.
"""

import os
import sys
from typing import List


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    For user-modifiable files (like config.json), this function will:
    1. First check in the directory where the executable/script is located
    2. Fall back to the bundled resource if not found

    Args:
        relative_path: Relative path to the resource file

    Returns:
        Absolute path to the resource
    """
    # Get the directory where the executable or script is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Check if file exists in application directory (user's config)
    user_file_path = os.path.join(application_path, relative_path)
    if os.path.exists(user_file_path):
        return user_file_path

    # Fall back to bundled resource for frozen apps
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', application_path)
        return os.path.join(base_path, relative_path)

    # For development, return the normal path
    return user_file_path


def get_writable_path(relative_path: str) -> str:
    """
    Get writable path for user data files.
    Always returns path in the directory where the executable/script is located.

    Args:
        relative_path: Relative path to the file

    Returns:
        Absolute writable path
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(application_path, relative_path)

# Application Information
APP_NAME = "Torchlight Price Checker"
APP_VERSION = "0.0.3"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# File Paths
CONFIG_FILE = "config.json"
FULL_TABLE_FILE = "full_table.json"
EN_ID_TABLE_FILE = "en_id_table.json"
DROP_LOG_FILE = "drop.txt"

# Game Detection
GAME_WINDOW_TITLE = "Torchlight: Infinite  "
LOG_FILE_RELATIVE_PATH = "../../../TorchLight/Saved/Logs/UE_game.log"

# Regular Expression Patterns
PATTERN_PRICE_ID = r'XchgSearchPrice----SynId = (\d+).*?\+refer \[(\d+)\]'
PATTERN_BAG_MODIFY = r'\[.*?\]GameLog: Display: \[Game\] BagMgr@:Modfy BagItem PageId = (\d+) SlotId = (\d+) ConfigBaseId = (\d+) Num = (\d+)'
PATTERN_BAG_INIT = r'\[.*?\]GameLog: Display: \[Game\] BagMgr@:InitBagData PageId = (\d+) SlotId = (\d+) ConfigBaseId = (\d+) Num = (\d+)'
PATTERN_MAP_ENTER = r"PageApplyBase@ _UpdateGameEnd: LastSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200' NextSceneName = World'/Game/Art/Maps"
PATTERN_MAP_EXIT = r"NextSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200'"

# Item Types
ITEM_TYPES: List[str] = [
    "Compass",
    "Currency",
    "Special Item",
    "Memory Material",
    "Equipment Material",
    "Gameplay Ticket",
    "Game Ticket",
    "Map Ticket",
    "Cube Material",
    "Magic Cube Material",
    "Magic Cube Materials",
    "Corruption Material",
    "Corrosion Material",
    "Erosion Material",
    "Dream Material",
    "Tower Material",
    "Tower Materials",
    "BOSS Ticket",
    "Boss Ticket",
    "Memory Glow",
    "Memory Fluorescence",
    "Divine Emblem",
    "God's Emblem",
    "Overlap Material",
    "Overlay Material",
    "Remembrance Material",
    "Hard Currency"
]

# Item Type Filters
FILTER_CURRENCY = ["Currency", "Hard Currency"]
FILTER_ASHES = ["Equipment Material", "Ashes"]
FILTER_COMPASS = ["Compass"]
FILTER_GLOW = ["Memory Glow", "Memory Fluorescence"]
FILTER_OTHERS = [
    "Special Item",
    "Memory Material",
    "Gameplay Ticket",
    "Game Ticket",
    "Map Ticket",
    "Cube Material",
    "Magic Cube Material",
    "Magic Cube Materials",
    "Corruption Material",
    "Corrosion Material",
    "Erosion Material",
    "Dream Material",
    "Tower Material",
    "Tower Materials",
    "BOSS Ticket",
    "Boss Ticket",
    "Divine Emblem",
    "God's Emblem",
    "Overlap Material",
    "Overlay Material",
    "Remembrance Material"
]

# UI Configuration
UI_FONT_FAMILY = "Arial"
UI_FONT_SIZE_LARGE = 14
UI_FONT_SIZE_MEDIUM = 10
UI_LISTBOX_HEIGHT = 15
UI_LISTBOX_WIDTH = 45

# Price Configuration
TAX_RATE = 0.875  # 12.5% tax
PRICE_SAMPLE_SIZE = 30
EXCLUDED_ITEM_ID = "100300"

# Status Indicators
STATUS_FRESH = "✔"  # < 2 hours
STATUS_STALE = "◯"  # 2-24 hours
STATUS_OLD = "✘"    # > 24 hours

TIME_FRESH_THRESHOLD = 7200    # 2 hours in seconds
TIME_STALE_THRESHOLD = 86400    # 24 hours in seconds

# Initialization Configuration
MIN_BAG_ITEMS_FOR_INIT = 20
MIN_BAG_ITEMS_LEGACY = 10

# Threading Configuration
LOG_POLL_INTERVAL = 1.0  # seconds

# API Configuration
API_CACHE_TTL = 3600  # seconds - How long to cache API responses (matches API_UPDATE_THROTTLE)
API_RETRY_BASE_DELAY = 2  # seconds - Base delay for exponential backoff
API_UPDATE_THROTTLE = 3600  # seconds - Minimum time between API updates for same item (1 hour)
API_RATE_LIMIT_CALLS = 100  # Maximum API calls per window
API_RATE_LIMIT_WINDOW = 60  # seconds - Rate limit window duration

# File Handle Configuration
LOG_FILE_REOPEN_INTERVAL = 30.0  # seconds - How often to check if log file needs reopening

# UI Configuration - Additional
UI_LISTBOX_ITEM_HEIGHT = 20  # pixels - Approximate height per list item
UI_MIN_WINDOW_WIDTH = 400
UI_MIN_WINDOW_HEIGHT = 600
UI_DEFAULT_WINDOW_WIDTH = 500
UI_DEFAULT_WINDOW_HEIGHT = 800

# UI Color Palette
UI_COLORS = {
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

# Excel Export Configuration
EXCEL_HEADER_COLOR = "8b5cf6"
EXCEL_CATEGORY_COLOR = "2a2a3e"
EXCEL_MAX_COLUMN_WIDTH = 50
EXCEL_COLUMN_PADDING = 2

# Default Configuration
DEFAULT_CONFIG = {
    "opacity": 1.0,
    "tax": 0,
    "user": "",
    "api_enabled": True,
    "api_url": "https://torchlight-price-tracker.onrender.com",
    "api_timeout": 60,
    "use_local_fallback": True
}


def calculate_price_with_tax(price: float, item_id: str, tax_enabled: bool) -> float:
    """
    Calculate item price with tax applied if enabled.

    Args:
        price: Base item price
        item_id: Item ID (some items are excluded from tax)
        tax_enabled: Whether tax calculation is enabled

    Returns:
        Price with tax applied if applicable
    """
    if tax_enabled and item_id != EXCLUDED_ITEM_ID:
        return price * TAX_RATE
    return price


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "2h 30m 45s" or "5m 12s"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def get_price_freshness_status(last_update: float, current_time: float) -> str:
    """
    Determine the freshness status of a price based on last update time.

    Args:
        last_update: Timestamp of last price update
        current_time: Current timestamp

    Returns:
        Status string: "Fresh", "Stale", or "Old"
    """
    time_passed = current_time - last_update

    if time_passed < TIME_FRESH_THRESHOLD:
        return "Fresh"
    elif time_passed < TIME_STALE_THRESHOLD:
        return "Stale"
    else:
        return "Old"


def get_price_freshness_indicator(last_update: float, current_time: float) -> str:
    """
    Get the visual indicator for price freshness.

    Args:
        last_update: Timestamp of last price update
        current_time: Current timestamp

    Returns:
        Status indicator: STATUS_FRESH, STATUS_STALE, or STATUS_OLD
    """
    time_passed = current_time - last_update

    if time_passed < TIME_FRESH_THRESHOLD:
        return STATUS_FRESH
    elif time_passed < TIME_STALE_THRESHOLD:
        return STATUS_STALE
    else:
        return STATUS_OLD


def calculate_fe_per_hour(income: float, duration: float) -> float:
    """
    Calculate Flame Elementium per hour rate.

    Args:
        income: Total FE earned
        duration: Duration in seconds

    Returns:
        FE per hour rate (0 if duration is 0)
    """
    if duration <= 0:
        return 0.0
    return income / (duration / 3600)
