import pyaudio
import wave
import webrtcvad
import collections
import datetime
import audioop
import threading
import subprocess
import os
from colorama import Fore, Style, init
import json
import curses
import socket
import sys

# Instance manager for whisper
transcription_lock = threading.Lock()

# Pause recording trigger manager
is_paused = threading.Event()
is_paused.clear()  # Set this to true to pause the recording


# Initialize colorama
init(autoreset=True)

# Initialize VAD
def create_vad(aggressiveness=1):
    vad = webrtcvad.Vad(aggressiveness)
    return vad

# Calculate RMS level
def rms_level(data):
    rms = audioop.rms(data, 2)  # width=2 for format=pyaudio.paInt16
    return rms
    





def log_transcription(json_data, filename):
    with open(filename, 'w') as f:
        json.dump(json_data, f)
        
def display_transcription_as_html(json_data):
    html_content = '<html><body>'
    for entry in json_data:
        html_content += f"<p>{entry['timestamp']} - {entry['text']}</p>"
    html_content += '</body></html>'
    return html_content

def transcribe_and_log(filename, start_timestamp):
    with transcription_lock:
        # Ensure the command uses properly quoted paths
        cmd = f"whisper-ctranslate2 --vad_filter True --model medium.en --language en --output_dir \"{os.path.dirname(filename)}\" --device cpu \"{filename}\""
        try:
            # Run the command and capture output
            result = subprocess.run(cmd, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            # Print error if the command fails
            print("Error:", e.stderr)
            return

        # Assuming the transcription tool outputs a .txt file in the same directory
        txt_filename = f"{filename[:-4]}.txt"  # Replaces .wav with .txt
        if os.path.exists(txt_filename):
            with open(txt_filename, 'r') as file:
                transcription = file.read()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - {transcription}\n"

            # Append to log file
            log_file_path = os.path.join(os.path.dirname(filename), "transcriptions.log")
            with open(log_file_path, "a") as log_file:
                log_file.write(log_entry)

            # Print in another console or window (simulated here)
            print(Fore.CYAN + f"Transcription ({timestamp}): {transcription}")


#adjusted max silence ms to be in line with countdown_timer
def continuous_record(device_id, format=pyaudio.paInt16, channels=1, rate=16000, chunk_duration_ms=30, max_silence_ms=5000):
    chunk_size = int(rate * chunk_duration_ms / 1000)
    vad = create_vad()
    p = pyaudio.PyAudio()
    stream = p.open(format=format, channels=channels, rate=rate, input=True, input_device_index=device_id, frames_per_buffer=chunk_size)

    print("Recording started. Speak into the microphone.")
    audio_data = collections.deque()
    countdown_timer = 5.0  # Countdown timer in seconds
    voice_detected_for = 0.0  # Initialize the duration of voice presence
    last_time_checked = datetime.datetime.now()
    v_det = False  # Move outside the loop to maintain state

    try:
        while True:
            frame = stream.read(chunk_size)
            is_speech = vad.is_speech(frame, rate)
            now = datetime.datetime.now()
            audio_data.append(frame)

            # Calculate RMS and decide color
            level = rms_level(frame)
            level_color = 'RED' if level < 100 else 'GREEN'
            print(f"{level_color} RMS Level: {level}", end=' ')

            if is_speech:
                voice_detected_for += (now - last_time_checked).total_seconds()
                print("Voice detected", end='          \r')
                if voice_detected_for >= 0.5:
                    v_det = True  # Voice detected long enough to set v_det true
                    countdown_timer = 5.0
            else:
                voice_detected_for = 0.0

            # Reduce countdown timer
            countdown_timer -= (now - last_time_checked).total_seconds()
            last_time_checked = now

            if countdown_timer <= 0:
                
                if v_det:
                    print(f"\nSAVED: Timer expired at: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    filename = save_audio(list(audio_data), p, format, channels, rate)
                    audio_data.clear()
                    threading.Thread(target=transcribe_and_log, args=(filename,)).start()
                    countdown_timer = 5.0  # Reset the countdown after processing
                    v_det = False  # Reset v_det after handling
                    # change countdown timer here to 60s later so we get 1m+ recordings?
                else:
                    print(f"\nRecording discarded - no voice detected. Timer expired at: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    audio_data.clear()
                    countdown_timer = 5.0
                #countdown_timer = 15.0  # Reset the countdown after processing
                #v_det = False  # Reset v_det after handling
            else:
                print(f"Timer: {countdown_timer:.2f}s remaining", end='          \r')
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("\nRecording stopped.")






# Save the audio data to a WAV file in Y:\__MEDIA\__Transcribing and Recording\2024\Dad Auto Transcriber3
def save_audio(audio_frames, pyaudio_instance, format, channels, rate):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory = r"Y:\__MEDIA\__Transcribing and Recording\2024\Dad Auto Transcriber"  # Use a raw string for the path
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)  # Create the directory if it does not exist
    filename = f"{timestamp}.wav"
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio_instance.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(audio_frames))
    wf.close()
    print(f"\nAudio saved as {filename}")
    return filename, timestamp
    
def send_audio(file_path):
    host = 'server_address'  # IP address of the server
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        # Send the path of the audio file to the server
        sock.sendall(file_path.encode())

        # Wait for the server to send back the transcribed text
        data = sock.recv(1024)
        print("Received:", data.decode())
    
def convert_to_flac(wav_filename):
    flac_filename = wav_filename.replace('.wav', '.flac')
    subprocess.run(['ffmpeg', '-i', wav_filename, '-c:a', 'flac', '-compression_level', '12', flac_filename])
    return flac_idlename

# Initialize PyAudio
pSys = pyaudio.PyAudio()
# Initialize microphone PyAudio - duplicate of __main__
p = pyaudio.PyAudio()

# Function to capture system audio
def capture_system_audio(stream, stop_event):
    while not stop_event.is_set():
        data = stream.read(1024)
        rms = audioop.rms(data, 2)
        if rms > 100:  # Threshold for 'significant audio'
            print("Significant system audio detected")
            stop_event.set()  # Signal to pause microphone recording

# Function to capture microphone audio
def capture_microphone_audio(stream, stop_event):
    while not stop_event.is_set():
        data = stream.read(1024)
        print("Recording microphone...")
        # Here you would add your processing logic
        
        
        
# GPT proposed queue management        
def setup_and_run():
    # Setup audio streams
    system_stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True,
                            input_device_index=DEVICE_INDEX_FOR_SYSTEM,  # Set appropriately
                            frames_per_buffer=1024, as_loopback=True)
    mic_stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True,
                        input_device_index=DEVICE_INDEX_FOR_MIC,  # Set appropriately
                        frames_per_buffer=1024)
    
    stop_event = threading.Event()

    # Start threads
    system_thread = threading.Thread(target=capture_system_audio, args=(system_stream, stop_event))
    mic_thread = threading.Thread(target=capture_microphone_audio, args=(mic_stream, stop_event))

    system_thread.start()
    mic_thread.start()

    # Join threads
    system_thread.join()
    mic_thread.join()

    # Cleanup
    system_stream.stop_stream()
    system_stream.close()
    mic_stream.stop_stream()
    mic_stream.close()
    p.terminate()

#if __name__ == "__main__":
#    setup_and_run()

    if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_file_path = sys.argv[1]
        send_audio(audio_file_path)
    else:
        print("Usage: python client.py <audio_file_path>")
    setup_and_run()


# Main function
def main():
    print("Available recording devices:")
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"Device ID {i}: {dev['name']}")
    p.terminate()

    #device_id = int(input("Enter the device ID you want to use: "))
    continuous_record(0)

if __name__ == "__main__":
    main()
