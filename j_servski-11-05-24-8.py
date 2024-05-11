import os
import sys
import signal
from os.path import join, splitext
import threading
from threading import Thread, Event, Lock
import time
import subprocess
from queue import Queue
import logging
from collections import defaultdict
import datetime
import whisper
import numpy as np
import torch
#from whisper_ctranslate2 import WhisperTranslator


# Globals
# Choose transcription method: 'python_whisper' or 'ctranslate2'
transcription_method = 'python_whisper'
torch.set_num_threads(6)


known_files = set()
transcribe_queue = Queue()
convert_queue = Queue()
skip_files = set()
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



# Load the model once and keep it in memory
model = whisper.load_model("medium.en", device="cpu")
#translator = WhisperTranslator.from_whisper_model(model, device="cpu")  # You can specify "cuda" or "cpu" depending on your setup # Convert Whisper model to CTranslate2

import os

def transcribe_audio(file_path):
    """
    Transcribes the audio using the Whisper model.
    :param file_path: Path to the audio file (wav format expected)
    :return: The transcribed text
    """
    try:
        # Load and preprocess the audio
        audio = whisper.load_audio(file_path)

        # Generate Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # Decode the audio
        options = whisper.DecodingOptions()
        result = model.decode(mel, options)

        logging.info("Transcription completed successfully.")
        return result.text
    except Exception as e:
        filename = os.path.basename(file_path)
        logging.error(f"Error in transcribing audio {filename}: {e}")
        
        return None





def scanner(directory, known_files, currently_processing, file_groups):
    while True:
        try:
            current_files = set(os.listdir(directory))
            logging.debug(f"Scanned files: {len(current_files)}")
            new_files = list(current_files - known_files)

            # Update file groups and filter valid files
            valid_files = []
            for file in new_files:
                if file not in skip_files:
                    prefix, extension = os.path.splitext(file)
                    try:
                        # Validate file timestamp format
                        datetime.datetime.strptime(prefix, '%Y-%m-%d_%H-%M-%S')
                        # Add to file groups
                        if prefix not in file_groups or extension not in file_groups[prefix]:
                            file_groups[prefix].append(extension)
                        # Filter valid files for further processing
                        valid_files.append(file)
                    except ValueError:
                        logging.error(f"Filename {file} does not match the expected format and will be ignored.")
                        skip_files.add(file)
                else:
                    logging.info(f"File {file} is skipped as it's in the skip list.")

            for file in valid_files:
                if file.endswith(".wav"):
                    if file not in currently_processing:
                        logging.info(f"Adding {file} to transcription queue")
                        transcribe_queue.put(file)
                        currently_processing.add(file)  # Mark this file as currently being processed
                        logging.info(f"File {file} added to processing queue")

            known_files.update(new_files)

        except Exception as e:
            logging.error(f"An error occurred in the scanner function: {e}")

        time.sleep(5)  # Scan every 5 seconds




def transcribe_ct2(input_path):
    output_path = splitext(input_path)[0] + '.txt'
    cmd = ["whisper-ctranslate2", input_path, "--model", "medium.en", "--language", "en", "--output_dir", output_path, "--device", "cpu"]

    try:
        # Using Popen to allow streaming output
        output_text = []
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1) as proc:
            for line in proc.stdout:
                output_text.append(line)
            if proc.stderr:
                for err_line in proc.stderr:
                
                    logging.error(f"Transcription errors: {err_line.strip()}")

        proc.wait()  # Wait for the subprocess to finish
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
        return ''.join(output_text)

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to transcribe {input_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"An error occurred while transcribing {input_path}: {e}")
        return None


#faster but less programmatically accessible than the direct python whisper implementation
def transcribe_ct2_old(currently_processing):
    global process_status, transcribe_queue, convert_queue, transcribing_active, transcribing_lock, transcription_complete

    while True:
        file = transcribe_queue.get()
        logging.info(f"Starting transcription for {file} ({len(transcribe_queue)} remaining)")
        process_status = f'transcribing {file}'
        transcribing_active.set()  # Signal that transcribing is active

        with transcribing_lock:
            input_path = join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = splitext(input_path)[0] + '.txt'
            cmd = ["whisper-ctranslate2", input_path, "--model", "medium.en", "--language", "en", "--output_dir", output_path, "--device", "cpu"]

            try:
                # Using Popen to allow streaming output
                with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1) as proc:
                    for line in proc.stdout:
                        print(line, end='')  # Print to stdout in real-time
                        logging.info(f"Transcription output: {line.strip()}")  # Log the output
                    if proc.stderr:
                        for err_line in proc.stderr:
                            logging.error(f"Transcription errors: {err_line.strip()}")

                proc.wait()  # Wait for the subprocess to finish
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode, cmd)

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



