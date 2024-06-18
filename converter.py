import logging
import os
from queue import Queue
from utils import wav2flac as convert_audio
from db_worker import DBWorker

audio_extensions = ['wav', 'flac', 'mp3', 'ogg', 'amr']

def is_audio_file(file_path):
    _, ext = os.path.splitext(file_path)
    return ext[1:].lower() in audio_extensions

def is_skip_file(db_worker, known_file_id):
    query = 'SELECT EXISTS(SELECT 1 FROM skip_files WHERE known_file_id=?)'
    result_queue = Queue()
    db_worker.fetch_all(query, (known_file_id,), result_queue)
    result = result_queue.get()
    if isinstance(result, Exception):
        logging.error(f"Error checking skip file: {result}")
        return False
    return result[0][0] == 1

def converter(convert_queue, db_worker):
    while True:
        known_file_id = convert_queue.get()

        # Check if the file is in the skip_files table
        if is_skip_file(db_worker, known_file_id):
            logging.info(f"Skipping file with known_file_id {known_file_id} as it is marked to be skipped.")
            convert_queue.task_done()
            continue

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
            convert_queue.task_done()
            continue

        file_name, folder_path, extension = result[0]
        input_file = os.path.join(folder_path, f"{file_name}.{extension}")
        output_file = os.path.join(folder_path, f"{file_name}.flac")

        if not os.path.exists(input_file):
            logging.error(f"File {input_file} does not exist.")
            convert_queue.task_done()
            continue

        if not is_audio_file(input_file):
            logging.info(f"Skipping non-audio file: {input_file}")
            convert_queue.task_done()
            continue

        logging.info(f"Starting conversion for {input_file}.")

        try:
            convert_audio(input_file, output_file)
            logging.info(f"File {input_file} conversion completed successfully.")
        except Exception as e:
            logging.error(f"Error converting file {input_file}: {e}")
        finally:
            convert_queue.task_done()

if __name__ == "__main__":
    convert_queue = Queue()
    db_worker = DBWorker()
    db_worker.start()
    converter(convert_queue, db_worker)
    db_worker.stop()
    db_worker.join()

