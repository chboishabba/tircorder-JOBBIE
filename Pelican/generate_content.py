"""Build the timeline HTML page."""

import json
import os

from generate_html_timeline_item import generate_html_timeline_item
from generate_html_dangling_audio import generate_html_dangling_audio
from generate_html_dangling_transcripts import generate_html_dangling_transcripts
from transcript_frequency import calculate_noun_frequency


# Load matches and dangling files
with open("matches.json", "r") as f:
    matches = json.load(f)

print("Loaded matches:", matches)  # Debug print

with open("dangling_audio.json", "r") as f:
    dangling_audio = json.load(f)

print("Loaded dangling audio:", dangling_audio)  # Debug print

with open("dangling_transcripts.json", "r") as f:
    dangling_transcripts = json.load(f)

print("Loaded dangling transcripts:", dangling_transcripts)  # Debug print

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

    # Create symbolic links
    audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
    transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript_file))

    if not os.path.exists(audio_symlink):
        os.symlink(audio_file, audio_symlink)
    if not os.path.exists(transcript_symlink):
        os.symlink(transcript_file, transcript_symlink)

    # Determine a frequency metric using noun detection for the transcript
    frequency = calculate_noun_frequency(transcript_file)

    html_content += generate_html_timeline_item(
        os.path.basename(audio_symlink),
        os.path.basename(transcript_symlink),
        transcript_symlink,
        platform,
        contact,
        frequency,
    )

html_content += """
            </div>
        </section>
        <section id="dangling-files">
            <h2>Dangling Files</h2>
"""

html_content += generate_html_dangling_audio(dangling_audio, symlink_dir)
html_content += generate_html_dangling_transcripts(dangling_transcripts, symlink_dir)

html_content += """
        </section>
    </main>
    <script src="scripts.js"></script>
    <script src="timeline3d.js"></script>
</body>
</html>
"""

# Write the HTML content to a file
with open("content/timeline.html", "w") as f:
    f.write(html_content)

print("HTML content generated successfully.")
