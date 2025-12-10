import os
import argparse
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
from datetime import datetime, timedelta
import whisper
import numpy as np
import torch
import json
import ctranslate2
from faster_whisper import WhisperModel
import librosa
import warnings
from tircorder.utils import DEFAULT_WEBUI_CONFIG, transcribe_webui


warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


# Configure logging
logging.basicConfig(level=logging.INFO)
# Keep track of proc_comp_timestamps_transcribe
proc_comp_timestamps_transcribe = []

# Globals

# Choose transcription method: 'python_whisper', 'ctranslate2', or 'ctranslate2_nonpythonic'
transcription_method = 'ctranslate2'


#ctranslate2_model_path = "/home/c/Documents/TiRCORDER - BETA 'jobbie'/faster-whisper-medium-en"
model = WhisperModel("medium.en", device="cpu", compute_type="int8")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#translator = ctranslate2.Translator(ctranslate2_model_path)
# Choose transcription method: 'python_whisper' or 'ctranslate2'
transcription_method = 'ctranslate2'
torch.set_num_threads(12)

known_files = set()
TRANSCRIBE_QUEUE = Queue()
CONVERT_QUEUE = Queue()

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

transcription_complete = Event() # Event to manage synchronization between transcribe and conversion

# Load the model once and keep it in memory
model = whisper.load_model("medium.en", device="cpu")

