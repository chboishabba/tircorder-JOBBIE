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
