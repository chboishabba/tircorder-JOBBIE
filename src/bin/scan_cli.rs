use std::env;
use std::path::PathBuf;

use tircorder_rs::scanner::scan_directories;

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut dirs = Vec::new();
    for chunk in args.chunks(3) {
        if chunk.len() == 3 {
            let path = PathBuf::from(&chunk[0]);
            let ignore_t = &chunk[1] == "1";
            let ignore_c = &chunk[2] == "1";
            dirs.push((path, ignore_t, ignore_c));
        }
    }
    let (transcribe, convert) = scan_directories(dirs);
    for p in transcribe {
        println!("T:{}", p.display());
    }
    for p in convert {
        println!("C:{}", p.display());
    }
}
