import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from queue import Queue
from typing import Dict, Optional

from .sb_adapter import build_execution_envelope, write_execution_envelope
from .state import export_queues_and_files, load_state
from .utils import (
    get_transcription_backend,
    transcribe_audio,
    transcribe_ct2,
    transcribe_ct2_nonpythonic,
    transcribe_webui,
)

audio_extensions = [".wav", ".flac", ".mp3", ".ogg", ".amr"]


def _coerce_bool(value: Optional[object], default: bool = True) -> bool:
    """Return a boolean value from user-provided configuration."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off", ""}
    return bool(value)


def transcriber(
    TRANSCRIBE_QUEUE,
    CONVERT_QUEUE,
    TRANSCRIBE_ACTIVE,
    transcription_complete,
    model,
    transcription_method: Optional[str] = None,
    backend_overrides: Optional[Dict[str, Dict[str, object]]] = None,
):
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = (
        load_state()
    )
    proc_comp_timestamps_transcribe = []

    backend_overrides = backend_overrides or {}
    transcription_method, configured_backend = get_transcription_backend(
        transcription_method
    )
    webui_config = configured_backend if isinstance(configured_backend, dict) else {}
    if transcription_method == "webui":
        override_values = backend_overrides.get("webui", {})
        webui_config = {**webui_config, **override_values}

    def execute_with_retry(query, params=(), retries=5, delay=1):
        conn = sqlite3.connect("state.db")
        cursor = conn.cursor()
        for attempt in range(retries):
            try:
                cursor.execute(query, params)
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(
                        f"Database is locked, retrying in {delay} seconds... (attempt {attempt + 1})"
                    )
                    time.sleep(delay)
                else:
                    raise
            finally:
                conn.close()
        logging.error(f"Failed to execute query after {retries} attempts: {query}")
        raise sqlite3.OperationalError("Database is locked and retries exhausted")

    while True:
        known_file_id = TRANSCRIBE_QUEUE.get()
        start_time = datetime.now()
        TRANSCRIBE_ACTIVE.set()

        conn = sqlite3.connect("state.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT k.file_name, r.folder_path FROM known_files k JOIN recordings_folders r ON k.folder_id = r.id WHERE k.id = ?",
            (known_file_id,),
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            logging.error(
                f"File with known_file_id {known_file_id} not found in database."
            )
            continue

        file_name, folder_path = result
        file = os.path.join(folder_path, file_name)

        if not file_name.endswith(tuple(audio_extensions)):
            logging.info(f"Skipping non-audio file: {file}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(
            f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting transcription for {file}."
        )

        output_text = None
        audio_duration = 0.0
        metadata = {}

        if transcription_method == "python_whisper":
            output_text = transcribe_audio(file)
        elif transcription_method == "ctranslate2":
            output_text, audio_duration = transcribe_ct2(file, model, skip_files)
        elif transcription_method == "ctranslate2_nonpythonic":
            output_text, audio_duration = transcribe_ct2_nonpythonic(file)
        elif transcription_method == "webui":
            if not webui_config.get("base_url"):
                error_message = "WebUI base_url is not configured"
                logging.error(error_message)
                metadata = {"error": error_message}
            else:
                timeout_value = webui_config.get("timeout")
                if timeout_value is not None:
                    try:
                        timeout_value = float(timeout_value)
                    except (TypeError, ValueError):
                        logging.warning(
                            "Invalid timeout value '%s' provided for WebUI backend; using no timeout",
                            timeout_value,
                        )
                        timeout_value = None

                headers = dict(webui_config.get("headers") or {})
                api_key = webui_config.get("api_key")
                if api_key and "authorization" not in {
                    key.lower(): key for key in headers
                }:
                    headers["Authorization"] = f"Bearer {api_key}"

                auth_credentials = None
                if webui_config.get("username"):
                    auth_credentials = (
                        webui_config.get("username"),
                        webui_config.get("password", ""),
                    )

                output_text, audio_duration, metadata = transcribe_webui(
                    file,
                    base_url=webui_config.get("base_url", ""),
                    options=webui_config.get("options"),
                    transcribe_path=webui_config.get("transcribe_path", "/_transcribe_file"),
                    timeout=timeout_value,
                    auth=auth_credentials,
                    headers=headers,
                    verify_ssl=_coerce_bool(webui_config.get("verify_ssl"), True),
                )
            if metadata.get("task_id"):
                logging.info(
                    "WhisperX-WebUI task %s started for %s",
                    metadata["task_id"],
                    file,
                )
            if metadata.get("error"):
                logging.error(
                    "WhisperX-WebUI transcription error for %s: %s",
                    file,
                    metadata["error"],
                )
        else:
            logging.error(f"Unsupported transcription method: {transcription_method}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(f"Processing audio with duration {audio_duration:.3f}s")

        if output_text is not None:
            output_path = os.path.splitext(file)[0] + ".txt"
            try:
                with open(output_path, "w") as f:
                    f.write(output_text)
                if transcription_method == "webui" and webui_config.get("emit_envelope"):
                    transcript_payload = {
                        "text": output_text,
                        "model": metadata.get("model"),
                        "language": metadata.get("language"),
                        "segments": metadata.get("segments") or [],
                    }
                    envelope_payload = build_execution_envelope(
                        transcript_payload,
                        source="whisperx_webui",
                        model=metadata.get("model"),
                        language=metadata.get("language"),
                        audio_path=file,
                        adapter_label="tircorder_whisperx_webui_v1",
                        envelope_format=webui_config.get(
                            "envelope_format", "sb_execution_envelope_v1"
                        ),
                    )
                    envelope_dir = webui_config.get("envelope_dir")
                    envelope_path = (
                        os.path.join(envelope_dir, os.path.basename(output_path))
                        if envelope_dir
                        else output_path
                    )
                    envelope_path = (
                        os.path.splitext(envelope_path)[0]
                        + ".execution_envelope.json"
                    )
                    write_execution_envelope(envelope_path, envelope_payload)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                real_time_factor = (
                    audio_duration / elapsed_time if elapsed_time > 0 else 0
                )
                proc_comp_timestamps_transcribe.append(datetime.now())
                logging.info(
                    f"SYSTIME: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | File {file} transcribed in {elapsed_time:.2f}s (x{real_time_factor:.2f})."
                )
                TRANSCRIBE_QUEUE.task_done()
            except Exception as e:
                logging.error(f"Error writing transcription output for {file}: {e}")
                skip_files.add(file)
                skip_reasons[file] = "transcription_output_error"
                execute_with_retry(
                    "INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)",
                    (known_file_id, "transcription_output_error"),
                )
                TRANSCRIBE_QUEUE.task_done()
                continue
        else:
            logging.error(f"Transcription failed for {file}.")
            skip_files.add(file)
            error_reason = None
            if transcription_method == "webui" and metadata.get("error"):
                error_reason = f"webui_error:{metadata['error']}"
            elif metadata.get("error"):
                error_reason = str(metadata["error"])
            skip_reason = error_reason or "transcription_failed"
            skip_reasons[file] = skip_reason
            execute_with_retry(
                "INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)",
                (known_file_id, skip_reason),
            )
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(
            f"SYSTIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | File {file} added to conversion queue. {CONVERT_QUEUE.qsize() + 1} files waiting for conversion. {TRANSCRIBE_QUEUE.qsize()} left to transcribe. Processing rates: {len(proc_comp_timestamps_transcribe) / (timedelta(seconds=len(proc_comp_timestamps_transcribe)).total_seconds() / 60):.2f} files/hour, {len(proc_comp_timestamps_transcribe) / (timedelta(seconds=len(proc_comp_timestamps_transcribe)).total_seconds() / 60):.2f} files/minute."
        )
        conversion_payload = {
            "known_file_id": known_file_id,
            "folder_path": folder_path,
            "file_name": file_name,
        }
        execute_with_retry(
            "INSERT INTO convert_queue (known_file_id) VALUES (?)", (known_file_id,)
        )
        CONVERT_QUEUE.put(conversion_payload)
        if TRANSCRIBE_QUEUE.qsize() == 0:
            logging.info(
                "All transcription tasks completed, entering housekeeping mode."
            )
            transcription_complete.set()
            TRANSCRIBE_ACTIVE.clear()
