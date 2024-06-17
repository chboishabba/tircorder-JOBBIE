import subprocess
import os
import shutil
import time

# Define the paths to your scripts
scripts = [
    "dir_traversal.py",
    "match_audio_transcript.py",
    "generate_html.py",
]

# Execute each script in sequence
for script in scripts:
    result = subprocess.run(["python", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {script}: {result.stderr}")
        break
    else:
        print(f"Successfully executed {script}: {result.stdout}")

# Check if the timeline.html file is created
timeline_path = os.path.join("content", "timeline.html")
if os.path.exists(timeline_path):
    print(f"timeline.html found at {timeline_path}")
else:
    print("timeline.html not found. Please check generate_html.py for issues.")
    exit(1)

# Run Pelican to generate the site
try:
    subprocess.run(["pelican", "content", "-o", "output", "-s", "pelicanconf.py"], check=True)
    print("Pelican content generation successful.")
except subprocess.CalledProcessError as e:
    print(f"Error executing Pelican: {e}")
    exit(1)

# Copy timeline.html to the output directory, always overwriting
output_timeline_path = os.path.join("output", "timeline.html")
try:
    shutil.copy(timeline_path, output_timeline_path)
    print(f"Copied {timeline_path} to {output_timeline_path}")
except IOError as e:
    print(f"Error copying timeline.html to output directory: {e}")
    exit(1)

# Copy CSS and JavaScript files to the output directory
for file in ["styles.css", "scripts.js"]:
    try:
        shutil.copy(file, "output")
        print(f"Copied {file} to output directory.")
    except IOError as e:
        print(f"Error copying {file} to output directory: {e}")
        exit(1)

# Change directory to output and start the HTTP server
try:
    os.chdir("output")
    print("Changed directory to output.")
    # Start the server
    server = subprocess.Popen(["python", "-m", "http.server"])

    # Keep the script alive as long as the server is running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("HTTP server stopped.")
        server.terminate()
except subprocess.CalledProcessError as e:
    print(f"Error starting the HTTP server: {e}")

