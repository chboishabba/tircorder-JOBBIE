import json
import socket
import subprocess

from tircorder.schemas import (
    validate_rule_check_request,
    validate_rule_check_response,
)

def transcribe_audio(audio_data):
    # Placeholder: replace with actual transcription logic
    print("Transcribing audio...")
    # Assume we return the transcription
    return "Transcribed text"

def transcode_to_flac(audio_file):
    # Placeholder: replace with actual transcoding logic using ffmpeg
    print("Transcoding to FLAC...")
    flac_filename = audio_file.replace('.wav', '.flac')
    subprocess.run(['ffmpeg', '-i', audio_file, '-c:a', 'flac', '-compression_level', '12', flac_filename])

def handle_client(connection):
    try:
        while True:
            # Receive data from the client
            data = connection.recv(1024)
            if not data:
                break
            try:
                payload = json.loads(data.decode())
            except json.JSONDecodeError:
                transcription = transcribe_audio(data.decode())
                transcode_to_flac(data.decode())
                connection.sendall(transcription.encode())
                continue
            response = handle_rule_check(payload)
            connection.sendall(json.dumps(response).encode())
    finally:
        connection.close()


def handle_rule_check(payload: dict) -> dict:
    """Validate a rule check request and produce a response."""
    validate_rule_check_request(payload)
    response = {
        "rule_id": payload["rule_id"],
        "allowed": True,
        "message": "ok",
    }
    validate_rule_check_response(response)
    return response

def start_server():
    host = ''
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    serverimeout(0.5)
    server_socket.listen()

    print("Server listening on port", port)
    try:
        while True:
            try:
                client_socket, addr = server_socket.accept()
                print('Connected by', addr)
                handle_client(client_socket)
            except socket.timeout:
                continue
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()

