import logging
import os
import sqlite3
from datetime import datetime, timedelta
from queue import Queue
from .state import export_queues_and_files, load_state
from .utils import transcribe_audio, transcribe_ct2, transcribe_ct2_nonpythonic

audio_extensions = ['.wav', '.flac', '.mp3', '.ogg', '.amr']

def transcriber(TRANSCRIBE_QUEUE, CONVERT_QUEUE, transcription_method, TRANSCRIBE_ACTIVE, transcription_complete, model):
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()
    proc_comp_timestamps_transcribe = []

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
        known_file_id = TRANSCRIBE_QUEUE.get()
        start_time = datetime.now()
        TRANSCRIBE_ACTIVE.set()

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

        if not file_name.endswith(tuple(audio_extensions)):
            logging.info(f"Skipping non-audio file: {file}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting transcription for {file}.")

        output_text = None
        audio_duration = 0

        if transcription_method == 'python_whisper':
            output_text = transcribe_audio(file)
        elif transcription_method == 'ctranslate2':
            output_text, audio_duration = transcribe_ct2(file, model, skip_files)
        elif transcription_method == 'ctranslate2_nonpythonic':
            output_text, audio_duration = transcribe_ct2_nonpythonic(file)
        else:
            logging.error(f"Unsupported transcription method: {transcription_method}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(f"Processing audio with duration {audio_duration:.3f}s")

        if output_text is not None:
            output_path = os.path.splitext(file)[0] + '.txt'
            try:
                with open(output_path, 'w') as f:
                    f.write(output_text)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                real_time_factor = audio_duration / elapsed_time if elapsed_time > 0 else 0
                proc_comp_timestamps_transcribe.append(datetime.now())
                logging.info(f"SYSTIME: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | File {file} transcribed in {elapsed_time:.2f}s (x{real_time_factor:.2f}).")
                TRANSCRIBE_QUEUE.task_done()
            except Exception as e:
                logging.error(f"Error writing transcription output for {file}: {e}")
                skip_files.add(file)
                skip_reasons[file] = "transcription_output_error"
                execute_with_retry('INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)', (known_file_id, "transcription_output_error"))
                TRANSCRIBE_QUEUE.task_done()
                continue
        else:
            logging.error(f"Transcription failed for {file}.")
            skip_files.add(file)
            skip_reasons[file] = "transcription_failed"
            execute_with_retry('INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)', (known_file_id, "transcription_failed"))
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(f"SYSTIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | File {file} added to conversion queue. {CONVERT_QUEUE.qsize() + 1} files waiting for conversion. {TRANSCRIBE_QUEUE.qsize()} left to transcribe. Processing rates: {len(proc_comp_timestamps_transcribe) / (timedelta(seconds=len(proc_comp_timestamps_transcribe)).total_seconds() / 60):.2f} files/hour, {len(proc_comp_timestamps_transcribe) / (timedelta(seconds=len(proc_comp_timestamps_transcribe)).total_seconds() / 60):.2f} files/minute.")
        execute_with_retry('INSERT INTO convert_queue (known_file_id) VALUES (?)', (known_file_id,))
        CONVERT_QUEUE.put(known_file_id)
        if TRANSCRIBE_QUEUE.qsize() == 0:
            logging.info("All transcription tasks completed, entering housekeeping mode.")
            transcription_complete.set()
            TRANSCRIBE_ACTIVE.clear()

