# Facebook Backup Integration

TiRCorder can ingest Facebook data downloads created using the **"Download Your Information"** tool.  Extract the archive and point the connector at the top-level directory.

## Expected Directory Layout

```
archive/
├── posts/your_posts.json
├── messages/inbox/<thread>/message_1.json
├── reactions/reactions.json
└── media/...
```

- `posts/your_posts.json` contains a `posts` array with `timestamp` and `data.post` fields.  Attachments may specify `data.media.uri` pointing to files under `media/`.
- `messages/inbox/<thread>/message_*.json` contain `messages` entries with `timestamp_ms`, `sender_name`, `content` and optional `photos.uri` values.
- `reactions/reactions.json` lists reactions with `timestamp`, `title` and `uri` keys.

Media references are resolved relative to the archive root and exposed in the `media` field of emitted events.