def get_sorted_files(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.wav')]
    files.sort(key=lambda x: os.path.basename(x), reverse=True)
    return files


def valid_filename(file):
    try:
        datetime.strptime(file, '%Y-%m-%d_%H-%M-%S')
        return True
    except ValueError:
        return False

def check_for_subtitle(prefix):
    extensions = ['.vtt', '.srt', '.txt', '.json']
    return any(os.path.exists(prefix + ext) for ext in extensions)

def transcribe_audio(file_path):
    try:
        audio = whisper.load_audio(file_path)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        options = whisper.DecodingOptions()
        result = model.decode(mel, options)
        logging.info("Transcription completed successfully.")
        return result.text
    except AssertionError as e:
        filename = os.path.basename(file_path)
        logging.error(f"Error in transcribing audio {filename}: {e}")
        skip_files.add(filename)
        return None
    except Exception as e:
        filename = os.path.basename(file_path)
        logging.error(f"Unhandled error in transcribing audio {filename}: {e}")
        skip_files.add(filename)
        return None

def load_traversal_results(json_path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.warning(f"Traversal results file not found: {json_path}")
        data = {'audio_files': [], 'transcript_files': []}
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(data, f)
        return data
    except Exception as e:
        logging.error(f"Failed to load traversal results: {e}")
        return {'audio_files': [], 'transcript_files': []}

def scanner(directory, known_files, currently_processing, file_groups, traversal_results):
    audio_extensions = ['.wav', '.flac']
    subtitle_extensions = ['.vtt', '.srt', '.txt', '.json']
    while True:
        try:
            current_files = set(os.listdir(directory))
            new_files = list(current_files - known_files)
            new_files.sort(reverse=True)  # Sort files from most recent to oldest

            valid_files = []
            for file in new_files:
                prefix, extension = os.path.splitext(file)
                if file not in skip_files:
                    try:
                        # Correctly parse datetime
                        datetime.strptime(prefix, '%Y-%m-%d_%H-%M-%S')
                        if prefix not in file_groups:
                            file_groups[prefix] = []
                        file_groups[prefix].append(extension)

                        # Check if the file is already processed
                        if file in traversal_results['audio_files'] or file in traversal_results['transcript_files']:
                            logging.info(f"Skipping already processed file: {file}")
                            continue

                        if extension in audio_extensions:
                            # Check for existing transcript files
                            transcripts_exist = any(os.path.exists(join(directory, prefix + ext)) for ext in subtitle_extensions)
                            if transcripts_exist:
                                logging.debug(f"Skipping processing for {file}: transcript file already exists.")
                                continue

                            if extension == ".wav":
                                flac_exists = os.path.exists(join(directory, prefix + '.flac'))
                                if not flac_exists:
                                    TRANSCRIBE_QUEUE.put(file)
                                    currently_processing.add(file)
                                    logging.debug(f"File {file} added to transcription queue")
                                else:
                                    logging.info(f"Skipping FLAC conversion for {file}: FLAC file already exists.")
                            
                            elif extension == ".flac":
                                TRANSCRIBE_QUEUE.put(file)
                                currently_processing.add(file)
                                logging.debug(f"File {file} added to transcription queue for flac")

                        elif extension in subtitle_extensions:
                            audio_files_exist = any(os.path.exists(join(directory, prefix + ext)) for ext in audio_extensions)
                            if not audio_files_exist:
                                logging.info(f"No corresponding audio file for {file}; skipping.")

                        valid_files.append(file)

                    except ValueError:
                        logging.error(f"Filename {file} does not match the expected format and will be ignored.")
                        skip_files.add(file)
                else:
                    logging.info(f"File {file} is skipped as it's in the skip list.")

            known_files.update(new_files)

        except Exception as e:
            logging.error(f"An error occurred in the scanner function: {e}")
        time.sleep(5)




def transcriber(base_directory, webui_url=None, webui_path="/_transcribe_file"):
    global process_status, proc_comp_timestamps_transcribe
    while True:
        file = TRANSCRIBE_QUEUE.get()
        start_time = datetime.now()
        TRANSCRIBE_ACTIVE.set()
        logging.info(f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting transcription for {file}.")
        
        if transcription_method == 'webui' and webui_url:
            file_path = join(base_directory, file)
            output_text, audio_duration, metadata = transcribe_webui(
                file_path,
                base_url=webui_url,
                options=DEFAULT_WEBUI_CONFIG["options"],
                timeout=DEFAULT_WEBUI_CONFIG["timeout"],
                verify_ssl=DEFAULT_WEBUI_CONFIG["verify_ssl"],
                transcribe_path=webui_path or DEFAULT_WEBUI_CONFIG["transcribe_path"],
            )
            if output_text is None:
                logging.error(f"WebUI transcription failed for {file}: {metadata.get('error')}")
        elif transcription_method == 'python_whisper':
            output_text, audio_duration = transcribe_audio(file)
        elif transcription_method == 'ctranslate2':
            file_path = join(base_directory, file)
            output_text, audio_duration = transcribe_ct2(file_path)
        elif transcription_method == 'ctranslate2_nonpythonic':
            file_path = join(base_directory, file)
            output_text, audio_duration = transcribe_ct2_nonpythonic(file_path)
        else:
            logging.error(f"Unsupported transcription method: {transcription_method}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        if output_text is not None:
            output_path = join(base_directory, splitext(file)[0] + '.txt')
            try:
                with open(output_path, 'w') as f:
                    f.write(output_text)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                real_time_factor = audio_duration / elapsed_time if elapsed_time > 0 else 0
                logging.info(f"SYSTIME: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | Transcription completed and saved for {file}. Real-time factor: {real_time_factor:.2f}x.")
            except PermissionError as e:
                logging.error(f"Permission denied while saving transcription for {file}: {e}")
            except FileNotFoundError as e:
                logging.error(f"File not found error while saving transcription for {file}: {e}")
            except Exception as e:
                logging.error(f"An error occurred while saving transcription for {file}: {e}")
        else:
            logging.error(f"Transcription failed for {file}.")

        CONVERT_QUEUE.put(file)
        
        # Calculate processing rates
        now = datetime.now()
        proc_comp_timestamps_transcribe.append(now)
        
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        # Filter timestamps
        proc_comp_timestamps_transcribe = [t for t in proc_comp_timestamps_transcribe if t > one_hour_ago]
        files_per_hour = len([t for t in proc_comp_timestamps_transcribe if t > one_hour_ago])
        files_per_minute = len([t for t in proc_comp_timestamps_transcribe if t > one_minute_ago])

        logging.info(f"SYSTIME: {now.strftime('%Y-%m-%d %H:%M:%S')} | File {file} added to conversion queue. {CONVERT_QUEUE.qsize()} files waiting for conversion. {TRANSCRIBE_QUEUE.qsize()} left to transcribe. Processing rates: {files_per_hour} files/hour, {files_per_minute} files/minute.")
        
        TRANSCRIBE_QUEUE.task_done()
        TRANSCRIBE_ACTIVE.clear()

        if not TRANSCRIBE_QUEUE.qsize():
            process_status = 'housekeeping'
            logging.info("All transcription tasks completed, entering housekeeping mode.")
        else:
            logging.info(f"{TRANSCRIBE_QUEUE.qsize()} transcription tasks remaining.")




def transcribe_ct2_nonpythonic(input_path):
    output_dir = os.path.dirname(input_path)
    cmd = [
        "whisper-ctranslate2",
        input_path,  # No need to quote within the list
        "--model", "medium.en",
        "--language", "en",
        "--output_dir", output_dir,  # No need to quote within the list
        "--device", "cpu"
    ]

    try:
        output_text = []
        start_time = None
        end_time = None
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                if "Processing audio" in line:
                    # Extract segment times from the line
                    parts = line.split()
                    start_time = float(parts[3].replace('s', ''))
                    end_time = float(parts[5].replace('s', ''))
                output_text.append(line)
                logging.info(line.strip())  # Log the progressive output
            for err_line in proc.stderr:
                logging.error(f"Transcription errors: {err_line.strip()}")

        proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

        total_audio_duration = end_time - start_time if start_time and end_time else 0
        return ''.join(output_text), total_audio_duration

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to transcribe {input_path}: {e}")
        return None, 0
    except FileNotFoundError as e:
        logging.error(f"File not found error while transcribing {input_path}: {e}")
        return None, 0
    except PermissionError as e:
        logging.error(f"Permission denied while transcribing {input_path}: {e}")
        return None, 0
    except Exception as e:
        logging.error(f"An error occurred while transcribing {input_path}: {e}")
        return None, 0



def transcribe_ct2(file_path):
    try:
        # Load and preprocess the audio
        audio, _ = librosa.load(file_path, sr=16000, mono=True)

        # Transcribe audio using the model
        result = model.transcribe(file_path, beam_size=5)

        logging.debug(f"Transcription result type: {type(result)}")
        logging.debug(f"Transcription result: {result}")

        transcription = result['text']
        segments = result['segments']
        language = result['language']

        logging.info(f"Detected language {language}")
        logging.info("Transcription completed successfully.")
        
        detailed_transcription = ""
        total_audio_duration = 0.0
        for segment in segments:
            start = segment['start']
            end = segment['end']
            total_audio_duration += (end - start)
            detailed_transcription += f"[{start:.2f}s -> {end:.2f}s] {segment['text']}\n"
        det_trans_stripped = detailed_transcription.strip()
        logging.info(det_trans_stripped)

        return det_trans_stripped, total_audio_duration
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        logging.error(f"Result from model.transcribe: {result}")
        filename = os.path.basename(file_path)
        skip_files.add(filename)
        return None, 0
    except AssertionError as e:
        filename = os.path.basename(file_path)
        logging.error(f"Error in transcribing audio {filename}: {e}")
        skip_files.add(filename)
        return None, 0
    except FileNotFoundError as e:
        filename = os.path.basename(file_path)
        logging.error(f"File not found error while transcribing {file_path}: {e}")
        skip_files.add(filename)
        return None, 0
    except PermissionError as e:
        filename = os.path.basename(file_path)
        logging.error(f"Permission denied while transcribing {file_path}: {e}")
        skip_files.add(filename)
        return None, 0
    except Exception as e:
        filename = os.path.basename(file_path)
        logging.error(f"An error occurred while transcribing {file_path}: {e}")
        skip_files.add(filename)
        return None, 0




def wav2flac(base_directory):
    global process_status, converting_lock, transcribing_active, transcription_complete
    while True:
        transcription_complete.wait()
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
            input_path = join(base_directory, file)
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

            CONVERT_QUEUE.task_done()
            transcription_complete.clear()
            if not CONVERT_QUEUE.qsize():
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
        time.sleep(10)

def handle_shutdown_signal(signum, frame):
    logging.info("Shutdown signal received. Exporting queues, known files, and skip files...")
    export_queues_and_files(known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons)
    sys.exit(0)

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
        
        known_files = set(data["known_files"])

        transcribe_queue = Queue()
        for item in data["transcribe_queue"]:
            TRANSCRIBE_QUEUE.put(item)

        convert_queue = Queue()
        for item in data["convert_queue"]:
            CONVERT_QUEUE.put(item)

        skip_files = set(data["skip_files"])
        skip_reasons = data.get("skip_reasons", [])

        if not skip_reasons:
            skip_reasons = [
                "Error in transcription",
                "Incorrect audio shape",
                "File already processed",
                "File ignored by user request",
                "Other error"
            ]

        return known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons
    except FileNotFoundError:
        logging.error("No state file found, initializing with empty structures.")
        return set(), Queue(), Queue(), set(), [
            "Error in transcription",
            "Incorrect audio shape",
            "File already processed",
            "File ignored by user request",
            "Other error"
        ]
    except Exception as e:
        logging.error(f"Failed to load state from disk: {e}")
        return set(), Queue(), Queue(), set(), [
            "Error in transcription",
            "Incorrect audio shape",
            "File already processed",
            "File ignored by user request",
            "Other error"
        ]

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Tircorder server")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=(
            "/mnt/smbshare/Y/__MEDIA/__Transcribing and Recording/2024/"
            "Dad Auto Transcriber/"
        ),
        help="Directory to watch for recordings and transcripts",
    )
    parser.add_argument(
        "--webui-url",
        type=str,
        help="Optional WhisperX-WebUI base URL to use for transcription",
    )
    parser.add_argument(
        "--webui-path",
        type=str,
        default="/_transcribe_file",
        help="Transcription endpoint path for WhisperX-WebUI",
    )
    args = parser.parse_args()

    directory = args.data_dir
    os.makedirs(directory, exist_ok=True)
    currently_processing = set()
    file_groups = defaultdict(list)

    pelican_dir = os.path.join(directory, "Pelican")
    os.makedirs(pelican_dir, exist_ok=True)
    traversal_json = os.path.join(pelican_dir, "traversal_results.json")
    traversal_results = load_traversal_results(traversal_json)

    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    logging.info("Starting scanner thread...")
    scanner_thread = Thread(target=scanner, args=(directory, known_files, currently_processing, file_groups, traversal_results))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcribe thread...")
    if args.webui_url:
        transcription_method = 'webui'

    transcribe_thread = Thread(
        target=transcriber, args=(directory, args.webui_url, args.webui_path)
    )
    transcribe_thread.daemon = True
    transcribe_thread.start()

    logging.info("Starting convert thread...")
    convert_thread = Thread(target=wav2flac, args=(directory,))
    convert_thread.daemon = True
    convert_thread.start()

    try:
        while True:
            time.sleep(5)
            logging.debug("Main loop running...")
            logging.debug(f"Transcribing Active: {TRANSCRIBE_ACTIVE.is_set()}")
            logging.debug(f"Transcription Queue Size: {TRANSCRIBE_QUEUE.qsize()}")
            logging.debug(f"Conversion Queue Size: {CONVERT_QUEUE.qsize()}")

    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    main()
