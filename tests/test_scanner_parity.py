import os
import subprocess
from pathlib import Path

from tircorder.scanner import scan_directories


def create_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"data")


def test_scanner_parity(tmp_path):
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir3 = tmp_path / "dir3"
    dir1.mkdir()
    dir2.mkdir()
    dir3.mkdir()

    a = dir1 / "a.wav"
    create_file(a)
    b = dir1 / "b.wav"
    create_file(b)
    create_file(dir1 / "b.flac")
    c = dir1 / "c.wav"
    create_file(c)
    create_file(dir1 / "c.srt")

    d = dir2 / "d.wav"
    create_file(d)

    e = dir3 / "e.wav"
    create_file(e)

    dirs = [
        (str(dir1), False, False),
        (str(dir2), True, False),
        (str(dir3), False, True),
    ]

    py_transcribe, py_convert = scan_directories(dirs)

    cmd = [
        "cargo",
        "run",
        "--quiet",
        "--bin",
        "scan_cli",
        "--",
    ]
    for path, ignore_t, ignore_c in dirs:
        cmd.extend([path, "1" if ignore_t else "0", "1" if ignore_c else "0"])
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=repo_root)
    rust_transcribe = []
    rust_convert = []
    for line in result.stdout.strip().splitlines():
        if line.startswith("T:"):
            rust_transcribe.append(line[2:])
        elif line.startswith("C:"):
            rust_convert.append(line[2:])

    assert sorted(py_transcribe) == sorted(rust_transcribe)
    assert sorted(py_convert) == sorted(rust_convert)
