import json
import html
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from generate_html_header import generate_html_header
from generate_html_footer import generate_html_footer
from sort_audio_transcript import extract_date

AUDIO_EXTS = {'.wav', '.flac', '.mp3', '.ogg'}


def load_recordings(recordings_dir, by_day):
    """Populate by_day with recordings grouped by date."""
    for path in Path(recordings_dir).glob('*'):
        if path.suffix.lower() in AUDIO_EXTS:
            day = extract_date(str(path)).date().isoformat()
            link = f'<a href="{path}">{html.escape(path.name)}</a>'
            by_day[day]['recordings'].append(link)


def load_messages(messages_dir, by_day):
    """Read Facebook message JSON files and group messages by day."""
    for json_file in Path(messages_dir).rglob('*.json'):
        try:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        for msg in data.get('messages', []):
            ts = msg.get('timestamp_ms')
            if ts is None:
                continue
            day = datetime.utcfromtimestamp(ts / 1000).date().isoformat()
            text = msg.get('content')
            if text:
                by_day[day]['messages'].append(html.escape(text))
            elif msg.get('photos'):
                by_day[day]['messages'].append('[photo]')
            elif msg.get('videos'):
                by_day[day]['messages'].append('[video]')
            else:
                by_day[day]['messages'].append('[non-text message]')


def load_posts(posts_json, by_day):
    """Read a Facebook posts JSON file and group posts by day."""
    path = Path(posts_json)
    if not path.exists():
        return
    try:
        data = json.load(open(path, encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return
    posts = data.get('posts') or data.get('entries') or []
    for post in posts:
        ts = post.get('timestamp') or post.get('timestamp_ms')
        if ts is None:
            continue
        if isinstance(ts, str):
            try:
                ts = int(ts)
            except ValueError:
                continue
        day = datetime.utcfromtimestamp(ts / 1000 if ts > 1e12 else ts).date().isoformat()
        text = ''
        if 'data' in post and post['data']:
            entry = post['data'][0]
            text = entry.get('post') or entry.get('share', {}).get('original_text') or ''
        by_day[day]['posts'].append(html.escape(text) if text else '[post]')


def generate_table(by_day):
    """Return an HTML table for the aggregated day data."""
    lines = [
        '<table>',
        '<thead><tr><th>Date</th><th>Recordings</th><th>Messages</th><th>Posts</th></tr></thead>',
        '<tbody>'
    ]
    for day in sorted(by_day):
        rec_html = '<br>'.join(by_day[day]['recordings'])
        msg_html = '<br>'.join(by_day[day]['messages'])
        post_html = '<br>'.join(by_day[day]['posts'])
        lines.append(f'<tr><td>{day}</td><td>{rec_html}</td><td>{msg_html}</td><td>{post_html}</td></tr>')
    lines.append('</tbody></table>')
    return '\n'.join(lines)


def main(facebook_dir, recordings_dir, output_file):
    by_day = defaultdict(lambda: {'recordings': [], 'messages': [], 'posts': []})
    load_recordings(recordings_dir, by_day)
    load_messages(Path(facebook_dir) / 'messages', by_day)
    load_posts(Path(facebook_dir) / 'posts/your_posts.json', by_day)

    html_content = generate_html_header()
    html_content += generate_table(by_day)
    html_content += generate_html_footer()

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate daily table from Facebook export.')
    parser.add_argument('facebook_dir', help='Path to extracted Facebook data')
    parser.add_argument('recordings_dir', help='Path to recordings directory')
    parser.add_argument('--output', default='content/facebook.html', help='Output HTML file')
    args = parser.parse_args()
    main(args.facebook_dir, args.recordings_dir, args.output)
