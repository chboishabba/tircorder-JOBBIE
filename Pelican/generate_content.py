import json
import os
import urllib.parse
from datetime import datetime

from contact_frequency_cache import ContactFrequencyCache
from generate_html_timeline_item import generate_html_timeline_item
from generate_html_dangling_audio import generate_html_dangling_audio
from generate_html_dangling_transcripts import generate_html_dangling_transcripts


# Load matches and dangling files
with open("matches.json", "r") as f:
    matches = json.load(f)

cache = ContactFrequencyCache()

with open("dangling_audio.json", "r") as f:
    dangling_audio = json.load(f)

with open("dangling_transcripts.json", "r") as f:
    dangling_transcripts = json.load(f)

# Create symbolic links directory if not exists
symlink_dir = "output/symlinks"
os.makedirs(symlink_dir, exist_ok=True)

# Generate HTML content
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Recordings Timeline</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Audio Recordings Timeline</h1>
    </header>
    <main>
        <section id="timeline">
            <h2>Timeline</h2>
            <div class="timeline-container">
"""

for match in matches:
    audio_file = match[0]
    transcript_file = match[1]
    platform = match[2]
    contact = match[3]

    timestamp = datetime.fromtimestamp(os.path.getmtime(audio_file))
    cache.record(contact, timestamp)

    # Create symbolic links
    audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
    transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript_file))

    if not os.path.exists(audio_symlink):
        os.symlink(audio_file, audio_symlink)
    if not os.path.exists(transcript_symlink):
        os.symlink(transcript_file, transcript_symlink)

    # URL-encode the paths for HTML
    encoded_audio_symlink = urllib.parse.quote(os.path.basename(audio_symlink))
    encoded_transcript_symlink = urllib.parse.quote(
        os.path.basename(transcript_symlink)
    )

    html_content += generate_html_timeline_item(
        encoded_audio_symlink,
        encoded_transcript_symlink,
        transcript_symlink,
        platform,
        contact,
    )

frequency_ranking = [
    {"contact": contact, "count": count} for contact, count in cache.frequency_ranking()
]

html_content += """
            </div>
        </section>
        <section id="dangling-files">
            <h2>Dangling Files</h2>
"""

html_content += generate_html_dangling_audio(dangling_audio, symlink_dir)
html_content += generate_html_dangling_transcripts(dangling_transcripts, symlink_dir)

html_content += (
    """
        </section>
    </main>
    <script>window.contactFrequencies = """
    + json.dumps(frequency_ranking)
    + """;</script>
    <script src="scripts.js"></script>
    <script src="timeline3d.js"></script>
</body>
</html>
"""
)

# Write the HTML content to a file
with open("content/timeline.html", "w") as f:
    f.write(html_content)

print("HTML content generated successfully.")
