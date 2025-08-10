from Pelican.transcript_frequency import calculate_noun_frequency


def test_calculate_noun_frequency_counts_nouns(tmp_path):
    transcript = tmp_path / "sample.txt"
    transcript.write_text("Alice met Bob in Wonderland. Alice saw the rabbit.")

    freq = calculate_noun_frequency(str(transcript))

    # Expected nouns: Alice, Bob, Wonderland, Alice, rabbit -> 5 occurrences
    assert freq == 5
