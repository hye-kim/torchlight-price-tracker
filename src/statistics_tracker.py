"""
Statistics tracking for the Torchlight Infinite Price Tracker.
Manages drop statistics, income calculations, and map tracking.
"""

import logging
import time
from typing import Dict, List, Tuple, Optional, Set
from threading import Lock
from datetime import datetime

from .file_manager import FileManager
from .config_manager import ConfigManager
from .constants import TAX_RATE, EXCLUDED_ITEM_ID

logger = logging.getLogger(__name__)


class StatisticsTracker:
    """Tracks statistics for drops, income, and map runs."""

    def __init__(self, file_manager: FileManager, config_manager: ConfigManager):
        """
        Initialize the statistics tracker.

        Args:
            file_manager: FileManager instance for file operations.
            config_manager: ConfigManager instance for configuration.
        """
        self.file_manager = file_manager
        self.config_manager = config_manager

        self.is_in_map = False
        self.map_start_time = time.time()
        self.total_time = 0.0
        self.map_count = 0

        self.drop_list: Dict[str, int] = {}
        self.drop_list_all: Dict[str, int] = {}
        self.income = 0.0
        self.income_all = 0.0

        self.exclude_list: Set[str] = set()
        self.pending_items: Dict[str, int] = {}

        self._lock = Lock()

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.drop_list.clear()
            self.drop_list_all.clear()
            self.income = 0.0
            self.income_all = 0.0
            self.total_time = 0.0
            self.map_count = 0
            self.is_in_map = False
            self.map_start_time = time.time()
            self.pending_items.clear()
            logger.info("Statistics reset")

    def enter_map(self) -> None:
        """Mark entering a map."""
        with self._lock:
            self.is_in_map = True
            self.map_start_time = time.time()
            self.drop_list.clear()
            self.income = 0.0
            self.map_count += 1
            logger.info(f"Entered map #{self.map_count}")

    def exit_map(self) -> None:
        """Mark exiting a map."""
        with self._lock:
            if self.is_in_map:
                self.total_time += time.time() - self.map_start_time
                self.is_in_map = False
                logger.info(f"Exited map (duration: {time.time() - self.map_start_time:.1f}s)")

    def process_item_changes(self, changes: List[Tuple[str, int]]) -> List[Tuple[str, str, int, float]]:
        """
        Process item changes and update statistics.

        Args:
            changes: List of (item_id, amount) tuples.

        Returns:
            List of (item_id, item_name, amount, price) tuples for processed items.
        """
        with self._lock:
            full_table = self.file_manager.load_full_table()
            processed = []

            # Consolidate changes for the same item
            consolidated: Dict[str, int] = {}
            for item_id, amount in changes:
                item_id = str(item_id)
                if item_id not in consolidated:
                    consolidated[item_id] = 0
                consolidated[item_id] += amount

            # Process each consolidated change
            for item_id, amount in consolidated.items():
                result = self._process_single_item_change(item_id, amount, full_table)
                if result:
                    processed.append(result)

            return processed

    def _process_single_item_change(
        self,
        item_id: str,
        amount: int,
        full_table: Dict[str, any]
    ) -> Optional[Tuple[str, str, int, float]]:
        """
        Process a single item change.

        Args:
            item_id: Item ID.
            amount: Amount changed.
            full_table: Full item table.

        Returns:
            Tuple of (item_id, item_name, amount, price) or None if excluded/unknown.
        """
        # Get item name
        if item_id in full_table:
            item_name = full_table[item_id].get("name", f"Unknown item (ID: {item_id})")
        else:
            item_name = f"Unknown item (ID: {item_id})"
            if item_id not in self.pending_items:
                logger.warning(f"Unknown item ID: {item_id}")
                self.pending_items[item_id] = amount
            else:
                self.pending_items[item_id] += amount
            return None

        # Check if excluded
        if self.exclude_list and item_name in self.exclude_list:
            logger.debug(f"Excluded: {item_name} x{amount}")
            return None

        # Update drop lists
        if item_id not in self.drop_list:
            self.drop_list[item_id] = 0
        self.drop_list[item_id] += amount

        if item_id not in self.drop_list_all:
            self.drop_list_all[item_id] = 0
        self.drop_list_all[item_id] += amount

        # Calculate price
        price = 0.0
        if item_id in full_table:
            price = full_table[item_id].get("price", 0.0)

            # Apply tax if enabled
            if self.config_manager.is_tax_enabled() and item_id != EXCLUDED_ITEM_ID:
                price = price * TAX_RATE

            # Update income
            self.income += price * amount
            self.income_all += price * amount

        # Log to file
        self._log_item_change(item_name, amount, price)

        # Log to console
        if amount > 0:
            logger.info(f"Drop: {item_name} x{amount} ({round(price, 3)}/each)")
        else:
            logger.info(f"Consumed: {item_name} x{abs(amount)} ({round(price, 3)}/each)")

        return (item_id, item_name, amount, price)

    def _log_item_change(self, item_name: str, amount: int, price: float) -> None:
        """
        Log item change to drop log file.

        Args:
            item_name: Name of the item.
            amount: Amount changed.
            price: Price per item.
        """
        if amount > 0:
            message = f"Drop: {item_name} x{amount} ({round(price, 3)}/each)"
        else:
            message = f"Consumed: {item_name} x{abs(amount)} ({round(price, 3)}/each)"

        self.file_manager.append_to_drop_log(message)

    def get_current_map_stats(self) -> Dict[str, any]:
        """
        Get statistics for the current map.

        Returns:
            Dictionary containing current map statistics.
        """
        with self._lock:
            if self.is_in_map:
                duration = time.time() - self.map_start_time
            else:
                duration = 0

            return {
                "drops": self.drop_list.copy(),
                "income": self.income,
                "duration": duration,
                "income_per_minute": (self.income / (duration / 60)) if duration > 0 else 0
            }

    def get_total_stats(self) -> Dict[str, any]:
        """
        Get total statistics across all maps.

        Returns:
            Dictionary containing total statistics.
        """
        with self._lock:
            total_time = self.total_time
            if self.is_in_map:
                total_time += time.time() - self.map_start_time

            return {
                "drops": self.drop_list_all.copy(),
                "income": self.income_all,
                "duration": total_time,
                "map_count": self.map_count,
                "income_per_minute": (self.income_all / (total_time / 60)) if total_time > 0 else 0
            }

    def get_formatted_time(self, seconds: float) -> str:
        """
        Format seconds as "Xm Ys" string.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted time string.
        """
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m{s}s"
