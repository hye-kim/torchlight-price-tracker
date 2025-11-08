"""
Inventory tracking for the Torchlight Infinite Price Tracker.
Manages bag state and detects item changes.
"""

import logging
from typing import Dict, List, Tuple, Optional
from threading import Lock

from .log_parser import LogParser
from .constants import MIN_BAG_ITEMS_FOR_INIT, MIN_BAG_ITEMS_LEGACY

logger = logging.getLogger(__name__)


class InventoryTracker:
    """Tracks inventory state and detects item changes."""

    def __init__(self, log_parser: LogParser):
        """
        Initialize the inventory tracker.

        Args:
            log_parser: LogParser instance for parsing log data.
        """
        self.log_parser = log_parser
        self.bag_state: Dict[str, int] = {}
        self.bag_initialized = False
        self.initialization_complete = False
        self.awaiting_initialization = False
        self.initialization_in_progress = False
        self.first_scan = True
        self._lock = Lock()

    def reset(self) -> None:
        """Reset all tracking state."""
        with self._lock:
            self.bag_state.clear()
            self.bag_initialized = False
            self.initialization_complete = False
            self.awaiting_initialization = False
            self.initialization_in_progress = False
            self.first_scan = True
            logger.info("Inventory tracker reset")

    def start_initialization(self) -> bool:
        """
        Start the initialization process.

        Returns:
            True if initialization started, False if already in progress.
        """
        with self._lock:
            if self.initialization_in_progress:
                logger.warning("Initialization already in progress")
                return False

            self.awaiting_initialization = True
            self.initialization_in_progress = True
            logger.info("Initialization started - waiting for bag update")
            return True

    def process_initialization(self, text: str) -> Tuple[bool, Optional[int]]:
        """
        Process log text for initialization by scanning for InitBagData entries.

        Args:
            text: Log text to process.

        Returns:
            Tuple of (success, item_count). success is True if initialization completed.
        """
        with self._lock:
            if not self.awaiting_initialization:
                return False, None

            bag_init_entries = self.log_parser.extract_bag_init_data(text)

            if len(bag_init_entries) < MIN_BAG_ITEMS_FOR_INIT:
                return False, None

            logger.info(f"Found {len(bag_init_entries)} InitBagData entries - initializing")

            self.bag_state.clear()
            item_totals: Dict[str, int] = {}

            for page_id, slot_id, config_base_id, count in bag_init_entries:
                slot_key = f"{page_id}:{slot_id}:{config_base_id}"
                self.bag_state[slot_key] = count

                if config_base_id not in item_totals:
                    item_totals[config_base_id] = 0
                item_totals[config_base_id] += count

            # Store initial totals
            for item_id, total in item_totals.items():
                init_key = f"init:{item_id}"
                self.bag_state[init_key] = total

            self.bag_initialized = True
            self.initialization_complete = True
            self.awaiting_initialization = False
            self.initialization_in_progress = False

            logger.info(f"Initialization complete: {len(item_totals)} unique items, "
                       f"{len(bag_init_entries)} inventory slots")

            return True, len(item_totals)

    def initialize_bag_state_legacy(self, text: str) -> bool:
        """
        Legacy method to initialize bag state by scanning for bag modifications.

        Args:
            text: Log text to process.

        Returns:
            True if initialization completed, False otherwise.
        """
        with self._lock:
            if not self.first_scan:
                return False

            self.first_scan = False

            if self.log_parser.detect_player_login(text):
                logger.info("Detected player login - resetting bag state")
                self.bag_state.clear()
                return True

            bag_modifications = self.log_parser.extract_bag_modifications(text)

            if len(bag_modifications) > MIN_BAG_ITEMS_LEGACY:
                logger.info(f"Found {len(bag_modifications)} bag items - initializing (legacy)")

                for page_id, slot_id, config_base_id, count in bag_modifications:
                    item_key = f"{page_id}:{slot_id}:{config_base_id}"
                    self.bag_state[item_key] = count

                self.bag_initialized = True
                return True

            return False

    def detect_bag_changes(self, text: str) -> List[Tuple[str, int]]:
        """
        Detect changes to the bag and calculate gains and losses.

        Args:
            text: Log text to process.

        Returns:
            List of (item_id, net_change) tuples.
        """
        with self._lock:
            if not self.bag_initialized:
                return []

            bag_modifications = self.log_parser.extract_bag_modifications(text)

            if not bag_modifications:
                return []

            changes: List[Tuple[str, int]] = []
            slot_changes: Dict[str, int] = {}

            # Track changes per slot
            for page_id, slot_id, config_base_id, count in bag_modifications:
                slot_key = f"{page_id}:{slot_id}:{config_base_id}"
                prev_count = self.bag_state.get(slot_key, 0)
                self.bag_state[slot_key] = count

                if config_base_id not in slot_changes:
                    slot_changes[config_base_id] = 0
                slot_changes[config_base_id] += (count - prev_count)

            # Calculate net changes
            for item_id, slot_change in slot_changes.items():
                if slot_change == 0:
                    continue

                init_key = f"init:{item_id}"
                initial_total = self.bag_state.get(init_key, 0)

                # Calculate current total for this item
                current_total = sum(
                    value for key, value in self.bag_state.items()
                    if not key.startswith("init:") and key.endswith(f":{item_id}")
                )

                net_change = current_total - initial_total

                if net_change != 0:
                    changes.append((item_id, net_change))
                    self.bag_state[init_key] = current_total

            return changes

    def scan_for_changes(self, text: str) -> List[Tuple[str, int]]:
        """
        Enhanced bag change scanner that handles initialization.

        Args:
            text: Log text to process.

        Returns:
            List of (item_id, change_amount) tuples.
        """
        # Handle initialization if awaiting
        if self.awaiting_initialization:
            success, _ = self.process_initialization(text)
            if success:
                return []

        # If initialized and complete, detect changes
        if self.bag_initialized and self.initialization_complete:
            return self.detect_bag_changes(text)

        # Try legacy initialization if not initialized
        if not self.bag_initialized:
            if self.initialize_bag_state_legacy(text):
                return []

        # Fallback: simple detection without initialization
        return self._detect_changes_without_init(text)

    def _detect_changes_without_init(self, text: str) -> List[Tuple[str, int]]:
        """
        Detect item drops without proper initialization (fallback method).

        Args:
            text: Log text to process.

        Returns:
            List of (item_id, change_amount) tuples.
        """
        bag_modifications = self.log_parser.extract_bag_modifications(text)
        if not bag_modifications:
            return []

        drops: List[Tuple[str, int]] = []

        # Calculate previous totals
        previous_totals: Dict[str, int] = {}
        for item_key, qty in self.bag_state.items():
            if ":" not in item_key:
                continue
            parts = item_key.split(':')
            if len(parts) != 3:
                continue
            _, _, item_id = parts
            if item_id not in previous_totals:
                previous_totals[item_id] = 0
            previous_totals[item_id] += qty

        # Apply modifications
        current_state = self.bag_state.copy()
        for page_id, slot_id, config_base_id, count in bag_modifications:
            item_key = f"{page_id}:{slot_id}:{config_base_id}"
            current_state[item_key] = count

        # Calculate current totals
        current_totals: Dict[str, int] = {}
        for item_key, qty in current_state.items():
            if ":" not in item_key:
                continue
            parts = item_key.split(':')
            if len(parts) != 3:
                continue
            _, _, item_id = parts
            if item_id not in current_totals:
                current_totals[item_id] = 0
            current_totals[item_id] += qty

        # Find increases (drops)
        for item_id, current_total in current_totals.items():
            previous_total = previous_totals.get(item_id, 0)
            if current_total > previous_total:
                drops.append((item_id, current_total - previous_total))

        self.bag_state = current_state
        return drops

    def reset_map_baseline(self) -> int:
        """
        Reset the baseline for map tracking to current inventory state.

        Returns:
            Number of items in the new baseline.
        """
        with self._lock:
            item_totals: Dict[str, int] = {}

            for key, value in self.bag_state.items():
                if not key.startswith("init:") and ":" in key:
                    parts = key.split(':')
                    if len(parts) == 3:
                        item_id = parts[2]
                        if item_id not in item_totals:
                            item_totals[item_id] = 0
                        item_totals[item_id] += value

            for item_id, total in item_totals.items():
                init_key = f"init:{item_id}"
                self.bag_state[init_key] = total

            logger.info(f"Reset map baseline for {len(item_totals)} items")
            return len(item_totals)

    def get_bag_state_summary(self) -> Dict[str, int]:
        """
        Get a summary of current bag state grouped by item ID.

        Returns:
            Dictionary mapping item IDs to total quantities.
        """
        with self._lock:
            grouped: Dict[str, int] = {}

            for key, amount in self.bag_state.items():
                if key.startswith("init:"):
                    item_id = key.split(':')[1]
                elif ":" in key and len(key.split(':')) == 3:
                    _, _, item_id = key.split(':')
                else:
                    item_id = key

                if item_id not in grouped:
                    grouped[item_id] = 0
                grouped[item_id] += amount

            return grouped
