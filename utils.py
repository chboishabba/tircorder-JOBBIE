import os
import json
import logging
import subprocess
import sqlite3
import torch
import torchaudio
import hashlib
from queue import Queue
from datetime import datetime
from pyannote.audio import Pipeline
from pyannote.core import Annotation
import whisperx
from huggingface_hub import login, whoami
import warnings
from rate_limit import RateLimiter

warnings.filterwarnings("ignore", message=".*set_audio_backend has been deprecated.*")
warnings.filterwarnings("ignore", message=".*Model was trained*")

USE_CPU = False

# Read the Hugging Face token from a file
with open('hf-token.txt', 'r') as file:
    HFTOKEN = file.read().strip()

# Log in to the Hugging Face hub
login(token=HFTOKEN)

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except FileNotFoundError:
        return None
    return sha256_hash.hexdigest()

def load_recordings_folders_from_db(db_path='state.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, folder_path, ignore_transcribing, ignore_converting FROM recordings_folders')
    folders = cursor.fetchall()
    conn.close()
    return folders

def get_all_files(folders, extensions):
    files = []
    for folder_id, folder, ignore_transcribing, ignore_converting in folders:
        if os.path.exists(folder):
            for root, _, file_names in os.walk(folder):
                for file_name in file_names:
                    if any(file_name.lower().endswith(ext) for ext in extensions):
                        files.append((folder_id, os.path.join(root, file_name)))
    return files

def wav2flac(input_path, output_path):
    try:
        result = subprocess.run(["ffmpeg", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stderr:
            logging.error(f"Conversion errors for {input_path}: {result.stderr.decode()}")
        logging.info(f"Conversion completed for {input_path}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to convert {input_path} to FLAC: {e}")
    except Exception as e:
        logging.error(f"An error occurred while converting {input_path} to FLAC: {e}")

def transcribe_audio(file_path, device="cuda", compute_type="float16", batch_size=16, hf_token=HFTOKEN):
    global USE_CPU

    def assign_word_speakers(diarize_segments, result):
        for segment in result.get('segments', []):
            for word in segment.get('words', []):
                word['speaker'] = "unknown"
                for diarize_segment in diarize_segments:
                    if diarize_segment['start'] <= word['start'] <= diarize_segment['end']:
                        word['speaker'] = diarize_segment['label']
        return result

    def perform_transcription(device, compute_type, model_name):
        model = whisperx.load_model(model_name, device, compute_type=compute_type)
        audio = whisperx.load_audio(file_path)
        result = model.transcribe(audio, batch_size=batch_size)
        logging.debug(f"{result}")
        logging.info("Transcription completed successfully.")
        
        # Align whisper output
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Convert audio to the required format for diarization
        waveform, sample_rate = torchaudio.load(file_path)
        waveform = waveform.to(device)
        logging.debug(f"Waveform shape: {waveform.shape}, Sample rate: {sample_rate}")

        # Diarize and assign speaker labels
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.0",
                use_auth_token=HFTOKEN
            )
            pipeline.to(torch.device("cuda") if not USE_CPU else torch.device("cpu"))
            diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
            diarize_segments = [
                {"start": segment.start, "end": segment.end, "label": label}
                for segment, label in diarization.itertracks(yield_label=True)
            ]
            result = assign_word_speakers(diarize_segments, result)
        except Exception as e:
            logging.error(f"Failed to load diarization model: {e}")
            diarize_segments = []
            result = assign_word_speakers(diarize_segments, result)

        # Include word-level confidence in JSON
        word_confidence = [{"word": segment.get('text', ''), "confidence": segment.get('confidence', 1.0)} for segment in result.get('segments', [])]
        transcript_json = {
            "text": result.get('text', ''),
            "segments": result.get('segments', []),
            "word_confidence": word_confidence,
            "diarization": diarize_segments
        }

        # Log the transcript
        logging.info(f"Transcript for {file_path}: {transcript_json['text']}")

        return transcript_json

    try:
        if USE_CPU or not torch.cuda.is_available() or device != "cuda":
            device = "cpu"
            compute_type = "int8"
            model_name = "medium.en"
            USE_CPU = True  # Ensure we stick to CPU once set
        else:
            model_name = "large-v2"
        
        return perform_transcription(device, compute_type, model_name)
        
    except RuntimeError as e:
        if "CUDA driver version is insufficient for CUDA runtime version" in str(e):
            logging.warning("CUDA error encountered. Switching to CPU.")
            device = "cpu"
            compute_type = "int8"
            model_name = "medium.en"
            USE_CPU = True  # Ensure we stick to CPU once set
            return perform_transcription(device, compute_type, model_name)
        else:
            logging.error(f"Runtime error in transcribing audio {os.path.basename(file_path)}: {e}")
            return None
    except AssertionError as e:
        logging.error(f"Assertion error in transcribing audio {os.path.basename(file_path)}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unhandled error in transcribing audio {os.path.basename(file_path)}: {e}")
        return None

