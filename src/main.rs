use crossbeam_channel::unbounded;
use log::error;
use std::env;
use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use tircorder_rs::{converter, scanner};

fn main() {
    env_logger::init();
    let shutdown = Arc::new(AtomicBool::new(false));
    let mut args = env::args().skip(1);
    match args.next().as_deref() {
        Some("scan") => {
            let dirs: Vec<PathBuf> = args.map(PathBuf::from).collect();
            let (tx_transcribe, _rx_t) = unbounded();
            let (tx_convert, rx_convert) = unbounded();
            let scanner_handle =
                scanner::start_scanner(dirs, tx_transcribe, tx_convert, shutdown.clone())
                    .expect("failed to start scanner");
            let converter_handle = converter::start_converter(rx_convert, shutdown.clone())
                .expect("failed to start converter");

            {
                let shutdown = shutdown.clone();
                ctrlc::set_handler(move || {
                    shutdown.store(true, Ordering::SeqCst);
                })
                .expect("Error setting Ctrl-C handler");
            }

            let _ = scanner_handle.join();
            let _ = converter_handle.join();
        }
        Some("convert") => {
            for file in args {
                if let Err(e) = converter::convert_file(PathBuf::from(file)) {
                    error!("Conversion failed: {e}");
                }
            }
        }
        _ => {
            error!("Usage: tircorder-rs <scan <dirs...>|convert <files...>>");
        }
    }
}
