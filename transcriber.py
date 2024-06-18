import logging
import os
import sqlite3
import json
from datetime import datetime
from queue import Queue, Empty
from state import export_queues_and_files, load_state
from utils import transcribe_audio
from db_worker import DBWorker
from huggingface_hub import login, whoami
import sys
import io
import concurrent.futures

audio_extensions = ['wav', 'flac', 'mp3', 'ogg', 'amr']

# Suppress stdout and stderr during Hugging Face login
class SuppressOutput(io.StringIO):
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self
    def __exit__(self, *args):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

# Read the Hugging Face token from a file
with open('hf-token.txt', 'r') as file:
    HFTOKEN = file.read().strip()

# Log in to the Hugging Face hub
with SuppressOutput():
    login(token=HFTOKEN)

def transcriber(transcribe_queue, convert_queue, transcription_method, transcribe_active, transcription_complete, db_worker, device="cuda", compute_type="float16", hf_token=HFTOKEN):
    known_files, _, _, skip_files, skip_reasons = load_state()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    futures = []

    while True:
        try:
            known_file_id = transcribe_queue.get(timeout=5)  # Add a timeout to exit gracefully
        except Empty:
            break  # Exit the loop if the queue is empty for a while

        start_time = datetime.now()
        transcribe_active.set()

        result_queue = Queue()
        query = '''
            SELECT k.file_name, r.folder_path, e.extension 
            FROM known_files k 
            JOIN recordings_folders r ON k.folder_id = r.id 
            JOIN extensions e ON k.extension_id = e.id 
            WHERE k.id = ?
        '''
        db_worker.fetch_all(query, (known_file_id,), result_queue)
        result = result_queue.get()

        if not result:
            logging.error(f"File with known_file_id {known_file_id} not found in database.")
            transcribe_queue.task_done()
            continue

        file_name, folder_path, extension = result[0]
        file = os.path.join(folder_path, f"{file_name}.{extension}")

        if extension not in audio_extensions:
            logging.info(f"Skipping non-audio file: {file}")
            transcribe_queue.task_done()
            continue

        logging.info(f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting transcription for {file}.")

        try:
            future = executor.submit(transcribe_audio, file, device=device, compute_type=compute_type, batch_size=16, hf_token=hf_token)
            futures.append((future, known_file_id, file, start_time))
        except RuntimeError as e:
            logging.error(f"Runtime error in transcribing audio {file_name}: {e}")
            transcribe_queue.task_done()
            continue

    # Ensure all futures complete before shutting down
    for future, known_file_id, file, start_time in futures:
        try:
            transcript_json = future.result()
            if transcript_json is not None:
                output_base = os.path.splitext(file)[0]
                output_text_path = output_base + '.txt'
                output_json_path = output_base + '.json'
                with open(output_text_path, 'w') as f:
                    f.write(transcript_json['text'])
                with open(output_json_path, 'w') as f:
                    json.dump(transcript_json, f)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logging.info(f"SYSTIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | File {file} transcribed in {elapsed_time:.2f}s.")

                if extension in audio_extensions:
                    convert_queue.put(known_file_id)  # Only add audio files to convert_queue
            else:
                logging.error(f"Transcription failed for {file}.")
                skip_files.add(file)
                skip_reasons[file] = "transcription_failed"
        except Exception as e:
            logging.error(f"Error writing transcription output for {file}: {e}")
            skip_files.add(file)
            skip_reasons[file] = "transcription_output_error"
        finally:
            transcribe_queue.task_done()

    executor.shutdown(wait=True)
    transcribe_active.clear()
    transcription_complete.set()

