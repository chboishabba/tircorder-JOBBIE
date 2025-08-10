"""Retrieve news articles for a specific day using the NewsAPI service."""

from datetime import date
from typing import Dict, List, Union

import requests

BASE_URL = "https://newsapi.org/v2/everything"


def search_news(
    query: str,
    day: Union[date, str],
    api_key: str,
    *,
    page_size: int = 10,
) -> List[Dict]:
    """Return news articles matching *query* published on *day*.

    Parameters
    ----------
    query:
        Keywords to search for.
    day:
        Date of interest as :class:`datetime.date` or ISO formatted string.
    api_key:
        API key for the NewsAPI service.
    page_size:
        Number of results to fetch (1-100). Defaults to 10.

    Returns
    -------
    list of dict
        Article entries as returned by the API. If the request fails,
        an empty list is returned.
    """

    day_str = day if isinstance(day, str) else day.isoformat()
    params = {
        "q": query,
        "from": day_str,
        "to": day_str,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": page_size,
        "apiKey": api_key,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []

    data = response.json()
    return data.get("articles", [])
