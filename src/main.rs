use crossbeam_channel::unbounded;
use rusqlite::{params, Connection};
use std::env;
use std::io::{self, Write};
use std::path::PathBuf;
use tircorder_rs::{converter, scanner};

fn main() {
    let mut args = env::args().skip(1);
    match args.next().as_deref() {
        Some("scan") => {
            let (tx_transcribe, _rx_t) = unbounded();
            let (tx_convert, rx_convert) = unbounded();
            let scanner_handle = scanner::start_scanner(tx_transcribe, tx_convert);
            let _converter_handle = converter::start_converter(rx_convert);
            let _ = scanner_handle.join();
        }
        Some("convert") => {
            for file in args {
                converter::convert_file(PathBuf::from(file));
            }
        }
        Some("init") => {
            let mut dirs: Vec<PathBuf> = args.map(PathBuf::from).collect();
            if dirs.is_empty() {
                print!("Enter folder paths separated by spaces: ");
                io::stdout().flush().unwrap();
                let mut input = String::new();
                io::stdin()
                    .read_line(&mut input)
                    .expect("Failed to read input");
                dirs = input.split_whitespace().map(PathBuf::from).collect();
            }
            if dirs.is_empty() {
                eprintln!("No folders provided.");
                return;
            }
            let conn = Connection::open("state.db").expect("Failed to open database");
            conn.execute(
                "CREATE TABLE IF NOT EXISTS recordings_folders (
                    id INTEGER PRIMARY KEY,
                    folder_path TEXT UNIQUE,
                    ignore_transcribing INTEGER DEFAULT 0,
                    ignore_converting INTEGER DEFAULT 0
                )",
                [],
            )
            .expect("Failed to create recordings_folders table");
            for dir in dirs {
                let changes = conn
                    .execute(
                        "INSERT OR IGNORE INTO recordings_folders (folder_path) VALUES (?1)",
                        params![dir.to_string_lossy()],
                    )
                    .expect("Failed to insert folder");
                if changes > 0 {
                    println!("Added folder: {}", dir.display());
                } else {
                    println!("Folder already exists: {}", dir.display());
                }
            }
        }
        _ => {
            eprintln!("Usage: tircorder-rs <scan|convert <files...>>");
            eprintln!("Usage: tircorder-rs <scan <dirs...>|convert <files...>|init [folders...]>");
        }
    }
}
