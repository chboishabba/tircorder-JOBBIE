import os
import json
from generate_html_header import generate_html_header
from generate_html_footer import generate_html_footer
from read_file_with_fallback import read_file_with_fallback
from generate_html_matches import generate_html_matches
from generate_html_dangling_audio import generate_html_dangling_audio
from generate_html_dangling_transcripts import generate_html_dangling_transcripts
from generate_symlinks import create_symlinks
from dir_traversal import perform_traversal, load_recordings_folders, save_traversal_results
from match_files import match_files
from sort_audio_transcript import extract_date

results_file = 'traversal_results.json'
recordings_folders_file = 'folders_file.json'
audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']

# Load the recordings folders
recordings_folders = load_recordings_folders(recordings_folders_file)

# Get the current state of files
audio_files, transcript_files = perform_traversal(recordings_folders)
save_traversal_results(results_file, audio_files, transcript_files)

print(f"Loaded {len(audio_files)} audio files and {len(transcript_files)} transcript files.")  # Debug print

# Create symbolic links directory if not exists
symlink_dir = "output/symlinks"
os.makedirs(symlink_dir, exist_ok=True)

# Process audio and transcript files
audio_dict = {os.path.basename(file): file for file in audio_files}
transcript_dict = {os.path.basename(file): file for file in transcript_files}

# Match audio and transcript files
matches, dangling_audio, dangling_transcripts = match_files(audio_dict, transcript_dict)

# Sort matches using extract_date
matches.sort(key=lambda x: extract_date(x[0]))

print(f"Matched files count: {len(matches)}")  # Debug print
print(f"Dangling audio count: {len(dangling_audio)}")  # Debug print
print(f"Dangling transcripts count: {len(dangling_transcripts)}")  # Debug print

# Create symlinks
create_symlinks(matches, dangling_audio, dangling_transcripts, symlink_dir)

# Generate HTML content
html_content = generate_html_header()

# Generate HTML for matches
html_content += generate_html_matches(matches, symlink_dir)

# Generate HTML for dangling audio and transcripts
html_content += """
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

