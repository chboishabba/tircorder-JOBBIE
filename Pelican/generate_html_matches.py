import os
import urllib.parse
import html
from read_file_with_fallback import read_file_with_fallback


def generate_html_matches(matches, symlink_dir):
    html_content = ""
    for match in matches:
        audio_file, transcript_file = match
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
        transcript_symlink = os.path.join(
            symlink_dir, os.path.basename(transcript_file)
        )

        encoded_audio_symlink = urllib.parse.quote(os.path.basename(audio_symlink))
        encoded_transcript_symlink = urllib.parse.quote(
            os.path.basename(transcript_symlink)
        )

        transcript_content = read_file_with_fallback(transcript_symlink)
        transcript_content = html.escape(transcript_content)

        print(f"Generating HTML for {audio_file} and {transcript_file}")  # Debug print

        html_content += f"""
            <div class="timeline-item" role="listitem">
                <a href="#" class="label" aria-describedby="timeline-instructions" data-audio="symlinks/{encoded_audio_symlink}" data-transcript="symlinks/{encoded_transcript_symlink}">{os.path.basename(audio_file)}</a>
                <div class="audio-player" style="display:none;" aria-hidden="true">
                    <audio controls aria-label="Audio player">
                        <source src="symlinks/{encoded_audio_symlink}">
                    </audio>
                    <pre aria-label="Transcript">{transcript_content}</pre>
                    <div class="transcript-display" role="status" aria-live="polite" aria-atomic="true" aria-label="Current transcript line"></div>
                </div>
            </div>
        """
    return html_content
