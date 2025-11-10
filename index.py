"""
Torchlight Infinite Profit Tracker - PyQt5 Version

This is a refactored version using PyQt5 with better code organization, error handling,
type hints, logging, and thread safety.
"""

import logging
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from src.config_manager import ConfigManager
from src.file_manager import FileManager
from src.log_parser import LogParser
from src.inventory_tracker import InventoryTracker
from src.statistics_tracker import StatisticsTracker
from src.game_detector import GameDetector
from src.ui.main_window import TrackerMainWindow
from src.monitoring.log_monitor import LogMonitorThread, WorkerSignals

# Setup logging with UTF-8 encoding to handle Unicode characters
# Note: When running as a GUI application (console=False), sys.stdout may be None
handlers: list[logging.Handler] = [logging.FileHandler('tracker.log', encoding='utf-8')]

# Only add console handler if stdout exists (i.e., when running with console)
if sys.stdout is not None:
    stream_handler = logging.StreamHandler(sys.stdout)
    handlers.append(stream_handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

# Set the StreamHandler to use UTF-8 encoding (only if stream exists and supports reconfigure)
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream is not None:
        try:
            if hasattr(handler.stream, 'reconfigure'):
                handler.stream.reconfigure(encoding='utf-8')
        except (AttributeError, OSError):
            # Ignore if reconfigure fails or isn't supported
            pass

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    logger.info("=== Torchlight Infinite Price Tracker Starting (PyQt5) ===")

    # Create QApplication
    app = QApplication(sys.argv)

    # Initialize managers
    config_manager = ConfigManager()
    file_manager = FileManager()

    # Initialize data files
    file_manager.ensure_file_exists("config.json", {"opacity": 1.0, "tax": 0, "user": ""})
    file_manager.initialize_full_table_from_en_table()

    # Initialize core components
    log_parser = LogParser(file_manager)
    inventory_tracker = InventoryTracker(log_parser)
    statistics_tracker = StatisticsTracker(file_manager, config_manager)

    # Detect game and log file
    game_detector = GameDetector()
    game_found, log_file_path = game_detector.detect_game()

    # Create and run the application
    tracker_app = TrackerMainWindow(
        config_manager,
        file_manager,
        inventory_tracker,
        statistics_tracker,
        log_file_path
    )

    # Show game not found warning after app is created
    if not game_found:
        logger.warning("Game not found - tracker will run without log monitoring")
        QTimer.singleShot(100, lambda: QMessageBox.warning(
            tracker_app,
            "Game Not Found",
            "Could not find Torchlight: Infinite game process or log file.\n\n"
            "The tool will continue running but won't be able to track drops "
            "until the game is started.\n\n"
            "Please make sure the game is running with logging enabled, "
            "then restart this tool."
        ))

    # Create WorkerSignals for thread communication
    signals = WorkerSignals()
    signals.initialization_complete.connect(tracker_app.on_initialization_complete)
    signals.update_display.connect(tracker_app.update_display)
    signals.reshow_drops.connect(tracker_app.reshow)

    # Start log monitoring thread
    monitor = LogMonitorThread(
        log_file_path,
        log_parser,
        inventory_tracker,
        statistics_tracker,
        signals,
        lambda: tracker_app.app_running
    )
    monitor.start()

    # Show the window
    tracker_app.show()

    # Run the application
    logger.info("Application started")
    exit_code = app.exec_()
    logger.info("Application shut down")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
