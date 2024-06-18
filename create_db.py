import sqlite3
import os
import stat

def create_tables():
    db_path = 'state.db'

    # Check if the current directory is writable
    if not os.access(os.getcwd(), os.W_OK):
        raise PermissionError("Current directory is not writable. Check permissions.")

    # Handle existing read-only database file, if necessary
    if os.path.exists(db_path):
        if not os.access(db_path, os.W_OK):
            try:
                # Try to change the file permissions to read-write
                os.chmod(db_path, stat.S_IWUSR | stat.S_IRUSR)
            except PermissionError as e:
                # If changing permissions fails, remove the read-only file
                try:
                    os.remove(db_path)
                    print(f"Removed read-only database file: {db_path}")
                except PermissionError as e:
                    raise PermissionError(f"Failed to change permissions or remove {db_path}: {e}")

    # Connect to the database (it will create the file if it does not exist)
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.OperationalError as e:
        raise sqlite3.OperationalError(f"Failed to create or connect to the database at {db_path}: {e}")

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
        extension_id INTEGER,
        datetimes TEXT,
        UNIQUE(file_name, datetimes),
        FOREIGN KEY(folder_id) REFERENCES recordings_folders(id),
        FOREIGN KEY(extension_id) REFERENCES extensions(id)
    )
    ''')

    # Create extensions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS extensions (
        id INTEGER PRIMARY KEY,
        extension TEXT UNIQUE NOT NULL
    )
    ''')

    # Create file_extensions table (optional, if needed)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_extensions (
        known_file_id INTEGER,
        extension_id INTEGER,
        FOREIGN KEY(known_file_id) REFERENCES known_files(id),
        FOREIGN KEY(extension_id) REFERENCES extensions(id),
        UNIQUE(known_file_id, extension_id)
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
    CREATE TABLE IF NOT EXISTS skip_reasons (
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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()

