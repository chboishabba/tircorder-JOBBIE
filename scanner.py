import os
import time
import logging
from datetime import datetime
from queue import Queue
from db_worker import DBWorker, insert_known_file, insert_extension

audio_extensions = ['wav', 'flac', 'mp3', 'ogg', 'amr']
transcript_extensions = ['srt', 'txt', 'vtt', 'json', 'tsv']

def scanner(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons, db_worker):
    folders = load_recordings_folders_from_db(db_worker)  # Fetch folders from DB

    while True:
        current_files = set()
        for folder_id, directory, ignore_transcribing, ignore_converting in folders:
            for f in os.listdir(directory):
                if any(f.endswith(ext) for ext in audio_extensions + transcript_extensions):
                    current_files.add((folder_id, os.path.join(directory, f)))

        new_files = current_files - known_files
        new_files_found = len(new_files) > 0

        if new_files_found:
            for folder_id, file in new_files:
                known_files.add((folder_id, file))
                file_name, file_extension = os.path.splitext(os.path.basename(file))
                file_extension = file_extension[1:]  # Remove the dot
                datetimes = str(datetime.now())  # Or any other datetime logic you want to implement
                extension_id = insert_extension(db_worker, file_extension)

                if not ignore_transcribing:
                    transcribe_queue.put(folder_id)
                if file_extension in audio_extensions:  # Only add audio files to convert_queue
                    try:
                        insert_known_file(db_worker, file_name, folder_id, extension_id, datetimes)
                    except Exception as e:
                        logging.error(f"Error inserting known file: {e}")
        else:
            logging.info("No new files found. Sleeping...")
            time.sleep(60)  # Sleep for a while before rescanning

def load_recordings_folders_from_db(db_worker):
    query = 'SELECT id, folder_path, ignore_transcribing, ignore_converting FROM recordings_folders'
    result_queue = Queue()
    db_worker.fetch_all(query, None, result_queue)
    return result_queue.get()

