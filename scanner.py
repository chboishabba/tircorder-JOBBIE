import os
import time
import logging
import sqlite3
from queue import Queue
from os.path import join
from state import export_queues_and_files, load_state
from rate_limit import RateLimiter

def scanner(known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, checked_files, skip_files, skip_reasons):
    def load_recordings_folders_from_db():
        conn = sqlite3.connect('state.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, folder_path, ignore_transcribing, ignore_converting FROM recordings_folders')
        folders = cursor.fetchall()
        conn.close()
        return folders

    def execute_with_retry(query, params=(), retries=5, delay=1):
        attempt = 0
        while attempt < retries:
            try:
                conn = sqlite3.connect('state.db')
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                logging.debug(f"In scanner(): Successfully executed query after {attempt + 1} attempts.")
                return
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    logging.debug(f"In scanner(): Database is locked, retrying in {delay} seconds... (attempt {attempt + 1})")
                    time.sleep(delay)
                    attempt += 1
                else:
                    logging.error(f"In scanner(): Failed to execute query: {e}")
                    raise
            finally:
                conn.close()
        logging.error(f"In scanner(): Failed to execute query after {retries} attempts: {query}")
        raise sqlite3.OperationalError("In scanner(): Database is locked and retries exhausted")

    directories = load_recordings_folders_from_db()

    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg', '.amr']
    transcript_extensions = ['.srt', '.txt', '.vtt', '.json', '.tsv']
    rate_limiter = RateLimiter()

    while True:
        try:
            logging.info("Ran scanner:")
            logging.info(f"Scanning: {len(directories)} directories.")
            current_files = set()
            for folder_id, directory, ignore_transcribing, ignore_converting in directories:
                logging.debug(f"Scanning: {directory}")
                try:
                    for f in os.listdir(directory):
                        if any(f.endswith(ext) for ext in audio_extensions + transcript_extensions):
                            current_files.add((folder_id, join(directory, f)))
                except FileNotFoundError as e:
                    logging.error(f"Directory not found: {directory}, error: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error reading directory: {directory}, error: {e}")
                    continue

            new_files = list(current_files - known_files)
            new_files.sort(reverse=True)  # Sort files from most recent to oldest

            logging.info(f"New files found: {len(new_files)}")

            if not new_files:
                rate_limiter.increment()
                rate_limiter.sleep()
            else:
                rate_limiter.reset()

            batch_size = 100
            for i in range(0, len(new_files), batch_size):
                batch = new_files[i:i + batch_size]
                try:
                    conn = sqlite3.connect('state.db')
                    cursor = conn.cursor()

                    for folder_id, file in batch:
                        if file in checked_files:
                            logging.debug(f"Skipping traversal on {file}: Reason 0 - File already checked.")
                            continue

                        prefix, extension = os.path.splitext(file)
                        if extension in audio_extensions:
                            transcripts_exist = any(os.path.exists(join(os.path.dirname(file), prefix + ext)) for ext in transcript_extensions)
                            if transcripts_exist:
                                logging.debug(f"Skipping transcription on {file}: Reason 1 - Transcript file already exists.")
                                checked_files.add(file)
                                continue

                            if not ignore_transcribing:
                                TRANSCRIBE_QUEUE.put(folder_id)
                                logging.info(f"File {file} added to transcription queue")

                        # Check if the FLAC file already exists before adding to the conversion queue
                        if extension == '.wav' and not os.path.exists(join(os.path.dirname(file), prefix + '.flac')):
                            if not ignore_converting:
                                CONVERT_QUEUE.put(folder_id)
                                logging.info(f"File {file} added to conversion queue")

                        checked_files.add(file)
                        known_files.add((folder_id, file))

                        cursor.execute('INSERT OR IGNORE INTO known_files (file_name, folder_id, extension) VALUES (?, ?, ?)', (os.path.basename(file), folder_id, extension))
                        
                        if extension in audio_extensions:
                            cursor.execute('INSERT OR IGNORE INTO audio_files (known_file_id, unix_timestamp) VALUES ((SELECT id FROM known_files WHERE file_name = ? AND folder_id = ?), ?)', (os.path.basename(file), folder_id, int(os.path.getmtime(file))))
                        if extension in transcript_extensions:
                            cursor.execute('INSERT OR IGNORE INTO transcript_files (known_file_id, unix_timestamp) VALUES ((SELECT id FROM known_files WHERE file_name = ? AND folder_id = ?), ?)', (os.path.basename(file), folder_id, int(os.path.getmtime(file))))

                    conn.commit()
                except sqlite3.OperationalError as e:
                    logging.error(f"Database operation error: {e}")
                    conn.rollback()
                except Exception as e:
                    logging.error(f"Error processing batch: {e}")
                finally:
                    conn.close()

            logging.info(f"Checked files: {len(checked_files)}")
            logging.info(f"Known files: {len(known_files)}")

        except Exception as e:
            logging.error(f"An error occurred in the scanner function: {e}")


