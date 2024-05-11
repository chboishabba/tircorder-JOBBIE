import os
import threading
import time
from queue import Queue




# Globals
transcribe_queue = Queue()
convert_queue = Queue()
active_processes = []
process_status = 'housekeeping'  # Default to housekeeping when no processes are active

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
        if not active_processes.count('transcribing'):
            active_processes.append('transcribing')
        print(f"Transcribing {file}")
        # Simulated transcription logic here
        time.sleep(5)  # Simulating transcription time
        active_processes.remove('transcribing')
        convert_queue.put(file.replace('.wav', '.flac'))
        transcribe_queue.task_done()
        if not transcribe_queue.qsize():
            process_status = 'housekeeping'

def wav2flac():
    global process_status
    while True:
        file = convert_queue.get()
        process_status = 'converting'
        if not active_processes.count('converting'):
            active_processes.append('converting')
        print(f"Converting {file} to FLAC")
        # Simulated conversion logic here
        time.sleep(3)  # Simulating conversion time
        active_processes.remove('converting')
        convert_queue.task_done()
        if not convert_queue.qsize():
            process_status = 'housekeeping'

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



