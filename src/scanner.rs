use crossbeam_channel::Sender;
use std::collections::HashSet;
use std::ffi::OsStr;
use std::io;
use std::path::{Path, PathBuf};
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
pub fn scan_directories(dirs: Vec<(PathBuf, bool, bool)>) -> (Vec<PathBuf>, Vec<PathBuf>) {
    let mut transcribe = Vec::new();
    let mut convert = Vec::new();

    for (dir, ignore_t, ignore_c) in dirs {
        if let Ok(entries) = std::fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                let ext = path
                    .extension()
                    .and_then(OsStr::to_str)
                    .map(|s| s.to_lowercase());
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
                    if ext_str == "wav" && !path.with_extension("flac").exists() && !ignore_c {
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

/// Start a background scanner that periodically inspects directories and queues
/// new audio files for transcription and conversion until `shutdown` is set.
pub fn start_scanner(
    dirs: Vec<PathBuf>,
    tx_transcribe: Sender<PathBuf>,
    tx_convert: Sender<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, io::Error> {
    let scan_dirs: Vec<(PathBuf, bool, bool)> =
        dirs.into_iter().map(|d| (d, false, false)).collect();

    Ok(thread::spawn(move || {
        let mut dispatched_transcribe: HashSet<PathBuf> = HashSet::new();
        let mut dispatched_convert: HashSet<PathBuf> = HashSet::new();

        while !shutdown.load(Ordering::SeqCst) {
            let (transcribe, convert) = scan_directories(scan_dirs.clone());

            for path in transcribe {
                if shutdown.load(Ordering::SeqCst) {
                    break;
                }
                if dispatched_transcribe.contains(&path) || transcript_exists(&path) {
                    continue;
                }
                if tx_transcribe.send(path.clone()).is_ok() {
                    dispatched_transcribe.insert(path);
                }
            }

            for path in convert {
                if shutdown.load(Ordering::SeqCst) {
                    break;
                }
                if dispatched_convert.contains(&path) || path.with_extension("flac").exists() {
                    continue;
                }
                if tx_convert.send(path.clone()).is_ok() {
                    dispatched_convert.insert(path);
                }
            }

            if shutdown.load(Ordering::SeqCst) {
                break;
            }

            thread::sleep(Duration::from_millis(50));
        }
    }))
}

fn transcript_exists(path: &Path) -> bool {
    let stem = match path.file_stem().and_then(OsStr::to_str) {
        Some(s) => s,
        None => return false,
    };

    match path.parent() {
        Some(parent) => TRANSCRIPT_EXTENSIONS
            .iter()
            .any(|ext| parent.join(format!("{stem}.{ext}")).exists()),
        None => false,
    }
}
