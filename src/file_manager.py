"""
File management utilities for the Torchlight Infinite Price Tracker.
Handles reading and writing JSON files with proper error handling.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .api_client import APIClient
from .constants import (
    API_UPDATE_THROTTLE,
    CONFIG_FILE,
    DROP_LOG_FILE,
    EN_ID_TABLE_FILE,
    FULL_TABLE_FILE,
    get_resource_path,
    get_writable_path,
)

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
        First checks for user config next to executable, then falls back to bundled version.

        Returns:
            Configuration dictionary.
        """
        try:
            config_path = get_resource_path(CONFIG_FILE)
            logger.info(f"Loading config from: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            return {}

    def ensure_file_exists(self, filepath: str, default_content: Any) -> None:
        """
        Ensure a file exists, creating it with default content if it doesn't.
        Uses writable path to ensure file can be created next to executable.

        Args:
            filepath: Path to the file.
            default_content: Default content to write if file doesn't exist.
        """
        # Check both user location and bundled location
        writable_path = get_writable_path(filepath)
        resource_path = get_resource_path(filepath)

        # If file doesn't exist in either location, create it in writable location
        if not Path(writable_path).exists() and not Path(resource_path).exists():
            logger.info(f"Creating file: {writable_path}")
            try:
                with open(writable_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=4)
            except IOError as e:
                logger.error(f"Failed to create file {writable_path}: {e}")
                raise

    def load_json(self, filepath: str, default: Any = None) -> Any:
        """
        Load JSON data from a file.
        First checks user location, then falls back to bundled resource.

        Args:
            filepath: Path to the JSON file.
            default: Default value to return if file doesn't exist or is invalid.

        Returns:
            Loaded JSON data or default value.
        """
        resolved_path = get_resource_path(filepath)
        default_value = default if default is not None else {}

        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            return default_value
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}", exc_info=True)
            return default_value
        except (IOError, OSError) as e:
            logger.error(f"Error reading {filepath}: {e}", exc_info=True)
            return default_value
        except Exception as e:
            logger.error(f"Unexpected error loading {filepath}: {e}", exc_info=True)
            return default_value

    def save_json(self, filepath: str, data: Any) -> bool:
        """
        Save JSON data to a file.
        Always writes to writable location (next to executable).

        Args:
            filepath: Path to the JSON file.
            data: Data to save.

        Returns:
            True if successful, False otherwise.
        """
        writable_path = get_writable_path(filepath)
        try:
            with open(writable_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            logger.error(f"Error writing to {writable_path}: {e}", exc_info=True)
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing data for {writable_path}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving {writable_path}: {e}", exc_info=True)
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
        Save the full item table to local file and update cache.
        Does NOT sync to API - use update_item() for API updates.

        Args:
            data: Full item table to save.

        Returns:
            True if successful, False otherwise.
        """
        # Save to local file
        success = self.save_json(FULL_TABLE_FILE, data)

        # Update cache if successful
        if success:
            self._full_table_cache = data

        return success

    def invalidate_cache(self) -> None:
        """Invalidate the cached full table data."""
        self._full_table_cache = None
        if self.api_client:
            self.api_client.invalidate_cache()
        logger.debug("Cache invalidated")

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a single item in the table.
        Only updates if local data is stale (>1 hour old).

        Logic:
        - Check last_update timestamp in local full_table.json
        - If > 1 hour old: Send PUT to API and update local file
        - If < 1 hour old: Skip update entirely (data is fresh enough)

        Args:
            item_id: The item ID to update.
            updates: Dictionary of fields to update.

        Returns:
            True if successful, False otherwise.
        """
        # Load current local data
        full_table = self.load_full_table(use_cache=True)

        if item_id not in full_table:
            logger.warning(f"Item {item_id} not found in table")
            return False

        # Check if local data is stale (>1 hour old)
        current_item = full_table[item_id]
        local_last_update = current_item.get('last_update', 0)
        current_time = time.time()
        time_since_update = current_time - local_last_update

        # If data is fresh (< 1 hour old), skip update entirely
        if time_since_update < API_UPDATE_THROTTLE:
            logger.debug(f"Skipping update for item {item_id}: local data is fresh ({time_since_update:.0f}s old)")
            return True  # Not an error, just skipping

        # Data is stale (> 1 hour old), proceed with update
        logger.info(f"Updating item {item_id}: local data is stale ({time_since_update:.0f}s old)")

        # If API is enabled, send PUT request
        if self.api_client:
            try:
                updated = self.api_client.update_item(item_id, updates)
                if updated:
                    logger.info(f"Updated item {item_id} via API")
                else:
                    logger.warning(f"Failed to update item {item_id} via API, updating locally only")
            except Exception as e:
                logger.error(f"Error updating item via API: {e}, updating locally only")

        # Update local file and cache
        full_table[item_id].update(updates)

        # Update cache
        if self._full_table_cache and item_id in self._full_table_cache:
            self._full_table_cache[item_id].update(updates)

        # Save to file
        return self.save_json(FULL_TABLE_FILE, full_table)


    def initialize_full_table_from_en_table(self) -> bool:
        """
        Initialize full_table.json from en_id_table.json if it doesn't exist.
        Only used as fallback when API is not available.

        Returns:
            True if initialization was performed, False otherwise.
        """
        full_table_path = Path(get_writable_path(FULL_TABLE_FILE))

        if full_table_path.exists():
            logger.debug("full_table.json already exists")
            return False

        # If API is enabled, load from API instead
        if self.api_client:
            try:
                logger.info("Loading initial data from API...")
                api_data = self.api_client.get_all_items(use_cache=False)
                if api_data:
                    self.save_full_table(api_data)
                    logger.info(f"Created {FULL_TABLE_FILE} from API ({len(api_data)} items)")
                    return True
            except Exception as e:
                logger.warning(f"Could not load from API: {e}, falling back to en_id_table.json")

        # Fallback: create from en_id_table.json
        en_table_path = Path(get_resource_path(EN_ID_TABLE_FILE))
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
                    "price": 0,
                    "last_update": 0
                }

            if self.save_full_table(full_table):
                logger.info(f"Created {FULL_TABLE_FILE} from {EN_ID_TABLE_FILE} ({len(full_table)} items)")
                return True
            return False

        except Exception as e:
            logger.error(f"Error initializing full table: {e}")
            return False

    def append_to_drop_log(self, message: str) -> None:
        """
        Append a message to the drop log file with timestamp.
        Writes to writable location.

        Args:
            message: Message to append.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            drop_log_path = get_writable_path(DROP_LOG_FILE)
            with open(drop_log_path, 'a', encoding='utf-8') as f:
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
