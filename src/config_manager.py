"""
Configuration management for the Torchlight Infinite Price Tracker.
Handles loading, saving, and validating configuration settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .constants import CONFIG_FILE, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration data class."""
    opacity: float = 1.0
    tax: int = 0
    user: str = ""

    def __post_init__(self):
        """Validate configuration values after initialization."""
        self.opacity = max(0.1, min(1.0, self.opacity))
        self.tax = max(0, min(1, self.tax))


class ConfigManager:
    """Manages application configuration with proper error handling and validation."""

    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file.
        """
        self.config_file = Path(config_file)
        self._config: Optional[AppConfig] = None
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """Create default configuration file if it doesn't exist."""
        if not self.config_file.exists():
            logger.info(f"Creating default configuration file: {self.config_file}")
            self._save_dict(DEFAULT_CONFIG)

    def _save_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Save configuration dictionary to file.

        Args:
            config_dict: Configuration dictionary to save.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def load(self) -> AppConfig:
        """
        Load configuration from file.

        Returns:
            Loaded and validated configuration.

        Raises:
            ValueError: If configuration file is invalid.
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            self._config = AppConfig(**config_dict)
            logger.info("Configuration loaded successfully")
            return self._config

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            self._config = AppConfig(**DEFAULT_CONFIG)
            return self._config
        except TypeError as e:
            logger.error(f"Invalid configuration format: {e}")
            raise ValueError(f"Invalid configuration: {e}")

    def save(self, config: Optional[AppConfig] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save. If None, saves current configuration.
        """
        if config is not None:
            self._config = config

        if self._config is None:
            logger.warning("No configuration to save")
            return

        self._save_dict(asdict(self._config))
        logger.info("Configuration saved successfully")

    def get(self) -> AppConfig:
        """
        Get current configuration.

        Returns:
            Current configuration. Loads from file if not already loaded.
        """
        if self._config is None:
            return self.load()
        return self._config

    def update_opacity(self, opacity: float) -> None:
        """
        Update opacity setting.

        Args:
            opacity: New opacity value (0.1 to 1.0).
        """
        config = self.get()
        config.opacity = max(0.1, min(1.0, opacity))
        self.save()
        logger.debug(f"Opacity updated to {config.opacity}")

    def update_tax(self, tax_enabled: int) -> None:
        """
        Update tax setting.

        Args:
            tax_enabled: 0 for no tax, 1 for tax enabled.
        """
        config = self.get()
        config.tax = max(0, min(1, tax_enabled))
        self.save()
        logger.debug(f"Tax setting updated to {config.tax}")

    def is_tax_enabled(self) -> bool:
        """
        Check if tax is enabled.

        Returns:
            True if tax is enabled, False otherwise.
        """
        return self.get().tax == 1
