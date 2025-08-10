"""Helpers for building timeline HTML blocks."""

from __future__ import annotations

import urllib.parse

from .read_file_with_fallback import read_file_with_fallback


def generate_html_timeline_item(
    audio_symlink: str,
    transcript_symlink: str,
    transcript_path: str,
    platform: str,
    contact: str,
    frequency: int | float | None = None,
) -> str:
    """Return an HTML snippet for a single timeline item.

    Parameters
    ----------
    audio_symlink:
        Filename of the audio symlink relative to the ``symlinks`` directory.
    transcript_symlink:
        Filename of the transcript symlink relative to the ``symlinks`` directory.
    transcript_path:
        Path to the transcript file used for the ``pre`` tag contents.
    platform:
        Name of the platform the recording originated from.
    contact:
        Name of the contact associated with the recording.
    frequency:
        Optional frequency value to emit as a ``data-frequency`` attribute.

    Returns
    -------
    str
        A block of HTML representing the timeline item.
    """

    transcript_content = read_file_with_fallback(transcript_path)

    # Ensure proper URL encoding for use in HTML attributes
    encoded_audio = urllib.parse.quote(audio_symlink)
    encoded_transcript = urllib.parse.quote(transcript_symlink)

    freq_attr = f' data-frequency="{frequency}"' if frequency is not None else ""

    return (
        f'<div class="timeline-item" role="listitem" '
        f'data-platform="{platform}" data-contact="{contact}"{freq_attr}>'
        f'<a href="#" class="label" data-audio="symlinks/{encoded_audio}" '
        f'data-transcript="symlinks/{encoded_transcript}">{encoded_audio}</a>'
        '<div class="audio-player" style="display: none;">'
        "<audio controls>"
        f'<source data-src="symlinks/{encoded_audio}" type="audio/mpeg">'
        "</audio>"
        f"<pre>{transcript_content}</pre>"
        '<div class="highlight-container"></div>'
        "</div>"
        "</div>"
    )
