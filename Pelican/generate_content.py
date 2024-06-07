import json
from jinja2 import Template
import os

# Load matches from the JSON file
with open('matches.json', 'r') as f:
    matches = json.load(f)

# Load dangling_audio from the JSON file, create an empty list if the file does not exist
try:
    with open('dangling_audio.json', 'r') as f:
        dangling_audio = json.load(f)
except FileNotFoundError:
    dangling_audio = []

# Load dangling_transcripts from the JSON file, create an empty list if the file does not exist
try:
    with open('dangling_transcripts.json', 'r') as f:
        dangling_transcripts = json.load(f)
except FileNotFoundError:
    dangling_transcripts = []

template = Template("""
Title: Audio Recordings Timeline
Date: {{ date }}
Category: Recordings
Tags: audio, transcripts
Slug: audio-recordings-timeline
Author: Your Name
Summary: A timeline of audio recordings and transcripts.

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Audio Recordings Timeline</title>
    <style>
        /* Add your CSS here */
    </style>
</head>
<body>
    <h1>Audio Recordings Timeline</h1>
    <div id="timeline">
        {% for audio, transcript in matches %}
            <div class="recording" data-audio="{{ audio }}" data-transcript="{{ transcript }}">
                {{ audio }}
            </div>
        {% endfor %}
    </div>
    <h2>Dangling Files</h2>
    <h3>Audio without Transcripts</h3>
    <ul>
        {% for audio in dangling_audio %}
            <li>{{ audio }}</li>
        {% endfor %}
    </ul>
    <h3>Transcripts without Audio</h3>
    <ul>
        {% for transcript in dangling_transcripts %}
            <li>{{ transcript }}</li>
        {% endfor %}
    </ul>
    <script>
        /* Add your JavaScript here */
    </script>
</body>
</html>
""")

output = template.render(
    date="2024-06-07T14:00:00",  # Use the current date or a dynamic date if needed
    matches=matches,
    dangling_audio=dangling_audio,
    dangling_transcripts=dangling_transcripts
)

# Ensure the content directory exists
os.makedirs('content', exist_ok=True)

with open('content/timeline.html', 'w') as f:
    f.write(output)

print("Generated content written to content/timeline.html")

