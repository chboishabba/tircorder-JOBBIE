from datetime import date, datetime, timedelta
from calendar_utils import get_relative_counts, build_day_segments, _get_date_range
from hourly_cache import HourlyEventCache

import pytest


def make_dt(y, m, d, h=0):
    return datetime(y, m, d, h)


def test_relative_counts_week():
    reference = date(2024, 5, 6)  # Monday
    entries = [
        make_dt(2024, 5, 6, 10),
        make_dt(2024, 5, 6, 12),
        make_dt(2024, 5, 7, 8),
        make_dt(2024, 5, 7, 9),
        make_dt(2024, 5, 8, 11),
    ]
    intensities = get_relative_counts(entries, view="week", reference_date=reference)
    assert intensities[date(2024, 5, 6)] == 1.0
    assert intensities[date(2024, 5, 7)] == 1.0
    assert intensities[date(2024, 5, 8)] == 0.5
    # days with no entries should be zero
    assert intensities[date(2024, 5, 9)] == 0


def test_relative_counts_empty():
    reference = date(2024, 5, 6)
    intensities = get_relative_counts([], view="week", reference_date=reference)
    assert all(v == 0 for v in intensities.values())


def test_build_day_segments_minute():
    day = date(2024, 5, 6)
    entries = [
        datetime(2024, 5, 6, 0, 1),
        datetime(2024, 5, 6, 0, 2),
    ]
    counts = build_day_segments(entries, day)
    assert len(counts) == 24 * 60
    assert counts[1] == 1
    assert counts[2] == 1
    assert sum(counts) == 2


def test_build_day_segments_by_app():
    day = date(2024, 5, 6)
    entries = [
        (datetime(2024, 5, 6, 0, 1), "sms"),
        (datetime(2024, 5, 6, 0, 1), "email"),
        (datetime(2024, 5, 6, 0, 2), "sms"),
    ]
    counts = build_day_segments(entries, day, by_app=True)
    assert counts["sms"][1] == 1
    assert counts["sms"][2] == 1
    assert counts["email"][1] == 1


def test_hourly_cache_counts_and_use_in_relative_counts():
    cache = HourlyEventCache(":memory:")
    base = datetime(2024, 5, 6, 0, 0)
    timestamps = [base + timedelta(minutes=i) for i in range(120)]
    cache.bulk_record(timestamps)

    day_counts = cache.day_counts(date(2024, 5, 6), date(2024, 5, 6))
    assert day_counts[date(2024, 5, 6)] == 120

    intensities = get_relative_counts(
        [], view="week", reference_date=date(2024, 5, 6), cache=cache, threshold=10
    )
    assert intensities[date(2024, 5, 6)] == 1.0


def test_get_date_range_invalid_view():
    with pytest.raises(ValueError):
        _get_date_range("invalid", date.today())


def test_build_day_segments_invalid_resolution():
    with pytest.raises(ValueError):
        build_day_segments([], date.today(), resolution="hour")
