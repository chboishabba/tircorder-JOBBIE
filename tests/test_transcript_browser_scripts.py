"""Keep bounded JS regression coverage on the legacy transcript-browser helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def test_transcript_browser_scripts_unit_suite() -> None:
    """Validate retained legacy behavior while the UI migrates to `itir-svelte/`."""

    node_binary = shutil.which("node")
    if node_binary is None:
        pytest.skip("node is not installed")

    repo_root = Path(__file__).resolve().parents[1]
    script_test = repo_root / "tests" / "node" / "test_transcript_browser_scripts.test.js"
    result = subprocess.run(
        [node_binary, "--test", str(script_test)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        pytest.fail(f"Node transcript browser tests failed:\n{output}")
