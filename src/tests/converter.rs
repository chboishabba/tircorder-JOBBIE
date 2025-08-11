use crate::converter::convert_file;
use crate::tests::common::write_dummy_wav;
use tempfile::tempdir;

#[test]
fn converts_wav_to_flac() {
    let dir = tempdir().unwrap();
    let wav_path = dir.path().join("sample.wav");
    write_dummy_wav(&wav_path);

    convert_file(wav_path.clone());

    let flac_path = wav_path.with_extension("flac");
    assert!(flac_path.exists());
}
