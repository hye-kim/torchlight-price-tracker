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
TRANSLATION_MAPPING_FILE = "translation_mapping.json"
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

# Default Configuration
DEFAULT_CONFIG = {
    "opacity": 1.0,
    "tax": 0,
    "user": ""
}
