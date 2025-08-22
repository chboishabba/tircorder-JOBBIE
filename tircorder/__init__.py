"""Core modules for the TiRCorder project.

The heavy dependencies used by some modules are optional so they are imported
within a ``try`` block. This allows lightweight components such as schema
validation to be used without pulling in the full stack during documentation or
testing.
"""

try:  # pragma: no cover - optional at import time
    from .scanner import scanner
    from .transcriber import transcriber
    from .utils import load_recordings_folders_from_db, wav2flac
    from .state import export_queues_and_files, load_state
    from .rate_limit import RateLimiter
    from .db_match_audio_transcript import match_audio_transcripts
    from contact_frequency_cache import ContactFrequencyCache
except Exception:  # pragma: no cover - dependencies may be missing
    scanner = None
    transcriber = None
    load_recordings_folders_from_db = None
    wav2flac = None
    export_queues_and_files = None
    load_state = None
    RateLimiter = None
    match_audio_transcripts = None
    ContactFrequencyCache = None

__all__ = [
    "scanner",
    "transcriber",
    "load_recordings_folders_from_db",
    "wav2flac",
    "export_queues_and_files",
    "load_state",
    "RateLimiter",
    "match_audio_transcripts",
    "ContactFrequencyCache",
]
