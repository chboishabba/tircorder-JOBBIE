import os
import urllib.parse
from read_file_with_fallback import read_file_with_fallback

def generate_html_timeline_item(
    encoded_audio_symlink,
    encoded_transcript_symlink,
    transcript_symlink,
    platform,
    contact,
):
    transcript_content = read_file_with_fallback(transcript_symlink)

    # Use urllib.parse.quote to ensure proper encoding
    encoded_audio_symlink = urllib.parse.quote(encoded_audio_symlink)
    encoded_transcript_symlink = urllib.parse.quote(encoded_transcript_symlink)

    return f"""
        <div class="timeline-item" data-platform="{platform}" data-contact="{contact}">
            <a href="#" class="label" data-audio="symlinks/{encoded_audio_symlink}" data-transcript="symlinks/{encoded_transcript_symlink}">{encoded_audio_symlink}</a>
            <div class="audio-player" style="display: none;">
                <audio controls>
                    <source data-src="symlinks/{encoded_audio_symlink}" type="audio/mpeg">
                </audio>
                <pre>{transcript_content}</pre>
                <div class="highlight-container"></div>
            </div>
        </div>
    """

