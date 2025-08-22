"""Schema loading and validation utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import validate

_SCHEMAS: Dict[str, Dict[str, Any]] = {}
_SCHEMA_DIR = Path(__file__).resolve().parent


def load_schema(name: str) -> Dict[str, Any]:
    """Load a schema by ``name`` from the schemas directory."""
    if name not in _SCHEMAS:
        with open(_SCHEMA_DIR / f"{name}.schema.yaml", "r", encoding="utf-8") as fh:
            _SCHEMAS[name] = yaml.safe_load(fh)
    return _SCHEMAS[name]


def validate_story(data: Dict[str, Any]) -> None:
    """Validate a story event against ``story.schema.yaml``."""
    schema = load_schema("story")
    validate(instance=data, schema=schema)


def validate_rule_check_request(data: Dict[str, Any]) -> None:
    """Validate a rule check request against ``rule_check_request.schema.yaml``."""
    schema = load_schema("rule_check_request")
    validate(instance=data, schema=schema)


def validate_rule_check_response(data: Dict[str, Any]) -> None:
    """Validate a rule check response against ``rule_check_response.schema.yaml``."""
    schema = load_schema("rule_check_response")
    validate(instance=data, schema=schema)


__all__ = [
    "validate_story",
    "validate_rule_check_request",
    "validate_rule_check_response",
]
