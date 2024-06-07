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
import json
#from whisper_ctranslate2 import WhisperTranslator


# Globals
# Choose transcription method: 'python_whisper' or 'ctranslate2'
transcription_method = 'ctranslate2'
torch.set_num_threads(12)


known_files = set()
transcribe_queue = Queue()
convert_queue = Queue()


#skip_files = {}  # filename -> index of reason in skip_reasons list

skip_files = set()
skip_reasons = [
    "Error in transcription",
    "Incorrect audio shape",
    "File already processed",
    "Invalid file format", 
    "File ignored by user request",
    "Other error"
]



TRANSCRIBE_ACTIVE = Event()
KNOWN_FILES = set()
SKIP_FILES = set()
TRANSCRIBE_QUEUE = Queue()
CONVERT_QUEUE = Queue()


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

def valid_filename(file):
    try:
        datetime.datetime.strptime(file, '%Y-%m-%d_%H-%M-%S')
        return True
    except ValueError:
        return False
        
def check_for_subtitle(prefix):
    extensions = ['.vtt', '.srt', '.txt', '.json']
    return any(os.path.exists(prefix + ext) for ext in extensions)        


def transcribe_audio(file_path):
    try:
        # Load and preprocess the audio
        audio = whisper.load_audio(file_path)
        #audio = whisper.pad_or_trim(audio)  # Ensure the audio is of correct length or padded appropriately

        # Generate Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # Decode the audio
        options = whisper.DecodingOptions()
        result = model.decode(mel, options)

        logging.info("Transcription completed successfully.")
        return result.text
    except AssertionError as e:
        filename = os.path.basename(file_path)
        logging.error(f"Error in transcribing audio {filename}: {e}")
        skip_files[filename] = skip_reasons.index("Incorrect audio shape")  # Use the index of the specific error reason
        return None
    except Exception as e:
        filename = os.path.basename(file_path)
        logging.error(f"Unhandled error in transcribing audio {filename}: {e}")
        skip_files[filename] = skip_reasons.index("Error in transcription")  # General transcription error
        return None
        
        
        
        
        
        
        


# Worker functions
def scanner(directory):
    global KNOWN_FILES
    while True:
        try:
            current_files = set(os.listdir(directory))
            new_files = current_files - KNOWN_FILES

            for file in new_files:
                if file in SKIP_FILES:
                    continue

                prefix, extension = os.path.splitext(file)
                if not valid_filename(prefix):
                    logging.error(f"Filename {file} does not match the expected format and will be ignored.")
                    continue

                if extension in ['.wav', '.flac']:
                    if check_for_subtitle(prefix):
                        logging.info(f"Skipping {file}: subtitle file already exists.")
                        continue

                    if extension == '.wav' and not os.path.exists(prefix + '.flac'):
                        TRANSCRIBE_QUEUE.put(file)
                        logging.info(f"File {file} added to transcription queue")

                    if extension == '.flac':
                        TRANSCRIBE_QUEUE.put(file)
                        logging.info(f"File {file} added to transcription queue for flac")

                KNOWN_FILES.add(file)

        except Exception as e:
            logging.error(f"Error in scanner: {e}")

def transcriber():
    while True:
        file = TRANSCRIBE_QUEUE.get()
        TRANSCRIBE_ACTIVE.set()
        # Simulate transcription process
        logging.info(f"Starting transcription for {file}.")
        # Imagine transcription happens here
        TRANSCRIBE_ACTIVE.clear()
        CONVERT_QUEUE.put(file)
        logging.info(f"Transcription completed for {file}. File added to conversion queue.")
        TRANSCRIBE_QUEUE.task_done()

def converter():
    while True:
        file = CONVERT_QUEUE.get(block=True)
        if TRANSCRIBE_ACTIVE.is_set():
            CONVERT_QUEUE.put(file)
            logging.info(f"Conversion delayed for {file}, waiting for transcription to complete.")
            continue

        # Simulate conversion process
        logging.info(f"Starting conversion for {file}.")
        # Imagine conversion happens here
        logging.info(f"Conversion completed for {file}.")
        CONVERT_QUEUE.task_done()




##END GPT 4 segment 12-05-2024##
        





