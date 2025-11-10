"""
Game detection and log file location for Torchlight Infinite.
Handles finding the game process and log file.
"""

import logging
import os
from typing import Optional, Tuple, Any

# Import Windows-specific modules with proper fallbacks
WINDOWS_MODULES_AVAILABLE = False
win32gui: Any = None
win32process: Any = None
psutil: Any = None

try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
    import psutil  # type: ignore
    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class GameDetector:
    """Detects the Torchlight: Infinite game and locates its log file."""

    def __init__(self):
        """Initialize the game detector."""
        self.game_found = False
        self.log_file_path: Optional[str] = None
        self.game_exe_path: Optional[str] = None

    def _find_game_window(self) -> Optional[int]:
        """
        Find the game window by searching for windows containing 'Torchlight: Infinite'.

        Returns:
            Window handle (hwnd) if found, None otherwise.
        """
        if not WINDOWS_MODULES_AVAILABLE:
            return None

        found_hwnd: Optional[int] = None

        def enum_windows_callback(hwnd: int, _: Any) -> bool:
            nonlocal found_hwnd
            try:
                # Extra safety check for modules
                if not WINDOWS_MODULES_AVAILABLE:
                    return True

                if not win32gui.IsWindowVisible(hwnd):
                    return True  # Continue enumeration

                window_title = win32gui.GetWindowText(hwnd)
                window_title_lower = window_title.lower()

                # Search for "Torchlight: Infinite" in window title
                if "torchlight: infinite" in window_title_lower:
                    # Exclude false positives (Discord, browsers, etc.)
                    excluded_keywords = ["discord", "chrome", "firefox", "edge", "browser", "twitch", "youtube"]
                    if any(keyword in window_title_lower for keyword in excluded_keywords):
                        logger.debug(f"Skipping excluded window: '{window_title}'")
                        return True  # Continue enumeration

                    # Verify the process executable name to ensure it's the actual game
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        exe_name = os.path.basename(process.exe()).lower()

                        # The game executable should be something like "TorchLight.exe" or similar
                        # Accept if it contains "torchlight" or "tl" in the exe name
                        if "torchlight" in exe_name or exe_name.startswith("tl"):
                            logger.info(f"Found game window with title: '{window_title}' (process: {exe_name})")
                            found_hwnd = hwnd
                            return False  # Stop enumeration
                        else:
                            logger.debug(f"Window title matches but process doesn't: '{window_title}' (process: {exe_name})")
                    except Exception as e:
                        # Process may have terminated or we don't have permission to access it
                        # Using broad Exception to catch psutil errors, OSError, and any Windows API errors
                        logger.debug(f"Cannot access process for window '{window_title}': {e}")
                        return True  # Continue enumeration

            except Exception as e:
                # Catch any other errors in the callback to prevent breaking EnumWindows
                logger.debug(f"Error in window enumeration callback for hwnd {hwnd}: {e}")

            return True  # Continue enumeration

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            logger.error(f"Error enumerating windows: {e}")

        return found_hwnd

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
            # Find window by searching for partial title match
            hwnd = self._find_game_window()
            if not hwnd:
                logger.info("Game window not found")
                return False, None

            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            exe_path = process.exe()
            self.game_exe_path = exe_path

            # Calculate log file path relative to game executable
            # Note: We concatenate directly to exe path (not dirname) to get correct relative navigation
            log_path = exe_path + "/../../../TorchLight/Saved/Logs/UE_game.log"
            log_path = log_path.replace("\\", "/")

            # Verify log file exists and is readable
            if not os.path.exists(log_path):
                logger.error(f"Log file not found at: {log_path}")
                return False, None

            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    preview = f.read(100)
                    # Remove BOM and other problematic characters for logging
                    preview_clean = preview.replace('\ufeff', '').replace('\r', '').replace('\n', ' ')
                    logger.info(f"Successfully opened log file. Preview: {preview_clean[:50]}...")
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
            hwnd = self._find_game_window()
            return hwnd is not None
        except Exception:
            return False
