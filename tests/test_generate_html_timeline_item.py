from Pelican.generate_html_timeline_item import generate_html_timeline_item


def test_generate_html_timeline_item_without_frequency(tmp_path):
    transcript = tmp_path / "sample.txt"
    transcript.write_text("hello world")

    html = generate_html_timeline_item(
        "audio.mp3",
        "transcript.txt",
        str(transcript),
        "phone",
        "Alice",
    )

    assert "data-frequency" not in html
    assert 'data-platform="phone"' in html
    assert 'data-contact="Alice"' in html
    assert '<source data-src="symlinks/audio.mp3" type="audio/mpeg">' in html
    assert '<div class="highlight-container"></div>' in html
    assert '<pre aria-label="Transcript">hello world</pre>' in html


def test_generate_html_timeline_item_with_frequency(tmp_path):
    transcript = tmp_path / "sample.txt"
    transcript.write_text("hello world")

    html = generate_html_timeline_item(
        "audio.mp3",
        "transcript.txt",
        str(transcript),
        "phone",
        "Alice",
        frequency=5,
    )

    assert 'data-frequency="5"' in html


def test_generate_html_timeline_item_url_encodes_paths(tmp_path):
    transcript = tmp_path / "sample transcript.txt"
    transcript.write_text("line")

    html = generate_html_timeline_item(
        "audio clip 01.mp3",
        "sample transcript.txt",
        str(transcript),
        "phone",
        "Alice",
    )

    assert 'data-audio="symlinks/audio%20clip%2001.mp3"' in html
    assert 'data-transcript="symlinks/sample%20transcript.txt"' in html
