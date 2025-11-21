use crossbeam_channel::Sender;
use log::warn;
use rusqlite::Connection;
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

/// Resolve scan directories from the database, falling back to CLI-specified
/// paths when no database entries are found.
///
/// Database entries take precedence over CLI arguments. The `recordings_folders`
/// table is created on demand if missing, and empty or unreadable databases
/// cause the function to return the provided CLI paths with default flags
/// (`ignore_transcribing = false`, `ignore_converting = false`).
/// Returns the directories alongside a flag indicating whether the database was
/// used.
pub fn load_recording_dirs(
    db_path: &Path,
    cli_dirs: Vec<PathBuf>,
) -> (Vec<(PathBuf, bool, bool)>, bool) {
    let fallback: Vec<_> = cli_dirs
        .into_iter()
        .map(|path| (path, false, false))
        .collect();

    let conn = match Connection::open(db_path) {
        Ok(conn) => conn,
        Err(err) => {
            warn!("Failed to open {}: {err}", db_path.display());
            return (fallback, false);
        }
    };

    if let Err(err) = conn.execute(
        "CREATE TABLE IF NOT EXISTS recordings_folders (
            id INTEGER PRIMARY KEY,
            folder_path TEXT UNIQUE,
            ignore_transcribing INTEGER DEFAULT 0,
            ignore_converting INTEGER DEFAULT 0
        )",
        [],
    ) {
        warn!("Failed to ensure recordings_folders table exists: {err}");
        return (fallback, false);
    }

    let mut stmt = match conn.prepare(
        "SELECT folder_path, ignore_transcribing, ignore_converting FROM recordings_folders",
    ) {
        Ok(stmt) => stmt,
        Err(err) => {
            warn!("Failed to prepare folder query: {err}");
            return (fallback, false);
        }
    };

    let db_dirs: rusqlite::Result<Vec<_>> = stmt
        .query_map([], |row| {
            let path: String = row.get(0)?;
            let ignore_transcribing: i64 = row.get(1)?;
            let ignore_converting: i64 = row.get(2)?;
            Ok((
                PathBuf::from(path),
                ignore_transcribing != 0,
                ignore_converting != 0,
            ))
        })
        .and_then(|rows| rows.collect());

    match db_dirs {
        Ok(dirs) if !dirs.is_empty() => (dirs, true),
        _ => (fallback, false),
    }
}

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

/// Start a simple background scanner that wakes periodically until shutdown.
///
/// The current implementation only keeps the thread alive; it does not perform
/// incremental scanning but provides a placeholder so that unit tests can
/// exercise the threading contract.
pub fn start_scanner(
    dirs: Vec<(PathBuf, bool, bool)>,
    tx_transcribe: Sender<PathBuf>,
    tx_convert: Sender<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, io::Error> {
    Ok(thread::spawn(move || {
        let (to_transcribe, to_convert) = scan_directories(dirs);

        for path in to_transcribe {
            if tx_transcribe.send(path).is_err() {
                break;
            }
        }

        for path in to_convert {
            if tx_convert.send(path).is_err() {
                break;
            }
        }

        while !shutdown.load(Ordering::SeqCst) {
            thread::sleep(Duration::from_millis(50));
        }
    }))
}
