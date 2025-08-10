import logging
import os
import sqlite3
from datetime import datetime, timedelta
from queue import Queue
from .state import export_queues_and_files, load_state
from .utils import wav2flac

audio_extensions = ['.wav', '.flac', '.mp3', '.ogg', '.amr']

def converter(CONVERT_QUEUE, TRANSCRIBE_ACTIVE):
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()
    proc_comp_timestamps_convert = []

    def execute_with_retry(query, params=(), retries=5, delay=1):
        conn = sqlite3.connect('state.db')
        cursor = conn.cursor()
        for attempt in range(retries):
            try:
                cursor.execute(query, params)
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    logging.warning(f"Database is locked, retrying in {delay} seconds... (attempt {attempt + 1})")
                    time.sleep(delay)
                else:
                    raise
            finally:
                conn.close()
        logging.error(f"Failed to execute query after {retries} attempts: {query}")
        raise sqlite3.OperationalError("Database is locked and retries exhausted")

    while True:
        known_file_id = CONVERT_QUEUE.get()
        start_time = datetime.now()

        conn = sqlite3.connect('state.db')
        cursor = conn.cursor()
        cursor.execute('SELECT k.file_name, r.folder_path FROM known_files k JOIN recordings_folders r ON k.folder_id = r.id WHERE k.id = ?', (known_file_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            logging.error(f"File with known_file_id {known_file_id} not found in database.")
            continue

        file_name, folder_path = result
        file = os.path.join(folder_path, file_name)

        if not file_name.endswith('.wav'):
            logging.info(f"Skipping non-WAV file: {file}")
            CONVERT_QUEUE.task_done()
            continue

        logging.info(f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting conversion for {file}.")

        output_file = os.path.splitext(file)[0] + '.flac'
        try:
            convert_to_flac(file, output_file)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            proc_comp_timestamps_convert.append(datetime.now())
            logging.info(f"SYSTIME: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | File {file} converted in {elapsed_time:.2f}s.")
            execute_with_retry('INSERT OR IGNORE INTO audio_files (known_file_id, unix_timestamp) VALUES (?, ?)', (known_file_id, int(os.path.getmtime(output_file))))
            CONVERT_QUEUE.task_done()
        except Exception as e:
            logging.error(f"Error converting file {file}: {e}")
            skip_files.add(file)
            skip_reasons[file] = "conversion_failed"
            execute_with_retry('INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)', (known_file_id, "conversion_failed"))
            CONVERT_QUEUE.task_done()
            continue

