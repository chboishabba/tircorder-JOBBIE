import os
import json
import re
from datetime import datetime

results_file = 'traversal_results.json'
recordings_folders_file = 'folders_file.json'
audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']

def load_recordings_folders(file):
    with open(file, 'r') as f:
        data = json.load(f)
        return data['recordings_folders']

def get_all_files(folders, extensions):
    files = []
    for folder in folders:
        if os.path.exists(folder):
            for root, _, file_names in os.walk(folder):
                for file_name in file_names:
                    if any(file_name.lower().endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, file_name))
    return files

def extract_date(filename):
    match = re.search(r'\d{8}-\d{6}', filename)
    if match:
        return datetime.strptime(match.group(), '%Y%m%d-%H%M%S')
    else:
        return datetime.fromtimestamp(os.path.getctime(filename))

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

# Sort matches using extract_date
matches.sort(key=lambda x: extract_date(x[0]))

# Save matches, dangling_audio, and dangling_transcripts to JSON files
with open('matches.json', 'w') as f:
    json.dump(matches, f)

with open('dangling_audio.json', 'w') as f:
    json.dump(dangling_audio, f)

with open('dangling_transcripts.json', 'w') as f:
    json.dump(dangling_transcripts, f)

print(f"Matches: {matches}")
print(f"Dangling audio files: {dangling_audio}")
print(f"Dangling transcript files: {dangling_transcripts}")

