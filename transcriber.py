import logging
import os
from datetime import datetime, timedelta
from queue import Queue
from state import export_queues_and_files, load_state
from utils import transcribe_audio, transcribe_ct2, transcribe_ct2_nonpythonic

def transcriber(TRANSCRIBE_QUEUE, CONVERT_QUEUE, transcription_method, TRANSCRIBE_ACTIVE, transcription_complete):
    known_files, transcribe_queue, convert_queue, skip_files, skip_reasons = load_state()

    while True:
        file = TRANSCRIBE_QUEUE.get()
        start_time = datetime.now()
        TRANSCRIBE_ACTIVE.set()
        logging.info(f"SYSTIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Starting transcription for {file}.")

        output_text = None
        if transcription_method == 'python_whisper':
            output_text = transcribe_audio(file)
        elif transcription_method == 'ctranslate2':
            output_text, _ = transcribe_ct2(file)
        elif transcription_method == 'ctranslate2_nonpythonic':
            output_text, _ = transcribe_ct2_nonpythonic(file)
        else:
            logging.error(f"Unsupported transcription method: {transcription_method}")
            TRANSCRIBE_QUEUE.task_done()
            continue

        if output_text is not None:
            output_path = os.path.splitext(file)[0] + '.txt'
            try:
                with open(output_path, 'w') as f:
                    f.write(output_text)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                real_time_factor = audio_duration / elapsed_time if elapsed_time > 0 else 0
                logging.info(f"SYSTIME: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | Transcription completed and saved for {file}. Real-time factor: {real_time_factor:.2f}x.")
            except Exception as e:
                logging.error(f"Error while saving transcription for {file}: {e}")
        else:
            logging.error(f"Transcription failed for {file}.")

        CONVERT_QUEUE.put(file)

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)

        proc_comp_timestamps_transcribe = [t for t in proc_comp_timestamps_transcribe if t > one_hour_ago]
        files_per_hour = len([t for t in proc_comp_timestamps_transcribe if t > one_hour_ago])
        files_per_minute = len([t for t in proc_comp_timestamps_transcribe if t > one_minute_ago])

        logging.info(f"SYSTIME: {now.strftime('%Y-%m-%d %H:%M:%S')} | File {file} added to conversion queue. {CONVERT_QUEUE.qsize()} files waiting for conversion. {TRANSCRIBE_QUEUE.qsize()} left to transcribe. Processing rates: {files_per_hour} files/hour, {files_per_minute} files/minute.")

        TRANSCRIBE_QUEUE.task_done()
        TRANSCRIBE_ACTIVE.clear()

        if not TRANSCRIBE_QUEUE.qsize():
            logging.info("All transcription tasks completed, entering housekeeping mode.")
        else:
            logging.info(f"{TRANSCRIBE_QUEUE.qsize()} transcription tasks remaining.")

        transcription_complete.set()

