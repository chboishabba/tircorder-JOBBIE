use crate::converter::convert_file;
use crate::tests::common::write_dummy_wav;
use tempfile::tempdir;

#[test]
#[ignore]
fn converts_wav_to_flac() {
    if std::process::Command::new("ffmpeg")
        .arg("-version")
        .output()
        .is_err()
    {
        eprintln!("ffmpeg not available; skipping conversion test");
        return;
    }

    let dir = tempdir().unwrap();
    let wav_path = dir.path().join("sample.wav");
    write_dummy_wav(&wav_path);

    let _ = convert_file(wav_path.clone());

    let flac_path = wav_path.with_extension("flac");
    assert!(flac_path.exists());
}
