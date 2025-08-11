use crossbeam_channel::Sender;
use std::collections::HashSet;
use std::ffi::OsStr;
use std::fs;
use std::io;
use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::Duration;

const AUDIO_EXTENSIONS: &[&str] = &["wav", "flac", "mp3", "ogg", "amr"];
const TRANSCRIPT_EXTENSIONS: &[&str] = &["srt", "txt", "vtt", "json", "tsv"];

/// Starts a background thread that scans `directories` for new audio or transcript files.
/// New WAV files are sent to `tx_convert` if no FLAC exists. Audio files without
/// accompanying transcripts are sent to `tx_transcribe`.
/// The provided `shutdown` flag terminates the loop when set to `true`.
pub fn start_scanner(
    directories: Vec<PathBuf>,
    tx_transcribe: Sender<PathBuf>,
    tx_convert: Sender<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, io::Error> {
    Ok(thread::spawn(move || {
        let mut known_files: HashSet<PathBuf> = HashSet::new();

        while !shutdown.load(Ordering::SeqCst) {
            let mut current_files = HashSet::new();

            for dir in &directories {
                if let Ok(entries) = fs::read_dir(dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if let Some(ext) = path.extension().and_then(OsStr::to_str) {
                            if AUDIO_EXTENSIONS.contains(&ext)
                                || TRANSCRIPT_EXTENSIONS.contains(&ext)
                            {
                                current_files.insert(path);
                            }
                        }
                    }
                }
            }

            let new_files: Vec<_> = current_files.difference(&known_files).cloned().collect();
            for file in &new_files {
                if let Some(ext) = file.extension().and_then(OsStr::to_str) {
                    if AUDIO_EXTENSIONS.contains(&ext) {
                        let mut transcript_exists = false;
                        if let Some(stem) = file.file_stem().and_then(OsStr::to_str) {
                            if let Some(parent) = file.parent() {
                                for t_ext in TRANSCRIPT_EXTENSIONS {
                                    let candidate = parent.join(format!("{}.{}", stem, t_ext));
                                    if candidate.exists() {
                                        transcript_exists = true;
                                        break;
                                    }
                                }
                            }
                        }
                        if !transcript_exists {
                            let _ = tx_transcribe.send(file.clone());
                        }
                        if ext == "wav" {
                            let flac = file.with_extension("flac");
                            if !flac.exists() {
                                let _ = tx_convert.send(file.clone());
                            }
                        }
                    }
                }
            }

            known_files.extend(current_files.into_iter());
            thread::sleep(Duration::from_secs(5));
        }
    }))
}
