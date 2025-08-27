# Twitter Backup Integration

TiRCorder can ingest data from Twitter's self-service data export. The download
contains JavaScript files such as `tweet.js`, `like.js`, and direct message
archives. Each file wraps the JSON payload in a variable assignment, e.g.:

```javascript
window.YTD.tweet.part0 = [ { "tweet": { ... } } ];
```

To parse these files the prefix and trailing semicolon must be stripped before
loading the JSON content.

## Direct Messages

Direct messages are grouped by conversation and exposed under the
`dmConversation` key. Each message has `messageCreate` metadata including
`createdAt`, `senderId`, and `text` fields.

## API and Rate Limits

Twitter's API enforces strict quotas. As of 2024 the free tier allows only a
small number of read requests per day and roughly 1,500 posts per month.
Downloading an archive avoids these limits but the export is only generated on
demand and may take hours to prepare.
