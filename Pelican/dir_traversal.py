import os
import re
import json
from datetime import datetime

recordings_folders_file = 'folders_file.json'  # Update this with the actual path to your JSON file

# Load the recordings folders from a JSON file
with open(recordings_folders_file, 'r') as f:
    data = json.load(f)
    recordings_folders = data['recordings_folders']

results_file = 'traversal_results.json'

audio_extensions = ['.wav', '.mp3', '.ogg']
transcript_extensions = ['.vtt', '.json']

# Check if the traversal results file exists
if os.path.exists(results_file):
    # Read the results from the file
    with open(results_file, 'r') as f:
        data = json.load(f)
        audio_files = data['audio_files']
        transcript_files = data['transcript_files']
else:
    # Perform the traversal and identify files
    audio_files = []
    transcript_files = []
    
    for recordings_folder in recordings_folders:
        for root, dirs, files in os.walk(recordings_folder):
            for file in files:
                filepath = os.path.join(root, file)
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(filepath)
                elif any(file.lower().endswith(ext) for ext in transcript_extensions):
                    transcript_files.append(filepath)
    
    # Save the traversal results to the file
    with open(results_file, 'w') as f:
        json.dump({'audio_files': audio_files, 'transcript_files': transcript_files}, f)

