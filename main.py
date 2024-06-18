import threading
import logging
import signal
import time
import sys
import threading
from threading import Event, Lock
from queue import Queue
from scanner import scanner
from transcriber import transcriber
from converter import wav2flac
from state import export_queues_and_files, load_state
from utils import load_recordings_folders_from_db, wav2flac
import db_match_audio_transcript
import whisper
from faster_whisper import WhisperModel
from rate_limit import RateLimiter
from multiprocessing import Value, Manager

# Import the new match_audio_transcripts function
from db_match_audio_transcript import match_audio_transcripts

# Globals
model = WhisperModel("medium.en", device="cpu", compute_type="int8")
TRANSCRIBE_QUEUE = Queue()
CONVERT_QUEUE = Queue()
known_files, skip_files, skip_reasons = set(), set(), {}

# Load recordings folders from the database
recordings_folders = load_recordings_folders_from_db()

TRANSCRIBE_ACTIVE = threading.Event()
transcribing_lock = threading.Lock()
transcription_complete = threading.Event()
checked_files = set()

def handle_shutdown_signal(signum, frame):
    logging.info("Shutdown signal received. Exporting queues, known files, and skip files...")
    export_queues_and_files(known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons)
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

def main():
    global TRANSCRIBE_QUEUE, CONVERT_QUEUE, known_files, checked_files, skip_files, skip_reasons
    global transcribing_active, transcription_complete, process_status, recordings_folders, converting_lock

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

    logging.info("Main function started")
    
    try:
        known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons = load_state()
    except Exception as e:
        logging.error(f"Error loading state: {e}")
        known_files, skip_files, skip_reasons = set(), set(), {}
        TRANSCRIBE_QUEUE = Queue()
        CONVERT_QUEUE = Queue()

    # Initialize shared variables
    manager = Manager()
    process_status = manager.Value('s', '')
    converting_lock = Lock()
    transcribing_active = Event()
    transcription_complete = Event()
    
    # Load recordings folders from the database
    recordings_folders = load_recordings_folders_from_db()

    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, checked_files, skip_files, skip_reasons))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcribe thread...")
    transcribe_thread = threading.Thread(target=transcriber, args=(TRANSCRIBE_QUEUE, CONVERT_QUEUE, 'ctranslate2', transcribing_active, transcription_complete, model))
    transcribe_thread.daemon = True
    transcribe_thread.start()

    logging.info("Starting convert thread...")
    convert_thread = threading.Thread(target=wav2flac, args=(CONVERT_QUEUE, converting_lock, transcribing_active, transcription_complete, process_status, recordings_folders))
    convert_thread.daemon = True
    convert_thread.start()

    try:
        while True:
            time.sleep(5)
            logging.info(f"Main loop running... Known files: {len(known_files)}")
            logging.info(f"Transcribing Active: {transcribing_active.is_set()}")
            logging.info(f"Transcription Queue Size: {TRANSCRIBE_QUEUE.qsize()}")
            logging.info(f"Conversion Queue Size: {CONVERT_QUEUE.qsize()}")

            if TRANSCRIBE_QUEUE.qsize() == 0 and not transcribing_active.is_set():
                logging.info("No transcription tasks running, ensuring conversion tasks are processed.")
                transcription_complete.set()
                try:
                    logging.debug(f"Ran match_audio_transcripts()")
                    match_audio_transcripts()  # Match audio and transcripts and update the database
                except Exception as e:
                    logging.error(f"Error in match_audio_transcripts: {e}")

    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    main()


