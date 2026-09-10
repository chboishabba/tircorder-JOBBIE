from tircorder.voice_edit_config import self_observation_policy_from_mapping


def test_missing_metric_config_is_fail_closed():
    policy = self_observation_policy_from_mapping({})
    assert policy.enabled is False
    assert policy.share_with_statibaker is False


def test_local_metric_does_not_imply_statibaker_share():
    policy = self_observation_policy_from_mapping(
        {"voice_edit": {"self_observation": {"enabled": True}}}
    )
    assert policy.enabled is True
    assert policy.share_with_statibaker is False


def test_statibaker_share_requires_metric_and_share_flags():
    disabled = self_observation_policy_from_mapping(
        {
            "voice_edit": {
                "self_observation": {
                    "enabled": False,
                    "share_with_statibaker": True,
                }
            }
        }
    )
    assert disabled.share_with_statibaker is False

    enabled = self_observation_policy_from_mapping(
        {
            "voice_edit": {
                "self_observation": {
                    "enabled": True,
                    "share_with_statibaker": True,
                    "window": "hour",
                    "purpose": "personal_reflection",
                }
            }
        }
    )
    assert enabled.share_with_statibaker is True
    assert enabled.window_label == "hour"
    assert enabled.purpose == "personal_reflection"
