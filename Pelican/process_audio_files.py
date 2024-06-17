import os

def process_audio_files(audio_files, symlink_dir):
    audio_dict = {}
    for audio in audio_files:
        base = os.path.splitext(os.path.basename(audio))[0]
        audio_dict[base] = audio

        # Create symbolic link
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio))
        if not os.path.exists(audio_symlink):
            os.symlink(audio, audio_symlink)

    return audio_dict

