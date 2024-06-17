import os

def process_transcript_files(transcript_files, symlink_dir):
    transcript_dict = {}
    for transcript in transcript_files:
        base = os.path.splitext(os.path.basename(transcript))[0]
        transcript_dict[base] = transcript

        # Create symbolic link
        transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript))
        if not os.path.exists(transcript_symlink):
            os.symlink(transcript, transcript_symlink)

    return transcript_dict

