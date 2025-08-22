from wordcloud_utils import WordCloudCache, generate_wordcloud


def test_wordcloud_generation_and_retrieval(tmp_path):
    db_path = tmp_path / "wc.sqlite"
    cache = WordCloudCache(db_path=str(db_path))

    text = "repeat words repeat words unique"
    summary1 = generate_wordcloud(text, cache)
    counts1 = summary1.word_counts
    html1 = summary1.wordcloud_html
    assert counts1["repeat"] == 2 and counts1["unique"] == 1
    assert "repeat" in html1 and "unique" in html1

    cache.close()
    cache2 = WordCloudCache(db_path=str(db_path))
    summary2 = generate_wordcloud(text, cache2)
    counts2 = summary2.word_counts
    html2 = summary2.wordcloud_html
    assert counts1 == counts2
    assert html1 == html2

    cur = cache2.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM wordclouds")
    assert cur.fetchone()[0] == 1
    cache2.close()


def test_empty_text_wordcloud(tmp_path):
    db_path = tmp_path / "wc.sqlite"
    cache = WordCloudCache(db_path=str(db_path))

    summary = generate_wordcloud("", cache)
    assert summary.word_counts == {}
    assert summary.wordcloud_html == '<div class="wordcloud"></div>'
    cache.close()
