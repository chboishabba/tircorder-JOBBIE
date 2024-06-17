import os
import logging
import subprocess
import time
from os.path import join
from state import export_queues_and_files, load_state

def wav2flac(CONVERT_QUEUE, converting_lock, transcribing_active, transcription_complete):
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()

    while True:
        transcription_complete.wait()
        transcription_complete.clear()
        
        if CONVERT_QUEUE.qsize() == 0:
            logging.debug("No conversion tasks in the queue.")
            continue

        while not transcribing_active.is_set() and CONVERT_QUEUE.qsize() > 0:
            file = CONVERT_QUEUE.get()
            attempts = 0

            while transcribing_active.is_set() and attempts < 5:
                logging.warning(f"Waiting to convert {file} as transcribing is active. Attempt {attempts+1}/5")
                time.sleep(10)
                attempts += 1

            if attempts == 5:
                logging.error(f"Conversion skipped for {file} after 5 attempts as transcribing is still active.")
                CONVERT_QUEUE.put(file)
                continue

            with converting_lock:
                process_status = f'converting {file}'
                input_path = join("/mnt/smbshare/Y/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
                output_path = input_path.replace('.wav', '.flac')
                
                try:
                    result = subprocess.run(["ffmpeg", "-n", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logging.info(f"Conversion completed for {file}.")
                    if result.stderr:
                        logging.info(f"ffmpeg output for {file}: {result.stderr.decode()}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to convert {file} to FLAC: {e}")
                except Exception as e:
                    logging.error(f"An error occurred while converting {file} to FLAC: {e}")

                CONVERT_QUEUE.task_done()
                transcription_complete.clear()
                if not CONVERT_QUEUE.qsize():
                    process_status = 'housekeeping'
                    logging.info("All conversion tasks completed, entering housekeeping mode.")

