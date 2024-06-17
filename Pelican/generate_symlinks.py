import os

def create_symlink(source, link_name):
    if not os.path.exists(link_name):
        os.symlink(source, link_name)
        print(f"Created symlink: {link_name} -> {source}")  # Debug print
    #else:
        #print(f"Symlink already exists: {link_name}")  # Debug print

def create_symlinks(matches, dangling_audio, dangling_transcripts, symlink_dir):
    for match in matches:
        audio_file, transcript_file = match
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio_file))
        transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript_file))

        create_symlink(audio_file, audio_symlink)
        create_symlink(transcript_file, transcript_symlink)

    for audio in dangling_audio:
        audio_symlink = os.path.join(symlink_dir, os.path.basename(audio))
        create_symlink(audio, audio_symlink)

    for transcript in dangling_transcripts:
        transcript_symlink = os.path.join(symlink_dir, os.path.basename(transcript))
        create_symlink(transcript, transcript_symlink)

    print("Symlinks created successfully.")

