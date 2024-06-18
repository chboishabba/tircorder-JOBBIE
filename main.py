import os
import signal
import logging
import sys
import threading
import time
from queue import Queue
from db_worker import DBWorker
from scanner import scanner
from transcriber import transcriber
from converter import converter
from state import export_queues_and_files, load_state

# Global variables
transcribe_queue = Queue()
convert_queue = Queue()
skip_files = set()
skip_reasons = {}
known_files = set()
transcribe_active = threading.Event()
transcription_complete = threading.Event()
db_worker = DBWorker()

def handle_shutdown_signal(signum, frame):
    logging.info("Shutdown signal received. Exporting queues, known files, and skip files...")
    try:
        # Wait for threads to complete their current task
        transcribe_active.wait(timeout=10)
        transcription_complete.wait(timeout=10)

        # Save the state with increased timeout
        export_queues_and_files(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons)
        logging.info("State of queues, files, and skip reasons has been saved.")
    except Exception as e:
        logging.error(f"Error exporting state: {e}")
    finally:
        db_worker.stop()
        db_worker.join()
        sys.exit(0)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    # Start the DB worker
    db_worker.start()

    # Load the state
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()

    # Start scanner thread
    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons, db_worker))
    scanner_thread.start()

    # Start transcriber thread
    logging.info("Starting transcriber thread...")
    transcriber_thread = threading.Thread(target=transcriber, args=(transcribe_queue, convert_queue, 'whisperx', transcribe_active, transcription_complete, db_worker))
    transcriber_thread.start()

    # Start converter thread
    logging.info("Starting converter thread...")
    converter_thread = threading.Thread(target=converter, args=(convert_queue, db_worker))
    converter_thread.start()

    # Main loop
    logging.info("Main loop running...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_shutdown_signal(None, None)

if __name__ == "__main__":
    main()

