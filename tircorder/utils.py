import json
import logging
import os
import sqlite3
import subprocess
import time
from copy import deepcopy
from datetime import datetime, timezone
from os.path import join
from queue import Queue
from threading import Event, Lock
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import librosa
import requests
from gradio_client import Client, handle_file

from tircorder.interfaces.config import TircorderConfig


DEFAULT_TRANSCRIPTION_METHOD = "ctranslate2"
DEFAULT_WEBUI_CONFIG: Dict[str, Any] = {
    "base_url": "http://localhost:7860",
    "protocol": "gradio",
    "transcribe_path": "/_transcribe_file",
    "backend": {
        "submit_path": "/transcription",
        "task_path_template": "/task/{identifier}",
        "poll_interval_seconds": 3.0,
        "max_polls": 120,
    },
    "options": {
        "input_folder_path": "",
        "include_subdirectory": False,
        "save_same_dir": True,
        "process_separately": True,
        "file_format": "SRT",
        "add_timestamp": False,
        "whisper_model": "medium.en",
        "whisper_language": "Automatic Detection",
        "translate_to_english_whisper": False,
        "whisper_beam_size": 5,
        "whisper_log_probability_threshold": -1,
        "whisper_no_speech_threshold": 0.6,
        "whisper_compute_type": "int8",
        "whisper_best_of": 5,
        "whisper_patience": 1,
        "whisper_condition_on_previous_text": True,
        "whisper_prompt_reset_on_temperature": 0.5,
        "whisper_initial_prompt": "",
        "whisper_temperature": 0,
        "whisper_compression_ratio_threshold": 2.4,
        "whisper_length_penalty": 1,
        "whisper_repetition_penalty": 1,
        "whisper_no_repeat_n_gram_size": 0,
        "whisper_prefix": "",
        "whisper_suppress_blank": True,
        "whisper_suppress_tokens": "[-1]",
        "whisper_max_initial_timestamp": 1,
        "whisper_word_timestamps": False,
        "whisper_enable_whisperx_alignment": False,
        "whisper_prepend_punctuations": "\"'([{-",
        "whisper_append_punctuations": "\"'.!?)]},",
        "whisper_max_new_tokens": 0,
        "whisper_chunk_length_s": 30,
        "whisper_hallucination_silence_threshold_sec": 0,
        "whisper_hotwords": "",
        "whisper_language_detection_threshold": 0.5,
        "whisper_language_detection_segments": 1,
        "whisper_batch_size": 12,
        "whisper_whisperx_minimum_word_confidence": 0.65,
        "whisper_show_confidence_scores": False,
        "whisper_offload_sub_model_when_finished": True,
        "vad_enable_silero_vad_filter": True,
        "vad_speech_threshold": 0.5,
        "vad_minimum_speech_duration_ms": 250,
        "vad_maximum_speech_duration_s": 9999,
        "vad_minimum_silence_duration_ms": 2000,
        "vad_speech_padding_ms": 400,
        "diarization_enable_diarization": False,
        "diarization_device": "cpu",
        "diarization_compute_type": "float16",
        "diarization_huggingface_token": "",
        "diarization_use_whisperx_diarization": False,
        "diarization_tag_words_with_speaker_labels": False,
        "diarization_fallback_to_nearest_speaker_when_no_overlap": False,
        "diarization_offload_sub_model_when_finished": True,
        "bgm_separation_enable_background_music_remover_filter": False,
        "bgm_separation_model": "UVR-MDX-NET-Inst_HQ_4",
        "bgm_separation_device": "cuda",
        "bgm_separation_segment_size": 256,
        "bgm_separation_save_separated_files_to_output": False,
        "bgm_separation_offload_sub_model_when_finished": True,
    },
    "timeout": 600.0,
    "username": None,
    "password": None,
    "api_key": None,
    "headers": {},
    "verify_ssl": True,
    "emit_envelope": False,
    "envelope_dir": None,
    "envelope_format": "sb_execution_envelope_v1",
    "downstream": {
        "persist_raw_transcript": True,
        "sensiblaw": {
            "enabled": False,
            "storage_path": None,
        },
        "statibaker": {
            "enabled": False,
            "log_root": None,
        },
    },
}


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge nested dictionaries while preserving unspecified defaults."""

    merged = deepcopy(base)
    for key, value in override.items():
        if (
            isinstance(value, dict)
            and isinstance(merged.get(key), dict)
        ):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_transcription_backend(
    method_override: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
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
        merged = _deep_merge_dicts(DEFAULT_WEBUI_CONFIG, configured)
        return method, merged

    return method, transcription_config.get(method, {})


def load_recordings_folders_from_db(db_path="state.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, folder_path, ignore_transcribing, ignore_converting FROM recordings_folders"
    )
    folders = cursor.fetchall()
    conn.close()
    return folders


def _normalize_conversion_payload(payload: Any) -> Dict[str, Any]:
    """Return a standardized conversion payload from various queue item shapes."""

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, (list, tuple)) and len(payload) >= 3:
        return {
            "known_file_id": payload[0],
            "folder_path": payload[1],
            "file_name": payload[2],
        }

    return {"known_file_id": payload}


def _resolve_conversion_paths(
    payload: Dict[str, Any], recordings_folders
) -> Tuple[Optional[str], Optional[str]]:
    """Determine the input and output paths for a conversion payload.

    The lookup prefers explicit folder and file values from the payload, then
    falls back to the database using ``known_file_id`` if provided. Finally,
    it attempts to locate the file by name within the configured
    ``recordings_folders``.
    """

    known_file_id = payload.get("known_file_id")
    folder_path = payload.get("folder_path")
    file_name = payload.get("file_name")

    if folder_path and file_name:
        input_path = join(folder_path, file_name)
        return input_path, input_path.replace(".wav", ".flac")

    if known_file_id is not None:
        try:
            conn = sqlite3.connect("state.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT k.file_name, r.folder_path FROM known_files k "
                "JOIN recordings_folders r ON k.folder_id = r.id WHERE k.id = ?",
                (known_file_id,),
            )
            row = cursor.fetchone()
            if row:
                file_name, folder_path = row
                input_path = join(folder_path, file_name)
                return input_path, input_path.replace(".wav", ".flac")
        except sqlite3.Error as exc:
            logging.error(
                "Failed to resolve paths for known_file_id %s: %s", known_file_id, exc
            )
        finally:
            if "conn" in locals():
                conn.close()

    if file_name:
        for _, directory, _, _ in recordings_folders:
            input_path = join(directory, file_name)
            if os.path.exists(input_path):
                return input_path, input_path.replace(".wav", ".flac")

    return None, None


def wav2flac(
    CONVERT_QUEUE,
    converting_lock,
    transcribing_active,
    transcription_complete,
    process_status,
    recordings_folders,
):

    while True:
        transcription_complete.wait()
        queue_item = CONVERT_QUEUE.get()
        payload = _normalize_conversion_payload(queue_item)
        known_file_id = payload.get("known_file_id")
        attempts = 0

        while transcribing_active.is_set() and attempts < 5:
            logging.warning(
                "Waiting to convert %s as transcribing is active. Attempt %s/5",
                payload,
                attempts + 1,
            )
            time.sleep(10)
            attempts += 1

        if attempts == 5:
            logging.error(
                "Conversion skipped for %s after 5 attempts as transcribing is still active.",
                payload,
            )
            CONVERT_QUEUE.put(payload)
            continue

        with converting_lock:
            process_status.value = f"converting {payload}"
            input_path, output_path = _resolve_conversion_paths(
                payload, recordings_folders
            )

            if not input_path or not output_path:
                logging.error(
                    "File paths not found for payload %s (known_file_id=%s). Skipping conversion.",
                    payload,
                    known_file_id,
                )
                CONVERT_QUEUE.task_done()
                continue

            try:
                result = subprocess.run(
                    ["ffmpeg", "-i", input_path, "-c:a", "flac", output_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                logging.info(
                    "Conversion completed for payload %s -> %s.", payload, output_path
                )
                if result.stderr:
                    logging.error(
                        "Conversion errors for %s: %s",
                        payload,
                        result.stderr.decode(),
                    )
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to convert {payload} to FLAC: {e}")
            except Exception as e:
                logging.error(
                    "An error occurred while converting %s to FLAC: %s", payload, e
                )

            CONVERT_QUEUE.task_done()
            transcription_complete.clear()
            if not CONVERT_QUEUE.qsize():
                process_status.value = "housekeeping"
                logging.info(
                    "All conversion tasks completed, entering housekeeping mode."
                )


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
        logging.error(
            f"Unhandled error in transcribing audio {os.path.basename(file_path)}: {e}"
        )
        return None


def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"{file_path} not found.")
        return None
    except Exception as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return None


def load_state_from_disk():
    return load_json("state_backup.json")


def load_traversal_results():
    return load_json("Pelican/traversal_results.json")


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
    """Convert WhisperX-WebUI segments into a transcript string."""

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


def _join_base_url(base_url: str, path: str) -> str:
    if not path:
        return base_url
    base = base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _normalize_webui_result(
    result: Any,
    *,
    protocol: str,
    task_id: Optional[str] = None,
    raw_status: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], float, Dict[str, Any]]:
    """Normalize Gradio and backend responses to one metadata shape."""

    metadata: Dict[str, Any] = {
        "error": None,
        "segments": None,
        "model": None,
        "language": None,
        "task_id": task_id,
        "session_id": task_id,
        "is_final": True,
        "sequence": None,
        "partial_updates": [],
        "protocol": protocol,
        "raw_result": result,
        "raw_status": raw_status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    transcript: Optional[str] = None
    audio_duration = 0.0

    if isinstance(result, (list, tuple)) and result:
        transcript_candidate = result[0]
        transcript = (
            str(transcript_candidate) if transcript_candidate is not None else None
        )
        if len(result) > 1 and isinstance(result[1], (int, float)):
            audio_duration = float(result[1])
        if all(isinstance(item, dict) for item in result):
            metadata["segments"] = result
    elif isinstance(result, dict):
        if "text" in result:
            transcript = result.get("text") or None
        elif "segments" in result:
            transcript = _segments_to_text(result.get("segments")) or None
        metadata["segments"] = result.get("segments")
        metadata["model"] = result.get("model") or result.get("model_id")
        metadata["language"] = result.get("language")
        metadata["session_id"] = (
            result.get("session_id")
            or result.get("sessionId")
            or metadata["session_id"]
        )
        if "is_final" in result or "final" in result:
            metadata["is_final"] = bool(result.get("is_final", result.get("final")))
        metadata["sequence"] = result.get("sequence", result.get("seq"))
        metadata["partial_updates"] = list(
            result.get("partial_updates")
            or result.get("partials")
            or result.get("updates")
            or []
        )
        if isinstance(result.get("audio_duration"), (int, float)):
            audio_duration = float(result["audio_duration"])
    elif isinstance(result, str):
        transcript = result

    if not transcript and isinstance(result, (list, tuple)):
        transcript = _segments_to_text(result) or None

    metadata["transcript_payload"] = {
        "text": transcript or "",
        "model": metadata.get("model"),
        "language": metadata.get("language"),
        "segments": metadata.get("segments") or [],
    }

    return transcript, audio_duration, metadata


def _transcribe_webui_backend(
    file_path: str,
    *,
    base_url: str,
    options: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = 600.0,
    auth: Optional[Tuple[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
    submit_path: str = "/transcription",
    task_path_template: str = "/task/{identifier}",
    poll_interval_seconds: float = 3.0,
    max_polls: int = 120,
) -> Tuple[Optional[str], float, Dict[str, Any]]:
    """Send audio to WhisperX backend queue API and poll for completion."""

    try:
        with requests.Session() as session:
            if auth:
                session.auth = auth
            if headers:
                session.headers.update(headers)

            with open(file_path, "rb") as file_handle:
                response = session.post(
                    _join_base_url(base_url, submit_path),
                    files={"file": (os.path.basename(file_path), file_handle, "application/octet-stream")},
                    data=_prepare_webui_payload(options),
                    timeout=timeout,
                    verify=verify_ssl,
                )
            response.raise_for_status()
            queue_payload = response.json()
            task_id = queue_payload.get("identifier")
            if not task_id:
                raise ValueError("Backend response did not include an identifier")

            last_status: Dict[str, Any] = dict(queue_payload)
            for _ in range(max_polls):
                status_response = session.get(
                    _join_base_url(
                        base_url,
                        task_path_template.format(identifier=task_id),
                    ),
                    timeout=timeout,
                    verify=verify_ssl,
                )
                status_response.raise_for_status()
                last_status = status_response.json()
                status = str(last_status.get("status", "")).lower()
                if status == "completed":
                    return _normalize_webui_result(
                        last_status.get("result"),
                        protocol="backend",
                        task_id=task_id,
                        raw_status=last_status,
                    )
                if status == "failed":
                    metadata = {
                        "error": last_status.get("error") or "backend task failed",
                        "segments": None,
                        "model": None,
                        "language": None,
                        "task_id": task_id,
                        "session_id": task_id,
                        "is_final": True,
                        "sequence": None,
                        "partial_updates": [],
                        "protocol": "backend",
                        "raw_result": None,
                        "raw_status": last_status,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "transcript_payload": {
                            "text": "",
                            "model": None,
                            "language": None,
                            "segments": [],
                        },
                    }
                    return None, 0.0, metadata
                time.sleep(poll_interval_seconds)

        raise TimeoutError(f"Backend task {task_id} did not complete within {max_polls} polls")
    except Exception as exc:  # pragma: no cover - network failures
        logging.error("Failed to run WhisperX-WebUI backend queue API: %s", exc)
        return None, 0.0, {
            "error": str(exc),
            "segments": None,
            "model": None,
            "language": None,
            "task_id": None,
            "session_id": None,
            "is_final": True,
            "sequence": None,
            "partial_updates": [],
            "protocol": "backend",
            "raw_result": None,
            "raw_status": None,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "transcript_payload": {
                "text": "",
                "model": None,
                "language": None,
                "segments": [],
            },
        }


def transcribe_webui(
    file_path: str,
    *,
    base_url: str,
    options: Optional[Dict[str, Any]] = None,
    protocol: str = "gradio",
    transcribe_path: str = "/_transcribe_file",
    backend_submit_path: str = "/transcription",
    backend_task_path_template: str = "/task/{identifier}",
    poll_interval_seconds: float = 3.0,
    max_polls: int = 120,
    timeout: Optional[float] = 600.0,
    auth: Optional[Tuple[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
) -> Tuple[Optional[str], float, Dict[str, Any]]:
    """Send audio to WhisperX-WebUI and normalize the result.

    `protocol="backend"` targets the queued FastAPI service.
    `protocol="gradio"` targets the synchronous Gradio endpoint.
    """

    if protocol == "backend":
        return _transcribe_webui_backend(
            file_path,
            base_url=base_url,
            options=options,
            timeout=timeout,
            auth=auth,
            headers=headers,
            verify_ssl=verify_ssl,
            submit_path=backend_submit_path,
            task_path_template=backend_task_path_template,
            poll_interval_seconds=poll_interval_seconds,
            max_polls=max_polls,
        )

    metadata: Dict[str, Any] = {"error": None, "segments": None, "model": None, "language": None}

    try:
        client_kwargs: Dict[str, Any] = {"ssl_verify": verify_ssl}
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        if auth:
            client_kwargs["auth"] = auth
        if headers:
            client_kwargs["headers"] = headers
        try:
            client = Client(base_url, **client_kwargs)
        except TypeError:
            logging.warning(
                "gradio_client.Client does not accept provided auth/header kwargs; retrying with limited options"
            )
            fallback_kwargs: Dict[str, Any] = {"ssl_verify": verify_ssl}
            if timeout is not None:
                try:
                    client = Client(base_url, timeout=timeout, ssl_verify=verify_ssl)
                except TypeError:
                    client = Client(base_url, **fallback_kwargs)
            else:
                client = Client(base_url, **fallback_kwargs)

        payload = {"files": [handle_file(file_path)]}
        payload.update(_prepare_webui_payload(options))

        predict_kwargs: Dict[str, Any] = {"api_name": transcribe_path, **payload}

        result = client.predict(**predict_kwargs)
    except Exception as exc:  # pragma: no cover - network failures
        logging.error("Failed to run WhisperX-WebUI via gradio_client: %s", exc)
        metadata.update(
            {
                "error": str(exc),
                "task_id": None,
                "session_id": None,
                "is_final": True,
                "sequence": None,
                "partial_updates": [],
                "protocol": "gradio",
                "raw_result": None,
                "raw_status": None,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "transcript_payload": {
                    "text": "",
                    "model": None,
                    "language": None,
                    "segments": [],
                },
            }
        )
        return None, 0.0, metadata

    transcript, audio_duration, normalized = _normalize_webui_result(
        result,
        protocol="gradio",
    )
    normalized["error"] = metadata["error"]
    return transcript, audio_duration, normalized


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
        "--model",
        "medium.en",
        "--language",
        "en",
        "--output_dir",
        output_dir,  # No need to quote within the list
        "--device",
        "cpu",
    ]

    try:
        output_text = []
        start_time = None
        end_time = None
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) as proc:
            for line in proc.stdout:
                if "Processing audio" in line:
                    # Extract segment times from the line
                    parts = line.split()
                    start_time = float(parts[3].replace("s", ""))
                    end_time = float(parts[5].replace("s", ""))
                output_text.append(line)
                logging.info(line.strip())  # Log the progressive output
            for err_line in proc.stderr:
                logging.error(f"Transcription errors: {err_line.strip()}")

        proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

        total_audio_duration = end_time - start_time if start_time and end_time else 0
        return "".join(output_text), total_audio_duration

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
