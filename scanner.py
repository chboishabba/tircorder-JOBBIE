import os
import time
import logging
from queue import Queue
from os.path import join
from state import export_queues_and_files, load_state

def scanner(directory, known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, checked_files, skip_reasons):
    audio_extensions = ['.wav', '.flac']
    subtitle_extensions = ['.vtt', '.srt', '.txt', '.json']
    no_new_files_counter = 0

    while True:
        try:
            logging.info("Ran scanner:")
            current_files = set(os.listdir(directory))
            new_files = list(current_files - known_files)
            new_files.sort(reverse=True)  # Sort files from most recent to oldest

            logging.info(f"New files found: {len(new_files)}")

            if not new_files:
                no_new_files_counter += 1
                if no_new_files_counter >= 2:
                    export_queues_and_files(known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons)
                    no_new_files_counter = 0
            else:
                no_new_files_counter = 0

            for file in new_files:
                if file in checked_files:
                    logging.info(f"Skipping traversal on {file}: Reason 0 - File already checked.")
                    continue

                prefix, extension = os.path.splitext(file)
                if extension in audio_extensions:
                    transcripts_exist = any(os.path.exists(join(directory, prefix + ext)) for ext in subtitle_extensions)
                    if transcripts_exist:
                        logging.debug(f"Skipping transcription on {file}: Reason 1 - Transcript file already exists.")
                        checked_files.add(file)
                        CONVERT_QUEUE.put(join(directory, file))
                        continue

                    TRANSCRIBE_QUEUE.put(join(directory, file))
                    logging.info(f"File {file} added to transcription queue")

                checked_files.add(file)
                known_files.add(file)

            logging.info(f"Checked files: {len(checked_files)}")
            logging.info(f"Known files: {len(known_files)}")

        except Exception as e:
            logging.error(f"An error occurred in the scanner function: {e}")
        time.sleep(5)

