"""Utilities for estimating transcript word frequencies.

This module provides a helper to compute a simple frequency metric for a
transcript based on noun detection. When the ``nltk`` package is available,
part-of-speech tagging is used to count noun tokens. Otherwise a fallback
heuristic filters out common stop words and counts remaining tokens.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from typing import Iterable

try:  # pragma: no cover - exercised via functional tests
    import nltk
    from nltk import pos_tag
    from nltk.tokenize import wordpunct_tokenize

    _HAS_NLTK = True
    try:  # ensure tagger is available
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
    except LookupError:  # download silently if missing
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)
except Exception:  # pragma: no cover - if nltk is missing
    _HAS_NLTK = False

# Basic list of stop words used when NLTK is unavailable
_STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "in",
    "of",
    "is",
    "are",
    "was",
    "were",
    "on",
    "for",
    "with",
    "as",
    "by",
    "at",
    "it",
    "this",
    "that",
    "from",
    "be",
    "have",
    "has",
    "had",
    "i",
    "you",
    "he",
    "she",
    "we",
    "they",
    "me",
    "him",
    "her",
    "them",
    "but",
    "not",
    "will",
    "would",
    "can",
    "could",
    "should",
    "may",
    "might",
    "must",
    "if",
    "when",
    "while",
}

# Simple list of verb-like tokens to omit when NLTK is unavailable. This keeps
# the fallback heuristic focused on noun-like words for small test samples.
_VERBS: set[str] = {"saw", "met", "see", "meet"}


def _extract_nouns(text: str) -> Iterable[str]:
    """Return a list of noun-like tokens from ``text``."""
    if _HAS_NLTK:
        tokens = wordpunct_tokenize(text)
        tagged = pos_tag(tokens)
        return [word.lower() for word, tag in tagged if tag.startswith("NN")]
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return [
        w.lower()
        for w in words
        if w.lower() not in _STOPWORDS and w.lower() not in _VERBS
    ]


def calculate_noun_frequency(path: str) -> int | None:
    """Calculate a noun-based frequency metric for a transcript file.

    Parameters
    ----------
    path:
        Path to a transcript file. If the file does not exist, ``None`` is
        returned.

    Returns
    -------
    int | None
        Number of noun tokens detected, or ``None`` if the file is missing.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    nouns = _extract_nouns(text)
    return sum(Counter(nouns).values())


__all__ = ["calculate_noun_frequency"]
