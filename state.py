import os
import pickle
import logging
import sqlite3
import time
from queue import Queue

DB_PATH = 'state.db'

def wrapper(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner

def export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons):
    state = {
        "known_files": known_files,
        "transcribe_queue": list(transcribe_queue.queue),
        "convert_queue": list(convert_queue.queue),
        "skip_files": skip_files,
        "skip_reasons": skip_reasons
    }
    with open("state.pkl", "wb") as f:
        pickle.dump(state, f)
    logging.info("State exported successfully.")

@wrapper
def load_state():
    known_files = set()
    transcribe_queue = Queue()
    convert_queue = Queue()
    skip_files = set()
    skip_reasons = {}

    # Load from the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load known files
    cursor.execute('SELECT file_name FROM known_files')
    known_files = set(row[0] for row in cursor.fetchall())

    # Load transcribe queue
    cursor.execute('SELECT known_file_id FROM transcribe_queue')
    for row in cursor.fetchall():
        transcribe_queue.put(row[0])

    # Load convert queue
    cursor.execute('SELECT known_file_id FROM convert_queue')
    convert_queue_results = cursor.fetchall()
    for row in convert_queue_results:
        if row:  # Ensure the row is not None
            convert_queue.put(row[0])

    # Load skip files
    cursor.execute('SELECT known_file_id FROM skip_files')
    skip_files = set(row[0] for row in cursor.fetchall())

    # Load skip reasons
    cursor.execute('SELECT known_file_id, reason FROM skip_reasons')
    skip_reasons = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return known_files, transcribe_queue, convert_queue, skip_files, skip_reasons

