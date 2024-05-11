import os
import threading
import time
import subprocess
from queue import Queue

from collections import defaultdict
import datetime

# Globals
transcribe_queue = Queue()
convert_queue = Queue()
active_processes = []
process_status = 'housekeeping'
transcribing_lock = threading.Lock()
converting_lock = threading.Lock()
transcribing_active = threading.Event()

playlists = defaultdict(list) # Playlist dictionary, mapping a date to a list of FLAC files

def scanner(directory, known_files, currently_processing):
    while True:
        current_files = set(os.listdir(directory))
        new_files = list(current_files - known_files)

        # Sort new files by the timestamp in the filename
        new_files.sort(key=lambda x: datetime.datetime.strptime(x.split('.')[0], '%Y-%m-%d_%H-%M-%S'))

        for file in new_files:
            if file.endswith(".wav"):
                datetime_str = file.split('.')[0]
                transcript_exists = any(os.path.exists(os.path.join(directory, f"{datetime_str}.{ext}")) for ext in ["txt", "srt", "vtt", "json"])
                if not transcript_exists and file not in currently_processing:
                    transcribe_queue.put(file)
                    currently_processing.add(file)  # Mark this file as currently being processed

        known_files.update(new_files)
        time.sleep(1)  # Scan every second



def transcribe(file):
    global process_status
    while True:
        file = transcribe_queue.get()
        process_status = f'transcribing {file}'
        transcribing_active.set()  # Signal that transcribing is active
        with transcribing_lock:
            print(f"Transcribing {file}")
            input_path = os.path.join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = os.path.splitext(input_path)[0] + '.txt'  # Using os.path.splitext to replace the extension correctly
            cmd = ["whisper", input_path, "--model", "medium", "--language", "en", "--output", output_path]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                print(f"Transcription output: {result.stdout}")
                if result.stderr:
                    print(f"Transcription errors: {result.stderr}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to transcribe {file}: {e}")
            except Exception as e:
                print(f"An error occurred while transcribing {file}: {e}")
            
            convert_queue.put(file.replace('.wav', '.flac'))
            transcribe_queue.task_done()
        
        transcribing_active.clear()  # Signal that transcribing is done
        if not transcribe_queue.qsize():
            process_status = 'housekeeping'


def wav2flac():
    global process_status
    while True:
        transcribing_active.wait()  # Wait until transcribing is not active
        file = convert_queue.get()
        with converting_lock:
            if transcribing_active.is_set():
                continue  # Skip conversion if transcribing has restarted
            process_status = 'converting' + file
            print(f"Converting {file} to FLAC")
            input_path = os.path.join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = input_path.replace('.wav', '.flac')
            subprocess.run(["ffmpeg", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE)
            convert_queue.task_done()
            if not convert_queue.qsize():
                process_status = 'housekeeping'

                


def update_playlists(directory, file):
    if file.endswith(".flac"):
        date_str = file.split('_')[0]
        playlists[date_str].append(file)

def scanner(directory, known_files):
    while True:
        current_files = set(os.listdir(directory))
        new_files = current_files - known_files
        for file in new_files:
            if file.endswith(".wav"):
                datetime_str = file.split('.')[0]
                transcript_exists = any(os.path.exists(os.path.join(directory, f"{datetime_str}.{ext}")) for ext in ["txt", "srt", "vtt", "json"])
                if not transcript_exists:
                    transcribe_queue.put(file)
                else:
                    convert_queue.put(file)
            elif file.endswith(".flac"):
                update_playlists(directory, file)
        known_files.update(new_files)
        print(len(playlists))  # Optionally print the current playlists for debugging
        time.sleep(1)  # Scan every second


def webSlinger():
    while True:
        print("Running webSlinger")
        # Web server logic goes here
        time.sleep(10)  # Refresh every 10 seconds


def main():
    directory = "/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"
    known_files = set()
    currently_processing = set()  # Set to keep track of files being processed

    threading.Thread(target=scanner, args=(directory, known_files, currently_processing), daemon=True).start()
    threading.Thread(target=transcribe, args=(currently_processing,), daemon=True).start()
    threading.Thread(target=wav2flac, daemon=True).start()

    try:
        while True:
            time.sleep(1)
            print(f"Active processes: {active_processes}")
            print(f"Current status: {process_status}")
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()

