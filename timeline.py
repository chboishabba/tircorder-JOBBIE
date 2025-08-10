"""Simple helpers for building activity timelines.

Timelines merge events from multiple data sources (audio transcripts, web
activity, etc.) into a single chronologically ordered stream.  Each event is a
dictionary with at least a ``time`` field.
"""
from datetime import datetime
from typing import Dict, Iterable, List, Mapping


def merge_event_streams(event_streams: Mapping[str, Iterable[Dict]]) -> List[Dict]:
    """Merge streams from different sources into a single sorted list.

    Parameters
    ----------
    event_streams:
        Mapping of source name to an iterable of event dictionaries.  Each
        event must contain a ``time`` key with a :class:`datetime` value.

    Returns
    -------
    list of dict
        Combined events tagged with their ``source`` and sorted by ``time``.
    """

    events: List[Dict] = []
    for source, stream in event_streams.items():
        for event in stream:
            item = dict(event)
            item["source"] = source
            events.append(item)
    events.sort(key=lambda e: e.get("time", datetime.min))
    return events


def bucket_by_day(events: Iterable[Dict]) -> Dict[datetime, List[Dict]]:
    """Group events into day buckets to enable zoomed-out views."""
    buckets: Dict[datetime, List[Dict]] = {}
    for event in events:
        time = event.get("time")
        if not isinstance(time, datetime):
            continue
        key = time.replace(hour=0, minute=0, second=0, microsecond=0)
        buckets.setdefault(key, []).append(event)
    return buckets
