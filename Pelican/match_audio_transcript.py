import os
import re
import sqlite3
from datetime import datetime

# Database setup
db_path = 'state.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create necessary tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS recordings_folders (
    id INTEGER PRIMARY KEY,
    folder_path TEXT UNIQUE NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    base_name TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS transcript_files (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    base_name TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS matched_pairs (
    audio_file TEXT NOT NULL,
    transcript_file TEXT NOT NULL,
    date_matched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Functions
def load_recordings_folders():
    cursor.execute('SELECT folder_path FROM recordings_folders')
    return [row[0] for row in cursor.fetchall()]

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
recordings_folders = load_recordings_folders()

# Get the current state of files
audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']
current_audio_files = get_all_files(recordings_folders, audio_extensions)
current_transcript_files = get_all_files(recordings_folders, transcript_extensions)

# Store current state of files in the database
cursor.executemany('INSERT OR IGNORE INTO audio_files (file_path, base_name) VALUES (?, ?)', [(file, os.path.splitext(os.path.basename(file))[0]) for file in current_audio_files])
cursor.executemany('INSERT OR IGNORE INTO transcript_files (file_path, base_name) VALUES (?, ?)', [(file, os.path.splitext(os.path.basename(file))[0]) for file in current_transcript_files])
conn.commit()

# Retrieve the files from the database
cursor.execute('SELECT file_path, base_name FROM audio_files')
audio_files = cursor.fetchall()
cursor.execute('SELECT file_path, base_name FROM transcript_files')
transcript_files = cursor.fetchall()

print(f"Loaded {len(audio_files)} audio files and {len(transcript_files)} transcript files.")

audio_dict = {base: file for file, base in audio_files}
transcript_dict = {base: file for file, base in transcript_files}

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

# Store matches in the database
cursor.execute('DELETE FROM matched_pairs')
cursor.executemany('INSERT INTO matched_pairs (audio_file, transcript_file) VALUES (?, ?)', matches)
conn.commit()

print(f"Matches: {len(matches)}")
print(f"Dangling audio files: {len(dangling_audio)}")
print(f"Dangling transcript files: {len(dangling_transcripts)}")

conn.close()

