def match_files(audio_dict, transcript_dict):
    matches = []
    dangling_audio = []
    dangling_transcripts = []

    for base in audio_dict.keys():
        if base in transcript_dict:
            matches.append((audio_dict[base], transcript_dict[base]))
        else:
            dangling_audio.append(audio_dict[base])

    for base in transcript_dict.keys():
        if base not in audio_dict:
            dangling_transcripts.append(transcript_dict[base])

    return matches, dangling_audio, dangling_transcripts

