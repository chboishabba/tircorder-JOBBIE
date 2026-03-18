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
import argparse
from pathlib import Path

from tircorder.utils import DEFAULT_WEBUI_CONFIG, transcribe_webui

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


# Determine a supported sample rate for the selected device, preferring the
# configured rate but falling back to the device default or common values.
def resolve_sample_rate(
    pyaudio_instance, device_id, channels, audio_format, preferred_rate
):
    """Return a supported sample rate for a device, favoring the preferred rate."""

    vad_supported_rates = {8000, 16000, 32000, 48000}

    def _is_supported(target_rate):
        if target_rate not in vad_supported_rates:
            return False
        try:
            return pyaudio_instance.is_format_supported(
                target_rate,
                input_device=device_id,
                input_channels=channels,
                input_format=audio_format,
            )
        except ValueError:
            return False

    device_info = pyaudio_instance.get_device_info_by_index(device_id)
    default_rate = int(device_info.get("defaultSampleRate", preferred_rate))
    candidate_rates = [
        int(preferred_rate),
        default_rate,
        16000,
        32000,
        48000,
        8000,
    ]
    seen = set()
    for candidate_rate in candidate_rates:
        if candidate_rate in seen:
            continue
        seen.add(candidate_rate)
        if _is_supported(candidate_rate):
            return candidate_rate, device_info.get("name", f"Device {device_id}")

    raise ValueError(
        f"No supported sample rate found for device {device_id} "
        f"({device_info.get('name', 'Unknown')})."
    )


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

def transcribe_and_log(filename, start_timestamp, webui_url, webui_path):
    """Run WhisperX-WebUI transcription on the WAV file and append text to a log."""
    with transcription_lock:
        transcript, duration, metadata = transcribe_webui(
            str(filename),
            base_url=webui_url,
            options=DEFAULT_WEBUI_CONFIG["options"],
            timeout=DEFAULT_WEBUI_CONFIG["timeout"],
            verify_ssl=DEFAULT_WEBUI_CONFIG["verify_ssl"],
            transcribe_path=webui_path or DEFAULT_WEBUI_CONFIG["transcribe_path"],
        )

        if not transcript:
            print(
                Fore.RED
                + f"Transcription failed for {filename}: {metadata.get('error')}"
            )
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} ({duration:.2f}s) - {transcript}\n"

        # --- Adapter for SL shared reducer ---
        try:
            import os
            import sys
            _SUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _SENSIBLAW_ROOT = os.path.join(_SUITE_ROOT, "SensibLaw")
            _SENSIBLAW_SRC = os.path.join(_SENSIBLAW_ROOT, "src")
            if _SENSIBLAW_ROOT not in sys.path:
                sys.path.insert(0, _SENSIBLAW_ROOT)
            if _SENSIBLAW_SRC not in sys.path:
                sys.path.insert(0, _SENSIBLAW_SRC)
            from sensiblaw.interfaces.shared_reducer import collect_canonical_lexeme_occurrences
            
            canonical_ids = [occ.norm_text for occ in collect_canonical_lexeme_occurrences(transcript)]
            if canonical_ids:
                log_entry = f"{timestamp} ({duration:.2f}s) [SL_CANONICAL_IDS: {','.join(canonical_ids)}] - {transcript}\n"
        except ImportError:
            pass
        # -------------------------------------

        log_file_path = os.path.join(os.path.dirname(filename), "transcriptions.log")
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry)

        print(Fore.CYAN + f"Transcription ({timestamp}): {transcript}")


