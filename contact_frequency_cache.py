import sqlite3
from datetime import date, datetime, timedelta


class ContactFrequencyCache:
    """Persistent cache of contact interaction counts per day.

    Parameters
    ----------
    db_path: str, optional
        Location of the SQLite database file. Use ``":memory:"`` for an
        in-memory cache.
    """

    def __init__(self, db_path: str = "contact_frequency_cache.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_counts (
                day TEXT NOT NULL,
                contact TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (day, contact)
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _day_key(ts: datetime) -> str:
        return ts.strftime("%Y-%m-%d")

    def record(self, contact: str, ts: datetime) -> None:
        """Record an interaction for ``contact`` at ``ts``."""
        key = self._day_key(ts)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO contact_counts(day, contact, count) VALUES(?, ?, 1)
            ON CONFLICT(day, contact) DO UPDATE SET count=count+1
            """,
            (key, contact),
        )
        self.conn.commit()

    def day_counts(self, start: date, end: date) -> dict[date, dict[str, int]]:
        """Return per-contact counts for each day between ``start`` and ``end``."""
        start_key = start.strftime("%Y-%m-%d")
        end_key = end.strftime("%Y-%m-%d")
        cur = self.conn.cursor()
        cur.execute(
            "SELECT day, contact, count FROM contact_counts WHERE day BETWEEN ? AND ?",
            (start_key, end_key),
        )
        rows = cur.fetchall()
        day_counts: dict[date, dict[str, int]] = {
            start + timedelta(days=i): {} for i in range((end - start).days + 1)
        }
        for day_str, contact, count in rows:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
            day_counts[day][contact] = count
        return day_counts


__all__ = ["ContactFrequencyCache"]
