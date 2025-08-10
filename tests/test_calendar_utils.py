from datetime import datetime, date

from calendar_utils import get_relative_counts, build_day_segments


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
