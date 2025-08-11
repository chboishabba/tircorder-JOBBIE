use crossbeam_channel::Receiver;
use ffmpeg_cli::{FfmpegBuilder, File, Parameter};
use std::ffi::OsStr;
use std::path::PathBuf;
use std::thread;

/// Starts a background thread that listens for files on `rx` and converts
/// each WAV file to FLAC using `ffmpeg`.
pub fn start_converter(rx: Receiver<PathBuf>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        for file in rx {
            if file.extension().and_then(OsStr::to_str) != Some("wav") {
                continue;
            }
            let output = file.with_extension("flac");
            let input_str = file.to_string_lossy().into_owned();
            let output_str = output.to_string_lossy().into_owned();
            let builder = FfmpegBuilder::new()
                .option(Parameter::Single("y"))
                .input(File::new(&input_str))
                .output(File::new(&output_str));
            let mut command = builder.to_command();
            if let Err(e) = command.status() {
                eprintln!("Failed to convert {:?}: {}", file, e);
            }
        }
    })
}

/// Convert a single file synchronously. This is useful for CLI integration.
pub fn convert_file(file: PathBuf) {
    let (tx, rx) = crossbeam_channel::unbounded();
    let handle = start_converter(rx);
    let _ = tx.send(file);
    drop(tx);
    let _ = handle.join();
}
