import subprocess
import os

# Define the paths to your scripts
scripts = [
    "dir_traversal.py",
    "match_audio_transcript.py",
    "sort_audio_transcript.py",
    "generate_content.py",
]

# Execute each script in sequence
for script in scripts:
    result = subprocess.run(["python", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {script}: {result.stderr}")
        break
    else:
        print(f"Successfully executed {script}: {result.stdout}")

# Run Pelican to generate the site and then start the HTTP server
try:
    subprocess.run(["pelican", "content", "-o", "output", "-s", "pelicanconf.py"], check=True)
    os.chdir("output")
    subprocess.run(["python", "-m", "http.server"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error executing Pelican or starting the server: {e}")