#adjusted max silence ms to be in line with countdown_timer
def continuous_record(
    device_id,
    format=pyaudio.paInt16,
    channels=1,
    preferred_rate=16000,
    chunk_duration_ms=30,
    max_silence_ms=5000,
    output_dir="recordings",
    webui_url="http://127.0.0.1:7860",
    webui_path="/_transcribe_file",
):
    """Record audio from the given device and trigger transcription on voice."""

    vad = create_vad()
    p = pyaudio.PyAudio()

    try:
        rate, device_name = resolve_sample_rate(
            p, device_id, channels, format, preferred_rate
        )
        print(
            Fore.GREEN
            + f"Using sample rate {rate} Hz on device '{device_name}' (id {device_id})"
        )
    except ValueError as exc:
        print(Fore.RED + f"Could not configure input device: {exc}")
        p.terminate()
        return

    chunk_size = int(rate * chunk_duration_ms / 1000)

    try:
        stream = p.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=chunk_size,
        )
    except OSError as exc:
        print(
            Fore.RED
            + f"Failed to open input stream on '{device_name}' (id {device_id}): {exc}"
        )
        p.terminate()
        return

    print("Recording started. Speak into the microphone.")
    audio_data = collections.deque()
    countdown_timer = 5.0  # Countdown timer in seconds
    voice_detected_for = 0.0  # Initialize the duration of voice presence
    last_time_checked = datetime.datetime.now()
    v_det = False  # Move outside the loop to maintain state

    try:
        while True:
            try:
                frame = stream.read(chunk_size, exception_on_overflow=False)
            except OSError as exc:
                print(Fore.RED + f"Audio read error (overflow): {exc}")
                continue
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
                    print(
                        "\nSAVED: Timer expired at: "
                        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    filename, saved_timestamp = save_audio(
                        list(audio_data), p, format, channels, rate, output_dir
                    )
                    audio_data.clear()
                    threading.Thread(
                        target=transcribe_and_log,
                        args=(filename, saved_timestamp, webui_url, webui_path),
                    ).start()
                    countdown_timer = 5.0  # Reset the countdown after processing
                    v_det = False  # Reset v_det after handling
                    # change countdown timer here to 60s later so we get 1m+ recordings?
                else:
                    print(
                        "\nRecording discarded - no voice detected. Timer expired at: "
                        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    audio_data.clear()
                    countdown_timer = 5.0
                #countdown_timer = 15.0  # Reset the countdown after processing
                #v_det = False  # Reset v_det after handling
            else:
                print(f"Timer: {countdown_timer:.2f}s remaining", end='          \r')
    finally:
        try:
            if stream.is_active():
                stream.stop_stream()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass
        p.terminate()
        print("\nRecording stopped.")






# Save the audio data to a WAV file in the configured capture directory.
def save_audio(audio_frames, pyaudio_instance, format, channels, rate, output_dir):
    """Persist recorded audio frames to a WAV file and return the path."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = directory / f"{timestamp}.wav"
    wf = wave.open(str(filename), "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio_instance.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b"".join(audio_frames))
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
    """Convert a WAV file to FLAC format."""
    flac_filename = wav_filename.replace('.wav', '.flac')
    subprocess.run(
        [
            'ffmpeg',
            '-i',
            wav_filename,
            '-c:a',
            'flac',
            '-compression_level',
            '12',
            flac_filename,
        ]
    )
    return flac_filename

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
    """Run concurrent capture of system and microphone audio."""
    # Setup audio streams
    system_stream = p.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        input=True,
        input_device_index=DEVICE_INDEX_FOR_SYSTEM,  # Set appropriately
        frames_per_buffer=1024,
        as_loopback=True,
    )
    mic_stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        input_device_index=DEVICE_INDEX_FOR_MIC,  # Set appropriately
        frames_per_buffer=1024,
    )
    
    stop_event = threading.Event()

    # Start threads
    system_thread = threading.Thread(
        target=capture_system_audio, args=(system_stream, stop_event)
    )
    mic_thread = threading.Thread(
        target=capture_microphone_audio, args=(mic_stream, stop_event)
    )

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

# Main function
def main():
    """Launch the audio client with optional device selection."""
    parser = argparse.ArgumentParser(description="Tircorder audio client")
    parser.add_argument(
        "--device-id",
        type=int,
        help="Logical device id (default maps to preferred/default input)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="recordings",
        help="Directory to store captured audio (created if missing)",
    )
    parser.add_argument(
        "--webui-url",
        type=str,
        default="http://127.0.0.1:7860",
        help="Base URL for WhisperX-WebUI backend",
    )
    parser.add_argument(
        "--webui-path",
        type=str,
        default="/_transcribe_file",
        help="Transcription endpoint path for WhisperX-WebUI",
    )
    args = parser.parse_args()

    print("Available recording devices:")
    p = pyaudio.PyAudio()
    discovered_devices = []
    default_actual_id = None
    for actual_id in range(p.get_device_count()):
        dev = p.get_device_info_by_index(actual_id)
        if dev["maxInputChannels"] > 0:
            name = dev["name"]
            if name.lower() == "default":
                default_actual_id = actual_id
            discovered_devices.append((actual_id, name))

    # Build logical ordering with "default" as logical 0 when present.
    ordered_devices = []
    if default_actual_id is not None:
        ordered_devices.append(
            (0, default_actual_id, "default")
        )
    logical_index = 1 if ordered_devices else 0
    for actual_id, name in discovered_devices:
        if actual_id == default_actual_id:
            continue
        ordered_devices.append((logical_index, actual_id, name))
        logical_index += 1

    if not ordered_devices:
        print(Fore.RED + "No input devices detected.")
        p.terminate()
        return

    print("Logical device list (use these IDs with --device-id):")
    for logical_id, actual_id, name in ordered_devices:
        print(f"  {logical_id}: {name} (actual id {actual_id})")

    # Resolve logical id to actual PyAudio id.
    logical_to_actual = {logical_id: actual_id for logical_id, actual_id, _ in ordered_devices}
    chosen_logical = args.device_id if args.device_id is not None else 0
    if chosen_logical not in logical_to_actual:
        available_ids = ", ".join(str(lid) for lid in logical_to_actual.keys())
        print(
            Fore.RED
            + f"Invalid logical device id {chosen_logical}. Available: {available_ids}"
        )
        p.terminate()
        return

    device_id = logical_to_actual[chosen_logical]

    p.terminate()
    continuous_record(
        device_id,
        output_dir=args.output_dir,
        webui_url=args.webui_url,
        webui_path=args.webui_path,
    )


if __name__ == "__main__":
    main()
