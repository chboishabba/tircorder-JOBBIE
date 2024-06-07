import os
import json
import sort_audio_transcript

results_file = 'traversal_results.json'

# Load the recordings folders from a JSON file
with open(results_file, 'r') as f:
    data = json.load(f)
    audio_files = data['audio_files']
    transcript_files = data['transcript_files']



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

e_matches = extract_date(matches)
e_dangling_audio = extract_date(dangling_audio)
e_dangling_transcripts = extract_date(dangling_transcripts)        
        

        
        
        
 
