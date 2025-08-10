Overview

TiRCorder is a voice‑activated recording and transcription component of the broader Intergenerational Trauma‑Informed Identity Rebuilder (ITIR) suite. It emphasizes professional‑grade features such as voice detection, task scheduling, GPU acceleration, and flexible Whisper/CT2 transcription options
Core Architecture

    Entry scripts
    tircorder.py and tircorder-linux.py bootstrap the system, installing dependencies and launching server/client modes as needed.

    Orchestration
    main.py initializes queues, loads a faster‑whisper model, and starts three worker threads:

        scanner for discovering files

        transcriber for Whisper/CT2 transcription

        wav2flac for post‑processing conversions

Directory scanner
scanner.py polls folders listed in state.db, filters new audio/transcript files, and queues them for processing

Transcription worker
transcriber.py chooses Python Whisper or ctranslate2, writes .txt outputs, and queues files for conversion if needed

Conversion worker
utils.wav2flac waits for transcription to finish, then converts WAV files to FLAC via ffmpeg, coordinating with shared locks/events

State persistence
state.py stores queue contents and known file metadata in a SQLite database for crash recovery or cross‑process handoffs

Rate limiting
RateLimiter slows scans exponentially when no new files appear, preventing constant polling

File matching & web output
db_match_audio_transcript.py records which audio files have transcripts, and the Pelican scripts (e.g., generate_html.py) produce HTML pages summarizing matches and “dangling” files

Example client
jobbie_client_dual-capture.py demonstrates capturing microphone and system audio simultaneously, using WebRTC VAD to detect speech and trigger pauses in recording or to assist in noise removal, as well as recording of, for example, psychologist meetings etc.



Key Concepts to Understand

    Queue-based pipeline – Scanner → Transcriber → Converter all communicate through Python Queue objects.

    SQLite-backed state – state.db persists file lists, pending work, and skip reasons.

    Whisper / ctranslate2 usage – Familiarity with faster-whisper and ctranslate2 APIs helps when adjusting models or decoding parameters.

    Thread synchronization – Locks and events (transcription_complete, transcribing_active) coordinate parallel tasks.

    ffmpeg integration – Conversion steps rely on ffmpeg; ensure it’s installed and paths are correct.

    HTML generation – The Pelican scripts can be extended for richer visualization or web publishing.

Next Steps for Learning

    Study the SQLite schema (tables like recordings_folders, known_files) to understand how folders and file metadata are stored.

    Experiment with transcription methods (python_whisper vs. ctranslate2) to gauge performance and quality trade‑offs.

    Customize recording directories via the database, then run the scanner/transcriber pipeline to see the full flow.

    Extend Pelican HTML output for user-facing timelines or dashboards.

    Explore client/server separation if running capture clients on multiple machines that feed a centralized server.

These areas will give you a solid foundation for contributing to TiRCorder or integrating it into a larger workflow.
