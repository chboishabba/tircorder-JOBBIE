import os
import json
import time

recordings_folders_file = 'folders_file.json'
results_file = 'traversal_results.json'

audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']

def load_recordings_folders(file):
    with open(file, 'r') as f:
        data = json.load(f)
        print(f"Loaded recordings folders: {data['recordings_folders']}")  # Debugging print
        return data['recordings_folders']

def get_latest_modification_time(folders):
    latest_time = 0
    for folder in folders:
        if os.path.exists(folder):
            folder_time = os.path.getmtime(folder)
            if folder_time > latest_time:
                latest_time = folder_time
    return latest_time

def load_traversal_results(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            data = json.load(f)
            return data['audio_files'], data['transcript_files']
    return [], []

def save_traversal_results(file, audio_files, transcript_files):
    with open(file, 'w') as f:
        json.dump({'audio_files': audio_files, 'transcript_files': transcript_files}, f)

def perform_traversal(folders):
    audio_files = []
    transcript_files = []

    for recordings_folder in folders:
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

    return audio_files, transcript_files

# Main script logic
recordings_folders = load_recordings_folders(recordings_folders_file)

# Get the latest modification times
folders_latest_time = get_latest_modification_time(recordings_folders)
results_latest_time = os.path.getmtime(results_file) if os.path.exists(results_file) else 0

if results_latest_time < folders_latest_time:
    print("Folders have been modified more recently than the results file. Performing traversal again.")
    audio_files, transcript_files = perform_traversal(recordings_folders)
    save_traversal_results(results_file, audio_files, transcript_files)
else:
    print("Results file is up-to-date. Loading existing results.")
    audio_files, transcript_files = load_traversal_results(results_file)

print(f"Found {len(audio_files)} audio files and {len(transcript_files)} transcript files.")
print(f"Audio files: {audio_files}")
print(f"Transcript files: {transcript_files}")

