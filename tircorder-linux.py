"""Launcher for starting the Tircorder server and client on Linux."""

from __future__ import annotations

import subprocess
import sys
from typing import Iterable, List

SERVER_COMMAND: List[str] = [sys.executable, "run", "j_servski-11-05-24-9.py"]
CLIENT_COMMAND: List[str] = [sys.executable, "jobbie_gpt_CLIENT_05-10-2024.py"]


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


def main_menu() -> str:
    """Prompt the user for which components to run."""

    return input(
        "Choose an option:\n0. Run Server\n1. Run Client\n2. Run Both\n"
        "Enter choice (0, 1, 2): "
    )


def launch_process(command: Iterable[str]) -> subprocess.Popen[str]:
    """Start a process in the current terminal."""

    command_list = list(command)
    print(f"Launching: {' '.join(command_list)}")
    return subprocess.Popen(command_list)


def run_server() -> subprocess.Popen[str]:
    """Start the server process."""

    print("Starting server...")
    return launch_process(SERVER_COMMAND)


def run_client() -> subprocess.Popen[str]:
    """Start the client process."""

    print("Starting client...")
    return launch_process(CLIENT_COMMAND)


if __name__ == "__main__":
    check_for_updates()
    check_install_requirements()

    choice = main_menu()
    if choice == "0":
        run_server().wait()
    elif choice == "1":
        run_client().wait()
    elif choice == "2":
        print("Running both server and client in separate processes.")
        processes = [run_server(), run_client()]
        for process in processes:
            process.wait()
    else:
        print("Invalid choice. Exiting...")
