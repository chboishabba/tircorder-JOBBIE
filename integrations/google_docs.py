"""Stubs for Google Docs/Drive activity integration."""
from datetime import datetime
from typing import Dict, List


def load_document_activity(credentials, start: datetime, end: datetime) -> List[Dict]:
    """Fetch activity within the given timeframe.

    This function is intentionally left as a stub.  It serves as a placeholder
    for future integration with the Google Drive Activity API which would
    allow TiRCorder to pull in document edits into the user timeline.
    """
    raise NotImplementedError("Google Docs integration not yet implemented")
