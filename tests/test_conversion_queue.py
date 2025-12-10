import os
import sqlite3
import threading
import types
from queue import Queue
from types import SimpleNamespace

import subprocess
import sys

# ``tircorder.utils`` depends on librosa, which is not installed in the test
# environment. Provide a minimal stub to satisfy imports during test collection.
if "librosa" not in sys.modules:
    sys.modules["librosa"] = types.SimpleNamespace(load=lambda *_, **__: ([], None))
if "requests" not in sys.modules:

    class _DummySession:
        pass

    sys.modules["requests"] = types.SimpleNamespace(
        get=lambda *_, **__: None,
        post=lambda *_, **__: None,
        Session=_DummySession,
    )

from tircorder.utils import (
    _normalize_conversion_payload,
    _resolve_conversion_paths,
    wav2flac,
)


def test_resolve_paths_prefers_payload(tmp_path):
    wav_file = tmp_path / "clip.wav"
    wav_file.write_bytes(b"RIFF")

    payload = {
        "known_file_id": 1,
        "folder_path": str(tmp_path),
        "file_name": wav_file.name,
    }

    input_path, output_path = _resolve_conversion_paths(payload, [])

    assert input_path == str(wav_file)
    assert output_path == str(wav_file).replace(".wav", ".flac")


def test_resolve_paths_falls_back_to_db(tmp_path, monkeypatch):
    db_path = tmp_path / "state.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE recordings_folders (id INTEGER PRIMARY KEY, folder_path TEXT, ignore_transcribing INTEGER, ignore_converting INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE known_files (id INTEGER PRIMARY KEY, file_name TEXT, folder_id INTEGER)"
    )
    cursor.execute(
        "INSERT INTO recordings_folders (id, folder_path, ignore_transcribing, ignore_converting) VALUES (1, ?, 0, 0)",
        (str(tmp_path),),
    )
    cursor.execute(
        "INSERT INTO known_files (id, file_name, folder_id) VALUES (42, 'db_clip.wav', 1)"
    )
    conn.commit()
    conn.close()

    # Ensure the resolver looks at the temporary database
    monkeypatch.chdir(tmp_path)

    payload = {"known_file_id": 42}
    input_path, output_path = _resolve_conversion_paths(payload, [])

    expected_input = os.path.join(str(tmp_path), "db_clip.wav")
    assert input_path == expected_input
    assert output_path == expected_input.replace(".wav", ".flac")


def test_wav2flac_consumes_structured_payload(tmp_path, monkeypatch):
    wav_file = tmp_path / "queued.wav"
    wav_file.write_bytes(b"RIFF")

    payload = _normalize_conversion_payload(
        {"known_file_id": 7, "folder_path": str(tmp_path), "file_name": wav_file.name}
    )

    convert_queue: Queue = Queue()
    convert_queue.put(payload)

    converting_lock = threading.Lock()
    transcribing_active = threading.Event()
    transcription_complete = threading.Event()
    transcription_complete.set()
    process_status = SimpleNamespace(value="")
    recordings_folders = [(1, str(tmp_path), False, False)]

    def fake_run(cmd, stdout=None, stderr=None):
        # Write an output file to simulate conversion success
        (tmp_path / "queued.flac").write_text("converted")
        return SimpleNamespace(stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    converter_thread = threading.Thread(
        target=wav2flac,
        args=(
            convert_queue,
            converting_lock,
            transcribing_active,
            transcription_complete,
            process_status,
            recordings_folders,
        ),
        daemon=True,
    )
    converter_thread.start()

    convert_queue.join()

    assert (tmp_path / "queued.flac").exists()
    assert process_status.value
