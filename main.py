import threading
import logging
import signal
import time
import sys
from queue import Queue
from scanner import scanner
from transcriber import transcriber
from converter import wav2flac
from state import export_queues_and_files, load_state

# Globals
TRANSCRIBE_QUEUE = Queue()
CONVERT_QUEUE = Queue()
known_files, skip_files, skip_reasons = set(), set(), {}

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
    global TRANSCRIBE_QUEUE, CONVERT_QUEUE, known_files, checked_files, skip_reasons

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

    logging.debug("Main function started")
    
    directory = "/mnt/smbshare/Y/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"

    known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, skip_files, skip_reasons = load_state()
    
    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(directory, known_files, TRANSCRIBE_QUEUE, CONVERT_QUEUE, checked_files, skip_reasons))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcribe thread...")
    transcribe_thread = threading.Thread(target=transcriber, args=(TRANSCRIBE_QUEUE, CONVERT_QUEUE, 'ctranslate2', TRANSCRIBE_ACTIVE, transcription_complete))
    transcribe_thread.daemon = True
    transcribe_thread.start()

    logging.info("Starting convert thread...")
    convert_thread = threading.Thread(target=wav2flac, args=(CONVERT_QUEUE, transcribing_lock, TRANSCRIBE_ACTIVE, transcription_complete))
    convert_thread.daemon = True
    convert_thread.start()

    try:
        while True:
            time.sleep(5)
            logging.debug(f"Main loop running... Known files: {len(known_files)}")
            logging.debug(f"Transcribing Active: {TRANSCRIBE_ACTIVE.is_set()}")
            logging.debug(f"Transcription Queue Size: {TRANSCRIBE_QUEUE.qsize()}")
            logging.debug(f"Conversion Queue Size: {CONVERT_QUEUE.qsize()}")

            if TRANSCRIBE_QUEUE.qsize() == 0 and not TRANSCRIBE_ACTIVE.is_set():
                logging.debug("No transcription tasks running, ensuring conversion tasks are processed.")
                transcription_complete.set()

    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    main()

