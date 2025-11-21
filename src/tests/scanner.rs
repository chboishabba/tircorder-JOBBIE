use crate::scanner::{scan_directories, start_scanner};
use crate::tests::common::write_dummy_wav;
use crossbeam_channel::unbounded;
use crossbeam_channel::TryRecvError;
use std::collections::HashSet;
use std::fs;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::Duration;
use tempfile::tempdir;

#[test]
fn scan_directories_respects_ignore_flags() {
    let dir1 = tempdir().unwrap();
    let dir2 = tempdir().unwrap();
    let dir3 = tempdir().unwrap();

    let a = dir1.path().join("a.wav");
    write_dummy_wav(&a);
    let b = dir1.path().join("b.wav");
    write_dummy_wav(&b);
    let b_flac = dir1.path().join("b.flac");
    fs::write(&b_flac, b"flac").unwrap();
    let c = dir1.path().join("c.wav");
    write_dummy_wav(&c);
    fs::write(dir1.path().join("c.srt"), "").unwrap();

    let d = dir2.path().join("d.wav");
    write_dummy_wav(&d);

    let (tx_transcribe, _rx_transcribe) = unbounded();
    let (tx_convert, _rx_convert) = unbounded();
    let shutdown = Arc::new(AtomicBool::new(false));

    let handle = start_scanner(
        vec![dir1.path().to_path_buf()],
        tx_transcribe,
        tx_convert,
        shutdown.clone(),
    )
    .unwrap();

    let e = dir3.path().join("e.wav");
    write_dummy_wav(&e);

    let dirs = vec![
        (dir1.path().to_path_buf(), false, false),
        (dir2.path().to_path_buf(), true, false),
        (dir3.path().to_path_buf(), false, true),
    ];

    let (transcribe, convert) = scan_directories(dirs);

    let transcribe_set: HashSet<_> = transcribe.iter().cloned().collect();
    let expected_transcribe: HashSet<_> = vec![a.clone(), b.clone(), b_flac.clone(), e.clone()]
        .into_iter()
        .collect();
    assert_eq!(transcribe_set, expected_transcribe);

    let convert_set: HashSet<_> = convert.iter().cloned().collect();
    let expected_convert: HashSet<_> = vec![a, c, d].into_iter().collect();
    assert_eq!(convert_set, expected_convert);
    shutdown.store(true, Ordering::SeqCst);
    handle.join().unwrap();
}

#[test]
fn start_scanner_dispatches_new_files() {
    let dir = tempdir().unwrap();
    let shutdown = Arc::new(AtomicBool::new(false));

    let (tx_transcribe, rx_transcribe) = unbounded();
    let (tx_convert, rx_convert) = unbounded();

    let handle = start_scanner(
        vec![dir.path().to_path_buf()],
        tx_transcribe,
        tx_convert,
        shutdown.clone(),
    )
    .unwrap();

    let audio = dir.path().join("sample.wav");
    write_dummy_wav(&audio);

    let transcribe_path = rx_transcribe.recv_timeout(Duration::from_secs(1)).unwrap();
    let convert_path = rx_convert.recv_timeout(Duration::from_secs(1)).unwrap();

    assert_eq!(transcribe_path, audio);
    assert_eq!(convert_path, audio);

    shutdown.store(true, Ordering::SeqCst);
    handle.join().unwrap();

    assert!(matches!(
        rx_transcribe.try_recv(),
        Err(TryRecvError::Empty | TryRecvError::Disconnected)
    ));
    assert!(matches!(
        rx_convert.try_recv(),
        Err(TryRecvError::Empty | TryRecvError::Disconnected)
    ));
}
