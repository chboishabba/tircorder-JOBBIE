import os
import json
import librosa
import logging
import subprocess
import time
import sqlite3
from queue import Queue
from threading import Event, Lock
from os.path import join
from datetime import datetime

def load_recordings_folders_from_db(db_path='state.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, folder_path, ignore_transcribing, ignore_converting FROM recordings_folders')
    folders = cursor.fetchall()
    conn.close()
    return folders


def wav2flac(CONVERT_QUEUE, converting_lock, transcribing_active, transcription_complete, process_status, recordings_folders):
    def get_file_paths(file):
        for folder_id, directory, ignore_transcribing, ignore_converting in recordings_folders:
            input_path = join(directory, file)
            if os.path.exists(input_path):
                output_path = input_path.replace('.wav', '.flac')
                return input_path, output_path
        return None, None

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
            process_status.value = f'converting {file}'
            input_path, output_path = get_file_paths(file)
            
            if not input_path or not output_path:
                logging.error(f"File paths not found for {file}. Skipping conversion.")
                CONVERT_QUEUE.task_done()
                continue

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
                process_status.value = 'housekeeping'
                logging.info("All conversion tasks completed, entering housekeeping mode.")

def transcribe_audio(file_path):
    try:
        audio = whisper.load_audio(file_path)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        options = whisper.DecodingOptions()
        result = model.decode(mel, options)
        logging.info("Transcription completed successfully.")
        return result.text
    except AssertionError as e:
        logging.error(f"Error in transcribing audio {os.path.basename(file_path)}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unhandled error in transcribing audio {os.path.basename(file_path)}: {e}")
        return None

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"{file_path} not found.")
        return None
    except Exception as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return None

def load_state_from_disk():
    return load_json('state_backup.json')

def load_traversal_results():
    return load_json('Pelican/traversal_results.json')

def transcribe_ct2(file_path, model, skip_files):
    try:
        # Load and preprocess the audio
        audio, _ = librosa.load(file_path, sr=16000, mono=True)

        # Transcribe audio using the model
        segments, info = model.transcribe(file_path, beam_size=5)

        logging.debug(f"Transcription result type: {type(segments)}")
        logging.debug(f"Transcription result: {segments}")

        transcription = "\n".join([segment.text for segment in segments])
        language = info.language
        total_audio_duration = info.duration

        logging.info(f"Detected language {language}")
        logging.info("Transcription completed successfully.")
        
        detailed_transcription = ""
        for segment in segments:
            start = segment.start
            end = segment.end
            detailed_transcription += f"[{start:.2f}s -> {end:.2f}s] {segment.text}\n"
        det_trans_stripped = detailed_transcription.strip()
        logging.info(det_trans_stripped)

        return det_trans_stripped, total_audio_duration
    except ValueError as e:
        logging.error(f"ValueError: {e}")
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
