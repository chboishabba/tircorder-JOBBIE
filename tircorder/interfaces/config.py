"""Configuration management for Tircorder interfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


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
