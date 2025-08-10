import os
import json
from generate_html_header import generate_html_header
from generate_html_footer import generate_html_footer
from match_audio_transcript import load_recordings_folders, get_all_files, extract_date
from process_audio_files import process_audio_files
from process_transcript_files import process_transcript_files
from match_files import match_files
from generate_html_matches import generate_html_matches
from generate_html_dangling_audio import generate_html_dangling_audio
from generate_html_dangling_transcripts import generate_html_dangling_transcripts

results_file = 'traversal_results.json'
recordings_folders_file = 'folders_file.json'
audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']

# Load the recordings folders
recordings_folders = load_recordings_folders(recordings_folders_file)

# Get the current state of files
current_audio_files = get_all_files(recordings_folders, audio_extensions)
current_transcript_files = get_all_files(recordings_folders, transcript_extensions)

# Check if the results file exists
if os.path.exists(results_file):
    with open(results_file, 'r') as f:
        data = json.load(f)
        audio_files = data['audio_files']
        transcript_files = data['transcript_files']

    # Compare current files with the recorded files
    if set(current_audio_files) != set(audio_files) or set(current_transcript_files) != set(transcript_files):
        print("Changes detected in audio or transcript files. Updating traversal results.")
        audio_files = current_audio_files
        transcript_files = current_transcript_files
        with open(results_file, 'w') as f:
            json.dump({'audio_files': audio_files, 'transcript_files': transcript_files}, f)
else:
    # If results file doesn't exist, use the current state
    audio_files = current_audio_files
    transcript_files = current_transcript_files
    with open(results_file, 'w') as f:
        json.dump({'audio_files': audio_files, 'transcript_files': transcript_files}, f)

print(f"Loaded {len(audio_files)} audio files and {len(transcript_files)} transcript files.")

# Create symbolic links directory if not exists
symlink_dir = "output/symlinks"
os.makedirs(symlink_dir, exist_ok=True)

# Process audio and transcript files
audio_dict = process_audio_files(audio_files, symlink_dir)
transcript_dict = process_transcript_files(transcript_files, symlink_dir)

# Match audio and transcript files
matches, dangling_audio, dangling_transcripts = match_files(audio_dict, transcript_dict)

# Sort matches using extract_date
matches.sort(key=lambda x: extract_date(x[0]))

# Generate HTML content
html_content = generate_html_header()

# Generate HTML for matches
html_content += generate_html_matches(matches, symlink_dir)

# Close the timeline section and open dangling section
html_content += """
            </div>
        </section>
        <section id="dangling-files">
            <h2>Dangling Files</h2>
            <div>
                <h3>Audio without Transcripts</h3>
                <ul>
"""
html_content += generate_html_dangling_audio(dangling_audio, symlink_dir)

html_content += """
                </ul>
            </div>
            <div>
                <h3>Transcripts without Audio</h3>
                <ul>
"""
html_content += generate_html_dangling_transcripts(dangling_transcripts, symlink_dir)

html_content += """
                </ul>
            </div>
        </section>
"""
html_content += generate_html_footer()

# Write the HTML content to a file
with open("content/timeline.html", "w") as f:
    f.write(html_content)

print("HTML content generated successfully.")

