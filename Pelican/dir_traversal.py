import os
import json

recordings_folders_file = 'folders_file.json'

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
        print(f"Traversing directory: {recordings_folder}")
        if not os.path.exists(recordings_folder):
            print(f"Directory does not exist: {recordings_folder}")
            continue
        for root, dirs, files in os.walk(recordings_folder):
            print(f"Checking directory: {root}")
            for file in files:
                print(f"Found file: {file}")
                filepath = os.path.join(root, file)
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(filepath)
                    print(f"Added audio file: {filepath}")
                elif any(file.lower().endswith(ext) for ext in transcript_extensions):
                    transcript_files.append(filepath)
                    print(f"Added transcript file: {filepath}")
    
    # Save the traversal results to the file
    with open(results_file, 'w') as f:
        json.dump({'audio_files': audio_files, 'transcript_files': transcript_files}, f)

print(f"Found {len(audio_files)} audio files and {len(transcript_files)} transcript files.")
print(f"Audio files: {audio_files}")
print(f"Transcript files: {transcript_files}")

