"""Minimal Zapier webhook helper."""
from typing import Dict

import requests


def send_event(webhook_url: str, data: Dict) -> bool:
    """POST *data* to a Zapier "Catch Hook" URL.

    Parameters
    ----------
    webhook_url:
        Zapier generated URL.
    data:
        JSON serialisable dictionary payload.

    Returns
    -------
    bool
        ``True`` if the request succeeded, otherwise ``False``.
    """

    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return False
    return True
