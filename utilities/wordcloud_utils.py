import sqlite3
import hashlib
import json
import re
from dataclasses import dataclass
from collections import Counter


@dataclass
class TopicSummary:
    """Summary information for a text topic.

    Exposes raw word counts and HTML for a generated word cloud representation.
    """

    word_counts: dict[str, int]
    wordcloud_html: str


class WordCloudCache:
    """Persistent cache mapping text hashes to word-frequency counts."""

    def __init__(self, db_path: str = "wordcloud_cache.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS wordclouds (
                text_hash TEXT PRIMARY KEY,
                counts TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _compute_counts(self, text: str) -> dict[str, int]:
        words = re.findall(r"\b\w+\b", text.lower())
        return dict(Counter(words))

    def get_or_create(self, text: str) -> dict[str, int]:
        """Return word-frequency counts for ``text``, generating if needed."""
        h = self._hash_text(text)
        cur = self.conn.cursor()
        cur.execute("SELECT counts FROM wordclouds WHERE text_hash=?", (h,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        counts = self._compute_counts(text)
        cur.execute(
            "INSERT INTO wordclouds(text_hash, counts) VALUES(?, ?)",
            (h, json.dumps(counts)),
        )
        self.conn.commit()
        return counts

    def close(self) -> None:
        self.conn.close()


def _build_html_from_counts(counts: dict[str, int]) -> str:
    if not counts:
        return '<div class="wordcloud"></div>'
    max_count = max(counts.values())
    parts = []
    for word, count in counts.items():
        weight = count / max_count
        size = 10 + weight * 40  # font-size between 10 and 50 px
        parts.append(
            f'<span class="wc-word" data-weight="{count}" style="font-size:{size:.1f}px">{word}</span>'
        )
    return '<div class="wordcloud">' + " ".join(parts) + "</div>"


def generate_wordcloud(text: str, cache: WordCloudCache | None = None) -> TopicSummary:
    """Generate a word cloud for ``text`` and return a ``TopicSummary``.

    Parameters
    ----------
    text:
        Input text to visualize.
    cache:
        Optional :class:`WordCloudCache` to use. If not supplied, a default
        on-disk cache will be used.
    """
    if cache is None:
        cache = WordCloudCache()
    counts = cache.get_or_create(text)
    html = _build_html_from_counts(counts)
    return TopicSummary(word_counts=counts, wordcloud_html=html)


__all__ = ["TopicSummary", "WordCloudCache", "generate_wordcloud"]
