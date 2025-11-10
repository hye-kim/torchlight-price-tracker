"""
Log monitoring thread for the Torchlight Infinite Price Tracker.
Monitors the game log file and processes events.
"""

import logging
import time
import threading
from typing import Optional

from PyQt5.QtCore import pyqtSignal, QObject

from ..constants import LOG_POLL_INTERVAL, LOG_FILE_REOPEN_INTERVAL
from ..log_parser import LogParser
from ..inventory_tracker import InventoryTracker
from ..statistics_tracker import StatisticsTracker

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    initialization_complete = pyqtSignal(int)
    update_display = pyqtSignal()
    reshow_drops = pyqtSignal()


class LogMonitorThread(threading.Thread):
    """Thread for monitoring the game log file."""

    def __init__(
        self,
        log_file_path: Optional[str],
        log_parser: LogParser,
        inventory_tracker: InventoryTracker,
        statistics_tracker: StatisticsTracker,
        signals: WorkerSignals,
        app_running_callback
    ):
        """
        Initialize the log monitor thread.

        Args:
            log_file_path: Path to the game log file
            log_parser: Log parser instance
            inventory_tracker: Inventory tracker instance
            statistics_tracker: Statistics tracker instance
            signals: Worker signals for thread-safe UI updates
            app_running_callback: Callable that returns True if app is running
        """
        super().__init__(daemon=True)
        self.log_file_path = log_file_path
        self.log_parser = log_parser
        self.inventory_tracker = inventory_tracker
        self.statistics_tracker = statistics_tracker
        self.signals = signals
        self.app_running_callback = app_running_callback
        self.log_file = None
        self.last_reopen_check = time.time()

    def _open_log_file(self) -> bool:
        """
        Open the log file and seek to end.

        Returns:
            True if successful, False otherwise
        """
        if not self.log_file_path:
            return False

        try:
            self.log_file = open(self.log_file_path, "r", encoding="utf-8")
            self.log_file.seek(0, 2)  # Seek to end
            logger.info("Log file opened successfully")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Could not open log file: {e}")
            self.log_file = None
            return False

    def _close_log_file(self) -> None:
        """Close the log file if open."""
        if self.log_file:
            try:
                self.log_file.close()
                logger.info("Log file closed")
            except (IOError, OSError) as e:
                logger.error(f"Error closing log file: {e}")
            finally:
                self.log_file = None

    def _check_and_reopen_log_file(self) -> None:
        """Check if log file needs reopening (e.g., was deleted or rotated)."""
        now = time.time()
        if now - self.last_reopen_check < LOG_FILE_REOPEN_INTERVAL:
            return

        self.last_reopen_check = now

        # Check if file still exists and is accessible
        if self.log_file_path:
            import os
            if not os.path.exists(self.log_file_path):
                logger.warning("Log file no longer exists, attempting to reopen")
                self._close_log_file()
                self._open_log_file()

    def run(self) -> None:
        """Run the log monitoring loop."""
        if not self.log_file_path:
            logger.warning("No log file path provided")
            return

        # Open log file initially
        self._open_log_file()

        try:
            while self.app_running_callback():
                try:
                    # Sleep in smaller chunks to be more responsive to shutdown
                    for _ in range(int(LOG_POLL_INTERVAL * 10)):
                        if not self.app_running_callback():
                            break
                        time.sleep(0.1)

                    if not self.app_running_callback():
                        break

                    # Check if log file needs reopening
                    self._check_and_reopen_log_file()

                    # Read and process log file
                    if self.log_file:
                        try:
                            text = self.log_file.read()
                            if text:
                                self._process_log_text(text)
                        except (IOError, OSError) as e:
                            logger.error(f"Error reading log file: {e}")
                            # Try to reopen the file
                            self._close_log_file()
                            self._open_log_file()

                    # Update display via signal
                    self.signals.update_display.emit()

                except Exception as e:
                    logger.error(f"Error in log monitor thread: {e}", exc_info=True)

        finally:
            # Ensure log file is closed on exit
            self._close_log_file()

    def _process_log_text(self, text: str) -> None:
        """
        Process new log text.

        Args:
            text: New log text to process
        """
        # Update prices
        self.log_parser.update_prices_in_table(text)

        # Check for initialization completion
        if self.inventory_tracker.awaiting_initialization:
            success, item_count = self.inventory_tracker.process_initialization(text)
            if success:
                self.signals.initialization_complete.emit(item_count)

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
            self.signals.reshow_drops.emit()

            # If not in map but got changes, assume we're in a map
            if not self.statistics_tracker.is_in_map:
                self.statistics_tracker.is_in_map = True
