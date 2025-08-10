"""Helpers for counting contact occurrences across days."""

from collections import defaultdict
from datetime import date, datetime


class ContactFrequencyCache:
    """Cache counting contact occurrences by day."""

    def __init__(self) -> None:
        self._data: dict[str, dict[date, int]] = defaultdict(lambda: defaultdict(int))

    def record(self, contact: str, ts: datetime) -> None:
        """Record a contact occurrence for the given timestamp."""
        day = ts.date()
        self._data[contact][day] += 1

    def daily_counts(self) -> dict[str, dict[date, int]]:
        """Return a mapping of contacts to their per-day counts."""
        return {c: dict(days) for c, days in self._data.items()}

    def frequency_ranking(self) -> list[tuple[str, int]]:
        """Return contacts sorted by total frequency descending."""
        totals = {c: sum(days.values()) for c, days in self._data.items()}
        return sorted(totals.items(), key=lambda item: item[1], reverse=True)


__all__ = ["ContactFrequencyCache"]
