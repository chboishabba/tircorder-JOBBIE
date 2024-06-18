import sqlite3

def create_tables():
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()

    # Create recordings_folders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recordings_folders (
        id INTEGER PRIMARY KEY,
        folder_path TEXT UNIQUE NOT NULL,
        ignore_transcribing INTEGER DEFAULT 0,
        ignore_converting INTEGER DEFAULT 0
    )
    ''')

    # Create known_files table with appropriate keys
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS known_files (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL,
        folder_id INTEGER,
        extension TEXT,
        hash TEXT UNIQUE,
        datetimes TEXT,
        UNIQUE(file_name, datetimes),
        FOREIGN KEY(folder_id) REFERENCES recordings_folders(id)
    )
    ''')

    # Create transcript_files table with foreign key referencing known_files
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcript_files (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        unix_timestamp INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    # Create audio_files table with foreign key referencing known_files
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audio_files (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        unix_timestamp INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    # Create other tables using known_file_id instead of file_name
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcribe_queue (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS convert_queue (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skip_files (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        reason TEXT,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matched_pairs (
        id INTEGER PRIMARY KEY,
        audio_file_id INTEGER,
        transcript_file_id INTEGER,
        FOREIGN KEY(audio_file_id) REFERENCES audio_files(id),
        FOREIGN KEY(transcript_file_id) REFERENCES transcript_files(id)
    )
    ''')

    # Ensure the checked_files table exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS checked_files (
        id INTEGER PRIMARY KEY,
        known_file_id INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()

