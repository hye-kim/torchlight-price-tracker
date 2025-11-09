"""
File management utilities for the Torchlight Infinite Price Tracker.
Handles reading and writing JSON files with proper error handling.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .constants import (
    FULL_TABLE_FILE,
    TRANSLATION_MAPPING_FILE,
    EN_ID_TABLE_FILE,
    DROP_LOG_FILE,
    CONFIG_FILE
)
from .api_client import APIClient

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file I/O operations with proper error handling and caching."""

    def __init__(self):
        """Initialize the file manager."""
        self._full_table_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0

        # Load configuration
        self.config = self._load_config()

        # Initialize API client if enabled
        self.api_client: Optional[APIClient] = None
        if self.config.get('api_enabled', False):
            api_url = self.config.get('api_url', '')
            api_timeout = self.config.get('api_timeout', 10)
            if api_url:
                self.api_client = APIClient(api_url, timeout=api_timeout)
                logger.info(f"API client initialized with URL: {api_url}")
            else:
                logger.warning("API enabled but no URL configured")

        self.use_local_fallback = self.config.get('use_local_fallback', True)

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from config.json.

        Returns:
            Configuration dictionary.
        """
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            return {}

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
        Uses API if enabled, falls back to local file if API fails.

        Args:
            use_cache: Whether to use cached data if available.

        Returns:
            Full item table dictionary.
        """
        if use_cache and self._full_table_cache is not None:
            return self._full_table_cache

        data = {}

        # Try API first if enabled
        if self.api_client:
            try:
                api_data = self.api_client.get_all_items(use_cache=use_cache)
                if api_data is not None:
                    data = api_data
                    logger.debug("Loaded full table from API")
                elif self.use_local_fallback:
                    logger.warning("API failed, falling back to local file")
                    data = self.load_json(FULL_TABLE_FILE, {})
            except Exception as e:
                logger.error(f"Error loading from API: {e}")
                if self.use_local_fallback:
                    logger.warning("Falling back to local file")
                    data = self.load_json(FULL_TABLE_FILE, {})
        else:
            # Use local file if API not enabled
            data = self.load_json(FULL_TABLE_FILE, {})

        if use_cache:
            self._full_table_cache = data
        return data

    def save_full_table(self, data: Dict[str, Any]) -> bool:
        """
        Save the full item table and update cache.
        If API is enabled, syncs data to API. Always saves to local file as backup.

        Args:
            data: Full item table to save.

        Returns:
            True if successful (API or local), False otherwise.
        """
        api_success = False
        local_success = False

        # Try to sync to API if enabled
        if self.api_client:
            try:
                # Sync all items to API
                synced = self.api_client.sync_local_to_api(data)
                api_success = synced > 0
                logger.info(f"Synced {synced} items to API")
            except Exception as e:
                logger.error(f"Error syncing to API: {e}")

        # Always save to local file as backup
        local_success = self.save_json(FULL_TABLE_FILE, data)

        # Update cache if either succeeded
        if api_success or local_success:
            self._full_table_cache = data

        return api_success or local_success

    def invalidate_cache(self) -> None:
        """Invalidate the cached full table data."""
        self._full_table_cache = None
        if self.api_client:
            self.api_client.invalidate_cache()
        logger.debug("Cache invalidated")

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a single item in the table.
        Uses API if enabled for efficient updates, otherwise updates local file.
        Only makes PUT requests to the API if the last update was over 1 hour ago.

        Args:
            item_id: The item ID to update.
            updates: Dictionary of fields to update.

        Returns:
            True if successful, False otherwise.
        """
        # If API is enabled, use API for efficient update
        if self.api_client:
            try:
                # Get current item data to check timestamp
                current_item = self.api_client.get_item(item_id)

                # Check if enough time has passed since last update (1 hour = 3600 seconds)
                should_update_api = True
                if current_item:
                    last_update = current_item.get('last_update', 0)
                    current_time = time.time()
                    time_since_update = current_time - last_update

                    if time_since_update < 3600:
                        logger.info(f"Skipping API update for item {item_id}: last updated {time_since_update:.0f} seconds ago (< 1 hour)")
                        should_update_api = False

                # Only make PUT request if enough time has passed or no timestamp found
                if should_update_api:
                    updated = self.api_client.update_item(item_id, updates)
                    if updated:
                        # Also update local cache
                        if self._full_table_cache and item_id in self._full_table_cache:
                            self._full_table_cache[item_id].update(updates)
                        # Also update local file as backup
                        full_table = self.load_json(FULL_TABLE_FILE, {})
                        if item_id in full_table:
                            full_table[item_id].update(updates)
                            self.save_json(FULL_TABLE_FILE, full_table)
                        logger.debug(f"Updated item {item_id} via API")
                        return True
                    else:
                        logger.warning(f"Failed to update item {item_id} via API")
                else:
                    # Still update local cache and file even if skipping API update
                    if self._full_table_cache and item_id in self._full_table_cache:
                        self._full_table_cache[item_id].update(updates)
                    full_table = self.load_json(FULL_TABLE_FILE, {})
                    if item_id in full_table:
                        full_table[item_id].update(updates)
                        self.save_json(FULL_TABLE_FILE, full_table)
                    return True
            except Exception as e:
                logger.error(f"Error updating item via API: {e}")

        # Fall back to local file update
        full_table = self.load_full_table(use_cache=False)
        if item_id in full_table:
            full_table[item_id].update(updates)
            return self.save_full_table(full_table)
        else:
            logger.warning(f"Item {item_id} not found in table")
            return False

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
