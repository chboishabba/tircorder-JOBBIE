import os
import urllib.parse

def generate_html_dangling_audio(dangling_audio, symlink_dir):
    html = ""
    for audio in dangling_audio:
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio))
        encoded_audio_symlink = urllib.parse.quote(os.path.basename(audio_symlink))
        html += f"<li>symlinks/{encoded_audio_symlink}</li>"
    return html

