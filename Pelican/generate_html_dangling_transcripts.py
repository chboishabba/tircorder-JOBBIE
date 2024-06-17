import os
import urllib.parse

def generate_html_dangling_transcripts(dangling_transcripts, symlink_dir):
    html = ""
    for transcript in dangling_transcripts:
        transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript))
        encoded_transcript_symlink = urllib.parse.quote(os.path.basename(transcript_symlink))
        html += f"<li>symlinks/{encoded_transcript_symlink}</li>"
    return html

