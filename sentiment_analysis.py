from __future__ import annotations
"""Utilities for computing basic sentiment metrics on transcripts.

This module exposes helpers to calculate word-level sentiment as well as
aggregate sentiment over time blocks (e.g. per hour or per day).  The
implementation relies on the `vaderSentiment` package which provides a simple
lexicon and rule-based sentiment analyser.

These functions are intentionally lightweight and operate on plain data
structures so that higher level interfaces (CLI, GUI, web) can consume the
results in whatever way makes sense for the TiRCorder project.
"""
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Dict, Iterable, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyser = SentimentIntensityAnalyzer()


@dataclass
class TranscriptSegment:
    """Represents a fragment of transcript text.

    Attributes
    ----------
    start: datetime
        Absolute start time of the segment.
    end: datetime
        Absolute end time of the segment.
    text: str
        Transcribed text for the segment.
    """

    start: datetime
    end: datetime
    text: str


def word_sentiments(text: str) -> List[Dict[str, float]]:
    """Return sentiment scores for each word in *text*.

    Parameters
    ----------
    text:
        Raw transcript text.

    Returns
    -------
    list of dict
        Each entry has the keys ``word`` and ``score`` (compound sentiment
        score ranging from -1..1).
    """

    words = re.findall(r"\w+", text)
    return [{"word": w, "score": _analyser.polarity_scores(w)["compound"]} for w in words]


def aggregate_sentiment(
    segments: Iterable[TranscriptSegment], *, level: str = "hour"
) -> Dict[datetime, float]:
    """Aggregate sentiment for *segments* grouped by time blocks.

    Parameters
    ----------
    segments:
        Iterable of :class:`TranscriptSegment` items.
    level:
        Either ``"hour"`` or ``"day"`` determining the aggregation bucket.

    Returns
    -------
    dict
        Mapping bucket start timestamps to mean compound sentiment score.
    """

    buckets: Dict[datetime, List[float]] = {}
    for seg in segments:
        if level == "day":
            bucket = seg.start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # default to hour resolution
            bucket = seg.start.replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(bucket, []).append(_analyser.polarity_scores(seg.text)["compound"])

    return {k: sum(v) / len(v) for k, v in buckets.items() if v}
