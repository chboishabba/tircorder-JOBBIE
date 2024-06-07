import os
import json
import re
from datetime import datetime
import sort_audio_transcript

results_file = 'traversal_results.json'

# Load the recordings folders from a JSON file
with open(results_file, 'r') as f:
    data = json.load(f)
    audio_files = data['audio_files']
    transcript_files = data['transcript_files']

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

def extract_date(filename):
    match = re.search(r'\d{8}-\d{6}', filename)
    if match:
        return datetime.strptime(match.group(), '%Y%m%d-%H%M%S')
    else:
        return datetime.fromtimestamp(os.path.getctime(filename))

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

