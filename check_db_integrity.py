import sqlite3
import os

DB_PATH = 'state.db'

def check_db_integrity():
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg', '.amr']
    transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']
    valid_extensions = audio_extensions + transcript_extensions

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all file names and extension IDs from known_files
    cursor.execute('''
        SELECT k.file_name, e.extension 
        FROM known_files k 
        LEFT JOIN extensions e ON k.extension_id = e.id
    ''')
    all_files = cursor.fetchall()
    
    invalid_files = []

    for file in all_files:
        file_name = file[0]
        db_extension = file[1]
        # Extract the actual file extension
        _, ext = os.path.splitext(file_name)
        ext = ext.lower().strip('.')
        # Check if the extension is not in the valid extensions list or does not match the db extension
        if db_extension is None or ext not in valid_extensions or ext != db_extension.lower():
            invalid_files.append((file_name, db_extension, ext))

    conn.close()

    if invalid_files:
        print("Files with invalid extensions found in the database:")
        for file in invalid_files:
            print(f"File Name: {file[0]}, DB Extension: {file[1]}, Actual Extension: {file[2]}")
        print(f"Returned {len(all_files)} files total and {len(invalid_files)} invalid files.")
    else:
        print(f"Returned {len(all_files)} files total and no invalid files found.")

if __name__ == "__main__":
    check_db_integrity()

