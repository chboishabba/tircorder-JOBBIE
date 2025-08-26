from datetime import datetime

from utilities.timeline import (
from tircorder_utils.timeline import (
    bucket_by_day,
    emails_for_day,
    index_emails_by_contact,
    merge_event_streams,
    step_index,
)


def _sample_events():
    return [
        {
            "timestamp": datetime(2024, 5, 1, 9).isoformat(),
            "source": "email",
            "contact": "Alice",
            "id": 1,
        },
        {
            "timestamp": datetime(2024, 5, 1, 10).isoformat(),
            "source": "chat",
            "contact": "Alice",
            "id": 2,
        },
        {
            "timestamp": datetime(2024, 5, 1, 8).isoformat(),
            "source": "email",
            "contact": "Bob",
            "id": 3,
        },
        {
            "timestamp": datetime(2024, 5, 2, 9).isoformat(),
            "source": "email",
            "contact": "Bob",
            "id": 4,
        },
    ]


def test_emails_for_day_filters_and_sorts():
    events = _sample_events()
    result = emails_for_day(events, datetime(2024, 5, 1))
    assert [e["id"] for e in result] == [3, 1]


def test_index_emails_by_contact_groups():
    emails = emails_for_day(_sample_events(), datetime(2024, 5, 1))
    index = index_emails_by_contact(emails)
    assert [e["id"] for e in index["Alice"]] == [1]
    assert [e["id"] for e in index["Bob"]] == [3]


def test_step_index_wraps():
    assert step_index(0, 1, 2) == 1
    assert step_index(1, 1, 2) == 0
    assert step_index(0, -1, 2) == 1
    assert step_index(3, 1, 0) == 0
    assert step_index(0, 2, -5) == 0


def test_merge_event_streams_sorts_and_tags():
    streams = {
        "a": [
            {
                "timestamp": datetime(2024, 5, 1, 12).isoformat(),
                "event_id": "1",
                "id": 1,
                "actor": "A",
                "action": "act",
                "details": {},
            },
            {
                "timestamp": datetime(2024, 5, 1, 10).isoformat(),
                "event_id": "2",
                "id": 2,
                "actor": "A",
                "action": "act",
                "details": {},
            },
        ],
        "b": [
            {
                "timestamp": datetime(2024, 5, 1, 11).isoformat(),
                "event_id": "3",
                "id": 3,
                "actor": "B",
                "action": "act",
                "details": {},
            }
        ],
    }
    result = merge_event_streams(streams)
    assert [e["id"] for e in result] == [2, 3, 1]
    assert [e["source"] for e in result] == ["a", "b", "a"]


def test_bucket_by_day_groups_and_skips_invalid():
    events = [
        {"timestamp": datetime(2024, 5, 1, 9).isoformat(), "id": 1},
        {"timestamp": datetime(2024, 5, 1, 10).isoformat(), "id": 2},
        {"timestamp": datetime(2024, 5, 2, 11).isoformat(), "id": 3},
        {"timestamp": "not a datetime", "id": 4},
    ]
    buckets = bucket_by_day(events)
    day_one = datetime(2024, 5, 1)
    day_two = datetime(2024, 5, 2)
    assert sorted(e["id"] for e in buckets[day_one]) == [1, 2]
    assert [e["id"] for e in buckets[day_two]] == [3]
    assert 4 not in [e["id"] for bucket in buckets.values() for e in bucket]
