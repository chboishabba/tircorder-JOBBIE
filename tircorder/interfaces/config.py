"""Configuration utilities for tircorder."""
"""Configuration management for Tircorder interfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_ENV_VAR = "TIRCORDER_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path.home() / ".tircorder" / "config.json"


class TircorderConfig:
    """Manage persistence of tircorder settings.

    Configuration values are stored in a JSON file whose path can be
    overridden by setting the ``TIRCORDER_CONFIG_PATH`` environment variable.
    When not set, the configuration is stored at ``~/.tircorder/config.json``.
    """

    @staticmethod
    def _get_config_path() -> Path:
        """Return the path to the configuration file, creating parent dirs."""
        path = os.getenv(CONFIG_ENV_VAR)
        config_path = Path(path).expanduser() if path else DEFAULT_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Load and return stored configuration values.

        Returns:
            A dictionary of configuration values. If the configuration file
            does not exist, an empty dictionary is returned.
        """

        config_path = cls._get_config_path()
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @classmethod
    def set_config(cls, config: Dict[str, Any]) -> None:
        """Persist configuration values to disk.

        Args:
            config: Mapping of configuration keys to values.
        """

        config_path = cls._get_config_path()
        with config_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, sort_keys=True)

class TircorderConfig:
    """Manage persistence of Tircorder settings in a JSON file."""

    CONFIG_ENV_VAR = "TIRCORDER_CONFIG_PATH"
    DEFAULT_FILENAME = ".tircorder_config.json"

    @classmethod
    def _get_config_path(cls) -> Path:
        """Return the path to the configuration file."""
        env_path = os.environ.get(cls.CONFIG_ENV_VAR)
        return Path(env_path) if env_path else Path.home() / cls.DEFAULT_FILENAME

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Retrieve configuration from disk.

        Returns an empty dictionary if the configuration file does not exist.
        """
        path = cls._get_config_path()
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    @classmethod
    def set_config(cls, config: Dict[str, Any]) -> None:
        """Persist the provided configuration dictionary to disk."""
        path = cls._get_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=2, sort_keys=True)
