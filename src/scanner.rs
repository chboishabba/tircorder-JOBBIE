use crossbeam_channel::Sender;
use rusqlite::{params, Connection};
use std::collections::{HashMap, HashSet};
use std::ffi::OsStr;
use std::fs;
use std::path::PathBuf;
use std::thread;
use std::time::{Duration, UNIX_EPOCH};

const AUDIO_EXTENSIONS: &[&str] = &["wav", "flac", "mp3", "ogg", "amr"];
const TRANSCRIPT_EXTENSIONS: &[&str] = &["srt", "txt", "vtt", "json", "tsv"];

struct RateLimiter {
    counter: u32,
    max_interval: Duration,
}

impl RateLimiter {
    fn new(max_secs: u64) -> Self {
        Self {
            counter: 0,
            max_interval: Duration::from_secs(max_secs),
        }
    }

    fn increment(&mut self) {
        self.counter += 1;
    }

    fn reset(&mut self) {
        self.counter = 0;
    }

    fn sleep(&self) {
        let secs = 2u64.pow(self.counter).min(self.max_interval.as_secs());
        thread::sleep(Duration::from_secs(secs));
    }
}

/// Starts a background thread that scans recordings folders from `state.db` for new files.
/// New WAV files are sent to `tx_convert` if no FLAC exists. Audio files without
/// accompanying transcripts are sent to `tx_transcribe`.
pub fn start_scanner(
    tx_transcribe: Sender<PathBuf>,
    tx_convert: Sender<PathBuf>,
) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let conn = Connection::open("state.db").expect("failed to open database");
        let directories = {
            let mut stmt = conn
                .prepare("SELECT id, folder_path, COALESCE(ignore_transcribing, 0), COALESCE(ignore_converting, 0) FROM recordings_folders")
                .expect("failed to prepare statement");
            stmt
                .query_map([], |row| {
                    let id: i64 = row.get(0)?;
                    let path: String = row.get(1)?;
                    let ignore_t: i64 = row.get(2)?;
                    let ignore_c: i64 = row.get(3)?;
                    Ok((id, PathBuf::from(path), ignore_t != 0, ignore_c != 0))
                })
                .expect("query failed")
                .filter_map(Result::ok)
                .collect::<Vec<_>>()
        };

        let mut known_files: HashSet<PathBuf> = HashSet::new();
        let mut rate_limiter = RateLimiter::new(60);

        loop {
            let mut current_files: HashMap<PathBuf, (i64, bool, bool)> = HashMap::new();
            for (folder_id, dir, ignore_t, ignore_c) in &directories {
                if let Ok(entries) = fs::read_dir(dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if let Some(ext) = path.extension().and_then(OsStr::to_str) {
                            if AUDIO_EXTENSIONS.contains(&ext) || TRANSCRIPT_EXTENSIONS.contains(&ext) {
                                current_files.insert(path, (*folder_id, *ignore_t, *ignore_c));
                            }
                        }
                    }
                }
            }

            let current_paths: HashSet<PathBuf> = current_files.keys().cloned().collect();
            let new_files: Vec<PathBuf> = current_paths
                .difference(&known_files)
                .cloned()
                .collect();

            println!("New files found: {}", new_files.len());
            if new_files.is_empty() {
                rate_limiter.increment();
                rate_limiter.sleep();
            } else {
                rate_limiter.reset();
            }

            for file in &new_files {
                if let Some((folder_id, ignore_t, ignore_c)) = current_files.get(file) {
                    if let Some(ext) = file.extension().and_then(OsStr::to_str) {
                        let ext_lower = ext.to_lowercase();
                        let basename = file.file_name().and_then(OsStr::to_str).unwrap_or("");

                        conn.execute(
                            "INSERT OR IGNORE INTO known_files (file_name, folder_id, extension) VALUES (?1, ?2, ?3)",
                            params![basename, folder_id, format!(".{}", ext_lower)],
                        )
                        .ok();
                        let known_file_id: i64 = conn
                            .query_row(
                                "SELECT id FROM known_files WHERE file_name = ?1 AND folder_id = ?2",
                                params![basename, folder_id],
                                |row| row.get(0),
                            )
                            .unwrap_or(0);

                        let unix_ts = fs::metadata(file)
                            .and_then(|m| m.modified())
                            .ok()
                            .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                            .map(|d| d.as_secs() as i64)
                            .unwrap_or(0);

                        if AUDIO_EXTENSIONS.contains(&ext_lower.as_str()) {
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
                            conn.execute(
                                "INSERT OR IGNORE INTO audio_files (known_file_id, unix_timestamp) VALUES (?1, ?2)",
                                params![known_file_id, unix_ts],
                            )
                            .ok();
                            if transcript_exists {
                                println!(
                                    "Skipping transcription for {}: transcript exists",
                                    file.display()
                                );
                            } else if !ignore_t {
                                let _ = tx_transcribe.send(file.clone());
                                println!("Queued {} for transcription", file.display());
                            } else {
                                println!(
                                    "Skipping transcription for {}: flagged to ignore",
                                    file.display()
                                );
                            }
                            if ext_lower == "wav" {
                                let flac = file.with_extension("flac");
                                if flac.exists() {
                                    println!(
                                        "Skipping conversion for {}: FLAC exists",
                                        file.display()
                                    );
                                } else if !ignore_c {
                                    let _ = tx_convert.send(file.clone());
                                    println!("Queued {} for conversion", file.display());
                                } else {
                                    println!(
                                        "Skipping conversion for {}: flagged to ignore",
                                        file.display()
                                    );
                                }
                            }
                        } else if TRANSCRIPT_EXTENSIONS.contains(&ext_lower.as_str()) {
                            conn.execute(
                                "INSERT OR IGNORE INTO transcript_files (known_file_id, unix_timestamp) VALUES (?1, ?2)",
                                params![known_file_id, unix_ts],
                            )
                            .ok();
                            println!("Registered transcript {}", file.display());
                        }
                    }
                }
            }

            known_files.clear();
            known_files.extend(current_paths.into_iter());
        }
    })
}
