
import os
import time
from threading import Thread, Lock
from queue import Queue

class FileProcessor:
    def __init__(self, scan_dir, modeflag):
        self.scan_dir = scan_dir
        self.modeflag = modeflag
        self.transcribe_queue = Queue()
        self.wav2flac_queue = Queue()
        self.process_status = []  # Active processes
        self.lock = Lock()
        self.stop_event = False
        
    def scanner(self):
        while not self.stop_event:
            current_files = os.listdir(self.scan_dir)
            datetimes = set()
            for file in current_files:
                parts = file.split('.')
                if len(parts) != 2:
                    continue
                datetime, ext = parts
                if datetime not in datetimes:
                    datetimes.add(datetime)
                    if ext == 'wav' and not any(os.path.exists(f"{self.scan_dir}/{datetime}.{t}") for t in ['txt', 'srt', 'vtt', 'json']):
                        self.transcribe_queue.put(datetime)
                    elif ext == 'wav' and any(os.path.exists(f"{self.scan_dir}/{datetime}.{t}") for t in ['txt', 'srt', 'vtt', 'json']):
                        self.wav2flac_queue.put(datetime)
            time.sleep(1)  # Check every second

    def transcribe(self):
        while not self.stop_event:
            if not self.transcribe_queue.empty():
                datetime = self.transcribe_queue.get()
                self.lock.acquire()
                self.process_status.append('transcribe')
                self.lock.release()
                print(f"Transcribing: {datetime}.wav")  # Placeholder for actual transcribe function
                # Simulated delay
                time.sleep(2)
                self.lock.acquire()
                self.process_status.remove('transcribe')
                if self.modeflag == 0:
                    self.process_status.append('housekeeping')
                self.lock.release()
            else:
                time.sleep(0.5)

    def wav2flac(self):
        while not self.stop_event:
            if not self.wav2flac_queue.empty():
                datetime = self.wav2flac_queue.get()
                self.lock.acquire()
                self.process_status.append('wav2flac')
                self.lock.release()
                print(f"Converting {datetime}.wav to FLAC")
                # Simulated delay
                time.sleep(2)
                self.lock.acquire()
                self.process_status.remove('wav2flac')
                self.lock.release()
            else:
                time.sleep(0.5)

    def start(self):
        Thread(target=self.scanner, daemon=True).start()
        Thread(target=self.transcribe, daemon=True).start()
        Thread(target=self.wav2flac, daemon=True).start()

    def stop(self):
        self.stop_event = True

# Usage:
processor = FileProcessor(scan_dir='smb://a@desktop-hg6qb3n/Y/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber/', modeflag=1)
processor.start()

# Let it run for some time and then stop it.
time.sleep(10)  # Simulate running time
processor.stop()