def scanner(directory, known_files, currently_processing, file_groups):
    subtitle_extensions = ['.vtt', '.srt', '.txt', '.json']  # Define subtitle extensions once at the start
    while True:
        try:
            current_files = set(os.listdir(directory))
            new_files = list(current_files - known_files)

            valid_files = []
            for file in new_files:
                prefix, extension = os.path.splitext(file)
                if file not in skip_files:
                    try:
                        # Validate file timestamp format
                        datetime.datetime.strptime(prefix, '%Y-%m-%d_%H-%M-%S')
                        if prefix not in file_groups:
                            file_groups[prefix] = []
                        file_groups[prefix].append(extension)

                        # Check for existing subtitle files for each audio file
                        if extension in ['.wav', '.flac']:
                            subtitles_exist = any(os.path.exists(prefix + ext) for ext in subtitle_extensions)
                            if subtitles_exist:
                                logging.info(f"Skipping processing for {file}: subtitle file already exists.")
                                continue

                            if extension == ".wav":
                                # Check if corresponding flac exists
                                flac_exists = os.path.exists(prefix + '.flac')
                                if not flac_exists:
                                    # If no corresponding flac, add wav to transcribe and possibly to convert
                                    subtitles_exist = any(os.path.exists(prefix + ext) for ext in subtitle_extensions)
                                    if subtitles_exist:
                                        logging.info(f"Skipping processing for {file}: subtitle file already exists.")
                                        continue
                                    else:
                                        transcribe_queue.put(file)
                                        currently_processing.add(file)
                                        logging.info(f"File {file} added to transcription queue")
                                else:
                                    logging.info(f"Skipping FLAC conversion for {file}: FLAC file already exists.")
                            
                            elif extension == ".flac":
                                # Add flac files to the transcription queue if no subtitles exist
                                transcribe_queue.put(file)
                                currently_processing.add(file)
                                logging.info(f"File {file} added to transcription queue for flac")

                        elif extension in subtitle_extensions:
                            # Ignore subtitle files if there is no corresponding audio file
                            audio_files_exist = any(os.path.exists(prefix + ext) for ext in ['.wav', '.flac'])
                            if not audio_files_exist:
                                logging.info(f"No corresponding audio file for {file}; skipping.")

                        valid_files.append(file)

                    except ValueError:
                        logging.error(f"Filename {file} does not match the expected format and will be ignored.")
                        skip_files[file] = skip_reasons.index("Invalid file format")
                else:
                    logging.info(f"File {file} is skipped as it's in the skip list.")

            known_files.update(new_files)

        except Exception as e:
            logging.error(f"An error occurred in the scanner function: {e}")
        time.sleep(5)






def transcribe_ct2(input_path):
    # Define the output path based on the input path
    output_path = os.path.splitext(input_path)[0] + '.txt'
    
    # Prepare the command with properly quoted paths
    cmd = [
        "whisper-ctranslate2",
        f"'{input_path}'",  # Quote the input path
        "--model", "medium.en",
        "--language", "en",
        "--output_dir", f"'{os.path.dirname(output_path)}'",  # Quote the output directory path
        "--device", "cpu"
    ]

    # Join the command list into a single string to ensure proper handling of spaces
    cmd_string = " ".join(cmd)

    try:
        # Execute the command using shell=True to interpret the whole command as a single string
        output_text = []
        with subprocess.Popen(cmd_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                output_text.append(line)
            if proc.stderr:
                for err_line in proc.stderr:
                    logging.error(f"Transcription errors: {err_line.strip()}")

        proc.wait()  # Wait for the subprocess to finish
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd_string)
        
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
    export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons)
    sys.exit(0)


# Setup signal handlers to ensure the export function is called on shutdown
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)


def export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons):
    output = {
        "known_files": list(known_files),
        "transcribe_queue": list(transcribe_queue.queue),
        "convert_queue": list(convert_queue.queue),
        "skip_files": list(skip_files),  # Ensure this is serializable
        "skip_reasons": skip_reasons
    }
    with open("state_backup.json", "w") as f:
        json.dump(output, f, indent=4)
    logging.info("State of queues, files, and skip reasons has been saved.")



    

def load_state_from_disk():
    try:
        with open("state_backup.json", "r") as f:
            data = json.load(f)
        
        # Convert the list back into a set for known_files
        known_files = set(data["known_files"])

        # Restore items into the transcription queue
        transcribe_queue = Queue()
        for item in data["transcribe_queue"]:
            transcribe_queue.put(item)

        # Restore items into the conversion queue
        convert_queue = Queue()
        for item in data["convert_queue"]:
            convert_queue.put(item)

        # Load the skip_files dictionary
        # Ensure that keys are converted back to their original type if needed, here assumed to be correct
        skip_files = data["skip_files"]

        # Load the skip_reasons list
        skip_reasons = data.get("skip_reasons", [])

        # Validate if loaded reasons match predefined ones or if additional handling is needed
        if not skip_reasons:
            # Load default reasons if file does not provide them or they are empty
            skip_reasons = [
                "Error in transcription",
                "Incorrect audio shape",
                "File already processed",
                "File ignored by user request",
                "Other error"
            ]

        return known_files, transcribe_queue, convert_queue, skip_files, skip_reasons
    except FileNotFoundError:
        logging.error("No state file found, initializing with empty structures.")
        return set(), Queue(), Queue(), {}, [
            "Error in transcription",
            "Incorrect audio shape",
            "File already processed",
            "File ignored by user request",
            "Other error"
        ]
    except Exception as e:
        logging.error(f"Failed to load state from disk: {e}")
        return set(), Queue(), Queue(), {}, [
            "Error in transcription",
            "Incorrect audio shape",
            "File already processed",
            "File ignored by user request",
            "Other error"
        ]






def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    directory = "/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"
    currently_processing = set()
    file_groups = defaultdict(list)  # Initialize file_groups

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    logging.info("Starting scanner thread...")
    scanner_thread = Thread(target=scanner, args=(directory, known_files, currently_processing, file_groups))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcribe thread...")
    transcribe_thread = Thread(target=transcriber)
    transcribe_thread.daemon = True
    transcribe_thread.start()

    logging.info("Starting convert thread...")
    convert_thread = Thread(target=converter)
    convert_thread.daemon = True
    convert_thread.start()

    try:
        while True:
            time.sleep(5)  # Keep the main thread alive.
            logging.debug("Main loop running...")
            logging.debug(f"Transcribing Active: {Event().is_set()}")
            logging.debug(f"Transcription Queue Size: {transcribe_queue.qsize()}")
            logging.debug(f"Conversion Queue Size: {convert_queue.qsize()}")

    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    main()




