from datetime import datetime

from timeline import emails_for_day, index_emails_by_contact, step_index


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
