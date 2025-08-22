use std::ffi::OsStr;
use std::fs;
use std::path::PathBuf;

const AUDIO_EXTENSIONS: &[&str] = &["wav", "flac", "mp3", "ogg", "amr"];
const TRANSCRIPT_EXTENSIONS: &[&str] = &["srt", "txt", "vtt", "json", "tsv"];

/// Scan the provided directories once and return audio files queued for
/// transcription and conversion.
///
/// Each directory entry is a tuple of `(path, ignore_transcribing, ignore_converting)`.
/// Files with existing transcript companions are excluded from the transcription
/// queue. WAV files with existing FLAC companions are excluded from the
/// conversion queue. `ignore_*` flags skip queueing entirely for that action.
pub fn scan_directories(
    dirs: Vec<(PathBuf, bool, bool)>,
) -> (Vec<PathBuf>, Vec<PathBuf>) {
    let mut transcribe = Vec::new();
    let mut convert = Vec::new();

    for (dir, ignore_t, ignore_c) in dirs {
        if let Ok(entries) = fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                let ext = path.extension().and_then(OsStr::to_str);
                if let Some(ext) = ext.map(|e| e.to_lowercase()) {
                    if AUDIO_EXTENSIONS.contains(&ext.as_str()) {
                        let mut transcript_exists = false;
                        if let Some(stem) = path.file_stem().and_then(OsStr::to_str) {
                            if let Some(parent) = path.parent() {
                                for t_ext in TRANSCRIPT_EXTENSIONS {
                                    if parent.join(format!("{}.{}", stem, t_ext)).exists() {
                                        transcript_exists = true;
                                        break;
                                    }
                                }
                            }
                        }

                        if !transcript_exists && !ignore_t {
                            transcribe.push(path.clone());
                        }

                        if ext == "wav" && !path.with_extension("flac").exists() && !ignore_c {
                            convert.push(path.clone());
                        }
                    }
                }
            }
        }
    }

    transcribe.sort();
    convert.sort();
    (transcribe, convert)
}
