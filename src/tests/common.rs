use hound::{SampleFormat, WavSpec, WavWriter};
use std::path::Path;

pub fn write_dummy_wav(path: &Path) {
    let spec = WavSpec {
        channels: 1,
        sample_rate: 8000,
        bits_per_sample: 16,
        sample_format: SampleFormat::Int,
    };
    let mut writer = WavWriter::create(path, spec).unwrap();
    writer.write_sample(0i16).unwrap();
    writer.finalize().unwrap();
}
