import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from queue import Empty, Queue
from typing import Dict, Optional, Tuple

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
        for attempt in range(retries):
            conn = sqlite3.connect("state.db")
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logging.warning(
                        "Database is locked, retrying in %s seconds... (attempt %s)",
                        delay,
                        attempt + 1,
                    )
                    time.sleep(delay)
                else:
                    raise
            finally:
                conn.close()
        logging.error("Failed to execute query after %s attempts: %s", retries, query)
        raise sqlite3.OperationalError("Database is locked and retries exhausted")

    def resolve_known_file(known_file_id: int) -> Optional[Tuple[str, str]]:
        conn = sqlite3.connect("state.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT k.file_name, r.folder_path FROM known_files k "
            "JOIN recordings_folders r ON k.folder_id = r.id WHERE k.id = ?",
            (known_file_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return result

    def finalize_transcription(
        *,
        known_file_id: int,
        file: str,
        start_time: datetime,
        output_text: Optional[str],
        audio_duration: float,
        metadata: Optional[Dict[str, object]] = None,
    ) -> None:
        metadata = metadata or {}

        logging.info("Processing audio with duration %.3fs", audio_duration)

        if output_text is not None:
            output_path = os.path.splitext(file)[0] + ".txt"
            try:
                with open(output_path, "w") as f:
                    f.write(output_text)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                real_time_factor = (
                    audio_duration / elapsed_time if elapsed_time > 0 else 0
                )
                proc_comp_timestamps_transcribe.append(datetime.now())
                logging.info(
                    "SYSTIME: %s | File %s transcribed in %.2fs (x%.2f).",
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    file,
                    elapsed_time,
                    real_time_factor,
                )
            except Exception as e:
                logging.error("Error writing transcription output for %s: %s", file, e)
                skip_files.add(file)
                skip_reasons[file] = "transcription_output_error"
                execute_with_retry(
                    "INSERT OR IGNORE INTO skip_files (known_file_id, reason) VALUES (?, ?)",
                    (known_file_id, "transcription_output_error"),
                )
                TRANSCRIBE_QUEUE.task_done()
                return

            execute_with_retry(
                "INSERT INTO convert_queue (known_file_id) VALUES (?)",
                (known_file_id,),
            )
            CONVERT_QUEUE.put(known_file_id)
            logging.info(
                "SYSTIME: %s | File %s added to conversion queue. %s files waiting for conversion. "
                "%s left to transcribe. Processing rates: %.2f files/hour, %.2f files/minute.",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                file,
                CONVERT_QUEUE.qsize(),
                TRANSCRIBE_QUEUE.qsize(),
                len(proc_comp_timestamps_transcribe)
                / (
                    timedelta(
                        seconds=len(proc_comp_timestamps_transcribe)
                    ).total_seconds()
                    / 60
                ),
                len(proc_comp_timestamps_transcribe)
                / (
                    timedelta(
                        seconds=len(proc_comp_timestamps_transcribe)
                    ).total_seconds()
                    / 60
                ),
            )
        else:
            logging.error("Transcription failed for %s.", file)
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

        if TRANSCRIBE_QUEUE.qsize() == 0:
            logging.info(
                "All transcription tasks completed, entering housekeeping mode."
            )
            transcription_complete.set()
            TRANSCRIBE_ACTIVE.clear()

    while True:
        known_file_id = TRANSCRIBE_QUEUE.get()
        start_time = datetime.now()
        TRANSCRIBE_ACTIVE.set()

        resolved = resolve_known_file(known_file_id)
        if not resolved:
            logging.error(
                "File with known_file_id %s not found in database.", known_file_id
            )
            TRANSCRIBE_QUEUE.task_done()
            continue

        file_name, folder_path = resolved
        file = os.path.join(folder_path, file_name)

        if not file_name.endswith(tuple(audio_extensions)):
            logging.info("Skipping non-audio file: %s", file)
            TRANSCRIBE_QUEUE.task_done()
            continue

        logging.info(
            "SYSTIME: %s | Starting transcription for %s.",
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            file,
        )

        if transcription_method == "webui":
            pending_fragments = [
                {"known_file_id": known_file_id, "file": file, "start_time": start_time}
            ]
            webui_task_states: Dict[str, str] = {}

            def enqueue_pending_fragment(k_file_id: int, source: str) -> None:
                fragment_record = resolve_known_file(k_file_id)
                if not fragment_record:
                    logging.error(
                        "File with known_file_id %s not found while batching.",
                        k_file_id,
                    )
                    TRANSCRIBE_QUEUE.task_done()
                    return

                frag_name, frag_folder = fragment_record
                frag_path = os.path.join(frag_folder, frag_name)
                if not frag_name.endswith(tuple(audio_extensions)):
                    logging.info("Skipping non-audio file during batch: %s", frag_path)
                    TRANSCRIBE_QUEUE.task_done()
                    return

                pending_fragments.append(
                    {
                        "known_file_id": k_file_id,
                        "file": frag_path,
                        "start_time": datetime.now(),
                    }
                )
                logging.info(
                    "Queued recorder fragment %s from %s pull (batch size=%d)",
                    frag_path,
                    source,
                    len(pending_fragments),
                )

            while True:
                try:
                    additional_known_file_id = TRANSCRIBE_QUEUE.get_nowait()
                except Empty:
                    break
                enqueue_pending_fragment(additional_known_file_id, "initial")

            processed_count = 0
            while pending_fragments:
                fragment = pending_fragments.pop(0)
                processed_count += 1
                fragment_file = fragment["file"]
                fragment_id = fragment["known_file_id"]
                fragment_start = fragment["start_time"]

                logging.info(
                    "Submitting Whisper-WebUI batch item %d (pending: %d): %s",
                    processed_count,
                    len(pending_fragments),
                    fragment_file,
                )

                if not webui_config.get("base_url"):
                    error_message = "WebUI base_url is not configured"
                    logging.error(error_message)
                    fragment_metadata = {"error": error_message}
                    fragment_output = None
                    fragment_duration = 0.0
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

                    fragment_output, fragment_duration, fragment_metadata = (
                        transcribe_webui(
                            fragment_file,
                            base_url=webui_config.get("base_url", ""),
                            options=webui_config.get("options"),
                            poll_interval=float(webui_config.get("poll_interval", 2.0)),
                            timeout=timeout_value,
                            auth=auth_credentials,
                            headers=headers,
                            verify_ssl=_coerce_bool(
                                webui_config.get("verify_ssl"), True
                            ),
                            status_path=webui_config.get(
                                "status_path", "/task/{task_id}"
                            ),
                        )
                    )

                task_id = fragment_metadata.get("task_id")
                if task_id:
                    webui_task_states[str(task_id)] = (
                        "completed" if not fragment_metadata.get("error") else "failed"
                    )
                    logging.info(
                        "Whisper-WebUI task %s completed for %s (%d processed, %d pending).",
                        task_id,
                        fragment_file,
                        processed_count,
                        len(pending_fragments),
                    )
                if fragment_metadata.get("error"):
                    logging.error(
                        "Whisper-WebUI transcription error for %s: %s",
                        fragment_file,
                        fragment_metadata["error"],
                    )

                finalize_transcription(
                    known_file_id=fragment_id,
                    file=fragment_file,
                    start_time=fragment_start,
                    output_text=fragment_output,
                    audio_duration=fragment_duration,
                    metadata=fragment_metadata,
                )

                while True:
                    try:
                        new_known_file_id = TRANSCRIBE_QUEUE.get_nowait()
                    except Empty:
                        break
                    enqueue_pending_fragment(new_known_file_id, "follow-up")

                logging.info(
                    "WebUI batch progress: %d completed, %d pending.",
                    processed_count,
                    len(pending_fragments),
                )

            if webui_task_states:
                logging.info("WebUI task states: %s", webui_task_states)

            continue

        output_text = None
        audio_duration = 0.0
        metadata: Dict[str, object] = {}

        if transcription_method == "python_whisper":
            output_text = transcribe_audio(file)
        elif transcription_method == "ctranslate2":
            output_text, audio_duration = transcribe_ct2(file, model, skip_files)
        elif transcription_method == "ctranslate2_nonpythonic":
            output_text, audio_duration = transcribe_ct2_nonpythonic(file)
        else:
            logging.error(f"Unsupported transcription method: {transcription_method}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        finalize_transcription(
            known_file_id=known_file_id,
            file=file,
            start_time=start_time,
            output_text=output_text,
            audio_duration=audio_duration,
            metadata=metadata,
        )
