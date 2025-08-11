"""Copy audio and transcript files into the Zola static directory.

This replaces the symlink generation used by the Pelican build.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYMLINK_DIR = ROOT / "Zola" / "static" / "symlinks"


def copy_assets(
    matches_file: Path, dangling_audio_file: Path, dangling_transcripts_file: Path
) -> None:
    """Copy audio and transcript files into ``SYMLINK_DIR``.

    Parameters
    ----------
    matches_file:
        JSON file containing pairs of matched audio and transcript paths.
    dangling_audio_file:
        JSON file listing audio files without transcripts.
    dangling_transcripts_file:
        JSON file listing transcript files without audio.
    """
    SYMLINK_DIR.mkdir(parents=True, exist_ok=True)

    matches = json.loads(matches_file.read_text())
    dangling_audio = json.loads(dangling_audio_file.read_text())
    dangling_transcripts = json.loads(dangling_transcripts_file.read_text())

    for audio_file, transcript_file in matches:
        shutil.copy2(audio_file, SYMLINK_DIR / Path(audio_file).name)
        shutil.copy2(transcript_file, SYMLINK_DIR / Path(transcript_file).name)

    for audio in dangling_audio:
        shutil.copy2(audio, SYMLINK_DIR / Path(audio).name)

    for transcript in dangling_transcripts:
        shutil.copy2(transcript, SYMLINK_DIR / Path(transcript).name)


if __name__ == "__main__":
    copy_assets(
        ROOT / "matches.json",
        ROOT / "dangling_audio.json",
        ROOT / "dangling_transcripts.json",
    )
