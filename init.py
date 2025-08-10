import os
import sqlite3
import subprocess
import logging
import signal
import sys
from tircorder.state import export_queues_and_files, load_state

DB_PATH = 'state.db'

def check_and_create_db():
    if not os.path.exists(DB_PATH):
        subprocess.run(['python', 'create_db.py'])
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(recordings_folders)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'ignore_transcribing' not in columns:
            cursor.execute("ALTER TABLE recordings_folders ADD COLUMN ignore_transcribing INTEGER DEFAULT 0")
        if 'ignore_converting' not in columns:
            cursor.execute("ALTER TABLE recordings_folders ADD COLUMN ignore_converting INTEGER DEFAULT 0")

        cursor.execute("PRAGMA table_info(audio_files)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'file_path' not in columns:
            cursor.execute("ALTER TABLE audio_files ADD COLUMN file_path TEXT DEFAULT ''")

        cursor.execute("PRAGMA table_info(known_files)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'extension' not in columns:
            cursor.execute("ALTER TABLE known_files ADD COLUMN extension TEXT")

        cursor.execute("PRAGMA table_info(checked_files)")
        if not cursor.fetchall():
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS checked_files (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL
            )
            ''')

        conn.commit()
        conn.close()

def get_folders_from_user():
    print("No directories loaded from the database.")
    print("You can input folder paths as a CSV list, newline separated, or one at a time.")
    
    folder_list = []
    while True:
        folders = input("Enter folder paths (leave blank to finish): ").strip()
        if not folders:
            break
        if ',' in folders:
            folder_list.extend([folder.strip() for folder in folders.split(',')])
        elif '\n' in folders:
            folder_list.extend([folder.strip() for folder in folders.split('\n')])
        else:
            folder_list.append(folders.strip())

    if not folder_list:
        print("No directories provided. Exiting...")
        exit(1)

    return folder_list

def save_folders_to_db(folders):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany('INSERT OR IGNORE INTO recordings_folders (folder_path) VALUES (?)', [(d,) for d in folders])
    conn.commit()
    conn.close()

def prompt_ignore_flags(folders):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for folder in folders:
        ignore_transcribing = input(f"Ignore transcribing for {folder}? (y/N): ").strip().lower() == 'y'
        ignore_converting = input(f"Ignore converting for {folder}? (y/N): ").strip().lower() == 'y'
        cursor.execute('UPDATE recordings_folders SET ignore_transcribing = ?, ignore_converting = ? WHERE folder_path = ?',
                       (ignore_transcribing, ignore_converting, folder))
    
    conn.commit()
    conn.close()

def handle_shutdown_signal(signum, frame):
    logging.info("Shutdown signal received. Exporting queues, known files, and skip files...")
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()
    export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons)
    logging.info("State of queues, files, and skip reasons has been saved.")
    sys.exit(0)

def init():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    check_and_create_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT folder_path FROM recordings_folders')
    folders = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not folders:
        folders = get_folders_from_user()
        save_folders_to_db(folders)
        prompt_ignore_flags(folders)

    subprocess.run(['python', 'main.py'])

if __name__ == "__main__":
    init()

