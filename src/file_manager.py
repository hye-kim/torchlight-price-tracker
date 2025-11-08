"""
File management utilities for the Torchlight Infinite Price Tracker.
Handles reading and writing JSON files with proper error handling.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .constants import (
    FULL_TABLE_FILE,
    TRANSLATION_MAPPING_FILE,
    EN_ID_TABLE_FILE,
    DROP_LOG_FILE
)

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file I/O operations with proper error handling and caching."""

    def __init__(self):
        """Initialize the file manager."""
        self._full_table_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0

    def ensure_file_exists(self, filepath: str, default_content: Any) -> None:
        """
        Ensure a file exists, creating it with default content if it doesn't.

        Args:
            filepath: Path to the file.
            default_content: Default content to write if file doesn't exist.
        """
        path = Path(filepath)
        if not path.exists():
            logger.info(f"Creating file: {filepath}")
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=4)
            except IOError as e:
                logger.error(f"Failed to create file {filepath}: {e}")
                raise

    def load_json(self, filepath: str, default: Any = None) -> Any:
        """
        Load JSON data from a file.

        Args:
            filepath: Path to the JSON file.
            default: Default value to return if file doesn't exist or is invalid.

        Returns:
            Loaded JSON data or default value.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            return default if default is not None else {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            return default if default is not None else {}
        except IOError as e:
            logger.error(f"Error reading {filepath}: {e}")
            return default if default is not None else {}

    def save_json(self, filepath: str, data: Any) -> bool:
        """
        Save JSON data to a file.

        Args:
            filepath: Path to the JSON file.
            data: Data to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Error writing to {filepath}: {e}")
            return False

    def load_full_table(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load the full item table with optional caching.

        Args:
            use_cache: Whether to use cached data if available.

        Returns:
            Full item table dictionary.
        """
        if use_cache and self._full_table_cache is not None:
            return self._full_table_cache

        data = self.load_json(FULL_TABLE_FILE, {})
        if use_cache:
            self._full_table_cache = data
        return data

    def save_full_table(self, data: Dict[str, Any]) -> bool:
        """
        Save the full item table and update cache.

        Args:
            data: Full item table to save.

        Returns:
            True if successful, False otherwise.
        """
        success = self.save_json(FULL_TABLE_FILE, data)
        if success:
            self._full_table_cache = data
        return success

    def invalidate_cache(self) -> None:
        """Invalidate the cached full table data."""
        self._full_table_cache = None
        logger.debug("Cache invalidated")

    def load_translation_mapping(self) -> Dict[str, str]:
        """
        Load translation mapping between Chinese and English item names.

        Returns:
            Translation mapping dictionary.
        """
        return self.load_json(TRANSLATION_MAPPING_FILE, {})

    def save_translation_mapping(self, mapping: Dict[str, str]) -> bool:
        """
        Save translation mapping to file.

        Args:
            mapping: Translation mapping dictionary.

        Returns:
            True if successful, False otherwise.
        """
        return self.save_json(TRANSLATION_MAPPING_FILE, mapping)

    def initialize_full_table_from_en_table(self) -> bool:
        """
        Initialize full_table.json from en_id_table.json if it doesn't exist.

        Returns:
            True if initialization was performed, False otherwise.
        """
        full_table_path = Path(FULL_TABLE_FILE)
        en_table_path = Path(EN_ID_TABLE_FILE)

        if full_table_path.exists():
            logger.debug("full_table.json already exists")
            return False

        if not en_table_path.exists():
            logger.warning(f"{EN_ID_TABLE_FILE} not found, cannot initialize full_table")
            return False

        try:
            english_items = self.load_json(EN_ID_TABLE_FILE)
            if not english_items:
                logger.error("en_id_table.json is empty or invalid")
                return False

            full_table = {}
            for item_id, item_data in english_items.items():
                full_table[item_id] = {
                    "name": item_data.get("name", f"Unknown_{item_id}"),
                    "type": item_data.get("type", "Unknown"),
                    "price": 0
                }

            if self.save_full_table(full_table):
                logger.info(f"Created {FULL_TABLE_FILE} from {EN_ID_TABLE_FILE}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error initializing full table: {e}")
            return False

    def append_to_drop_log(self, message: str) -> None:
        """
        Append a message to the drop log file with timestamp.

        Args:
            message: Message to append.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            with open(DROP_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except IOError as e:
            logger.error(f"Error writing to drop log: {e}")

    def get_item_name(self, item_id: str, full_table: Optional[Dict[str, Any]] = None) -> str:
        """
        Get item name from item ID.

        Args:
            item_id: Item ID to look up.
            full_table: Optional full table dict. If None, loads from file.

        Returns:
            Item name or "Unknown item (ID: xxx)" if not found.
        """
        if full_table is None:
            full_table = self.load_full_table()

        if item_id in full_table:
            return full_table[item_id].get("name", f"Unknown item (ID: {item_id})")
        return f"Unknown item (ID: {item_id})"

    def get_item_price(self, item_id: str, full_table: Optional[Dict[str, Any]] = None) -> float:
        """
        Get item price from item ID.

        Args:
            item_id: Item ID to look up.
            full_table: Optional full table dict. If None, loads from file.

        Returns:
            Item price or 0.0 if not found.
        """
        if full_table is None:
            full_table = self.load_full_table()

        if item_id in full_table:
            return full_table[item_id].get("price", 0.0)
        return 0.0
