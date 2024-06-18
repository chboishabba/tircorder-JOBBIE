# thread_manager.py
import torch
import threading
import logging
from scanner import scanner
from transcriber import transcriber
from converter import converter
from state import load_state
from utils import load_recordings_folders_from_db

def start_threads(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons):
    logging.info("Starting scanner thread...")
    scanner_thread = threading.Thread(target=scanner, args=(known_files, transcribe_queue, convert_queue, skip_files, skip_reasons))
    scanner_thread.daemon = True
    scanner_thread.start()

    logging.info("Starting transcriber thread...")
    transcribe_active = threading.Event()
    transcription_complete = threading.Event()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    transcriber_thread = threading.Thread(target=transcriber, args=(transcribe_queue, convert_queue, 'whisperx', transcribe_active, transcription_complete, device, compute_type))
    transcriber_thread.daemon = True
    transcriber_thread.start()

    logging.info("Starting converter thread...")
    convert_thread = threading.Thread(target=converter, args=(convert_queue,))
    convert_thread.daemon = True
    convert_thread.start()
