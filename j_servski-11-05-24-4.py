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
process_status = 'housekeeping'  # Default to housekeeping when no processes are active
transcribing_lock = threading.Lock()
converting_lock = threading.Lock()

playlists = defaultdict(list) # Playlist dictionary, mapping a date to a list of FLAC files

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
        known_files.update(new_files)
        time.sleep(1)  # Scan every second

def transcribe():
    global process_status
    while True:
        file = transcribe_queue.get()
        process_status = 'transcribing'
        with transcribing_lock:
            if 'converting' in active_processes:
                # Preemptively stop conversion if running
                converting_lock.acquire()
            if 'transcribing' not in active_processes:
                active_processes.append('transcribing')
            print(f"Transcribing {file}")
            
            input_path = os.path.join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = input_path.replace('.wav', '.txt')  # Assuming you want text output
            
            # Proper subprocess call for Whisper
            cmd = ["whisper", input_path, "--model", "medium", "--language", "en", "--output_dir", output_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print(f"Transcription successful: {file}")
                print(f"Transcript saved to: {output_path}")
            else:
                print(f"Error in transcription of {file}: {result.stderr}")

            active_processes.remove('transcribing')
            if converting_lock.locked():
                converting_lock.release()
            convert_queue.put(file.replace('.wav', '.flac'))
            transcribe_queue.task_done()
            if not transcribe_queue.qsize():
                process_status = 'housekeeping'




def wav2flac():
    global process_status
    while True:
        file = convert_queue.get()
        process_status = 'converting'
        with converting_lock:
            if 'converting' not in active_processes:
                active_processes.append('converting')
            input_path = os.path.join("/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/", file)
            output_path = input_path.replace('.wav', '.flac')
            print(f"Converting {file} to FLAC")
            # Using ffmpeg to convert WAV to FLAC
            result = subprocess.run(["ffmpeg", "-i", input_path, "-c:a", "flac", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Check if conversion was successful
            if result.returncode == 0:
                print(f"Conversion successful: {file}")
                # Delete the original .wav file to free up space
                os.remove(input_path)
                print(f"Deleted original WAV file: {input_path}")
            else:
                print(f"Error converting {file}: {result.stderr}")
                
            active_processes.remove('converting')
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
        print(playlists)  # Optionally print the current playlists for debugging
        time.sleep(1)  # Scan every second


def webSlinger():
    while True:
        print("Running webSlinger")
        # Web server logic goes here
        time.sleep(10)  # Refresh every 10 seconds

def main():
    directory = "/mnt/smbshare/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/"
    known_files = set()
    
    # Start the scanner thread
    scanner_thread = threading.Thread(target=scanner, args=(directory, known_files))
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # Start the transcribe thread
    transcribe_thread = threading.Thread(target=transcribe)
    transcribe_thread.daemon = True
    transcribe_thread.start()
    
    # Start the convert thread
    convert_thread = threading.Thread(target=wav2flac)
    convert_thread.daemon = True
    convert_thread.start()
    
    # Start the webSlinger thread
    web_slinger_thread = threading.Thread(target=webSlinger)
    web_slinger_thread.daemon = True
    web_slinger_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            print(f"Active processes: {active_processes}")
            print(f"Current status: {process_status}")
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()

