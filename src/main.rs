use std::env;
use std::path::PathBuf;
use crossbeam_channel::unbounded;
use tircorder_rs::{converter, scanner};

fn main() {
    let mut args = env::args().skip(1);
    match args.next().as_deref() {
        Some("scan") => {
            let dirs: Vec<PathBuf> = args.map(PathBuf::from).collect();
            let (tx_transcribe, _rx_t) = unbounded();
            let (tx_convert, rx_convert) = unbounded();
            let scanner_handle = scanner::start_scanner(dirs, tx_transcribe, tx_convert);
            let _converter_handle = converter::start_converter(rx_convert);
            let _ = scanner_handle.join();
        }
        Some("convert") => {
            for file in args {
                converter::convert_file(PathBuf::from(file));
            }
        }
        _ => {
            eprintln!("Usage: tircorder-rs <scan <dirs...>|convert <files...>>");
        }
    }
}
