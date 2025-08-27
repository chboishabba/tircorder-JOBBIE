from integrations.twitter_backup import TwitterBackupConnector


def test_parse_tweets(tmp_path):
    sample = (
        "window.YTD.tweet.part0 = ["
        '{"tweet":{"id":"1","created_at":"2024-05-10T12:34:56.000Z",'
        '"full_text":"hello"}}];'
    )
    p = tmp_path / "tweet.js"
    p.write_text(sample, encoding="utf-8")
    connector = TwitterBackupConnector()
    events = connector.parse_tweets(str(p))
    assert len(events) == 1
    event = events[0]
    assert event["event_id"] == "tweet_1"
    assert event["action"] == "tweet"
    assert event["details"]["text"] == "hello"


def test_parse_messages(tmp_path):
    sample = (
        "window.YTD.direct_message.part0 = ["
        '{\n  "dmConversation": {\n    "conversationId": "u-u",\n'
        '    "messages": [\n      {\n        "messageCreate": {\n'
        '          "id": "2",\n'
        '          "createdAt": "2024-05-10T13:00:00.000Z",\n'
        '          "senderId": "123",\n'
        '          "text": "hi"\n        }\n      }\n    ]\n  }\n}];'
    )
    p = tmp_path / "dm.js"
    p.write_text(sample, encoding="utf-8")
    connector = TwitterBackupConnector()
    events = connector.parse_messages(str(p))
    assert len(events) == 1
    event = events[0]
    assert event["event_id"] == "dm_2"
    assert event["actor"] == "123"
    assert event["details"]["conversation_id"] == "u-u"
    assert event["details"]["text"] == "hi"
