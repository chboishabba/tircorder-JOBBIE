"""Parse YouTube watch history exports.

The Google Takeout service allows users to export their YouTube watch history
as a JSON file.  This helper converts that export into a list of timeline
events that can be merged with other data sources.
"""
import json
from datetime import datetime
from typing import Dict, List


def load_watch_history(path: str) -> List[Dict]:
    """Load watch history events from *path*.

    Parameters
    ----------
    path:
        Location of the ``watch-history.json`` file exported from Google
        Takeout.

    Returns
    -------
    list of dict
        Each event contains ``time`` (as :class:`datetime`), ``title`` and
        ``url`` keys.
    """

    with open(path, "r", encoding="utf-8") as fh:
        raw_items = json.load(fh)

    events: List[Dict] = []
    for item in raw_items:
        time_str = item.get("time") or item.get("timestamp")
        if not time_str:
            continue
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            # Skip malformed timestamps.
            continue
        events.append(
            {
                "time": dt,
                "title": item.get("title", ""),
                "url": item.get("titleUrl"),
            }
        )
    return events
