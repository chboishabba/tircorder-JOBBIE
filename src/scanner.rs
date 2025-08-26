use std::ffi::OsStr;
use std::io;
use std::path::PathBuf;
use crossbeam_channel::Sender;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::Duration;

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
        if let Ok(entries) = std::fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                let ext = path.extension().and_then(OsStr::to_str).map(|s| s.to_lowercase());
                let ext_str = match ext {
                    Some(e) => e,
                    None => continue,
                };

                if AUDIO_EXTENSIONS.contains(&ext_str.as_str()) {
                    let stem = match path.file_stem().and_then(OsStr::to_str) {
                        Some(s) => s,
                        None => continue,
                    };
                    let mut transcript_exists = false;
                    if let Some(parent) = path.parent() {
                        for t_ext in TRANSCRIPT_EXTENSIONS {
                            if parent.join(format!("{stem}.{t_ext}")).exists() {
                                transcript_exists = true;
                                break;
                            }
                        }
                    }
                    if !transcript_exists && !ignore_t {
                        transcribe.push(path.clone());
                    }
                    if ext_str == "wav"
                        && !path.with_extension("flac").exists()
                        && !ignore_c
                    {
                        convert.push(path.clone());
                    }
                }
            }
        }
    }

    transcribe.sort();
    convert.sort();
    (transcribe, convert)
}

/// Start a simple background scanner that wakes periodically until shutdown.
///
/// The current implementation only keeps the thread alive; it does not perform
/// incremental scanning but provides a placeholder so that unit tests can
/// exercise the threading contract.
pub fn start_scanner(
    _dirs: Vec<PathBuf>,
    _tx_transcribe: Sender<PathBuf>,
    _tx_convert: Sender<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, io::Error> {
    Ok(thread::spawn(move || {
        while !shutdown.load(Ordering::SeqCst) {
            thread::sleep(Duration::from_millis(50));
        }
    }))
}

