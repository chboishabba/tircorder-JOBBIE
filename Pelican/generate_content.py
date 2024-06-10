import json
import os
import urllib.parse

results_file = 'traversal_results.json'

# Load the recordings folders from a JSON file
with open(results_file, 'r') as f:
    data = json.load(f)
    audio_files = data['audio_files']
    transcript_files = data['transcript_files']

# Sort and pair the files
audio_dict = {}
transcript_dict = {}

for audio in audio_files:
    base = os.path.splitext(os.path.basename(audio))[0]
    audio_dict[base] = audio

for transcript in transcript_files:
    base = os.path.splitext(os.path.basename(transcript))[0]
    transcript_dict[base] = transcript

matches = []
dangling_audio = []
dangling_transcripts = []

for base in audio_dict.keys():
    if base in transcript_dict:
        matches.append((audio_dict[base], transcript_dict[base]))
    else:
        dangling_audio.append(audio_dict[base])

for base in transcript_dict.keys():
    if base not in audio_dict:
        dangling_transcripts.append(transcript_dict[base])

# Function to read file with fallback encoding
def read_file_with_fallback(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            return f.read()

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
    <script src="scripts.js" defer></script>
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

    # Create symbolic links
    audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
    transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript_file))

    if not os.path.exists(audio_symlink):
        os.symlink(audio_file, audio_symlink)
    if not os.path.exists(transcript_symlink):
        os.symlink(transcript_file, transcript_symlink)

    # URL-encode the paths for HTML
    encoded_audio_symlink = urllib.parse.quote(os.path.basename(audio_symlink))
    encoded_transcript_symlink = urllib.parse.quote(os.path.basename(transcript_symlink))
    transcript_content = read_file_with_fallback(transcript_symlink)

    html_content += f"""
                <div class="timeline-item" data-audio="symlinks/{encoded_audio_symlink}" data-transcript="symlinks/{encoded_transcript_symlink}">
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">
                        <span class="label">{os.path.basename(audio_file)}</span>
                        <div class="audio-player" style="display: none;">
                            <audio controls>
                                <source data-src="symlinks/{encoded_audio_symlink}" type="audio/wav">
                            </audio>
                            <pre>{transcript_content}</pre>
                        </div>
                    </div>
                </div>
    """

html_content += """
            </div>
        </section>
        <section id="dangling-files">
            <h2>Dangling Files</h2>
            <div>
                <h3>Audio without Transcripts</h3>
                <ul>
"""

for audio in dangling_audio:
    audio_symlink = os.path.join(symlink_dir, os.path.basename(audio))
    if not os.path.exists(audio_symlink):
        os.symlink(audio, audio_symlink)
    html_content += f"<li>{os.path.basename(audio)}</li>"

html_content += """
                </ul>
            </div>
            <div>
                <h3>Transcripts without Audio</h3>
                <ul>
"""

for transcript in dangling_transcripts:
    transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript))
    if not os.path.exists(transcript_symlink):
        os.symlink(transcript, transcript_symlink)
    html_content += f"<li>{os.path.basename(transcript)}</li>"

html_content += """
                </ul>
            </div>
        </section>
    </main>
</body>
</html>
"""

# Write the HTML content to a file
with open("content/timeline.html", "w") as f:
    f.write(html_content)

print("HTML content generated successfully.")

