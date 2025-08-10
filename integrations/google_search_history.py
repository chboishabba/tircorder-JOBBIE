"""Parse Google search history exports."""
import json
from datetime import datetime
from typing import Dict, List


def load_search_history(path: str) -> List[Dict]:
    """Load search queries from a Google Takeout JSON export.

    Parameters
    ----------
    path:
        Location of the ``Search-history.json`` file from Google Takeout.

    Returns
    -------
    list of dict
        Each event contains ``time`` (as :class:`datetime`), ``query`` and
        optional ``url`` keys.
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
            continue
        title = item.get("title", "")
        if title.startswith("Searched for"):
            query = title.replace("Searched for", "").strip().strip('"')
        else:
            query = title
        events.append(
            {
                "time": dt,
                "query": query,
                "url": item.get("titleUrl"),
            }
        )
    return events
