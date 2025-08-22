use crossbeam_channel::Sender;
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

/// Starts a background thread that scans provided directories for new files.
/// WAV files are sent to `tx_convert` and audio files without accompanying
/// transcripts are sent to `tx_transcribe`.
/// The loop terminates when `shutdown` is set to `true`.
pub fn start_scanner(
    dirs: Vec<PathBuf>,
    tx_transcribe: Sender<PathBuf>,
    tx_convert: Sender<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, io::Error> {
    Ok(thread::spawn(move || {
        while !shutdown.load(Ordering::SeqCst) {
            for dir in &dirs {
                if let Ok(entries) = fs::read_dir(dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if let Some(ext) = path.extension().and_then(OsStr::to_str) {
                            let ext_lower = ext.to_lowercase();
                            if AUDIO_EXTENSIONS.contains(&ext_lower.as_str()) {
                                if ext_lower == "wav" {
                                    let _ = tx_convert.send(path.clone());
                                }
                                let mut transcript_exists = false;
                                if let Some(stem) = path.file_stem().and_then(OsStr::to_str) {
                                    for t_ext in TRANSCRIPT_EXTENSIONS {
                                        if path.with_file_name(format!("{stem}.{t_ext}")).exists() {
                                            transcript_exists = true;
                                            break;
                                        }
                                    }
                                }
                                if !transcript_exists {
                                    let _ = tx_transcribe.send(path.clone());
                                }
                            }
                        }
                    }
                }
            }
            thread::sleep(Duration::from_secs(5));
        }
    }))
}
