use assert_cmd::Command;
use crossbeam_channel::unbounded;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::Duration;
use tempfile::tempdir;

use crate::scanner::{load_recording_dirs, start_scanner};
use crate::tests::common::write_dummy_wav;

#[test]
fn scan_uses_db_entries_without_cli_args() {
    let workspace = tempdir().unwrap();
    let recordings = workspace.path().join("recordings");
    std::fs::create_dir_all(&recordings).unwrap();
    let wav = recordings.join("sample.wav");
    write_dummy_wav(&wav);

    #[allow(deprecated)]
    let mut init = Command::cargo_bin("tircorder-rs").unwrap();
    init.current_dir(workspace.path())
        .args(["init", recordings.to_str().unwrap()])
        .assert()
        .success();

    let (dirs, used_db) = load_recording_dirs(&workspace.path().join("state.db"), Vec::new());
    assert!(used_db, "Expected database entries to be used when present");
    assert_eq!(dirs.len(), 1);
    assert_eq!(dirs[0].0, recordings);

    let (tx_transcribe, rx_transcribe) = unbounded();
    let (tx_convert, rx_convert) = unbounded();
    let shutdown = Arc::new(AtomicBool::new(false));

    let handle = start_scanner(dirs, tx_transcribe, tx_convert, shutdown.clone()).unwrap();
    std::thread::sleep(Duration::from_millis(100));

    let transcribed: Vec<_> = rx_transcribe.try_iter().collect();
    let converted: Vec<_> = rx_convert.try_iter().collect();

    assert!(transcribed.contains(&wav));
    assert!(converted.contains(&wav));

    shutdown.store(true, Ordering::SeqCst);
    handle.join().unwrap();
}

#[test]
fn cli_paths_used_when_database_empty() {
    let workspace = tempdir().unwrap();
    let recordings = workspace.path().join("recordings");
    std::fs::create_dir_all(&recordings).unwrap();
    let wav = recordings.join("fallback.wav");
    write_dummy_wav(&wav);

    let (dirs, used_db) =
        load_recording_dirs(&workspace.path().join("state.db"), vec![recordings.clone()]);
    assert!(!used_db, "Database should not be used when no rows exist");
    assert_eq!(dirs.len(), 1);
    assert_eq!(dirs[0].0, recordings);

    let (tx_transcribe, rx_transcribe) = unbounded();
    let (tx_convert, rx_convert) = unbounded();
    let shutdown = Arc::new(AtomicBool::new(false));

    let handle = start_scanner(dirs, tx_transcribe, tx_convert, shutdown.clone()).unwrap();
    std::thread::sleep(Duration::from_millis(100));

    let transcribed: Vec<_> = rx_transcribe.try_iter().collect();
    let converted: Vec<_> = rx_convert.try_iter().collect();

    assert!(transcribed.contains(&wav));
    assert!(converted.contains(&wav));

    shutdown.store(true, Ordering::SeqCst);
    handle.join().unwrap();
}
