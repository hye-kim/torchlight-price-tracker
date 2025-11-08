"""
Game detection and log file location for Torchlight Infinite.
Handles finding the game process and log file.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    WINDOWS_MODULES_AVAILABLE = False

from .constants import GAME_WINDOW_TITLE, LOG_FILE_RELATIVE_PATH

logger = logging.getLogger(__name__)


class GameDetector:
    """Detects the Torchlight: Infinite game and locates its log file."""

    def __init__(self):
        """Initialize the game detector."""
        self.game_found = False
        self.log_file_path: Optional[str] = None
        self.game_exe_path: Optional[str] = None

    def detect_game(self) -> Tuple[bool, Optional[str]]:
        """
        Attempt to detect the running game and locate its log file.

        Returns:
            Tuple of (game_found, log_file_path).
        """
        if not WINDOWS_MODULES_AVAILABLE:
            logger.warning("Windows modules (win32gui, psutil) not available. "
                          "Game detection will not work.")
            return False, None

        try:
            hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
            if not hwnd:
                logger.info("Game window not found")
                return False, None

            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            self.game_exe_path = process.exe()

            # Calculate log file path relative to game executable
            log_path = os.path.join(
                os.path.dirname(self.game_exe_path),
                LOG_FILE_RELATIVE_PATH
            )
            log_path = os.path.normpath(log_path)
            log_path = log_path.replace("\\", "/")

            # Verify log file exists and is readable
            if not os.path.exists(log_path):
                logger.error(f"Log file not found at: {log_path}")
                return False, None

            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    preview = f.read(100)
                    logger.info(f"Successfully opened log file. Preview: {preview[:50]}...")
            except IOError as e:
                logger.error(f"Cannot read log file: {e}")
                return False, None

            self.game_found = True
            self.log_file_path = log_path
            logger.info(f"Game detected! Log file: {log_path}")

            return True, log_path

        except Exception as e:
            logger.error(f"Error detecting game: {e}")
            return False, None

    def get_log_file_path(self) -> Optional[str]:
        """
        Get the detected log file path.

        Returns:
            Log file path or None if not detected.
        """
        return self.log_file_path

    def is_game_running(self) -> bool:
        """
        Check if the game is currently running.

        Returns:
            True if game is running, False otherwise.
        """
        if not WINDOWS_MODULES_AVAILABLE:
            return False

        try:
            hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
            return hwnd is not None
        except Exception:
            return False
