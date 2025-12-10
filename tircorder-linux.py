"""Launcher for starting the Tircorder server and client on Linux."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable, List, Optional

import pyaudio

DEFAULT_SERVER_SCRIPT = "j_servski-11-05-24-9.py"
CLIENT_SCRIPT = "jobbie_gpt_CLIENT_05-10-2024.py"


def check_for_updates() -> None:
    """Fetch the latest code changes."""

    print("Checking for updates...")
    try:
        subprocess.run(["git", "pull"], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to update: {exc}")
    else:
        print("Update check complete.")


def check_install_requirements() -> None:
    """Install Python dependencies if needed."""

    print("Checking and installing requirements...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install required packages: {exc}")
    else:
        print("Requirements are up to date.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Tircorder launcher")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--server", action="store_true", help="Run server only")
    mode.add_argument("--client", action="store_true", help="Run client only")
    mode.add_argument("--both", action="store_true", help="Run server and client")

    parser.add_argument(
        "--server-script",
        help=f"Server script to run (defaults to {DEFAULT_SERVER_SCRIPT} or prompts)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Directory for server to watch for audio/transcripts",
    )
    parser.add_argument(
        "--device-id",
        type=int,
        help="Audio input device id to pass to the client",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to store client recordings (created if missing)",
    )
    parser.add_argument(
        "--webui-url",
        type=str,
        help="Base URL for WhisperX-WebUI backend",
    )
    parser.add_argument(
        "--webui-path",
        type=str,
        default="/_transcribe_file",
        help="Transcription endpoint path for WhisperX-WebUI",
    )
    return parser.parse_args()


def launch_process(command: Iterable[str]) -> subprocess.Popen[str]:
    """Start a process in the current terminal."""

    command_list = list(command)
    print(f"Launching: {' '.join(command_list)}")
    return subprocess.Popen(command_list)


def available_server_scripts() -> List[str]:
    """Return server scripts matching the naming convention."""

    scripts = sorted(Path(".").glob("j_servski-*.py"))
    return [str(path) for path in scripts]


def choose_server_script(provided: Optional[str]) -> str:
    """Resolve which server script to run."""

    if provided:
        if os.path.exists(provided):
            return provided
        raise FileNotFoundError(f"Server script not found: {provided}")

    options = available_server_scripts()
    if not options:
        raise FileNotFoundError("No server scripts found matching j_servski-*.py")

    if len(options) == 1:
        return options[0]

    print("Select a server script:")
    for idx, name in enumerate(options):
        print(f"{idx}. {name}")
    choice = input("Enter choice (default 0): ").strip()
    choice_idx = int(choice) if choice else 0
    if choice_idx < 0 or choice_idx >= len(options):
        raise ValueError("Invalid server selection.")
    return options[choice_idx]


def prompt_device_id() -> Optional[int]:
    """Prompt the user for a microphone device id."""

    p = pyaudio.PyAudio()
    devices = []
    print("Available input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append(i)
            print(f"{i}: {info['name']}")
    p.terminate()

    if not devices:
        print("No input devices detected.")
        return None

    choice = input(f"Select device id (default {devices[0]}): ").strip()
    device_id = int(choice) if choice else devices[0]
    if device_id not in devices:
        print("Invalid device id selected.")
        return None
    return device_id


def prompt_output_dir(default: str = "recordings") -> str:
    """Prompt the user for an output directory for recordings."""

    choice = input(f"Recording output directory (default {default}): ").strip()
    return choice or default


def build_server_command(
    server_script: str,
    data_dir: Optional[str],
    webui_url: Optional[str],
    webui_path: Optional[str],
) -> List[str]:
    """Build the server command line."""

    cmd = [sys.executable, server_script]
    if data_dir:
        cmd.extend(["--data-dir", data_dir])
    if webui_url:
        cmd.extend(["--webui-url", webui_url])
        if webui_path:
            cmd.extend(["--webui-path", webui_path])
    return cmd


def build_client_command(
    device_id: Optional[int],
    output_dir: Optional[str],
    webui_url: Optional[str],
    webui_path: Optional[str],
) -> List[str]:
    """Build the client command line."""

    cmd = [sys.executable, CLIENT_SCRIPT]
    if device_id is not None:
        cmd.extend(["--device-id", str(device_id)])
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if webui_url:
        cmd.extend(["--webui-url", webui_url])
        if webui_path:
            cmd.extend(["--webui-path", webui_path])
    return cmd


def main() -> None:
    args = parse_args()

    check_for_updates()
    check_install_requirements()

    mode = "prompt"
    if args.server:
        mode = "server"
    elif args.client:
        mode = "client"
    elif args.both:
        mode = "both"

    if mode == "prompt":
        mode_choice = input(
            "Choose an option:\n0. Run Server\n1. Run Client\n2. Run Both\n"
            "Enter choice (0, 1, 2): "
        )
        mode = {"0": "server", "1": "client", "2": "both"}.get(mode_choice, "invalid")
        if mode == "invalid":
            print("Invalid choice. Exiting...")
            return

    device_id = args.device_id
    output_dir = args.output_dir
    server_script = None
    data_dir = args.data_dir
    if mode in {"server", "both"} and data_dir is None:
        # Reuse output_dir if provided; otherwise prompt separately.
        data_dir = output_dir or prompt_output_dir()

    if mode in {"server", "both"}:
        server_script = choose_server_script(args.server_script)
    if mode in {"client", "both"}:
        if device_id is None:
            device_id = prompt_device_id()
        if output_dir is None:
            output_dir = prompt_output_dir()

    processes = []
    if mode in {"server", "both"}:
        server_cmd = build_server_command(
            server_script or DEFAULT_SERVER_SCRIPT,
            data_dir,
            args.webui_url,
            args.webui_path,
        )
        print("Starting server...")
        processes.append(launch_process(server_cmd))

    if mode in {"client", "both"}:
        client_cmd = build_client_command(
            device_id, output_dir, args.webui_url, args.webui_path
        )
        print("Starting client...")
        processes.append(launch_process(client_cmd))

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("Shutdown requested. Terminating child processes...")
        for process in processes:
            try:
                process.terminate()
            except Exception:
                pass
        for process in processes:
            try:
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
