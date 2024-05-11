import os
import sys
from os.path import join, splitext
import threading
from threading import Thread, Event, Lock
import time
import subprocess
from queue import Queue
import logging
from collections import defaultdict
import datetime

# Globals
transcribe_queue = Queue()
convert_queue = Queue()
active_processes = []
process_status = 'housekeeping'
transcribing_lock = threading.Lock()
converting_lock = threading.Lock()
transcribing_active = threading.Event()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    stream=sys.stdout)  # This forces logs to standard output


playlists = defaultdict(list) # Playlist dictionary, mapping a date to a list of FLAC files

transcription_complete = Event()# Event to manage synchronization between transcribe and conversion

def scanner(directory, known_files, currently_processing):
    while True:
        current_files = set(os.listdir(directory))
        new_files = list(current_files - known_files)

        try:
            new_files.sort(key=lambda x: datetime.datetime.strptime(x.split('.')[0], '%Y-%m-%d_%H-%M-%S'))
        except ValueError:
            # Log the error or ignore it
            continue

        for file in new_files:
            if file.endswith(".wav"):
                datetime_str = file.split('.')[0]
                transcript_exists = any(os.path.exists(os.path.join(directory, f"{datetime_str}.{ext}")) for ext in ["txt", "srt", "vtt", "json"])
                if not transcript_exists and file not in currently_processing:
                    transcribe_queue.put(file)
                    currently_processing.add(file)  # Mark this file as currently being processed

        known_files.update(new_files)
        time.sleep(1)  # Scan every second






def transcribe(currently_processing):
    global process_status
    while True:
        file = transcribe_queue.get()
        logging.info(f"Starting transcription for {file}")
        process_status = f'transcribing {file}'
        transcribing_active.set()  # Signal that transcribing is active

        with transcribing_lock:
            input_path = join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = splitext(input_path)[0] + '.txt'
            cmd = ["whisper", input_path, "--model", "medium.en", "--language", "en", "--output_dir", output_path]

            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                logging.info(f"Transcription output for {file}: {result.stdout}")
                if result.stderr:
                    logging.error(f"Transcription errors for {file}: {result.stderr}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to transcribe {file}: {e}")
            except Exception as e:
                logging.error(f"An error occurred while transcribing {file}: {e}")

            currently_processing.remove(file)  # Remove from processing list after done
            convert_queue.put(file.replace('.wav', '.flac'))
            transcription_complete.set()  # Signal transcription completion

            transcribe_queue.task_done()

        transcribing_active.clear()  # Signal that transcribing is done

        if not transcribe_queue.qsize():
            process_status = 'housekeeping'
            logging.info("All transcription tasks completed, entering housekeeping mode.")

            




def wav2flac():
    global process_status
    while True:
        transcription_complete.wait()  # Wait for a signal that transcription is complete
        file = convert_queue.get()
        logging.info(f"Starting conversion to FLAC for {file}")

        with converting_lock:
            if not transcribing_active.is_set():  # Check if transcribing has not restarted
                process_status = f'converting {file}'
                input_path = join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
                output_path = input_path.replace('.wav', '.flac')
                
                try:
                    result = subprocess.run(["ffmpeg", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logging.info(f"Conversion output for {file}: {result.stdout.decode()}")
                    if result.stderr:
                        logging.error(f"Conversion errors for {file}: {result.stderr.decode()}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to convert {file} to FLAC: {e}")
                except Exception as e:
                    logging.error(f"An error occurred while converting {file} to FLAC: {e}")
                
                convert_queue.task_done()
                transcription_complete.clear()  # Reset event for next cycle
                if not convert_queue.qsize():
                    process_status = 'housekeeping'
                    logging.info("All conversion tasks completed, entering housekeeping mode.")
            else:
                # If transcribing has restarted, skip this conversion and put it back in the queue
                convert_queue.put(file)
                logging.warning(f"Conversion skipped for {file} as transcribing restarted.")



                


def update_playlists(directory, file):
    if file.endswith(".flac"):
        date_str = file.split('_')[0]
        playlists[date_str].append(file)




def webSlinger():
    while True:
        print("Running webSlinger")
        # Web server logic goes here
        time.sleep(10)  # Refresh every 10 seconds


def main():
    print('ran')
    directory = "/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"
    known_files = set()
    currently_processing = set()

    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(directory, known_files, currently_processing))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcribe thread...")
    transcribe_thread = threading.Thread(target=transcribe, args=(currently_processing,))
    transcribe_thread.daemon = True
    transcribe_thread.start()

    logging.info("Starting convert thread...")
    convert_thread = threading.Thread(target=wav2flac)
    convert_thread.daemon = True
    convert_thread.start()

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive.
            logging.debug("Main loop running...")
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        
if __name__ == "__main__":
    main()




