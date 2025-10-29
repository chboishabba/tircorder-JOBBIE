import json
import logging
import os
import sqlite3
import subprocess
import time
from datetime import datetime
from os.path import join
from queue import Queue
from threading import Event, Lock
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import librosa
import requests

from tircorder.interfaces.config import TircorderConfig


DEFAULT_TRANSCRIPTION_METHOD = "ctranslate2"
DEFAULT_WEBUI_CONFIG: Dict[str, Any] = {
    "base_url": "http://localhost:7860",
    "options": {},
    "poll_interval": 2.0,
    "timeout": 600.0,
    "username": None,
    "password": None,
    "api_key": None,
    "headers": {},
    "verify_ssl": True,
    "status_path": "/task/{task_id}",
}

def get_transcription_backend(method_override: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Return the configured transcription backend and merged settings.

    Args:
        method_override: Explicit transcription method to use. When ``None``
            the persisted configuration is consulted.

    Returns:
        A tuple containing the resolved transcription method and a dictionary
        with configuration values for that backend. Unknown configuration keys
        are preserved so callers may pass custom options to downstream APIs.
    """

    config = TircorderConfig.get_config()
    transcription_config = config.get("transcription", {})
    method = method_override or transcription_config.get(
        "method", DEFAULT_TRANSCRIPTION_METHOD
    )

    if method == "webui":
        configured = transcription_config.get("webui", {})
        merged = {**DEFAULT_WEBUI_CONFIG, **configured}
        return method, merged

    return method, transcription_config.get(method, {})


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


def _prepare_webui_payload(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert complex option values to strings for multipart requests."""

    prepared: Dict[str, Any] = {}
    if not options:
        return prepared

    for key, value in options.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            prepared[key] = json.dumps(value)
        else:
            prepared[key] = value
    return prepared


def _segments_to_text(segments: Any) -> str:
    """Convert Whisper-WebUI segments into a transcript string."""

    if not segments:
        return ""

    lines = []
    if isinstance(segments, dict):
        segments = segments.get("segments", [])

    for segment in segments:
        text = ""
        start = None
        end = None
        if isinstance(segment, dict):
            text = segment.get("text", "")
            start = segment.get("start")
            end = segment.get("end")
        elif isinstance(segment, (list, tuple)) and segment:
            text = str(segment[-1])
        else:
            text = str(segment)

        if not text:
            continue

        if start is not None and end is not None:
            try:
                start_val = float(start)
                end_val = float(end)
                lines.append(f"[{start_val:.2f}s -> {end_val:.2f}s] {text}")
            except (TypeError, ValueError):
                lines.append(text)
        else:
            lines.append(text)

    return "\n".join(lines).strip()


def _build_status_url(base_url: str, status_path: str, task_id: str) -> str:
    """Compose the polling URL for a Whisper-WebUI task."""

    formatted_path = status_path.format(task_id=task_id)
    return urljoin(f"{base_url.rstrip('/')}/", formatted_path.lstrip("/"))


def transcribe_webui(
    file_path: str,
    *,
    base_url: str,
    options: Optional[Dict[str, Any]] = None,
    poll_interval: float = 2.0,
    timeout: Optional[float] = 600.0,
    auth: Optional[Tuple[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
    status_path: str = "/task/{task_id}",
    session: Optional[requests.Session] = None,
) -> Tuple[Optional[str], float, Dict[str, Any]]:
    """Send audio to Whisper-WebUI and return the resulting transcript.

    Args:
        file_path: Path to the audio file that should be transcribed.
        base_url: Base URL of the Whisper-WebUI deployment.
        options: Extra options forwarded to the `/transcribe_file` endpoint.
        poll_interval: Seconds between status checks.
        timeout: Maximum seconds to wait for a completed task. ``None``
            disables the timeout.
        auth: Optional HTTP basic authentication credentials.
        headers: Additional HTTP headers to include with requests.
        verify_ssl: Whether to verify SSL certificates for HTTPS targets.
        status_path: Endpoint template used to poll for task completion.
        session: Optional requests session injected for testing.

    Returns:
        A tuple ``(transcript_text, duration_seconds, metadata)``. The metadata
        dictionary always contains ``task_id`` and ``error`` keys. When the
        transcription fails ``transcript_text`` is ``None`` and ``error``
        includes the reported failure details.
    """

    metadata: Dict[str, Any] = {"task_id": None, "error": None}
    request_session = session or requests.Session()
    headers = headers or {}

    start_endpoint = urljoin(f"{base_url.rstrip('/')}/", "transcribe_file")
    payload = _prepare_webui_payload(options)

    try:
        with open(file_path, "rb") as handle:
            response = request_session.post(
                start_endpoint,
                files={"file": (os.path.basename(file_path), handle)},
                data=payload,
                headers=headers,
                auth=auth,
                verify=verify_ssl,
                timeout=timeout,
            )
        response.raise_for_status()
        start_data = response.json()
    except Exception as exc:  # pragma: no cover - network failures
        logging.error("Failed to start Whisper-WebUI transcription: %s", exc)
        metadata["error"] = str(exc)
        return None, 0.0, metadata

    task_id = None
    for key in ("task_id", "identifier", "id", "job_id", "queue_id"):
        if start_data.get(key):
            task_id = str(start_data[key])
            break

    if not task_id:
        logging.error("Whisper-WebUI response did not include a task identifier")
        metadata["error"] = "missing_task_id"
        return None, 0.0, metadata

    metadata["task_id"] = task_id

    status_url = _build_status_url(base_url, status_path, task_id)
    deadline = None if timeout is None else time.monotonic() + timeout

    while True:
        if deadline and time.monotonic() > deadline:
            metadata["error"] = "timeout"
            logging.error(
                "Timed out waiting for Whisper-WebUI task %s to finish", task_id
            )
            return None, 0.0, metadata

        try:
            poll_response = request_session.get(
                status_url,
                headers=headers,
                auth=auth,
                verify=verify_ssl,
                timeout=poll_interval + 5,
            )
            poll_response.raise_for_status()
            status_data = poll_response.json()
        except Exception as exc:  # pragma: no cover - network failures
            logging.error("Failed to poll Whisper-WebUI status: %s", exc)
            metadata["error"] = str(exc)
            return None, 0.0, metadata

        status = str(status_data.get("status", "")).lower()
        if not status:
            status = str(status_data.get("state", "")).lower()

        if status in {"queued", "pending", "in_progress", "processing"}:
            time.sleep(poll_interval)
            continue

        audio_duration = 0.0
        for key in ("duration", "audio_duration"):
            value = status_data.get(key)
            if value is not None:
                try:
                    audio_duration = float(value)
                except (TypeError, ValueError):
                    audio_duration = 0.0
                break

        if status in {"failed", "error", "cancelled"}:
            error_message = status_data.get("error") or f"task_{status}"
            metadata["error"] = error_message
            logging.error(
                "Whisper-WebUI task %s failed: %s", task_id, error_message
            )
            return None, audio_duration, metadata

        result = status_data.get("result")
        if isinstance(result, dict) and "text" in result:
            transcript = result.get("text") or ""
        elif isinstance(result, dict) and "segments" in result:
            transcript = _segments_to_text(result.get("segments"))
        elif isinstance(result, list):
            transcript = _segments_to_text(result)
        else:
            transcript = status_data.get("text", "")

        if not transcript:
            transcript = _segments_to_text(result)

        return transcript or None, audio_duration, metadata
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
