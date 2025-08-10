from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import calendar as _calendar
from typing import Optional

try:  # optional dependency
    from hourly_cache import HourlyEventCache  # type: ignore
except Exception:  # pragma: no cover - cache optional
    HourlyEventCache = None  # type: ignore


def _get_date_range(view: str, reference_date: date):
    """Return the inclusive date range for a given view."""
    if view == "day":
        start = reference_date
        end = reference_date
    elif view == "week":
        start = reference_date - timedelta(days=reference_date.weekday())
        end = start + timedelta(days=6)
    elif view == "fortnight":
        start = reference_date - timedelta(days=reference_date.weekday() + 7)
        end = start + timedelta(days=13)
    elif view == "month":
        start = reference_date.replace(day=1)
        last_day = _calendar.monthrange(reference_date.year, reference_date.month)[1]
        end = reference_date.replace(day=last_day)
    elif view == "year":
        start = reference_date.replace(month=1, day=1)
        end = reference_date.replace(month=12, day=31)
    else:
        raise ValueError(f"unknown view: {view}")
    return start, end


def get_relative_counts(
    entries=None,
    view: str = "week",
    reference_date: Optional[date] = None,
    cache: Optional["HourlyEventCache"] = None,
    threshold: int = 100,
):
    """Compute relative intensity per day for the selected view."""
    if reference_date is None:
        reference_date = date.today()

    start, end = _get_date_range(view, reference_date)

    entries = list(entries or [])
    use_cache = cache is not None and (not entries or len(entries) > threshold)

    if use_cache:
        day_counts = cache.day_counts(start, end)
    else:
        counts = Counter(dt.date() for dt in entries)
        num_days = (end - start).days + 1
        day_counts = {
            start + timedelta(days=i): counts.get(start + timedelta(days=i), 0)
            for i in range(num_days)
        }

    max_count = max(day_counts.values()) if day_counts else 0
    intensities = {
        day: (count / max_count if max_count else 0)
        for day, count in day_counts.items()
    }
    return intensities


def build_day_segments(
    entries,
    day: date,
    resolution: str = "minute",
    by_app: bool = False,
):
    """Return per-time-step counts for a specific day."""

    if resolution == "second":
        step_seconds = 1
        total_steps = 24 * 60 * 60
    elif resolution == "minute":
        step_seconds = 60
        total_steps = 24 * 60
    else:
        raise ValueError("resolution must be 'minute' or 'second'")

    def _extract(entry):
        if isinstance(entry, dict):
            ts = entry.get("timestamp")
            app = entry.get("app")
        else:
            try:
                ts, app = entry
            except (TypeError, ValueError):
                ts = entry
                app = None
        return ts, app

    start_dt = datetime.combine(day, datetime.min.time())

    if by_app:
        counts = defaultdict(lambda: [0] * total_steps)
    else:
        counts = [0] * total_steps

    for entry in entries:
        ts, app = _extract(entry)
        if ts.date() != day:
            continue
        index = int((ts - start_dt).total_seconds() // step_seconds)
        if 0 <= index < total_steps:
            if by_app:
                counts[app][index] += 1
            else:
                counts[index] += 1

    return counts


__all__ = ["get_relative_counts", "build_day_segments"]

