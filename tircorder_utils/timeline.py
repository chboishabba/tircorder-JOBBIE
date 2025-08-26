"""Simple helpers for building activity timelines.

Timelines merge events from multiple data sources (audio transcripts, web
activity, etc.) into a single chronologically ordered stream.  Each event is a
dictionary with at least a ``timestamp`` field.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping


def _extract_timestamp(event: Dict[str, Any]) -> datetime | None:
    """Return a ``datetime`` from common timestamp keys.

    Accepts either a ``datetime`` object or an ISO formatted string under
    ``"timestamp"`` or ``"time"``. Returns ``None`` if no valid timestamp is
    found.
    """

    ts = event.get("timestamp") or event.get("time")
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
    return None


def merge_event_streams(event_streams: Mapping[str, Iterable[Dict]]) -> List[Dict]:
    """Merge streams from different sources into a single sorted list.

    Each event may specify its time under ``"timestamp"`` (ISO string) or
    ``"time"`` (``datetime``). Events lacking a parsable timestamp are ignored.
    The returned events are tagged with their ``source`` and sorted
    chronologically.
    """

    events: List[Dict] = []
    for source, stream in event_streams.items():
        for event in stream:
            ts = _extract_timestamp(event)
            if ts is None:
                continue
            item = dict(event)
            item["source"] = source
            item["timestamp"] = ts.isoformat()
            events.append(item)
    events.sort(key=lambda e: _extract_timestamp(e) or datetime.min)
    return events


def bucket_by_day(events: Iterable[Dict]) -> Dict[datetime, List[Dict]]:
    """Group events into day buckets to enable zoomed-out views."""

    buckets: Dict[datetime, List[Dict]] = {}
    for event in events:
        ts = _extract_timestamp(event)
        if ts is None:
            continue
        key = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        buckets.setdefault(key, []).append(event)
    return buckets


def emails_for_day(events: Iterable[Dict], day: datetime) -> List[Dict]:
    """Return email events for a single day sorted chronologically.

    Parameters
    ----------
    events:
        Iterable of event dictionaries that include ``timestamp`` and ``source``
        keys.
    day:
        Day to filter by. Time portion is ignored.

    Returns
    -------
    list of dict
        Email events from the specified day ordered by ``timestamp``.
    """

    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    daily: List[Dict] = []
    for event in events:
        ts = _extract_timestamp(event)
        if ts is None or event.get("source") != "email":
            continue
        if start <= ts < end:
            daily.append(event)
    daily.sort(key=lambda e: _extract_timestamp(e) or datetime.min)
    return daily


def index_emails_by_contact(emails: Iterable[Dict]) -> Dict[str, List[Dict]]:
    """Group emails by contact, sorted chronologically within each contact."""

    index: Dict[str, List[Dict]] = {}
    for email in emails:
        contact = email.get("contact")
        if not contact:
            continue
        index.setdefault(contact, []).append(email)
    for messages in index.values():
        messages.sort(key=lambda e: _extract_timestamp(e) or datetime.min)
    return index


def step_index(current: int, step: int, total: int) -> int:
    """Move within a list using wrap-around semantics.

    Parameters
    ----------
    current:
        Current position in the list.
    step:
        Positive or negative number of steps to move.
    total:
        Length of the list.

    Returns
    -------
    int
        New index after applying ``step``. Returns 0 if ``total`` is 0.
    """

    if total <= 0:
        return 0
    return (current + step) % total
