import os
import urllib.parse
from read_file_with_fallback import read_file_with_fallback

def generate_html_matches(matches, symlink_dir):
    html = '<div class="timeline-container">'
    for match in matches:
        audio_file, transcript_file = match
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
        transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript_file))

        encoded_audio_symlink = urllib.parse.quote(os.path.basename(audio_symlink))
        encoded_transcript_symlink = urllib.parse.quote(os.path.basename(transcript_symlink))

        transcript_content = read_file_with_fallback(transcript_symlink)

        print(f"Generating HTML for {audio_file} and {transcript_file}")  # Debug print

        html += f"""
            <div class="timeline-item">
                <a href="#" class="label" data-audio="symlinks/{encoded_audio_symlink}" data-transcript="symlinks/{encoded_transcript_symlink}">{os.path.basename(audio_file)}</a>
                <div class="audio-player" style="display:none;">
                    <audio controls>
                        <source src="symlinks/{encoded_audio_symlink}">
                    </audio>
                    <pre>{transcript_content}</pre>
                    <div class="transcript-display"></div>
                </div>
            </div>
        """
    html += '</div>'
    return html

