import os
import re
import sqlite3
import logging
from datetime import datetime

# Database setup
db_path = 'state.db'

def match_audio_transcripts():
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def load_recordings_folders():
        cursor.execute('SELECT id, folder_path FROM recordings_folders')
        return cursor.fetchall()

    def get_all_files(folders, extensions):
        files = []
        for folder_id, folder in folders:
            if os.path.exists(folder):
                for root, _, file_names in os.walk(folder):
                    for file_name in file_names:
                        if any(file_name.lower().endswith(ext) for ext in extensions):
                            files.append((folder_id, os.path.join(root, file_name)))
        return files

    def extract_date(filename):
        match = re.search(r'\d{8}-\d{6}', filename)
        if match:
            return datetime.strptime(match.group(), '%Y%m%d-%H%M%S')
        else:
            return datetime.fromtimestamp(os.path.getctime(filename))

    # Load the recordings folders
    recordings_folders = load_recordings_folders()

    if not recordings_folders:
        print("No directories loaded from the database.")
        conn.close()
        return

    # Get the current state of files
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg', '.amr']
    transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']
    current_audio_files = get_all_files(recordings_folders, audio_extensions)
    current_transcript_files = get_all_files(recordings_folders, transcript_extensions)

    # Store current state of files in the database
    for folder_id, file_path in current_audio_files:
        base_name = os.path.basename(file_path)
        cursor.execute('INSERT OR IGNORE INTO known_files (file_name, folder_id) VALUES (?, ?)', (base_name, folder_id))
        cursor.execute('INSERT OR IGNORE INTO audio_files (known_file_id, unix_timestamp) VALUES ((SELECT id FROM known_files WHERE file_name = ? AND folder_id = ?), ?)', (base_name, folder_id, int(os.path.getmtime(file_path))))
    
    for folder_id, file_path in current_transcript_files:
        base_name = os.path.basename(file_path)
        cursor.execute('INSERT OR IGNORE INTO known_files (file_name, folder_id) VALUES (?, ?)', (base_name, folder_id))
        cursor.execute('INSERT OR IGNORE INTO transcript_files (known_file_id, unix_timestamp) VALUES ((SELECT id FROM known_files WHERE file_name = ? AND folder_id = ?), ?)', (base_name, folder_id, int(os.path.getmtime(file_path))))
    
    conn.commit()

    # Retrieve the files from the database
    cursor.execute('SELECT k.id, k.file_name FROM known_files k JOIN audio_files a ON k.id = a.known_file_id')
    audio_files = cursor.fetchall()
    cursor.execute('SELECT k.id, k.file_name FROM known_files k JOIN transcript_files t ON k.id = t.known_file_id')
    transcript_files = cursor.fetchall()

    print(f"Loaded {len(audio_files)} audio files and {len(transcript_files)} transcript files.")

    audio_dict = {file_id: file_name for file_id, file_name in audio_files}
    transcript_dict = {file_id: file_name for file_id, file_name in transcript_files}

    matches = []
    dangling_audio = []
    dangling_transcripts = []

    for audio_id, audio_base in audio_dict.items():
        transcript_id = next((id for id, base in transcript_dict.items() if base == audio_base), None)
        if transcript_id:
            matches.append((audio_id, transcript_id))
        else:
            dangling_audio.append(audio_id)

    for transcript_id, transcript_base in transcript_dict.items():
        if transcript_id not in [match[1] for match in matches]:
            dangling_transcripts.append(transcript_id)

    # Sort matches using extract_date
    matches.sort(key=lambda x: extract_date(audio_dict[x[0]]))

    # Store matches in the database
    cursor.execute('DELETE FROM matched_pairs')
    cursor.executemany('INSERT INTO matched_pairs (audio_file_id, transcript_file_id) VALUES (?, ?)', matches)
    conn.commit()

    print(f"Matches: {len(matches)}")
    print(f"Dangling audio files: {len(dangling_audio)}")
    print(f"Dangling transcript files: {len(dangling_transcripts)}")

    conn.close()

if __name__ == "__main__":
    try:
        match_audio_transcripts()
    except Exception as e:
        logging.error(f"Error in match_audio_transcripts: {e}")

