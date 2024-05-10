import pyaudio
import threading
import datetime
import audioop
import webrtcvad

# Configuration parameters
MIC_DEVICE_INDEX = 0  # Placeholder: set the correct device index for microphone
OUTPUT_DEVICE_INDEX = 0  # Placeholder: set the correct device index for system output
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
VAD_AGGRESSIVENESS = 3

# Global control flags
is_paused = threading.Event()
is_paused.clear()

# Initialize VAD
vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

def audio_stream_callback(data, frame_count, time_info, status):
    if is_paused.is_set():
        return (None, pyaudio.paAbort)
    return (data, pyaudio.paContinue)

def capture_audio(device_index, stream_type):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_stream_callback)
    print(f"Recording {stream_type} started.")
    stream.start_stream()

    try:
        while stream.is_active():
            data = stream.read(CHUNK, exception_on_overflow=False)
            rms = audioop.rms(data, 2)
            if stream_type == "microphone":
                is_speech = vad.is_speech(data, RATE)
                if is_speech:
                    print(f"Voice detected at {datetime.datetime.now()}")
            elif stream_type == "system output":
                if rms > 100:  # Example threshold for detecting any system output
                    print(f"System audio detected at {datetime.datetime.now()}")
                    is_paused.set()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print(f"Recording {stream_type} stopped.")

def main():
    # Threads for handling audio input and system output separately
    mic_thread = threading.Thread(target=capture_audio, args=(MIC_DEVICE_INDEX, "microphone"))
    output_thread = threading.Thread(target=capture_audio, args=(OUTPUT_DEVICE_INDEX, "system output"))

    mic_thread.start()
    output_thread.start()

    mic_thread.join()
    output_thread.join()

if __name__ == "__main__":
    main()
    
    



import threading
from pynput import mouse
import time

# Global variable to track the last time of mouse activity
last_mouse_activity = time.time()

def on_move(x, y):
    global last_mouse_activity
    last_mouse_activity = time.time()

def on_click(x, y, button, pressed):
    global last_mouse_activity
    last_mouse_activity = time.time()

def on_scroll(x, y, dx, dy):
    global last_mouse_activity
    last_mouse_activity = time.time()

def monitor_mouse():
    """Monitor mouse activity to update the last activity time."""
    with mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll) as listener:
        listener.join()

def transcription_logic():
    """Function to handle transcription based on activity."""
    while True:
        time.sleep(60)  # Check every minute
        current_time = time.time()
        if current_time - last_mouse_activity > 3600:  # 1 hour of inactivity
            print("No mouse activity for the last hour. Starting transcription...")
            # Call your transcription function here
        else:
            print("Mouse activity detected recently. Waiting to start transcription...")
            
import datetime

def is_within_time_range(start, end):
    """Check if the current time is within the specified range."""
    now = datetime.datetime.now().time()
    start_time = datetime.datetime.strptime(start, "%H:%M").time()
    end_time = datetime.datetime.strptime(end, "%H:%M").time()
    return start_time <= now <= end_time

def transcription_logic():
    """Adjusted function to handle transcription based on activity and time."""
    while True:
        time.sleep(60)  # Check every minute
        if is_within_time_range("09:00", "17:00"):  # Active only from 9 AM to 5 PM
            current_time = time.time()
            if current_time - last_mouse_activity > 3600:  # 1 hour of inactivity
                print("No mouse activity for the last hour and within time range. Starting transcription...")
                # Call your transcription function here
            else:
                print("Mouse activity detected recently or out of time range. Waiting...")
        else:
            print("Currently out of the active time range.")


def main():
    mouse_thread = threading.Thread(target=monitor_mouse)
    transcription_thread = threading.Thread(target=transcription_logic)

    mouse_thread.start()
    transcription_thread.start()

    mouse_thread.join()
    transcription_thread.join()

if __name__ == "__main__":
    main()
    
    
import time

def transcription_logic():
    """Function to handle transcription based on activity, checking once per minute."""
    while True:
        time.sleep(60)  # Sleep for 60 seconds between checks
        current_time = time.time()
        if current_time - last_mouse_activity > 3600:  # 1 hour of inactivity
            print("No mouse activity for the last hour. Starting transcription...")
            # Call your transcription function here
        else:
            print("Mouse activity detected recently. Waiting to start transcription...")
            
            
def transcription_logic():
    """Adjusted function to handle transcription based on activity and time."""
    while True:
        time.sleep(60)  # Check every minute
        if is_within_time_range("09:00", "17:00"):  # Active only from 9 AM to 5 PM
            current_time = time.time()
            if current_time - last_mouse_activity > 3600:  # 1 hour of inactivity
                print("No mouse activity for the last hour and within time range. Starting transcription...")
                # Call your transcription function here
            else:
                print("Mouse activity detected recently or out of time range. Waiting...")
        else:
            print("Currently out of the active time range.")




import time

def check_activity():
    """Simulated function to check mouse activity."""
    # This would interact with an actual mouse activity function
    # For demonstration, it randomly returns True or False
    import random
    return random.choice([True, False])

def transcription_logic():
    """Function to handle transcription based on user activity."""
    delay_check = 60  # Initial delay between checks in seconds
    while True:
        time.sleep(delay_check)  # Wait for the next check period
        activity_detected = False
        
        # Perform rapid checks for half a second
        start_time = time.time()
        while time.time() - start_time < 0.5:
            if check_activity():
                activity_detected = True
                break
            time.sleep(0.2)  # Check 5 times per second (5Hz)

        if activity_detected:
            print("Activity detected. Delaying next check.")
            delay_check = 600  # Delay the next check 10 times longer if activity is detected
        else:
            print("No activity detected. Resuming normal checks.")
            delay_check = 60  # Reset to normal check frequency




