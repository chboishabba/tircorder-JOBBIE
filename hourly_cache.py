import sqlite3
from datetime import datetime, date, timedelta

class HourlyEventCache:
    """Persistent cache of event counts binned by hour.

    Parameters
    ----------
    db_path: str, optional
        Location of the SQLite database file. Use ``":memory:"`` for an
        in-memory cache.
    """

    def __init__(self, db_path: str = "hourly_cache.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hour_counts (
                hour TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _hour_key(ts: datetime) -> str:
        return ts.strftime("%Y-%m-%dT%H")

    def record(self, ts: datetime, count: int = 1) -> None:
        """Record an event for the given timestamp."""
        key = self._hour_key(ts)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO hour_counts(hour, count) VALUES(?, ?)
            ON CONFLICT(hour) DO UPDATE SET count=count+?
            """,
            (key, count, count),
        )
        self.conn.commit()

    def bulk_record(self, timestamps) -> None:
        """Record multiple timestamps efficiently."""
        cur = self.conn.cursor()
        counts: dict[str, int] = {}
        for ts in timestamps:
            key = self._hour_key(ts)
            counts[key] = counts.get(key, 0) + 1
        cur.executemany(
            """
            INSERT INTO hour_counts(hour, count) VALUES(?, ?)
            ON CONFLICT(hour) DO UPDATE SET count=count+excluded.count
            """,
            list(counts.items()),
        )
        self.conn.commit()

    def day_counts(self, start: date, end: date) -> dict[date, int]:
        """Return counts per day between ``start`` and ``end`` inclusive."""
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        cur = self.conn.cursor()
        cur.execute(
            "SELECT hour, count FROM hour_counts WHERE hour BETWEEN ? AND ?",
            (self._hour_key(start_dt), self._hour_key(end_dt)),
        )
        rows = cur.fetchall()
        day_counts: dict[date, int] = {
            start + timedelta(days=i): 0 for i in range((end - start).days + 1)
        }
        for hour_str, count in rows:
            day = datetime.strptime(hour_str, "%Y-%m-%dT%H").date()
            day_counts[day] += count
        return day_counts

    def count_range(self, start: date, end: date) -> int:
        """Return total number of events between ``start`` and ``end``."""
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        cur = self.conn.cursor()
        cur.execute(
            "SELECT SUM(count) FROM hour_counts WHERE hour BETWEEN ? AND ?",
            (self._hour_key(start_dt), self._hour_key(end_dt)),
        )
        result = cur.fetchone()[0]
        return result or 0

__all__ = ["HourlyEventCache"]
