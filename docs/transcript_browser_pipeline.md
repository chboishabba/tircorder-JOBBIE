# Transcript Browser Website Logic

This note explains how the Pelican utilities turn recorded transcripts into the clickable web experience (audio player, transcript browser, and seek-on-click interactions).

## Inputs and discovery
- The scanner reads the list of source folders from `folders_file.json` and traverses each directory for known audio (`.wav`, `.flac`, `.mp3`, `.ogg`) and transcript (`.srt`, `.txt`, `.vtt`, `.json`, `.tsv`) extensions. It writes the current inventory to `traversal_results.json` so subsequent runs can reuse the snapshot. 【F:Pelican/generate_html.py†L1-L37】【F:Pelican/dir_traversal.py†L5-L39】
- File basenames drive pairing: audio and transcript entries are keyed by filename without the extension (e.g., `20240511-151702.wav` pairs with `20240511-151702.srt`). 【F:Pelican/generate_html.py†L30-L34】【F:Pelican/match_files.py†L1-L15】

## Matching and ordering
- `match_files` divides the inventory into matched pairs plus dangling audio/transcripts when a basename lacks a partner. 【F:Pelican/match_files.py†L1-L15】
- Matches are sorted chronologically. The sorter pulls a timestamp from a `YYYYMMDD-HHMMSS` pattern in the filename and falls back to file creation time when the pattern is missing. 【F:Pelican/sort_audio_transcript.py†L1-L10】

## Preparing web-safe assets
- The generator builds `output/symlinks/` and creates symlinks for every matched and dangling asset. Only the symlink names appear in the HTML, keeping the site layout stable even if the originals move. 【F:Pelican/generate_html.py†L20-L49】
- Transcript bodies are read with a UTF-8/ISO-8859-1 fallback, then HTML-escaped to avoid script injection before they land in the page. 【F:Pelican/generate_html_matches.py†L1-L35】

## HTML assembly
- `generate_html.py` stitches together the header/footer scaffolding with timeline items for each match and dangling lists for unmatched files. The output is written to `content/timeline.html`. 【F:Pelican/generate_html.py†L41-L77】
- Each timeline item is a `<div>` containing a label that stores `data-audio` and `data-transcript` URLs plus a hidden audio player. The player holds the transcript in a `<pre>` tag and an empty `.transcript-display` container for live highlights. 【F:Pelican/generate_html_matches.py†L7-L30】

## Browser behavior
- `scripts.js` wires accessibility and playback behavior. Clicking or pressing Enter on a label toggles the associated audio panel and lazy-loads the source from the `data-src` attribute. Arrow keys jump between timeline items. 【F:Pelican/scripts.js†L23-L65】
- During playback, `timeupdate` events parse SRT-style timestamps in the transcript, highlight the current line, and mirror the highlighted text into `.transcript-display` so the active caption is obvious. 【F:Pelican/scripts.js†L67-L93】
- If the environment supports it, a 3D timeline enhancer is loaded after the DOM is ready. 【F:Pelican/scripts.js†L1-L22】【F:Pelican/scripts.js†L95-L99】

## Running the generator
Run `python Pelican/generate_html.py` from the repository root after updating `folders_file.json` with your recording directories. The script refreshes symlinks and regenerates `content/timeline.html`, which you can serve as a static page alongside the bundled CSS/JS assets.
