"""
Log parsing utilities for the Torchlight Infinite Price Tracker.
Handles extraction of game events from log files.
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple

from .constants import (
    EXCLUDED_ITEM_ID,
    PATTERN_BAG_INIT,
    PATTERN_BAG_MODIFY,
    PATTERN_MAP_ENTER,
    PATTERN_MAP_EXIT,
    PATTERN_PRICE_ID,
    PRICE_SAMPLE_SIZE,
)
from .file_manager import FileManager

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for performance
_REGEX_PRICE_ID = re.compile(PATTERN_PRICE_ID, re.DOTALL)
_REGEX_BAG_MODIFY = re.compile(PATTERN_BAG_MODIFY)
_REGEX_BAG_INIT = re.compile(PATTERN_BAG_INIT)
_REGEX_MAP_ENTER = re.compile(PATTERN_MAP_ENTER)
_REGEX_MAP_EXIT = re.compile(PATTERN_MAP_EXIT)
_REGEX_VALUE_PATTERN = re.compile(r'\+\d+\s+\[([\d.]+)\]')


class LogParser:
    """Parses game log files to extract relevant information."""

    def __init__(self, file_manager: FileManager):
        """
        Initialize the log parser.

        Args:
            file_manager: FileManager instance for file operations.
        """
        self.file_manager = file_manager

    def extract_price_info(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract price information from game logs.

        Args:
            text: Log text to parse.

        Returns:
            List of (item_id, price) tuples.
        """
        price_updates = []
        try:
            matches = _REGEX_PRICE_ID.findall(text)

            for synid, item_id in matches:
                if item_id == EXCLUDED_ITEM_ID:
                    continue

                price = self._extract_price_for_item(text, synid, item_id)
                if price is not None:
                    price_updates.append((item_id, price))

        except Exception as e:
            logger.error(f"Error extracting price info: {e}", exc_info=True)

        return price_updates

    def _extract_price_for_item(self, text: str, synid: str, item_id: str) -> Optional[float]:
        """
        Extract price for a specific item from log text.

        Args:
            text: Log text to parse.
            synid: Synchronization ID.
            item_id: Item ID.

        Returns:
            Average price or None if not found.
        """
        try:
            pattern = re.compile(
                rf'----Socket RecvMessage STT----XchgSearchPrice----SynId = {synid}\s+'
                r'\[.*?\]\s*GameLog: Display: \[Game\]\s+'
                r'(.*?)(?=----Socket RecvMessage STT----|$)',
                re.DOTALL
            )

            match = pattern.search(text)
            if not match:
                logger.debug(f'No price data found for ID: {item_id}')
                return None

            data_block = match.group(1)

            # Extract all +number [value] patterns using pre-compiled regex
            values = _REGEX_VALUE_PATTERN.findall(data_block)

            if not values:
                return -1.0

            # Calculate average of first N values
            num_values = min(len(values), PRICE_SAMPLE_SIZE)
            sum_values = sum(float(values[i]) for i in range(num_values))
            average_value = sum_values / num_values

            return round(average_value, 4)

        except Exception as e:
            logger.error(f"Error extracting price for item {item_id}: {e}", exc_info=True)
            return None

    def update_prices_in_table(self, text: str) -> int:
        """
        Extract prices from log and update the full table.
        Uses efficient API updates when available.

        Args:
            text: Log text to parse.

        Returns:
            Number of prices updated.
        """
        price_updates = self.extract_price_info(text)
        if not price_updates:
            return 0

        update_count = 0
        current_time = round(time.time())

        # If API is enabled, update items individually for efficiency
        if self.file_manager.api_client:
            full_table = self.file_manager.load_full_table()

            for item_id, price in price_updates:
                if item_id in full_table:
                    updates = {
                        'last_time': current_time,
                        'from': "Local",
                        'price': price,
                        'last_update': current_time
                    }

                    if self.file_manager.update_item(item_id, updates):
                        item_name = full_table[item_id].get("name", item_id)
                        logger.info(f'Updated price: {item_name} (ID:{item_id}) = {price}')
                        update_count += 1
        else:
            # Use batch update for local file
            full_table = self.file_manager.load_full_table()

            for item_id, price in price_updates:
                if item_id in full_table:
                    full_table[item_id]['last_time'] = current_time
                    full_table[item_id]['from'] = "Local"
                    full_table[item_id]['price'] = price
                    full_table[item_id]['last_update'] = current_time

                    item_name = full_table[item_id].get("name", item_id)
                    logger.info(f'Updated price: {item_name} (ID:{item_id}) = {price}')
                    update_count += 1

            if update_count > 0:
                self.file_manager.save_full_table(full_table)

        return update_count

    def extract_bag_modifications(self, text: str) -> List[Tuple[str, str, str, int]]:
        """
        Extract bag modification events from log text.

        Args:
            text: Log text to parse.

        Returns:
            List of (page_id, slot_id, config_base_id, count) tuples.
        """
        matches = _REGEX_BAG_MODIFY.findall(text)
        return [(page_id, slot_id, config_base_id, int(count))
                for page_id, slot_id, config_base_id, count in matches]

    def extract_bag_init_data(self, text: str) -> List[Tuple[str, str, str, int]]:
        """
        Extract bag initialization data from log text.

        Args:
            text: Log text to parse.

        Returns:
            List of (page_id, slot_id, config_base_id, count) tuples.
        """
        matches = _REGEX_BAG_INIT.findall(text)
        return [(page_id, slot_id, config_base_id, int(count))
                for page_id, slot_id, config_base_id, count in matches]

    def detect_map_change(self, text: str) -> Tuple[bool, bool]:
        """
        Detect entering or leaving a map from the log text.

        Args:
            text: Log text to parse.

        Returns:
            Tuple of (entering_map, exiting_map) booleans.
        """
        entering_map = bool(_REGEX_MAP_ENTER.search(text))
        exiting_map = bool(_REGEX_MAP_EXIT.search(text))
        return entering_map, exiting_map

    def detect_player_login(self, text: str) -> bool:
        """
        Detect if player has logged in or initialized.

        Args:
            text: Log text to parse.

        Returns:
            True if login/initialization detected, False otherwise.
        """
        return "PlayerInitPkgMgr" in text or "Login2Client" in text
