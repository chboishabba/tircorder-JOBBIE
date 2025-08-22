use crate::scanner::start_scanner;
use crate::tests::common::write_dummy_wav;
use crossbeam_channel::unbounded;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::Duration;
use tempfile::tempdir;

#[test]
fn scanner_detects_wav_and_sends_to_queues() {
    let dir = tempdir().unwrap();
    let wav_path = dir.path().join("sample.wav");
    write_dummy_wav(&wav_path);


    let (tx_transcribe, rx_transcribe) = unbounded();
    let (tx_convert, rx_convert) = unbounded();
    let shutdown = Arc::new(AtomicBool::new(false));

    let handle =
        start_scanner(vec![dir.path().to_path_buf()], tx_transcribe, tx_convert, shutdown.clone())
            .unwrap();

    let transcribe_msg = rx_transcribe.recv_timeout(Duration::from_secs(2)).unwrap();
    let convert_msg = rx_convert.recv_timeout(Duration::from_secs(2)).unwrap();

    assert_eq!(transcribe_msg, wav_path);
    assert_eq!(convert_msg, wav_path);

    shutdown.store(true, Ordering::SeqCst);
    handle.join().unwrap();
}