def transcribe(currently_processing):
    global process_status, transcribe_queue, convert_queue, transcribing_active, transcribing_lock, transcription_complete, transcription_method

    while True:
        file = transcribe_queue.get()
        logging.info(f"Starting transcription for {file}. {transcribe_queue.qsize()} files remaining in transcription queue.")
        process_status = f'transcribing {file}'
        transcribing_active.set()  # Signal that transcribing is active

        with transcribing_lock:
            input_path = join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            if transcription_method == 'python_whisper':
                output_text = transcribe_audio(input_path)
            else:
                output_text = transcribe_ct2(input_path)

            if output_text is not None:
                output_path = splitext(input_path)[0] + '.txt'
                with open(output_path, 'w') as f:
                    f.write(output_text)
                logging.info(f"Transcription completed and saved for {file}.")
            else:
                logging.error(f"Transcription failed for {file}.")
                skip_files.add(file)  # Only add the filename, not the full path
                logging.error(f"Skip list now {len(skip_files)} long.")

            currently_processing.remove(file)  # Remove from processing list after done
            convert_queue.put(file)
            logging.info(f"File {file} added to conversion queue. {convert_queue.qsize()} files waiting for conversion.")
            transcription_complete.set()  # Signal transcription completion
            transcribe_queue.task_done()

        transcribing_active.clear()  # Signal that transcribing is done

        if not transcribe_queue.qsize():
            process_status = 'housekeeping'
            logging.info("All transcription tasks completed, entering housekeeping mode.")





            




def wav2flac():
    global process_status, converting_lock, transcribing_active, transcription_complete
    while True:
        transcription_complete.wait()  # Wait for a signal that transcription is complete
        file = convert_queue.get()
        attempts = 0

        while transcribing_active.is_set() and attempts < 5:  # Check if transcribing is active and limit retries
            logging.warning(f"Waiting to convert {file} as transcribing is active. Attempt {attempts+1}/5")
            time.sleep(10)  # Wait for 1 second before retrying
            attempts += 1

        if attempts == 5:
            logging.error(f"Conversion skipped for {file} after 5 attempts as transcribing is still active.")
            convert_queue.put(file)  # Re-enqueue file for later attempt
            continue

        with converting_lock:
            process_status = f'converting {file}'
            input_path = join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = input_path.replace('.wav', '.flac')
            
            try:
                result = subprocess.run(["ffmpeg", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info(f"Conversion completed for {file}.")
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






                


def update_playlists(directory, file):
    if file.endswith(".flac"):
        date_str = file.split('_')[0]
        playlists[date_str].append(file)
        logging.info(f"Updated playlists for {date_str}: {playlists[date_str]}")





def webSlinger():
    while True:
        print("Running webSlinger")
        # Web server logic goes here
        time.sleep(10)  # Refresh every 10 seconds
        


def handle_shutdown_signal(signum, frame):
    logging.info("Shutdown signal received. Exporting queues, known files, and skip files...")
    export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files)
    sys.exit(0)


# Setup signal handlers to ensure the export function is called on shutdown
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)



def export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files):
    import json
    from queue import SimpleQueue

    output = {
        "known_files": list(known_files),
        "transcribe_queue": [],
        "convert_queue": [],
        "skip_files": list(skip_files)
    }

    # Drain and restore the queues as in the previous example
    # ... similar code for draining and restoring queues ...

    # Write to file
    with open("queues_and_files_state.json", "w") as f:
        json.dump(output, f, indent=4)

    logging.info("Queues, known files, and skip files state has been exported to 'queues_and_files_state.json'")




def main():
    print('ran')
    directory = "/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"
    known_files = set()
    currently_processing = set()
    file_groups = defaultdict(list)  # Initialize file_groups

    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(directory, known_files, currently_processing, file_groups))
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
            time.sleep(5)  # Keep the main thread alive.
            logging.debug("Main loop running...")
            logging.debug(f"Transcribing Active: {transcribing_active.is_set()}")
            logging.debug(f"Transcription Queue Size: {transcribe_queue.qsize()}")
            logging.debug(f"Conversion Queue Size: {convert_queue.qsize()}")

    except KeyboardInterrupt:
        logging.info("Shutting down...")
        
if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    main()




