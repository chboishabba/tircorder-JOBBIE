use crossbeam_channel::{Receiver, RecvTimeoutError};
use ffmpeg_cli::{FfmpegBuilder, File, Parameter};
use std::ffi::OsStr;
use std::io;
use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::Duration;

/// Starts a background thread that listens for files on `rx` and converts
/// each WAV file to FLAC using `ffmpeg`.
/// The loop terminates when `shutdown` is set to `true` or `rx` is disconnected.
pub fn start_converter(
    rx: Receiver<PathBuf>,
    shutdown: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<Result<(), io::Error>>, io::Error> {
    Ok(thread::spawn(move || -> Result<(), io::Error> {
        while !shutdown.load(Ordering::SeqCst) {
            match rx.recv_timeout(Duration::from_secs(1)) {
                Ok(file) => {
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
                    let status = command.status()?;
                    if !status.success() {
                        return Err(io::Error::new(io::ErrorKind::Other, "ffmpeg failed"));
                    }
                }
                Err(RecvTimeoutError::Timeout) => continue,
                Err(RecvTimeoutError::Disconnected) => break,
            }
        }
        Ok(())
    }))
}

/// Convert a single file synchronously. This is useful for CLI integration.
pub fn convert_file(file: PathBuf) -> Result<(), io::Error> {
    let (tx, rx) = crossbeam_channel::unbounded();
    tx.send(file)
        .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
    drop(tx);
    let shutdown = Arc::new(AtomicBool::new(false));
    let handle = start_converter(rx, shutdown)?;
    handle
        .join()
        .map_err(|_| io::Error::new(io::ErrorKind::Other, "thread panicked"))??;
    Ok(())
}
