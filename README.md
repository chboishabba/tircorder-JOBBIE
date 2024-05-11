# TiRCorder: Part of the ITIR Suite


TiRCorder is an integral component of the Intergenerational Trauma-Informed Identity Rebuilder (ITIR) toolset. This multifaceted suite is designed to tackle complex challenges in data management, security, and user interaction, with a special focus on addressing the needs of those dealing with intergenerational trauma. Licensed under the Mozilla Public License, ITIR embodies a commitment to open, secure, and ethical technology development.


The BETA TiRCORDER Voice-Activated Recorder (codename 'jobbie') is a component of the larger ITIR project, which aims to provide a comprehensive suite of tools for recording and analyzing various forms of data. This specific component focuses on intelligently managing audio recordings through voice activation, ensuring efficient data capture and storage. More details about the larger project can be found at [TFYQA.biz](https://TFYQA.biz). If you found this tool useful, [buy us a coffee](https://www.paypal.com/paypalme/JohnABrown)!

[See TFYQA's history](https://web.archive.org/web/20070831084954/http://www.tfyqa.biz/)

## TiRCorder Specifics

TiRCorder, specifically tailored for professional environments, prioritizes security, efficiency, and user experience:

- **Voice Detection**: Utilizes advanced algorithms for effective voice capture throughout the day.
- **Task Scheduling**: Manages multiple tasks efficiently without conflicts.
- **Professional-Grade**: Designed for on-site data retention to meet stringent professional standards.
- **Multiple Client Support**: Equipped to handle numerous clients recording simultaneously.
- **GPU Acceleration**: Leverages GPU capabilities for enhanced performance (CPU also supported).
- **Whisper-ctranslate2 Integration**: Offers a choice between ultra-fast [cTranslate2-powered](https://github.com/Softcatala/whisper-ctranslate2) transcription and versatile Python-based [Whisper](https://github.com/openai/whisper)	 for extended functionality.

## Coming Soon

- **Speaker Diarization**
- **Word-level Transcripts**
- **Word-level Confidence Scores**
- **User-friendly Web Interface**
- **Streamlined Setup Process**

## Features

- **Voice Activation**: Automatically starts recording when voice is detected.
- **Activity-Based Recording Management**: Adjusts recording sensitivity based on user activity.
- **Resource Efficient**: Optimizes CPU and memory usage to ensure minimal impact on system performance.
- **Adaptive Recording**: Changes recording intervals based on detected activity to save storage and processing power.
- **Separated concerns**: Manage transcription on an external machine, ensuring the client can get on with things. 


## Installation

Ensure you have Python 3.8 (tested 3.9.18 arch linux) or higher installed on your system. Run tircorder-linux.py on linux. You can check your Python version by running:


```
python --version
```
# Dependencies

TiRCorder requires the command-line tool ffmpeg to be installed on your system, which is available from most package managers:
```
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
yay -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```
You may need rust installed as well, in case tiktoken does not provide a pre-built wheel for your platform. If you see installation errors during setup	, please follow the [Getting started](https://www.rust-lang.org/learn/get-started) page to install Rust development environment. Additionally, you may need to configure the PATH environment variable, e.g. export PATH="$HOME/.cargo/bin:$PATH". If the installation fails with No module named 'setuptools_rust', you need to install setuptools_rust, e.g. by running:
```
pip install setuptools-rust
```

## Setup

Clone the repository to your local machine:

```
git clone https://github.com/yourusername/tircorder.git
cd tircorder
python tircorder.py
```


##Usage

To start the voice-activated recorder, navigate to the cloned directory and run:

```
python tircorder.py
```


Most users will want mode 1. In this mode, the application will run in the background, monitoring for voice activity and user interactions to manage recording intervals intelligently. It will process recordings as they appear. You may notice some performance degradation while transcription is occurring.

It is recommended to disable when consuming media within range of the microphone as excessive storage may be consumed.

### Configuration
Choose betwen whisper-python and ctranslate


Modify the config.py file to adjust the sensitivity settings and other preferences according to your needs.
Contributing

Contributions to the TiRCORDER project are welcome. Please fork the repository, make your changes, and submit a pull request for review.
## License

ITIR and TiRCorder are products of TFYQA.biz provided under [Mozilla Public License - MPL 2.0](https://www.mozilla.org/en-US/MPL/). 
All rights are reserved where permitted.

