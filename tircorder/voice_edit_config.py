"""Configuration adapter for TiRCorder voice-edit/self-observation features."""

from __future__ import annotations

from typing import Any, Mapping

from .interfaces.config import TircorderConfig
from .voice_edits import SelfObservationPolicy


def _as_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def self_observation_policy_from_mapping(
    config: Mapping[str, Any],
) -> SelfObservationPolicy:
    """Read the explicit voice-edit metric policy from a config mapping.

    Missing configuration is fail-closed: the metric is disabled and no
    StatiBaker projection is permitted.  Sharing cannot become enabled merely
    because the local metric is enabled; it has its own explicit flag.
    """

    voice_edit = config.get("voice_edit") or {}
    if not isinstance(voice_edit, Mapping):
        voice_edit = {}
    observation = voice_edit.get("self_observation") or {}
    if not isinstance(observation, Mapping):
        observation = {}

    enabled = _as_bool(observation.get("enabled"), False)
    share = _as_bool(observation.get("share_with_statibaker"), False)
    return SelfObservationPolicy(
        enabled=enabled,
        share_with_statibaker=enabled and share,
        purpose=str(
            observation.get("purpose") or "personal_interoceptive_reflection"
        ),
        window_label=str(observation.get("window") or "session"),
    )


def load_self_observation_policy() -> SelfObservationPolicy:
    """Load policy from the normal ``TircorderConfig`` path."""

    return self_observation_policy_from_mapping(TircorderConfig.get_config())
