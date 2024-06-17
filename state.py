import sqlite3
import logging
from queue import Queue

DB_PATH = 'state.db'

def export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons):
    logging.debug("in state.py export_queues_and_files()")
    logging.debug(f"exporting lengths: known_files={len(known_files)}, transcribe_queue={transcribe_queue.qsize()}, convert_queue={convert_queue.qsize()}, skip_files={len(skip_files)}, skip_reasons={len(skip_reasons)}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM known_files')
        cursor.execute('DELETE FROM transcribe_queue')
        cursor.execute('DELETE FROM convert_queue')
        cursor.execute('DELETE FROM skip_files')

        cursor.executemany('INSERT INTO known_files (file_name) VALUES (?)', [(f,) for f in known_files])
        cursor.executemany('INSERT INTO transcribe_queue (file_name) VALUES (?)', [(f,) for f in list(transcribe_queue.queue)])
        cursor.executemany('INSERT INTO convert_queue (file_name) VALUES (?)', [(f,) for f in list(convert_queue.queue)])
        cursor.executemany('INSERT INTO skip_files (file_name, reason) VALUES (?, ?)', [(f, skip_reasons[f]) for f in skip_files])

        conn.commit()
    except Exception as e:
        logging.error(f"Error during database operation: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    logging.info("State of queues, files, and skip reasons has been saved.")

def load_state():
    logging.debug("in state.py load_state()")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT file_name FROM known_files')
    known_files = set(row[0] for row in cursor.fetchall())

    cursor.execute('SELECT file_name FROM transcribe_queue')
    transcribe_queue = Queue()
    for row in cursor.fetchall():
        transcribe_queue.put(row[0])

    cursor.execute('SELECT file_name FROM convert_queue')
    convert_queue = Queue()
    for row in cursor.fetchall():
        convert_queue.put(row[0])

    cursor.execute('SELECT file_name FROM skip_files')
    skip_files = set(row[0] for row in cursor.fetchall())

    cursor.execute('SELECT file_name, reason FROM skip_files')
    skip_reasons = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    logging.debug(f"loading lengths: known_files={len(known_files)}, transcribe_queue={transcribe_queue.qsize()}, convert_queue={convert_queue.qsize()}, skip_files={len(skip_files)}, skip_reasons={len(skip_reasons)}")
    return known_files, transcribe_queue, convert_queue, skip_files, skip_reasons

