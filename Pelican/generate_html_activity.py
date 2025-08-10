import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from generate_html_header import generate_html_header
from generate_html_footer import generate_html_footer
from sort_audio_transcript import extract_date


def word_count(text: str) -> int:
    """Return a simple word count for the provided text."""
    return len(text.split())


def load_transcripts(transcripts_dir, counts):
    """Accumulate word counts from transcript text files."""
    for path in Path(transcripts_dir).glob('*.txt'):
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        day = extract_date(str(path)).date().isoformat()
        counts[day] += word_count(text)


def load_facebook_messages(messages_dir, counts):
    """Accumulate word counts from Facebook message JSON files."""
    for json_file in Path(messages_dir).rglob('*.json'):
        try:
            data = json.loads(Path(json_file).read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        for msg in data.get('messages', []):
            ts = msg.get('timestamp_ms')
            if ts is None:
                continue
            day = datetime.utcfromtimestamp(ts / 1000).date().isoformat()
            text = msg.get('content')
            if text:
                counts[day] += word_count(text)
            elif any(msg.get(k) for k in ('photos', 'videos')):
                counts[day] += 1


def load_facebook_posts(posts_json, counts):
    """Accumulate word counts from a Facebook posts JSON file."""
    path = Path(posts_json)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
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
        counts[day] += word_count(text) if text else 1


def aggregate_periods(day_counts):
    """Return aggregated counts for week, month, and year."""
    week_counts = defaultdict(int)
    month_counts = defaultdict(int)
    year_counts = defaultdict(int)
    for day_str, words in day_counts.items():
        date_obj = datetime.fromisoformat(day_str).date()
        week_key = f"{date_obj.isocalendar().year}-W{date_obj.isocalendar().week:02d}"
        month_key = date_obj.strftime("%Y-%m")
        year_key = date_obj.strftime("%Y")
        week_counts[week_key] += words
        month_counts[month_key] += words
        year_counts[year_key] += words
    return week_counts, month_counts, year_counts


def generate_table_script(data):
    """Return HTML for the activity table and script."""
    json_data = json.dumps(data)
    return f"""
<select id=\"scale\">
  <option value=\"day\">Day</option>
  <option value=\"week\">Week</option>
  <option value=\"month\">Month</option>
  <option value=\"year\">Year</option>
</select>
<table>
  <thead><tr><th>Period</th><th>Words</th></tr></thead>
  <tbody id=\"activity-body\"></tbody>
</table>
<script>
const DATA = {json_data};
const select = document.getElementById('scale');
function render() {{
  const scale = select.value;
  const rows = Object.keys(DATA[scale]).sort().map(k => `<tr><td>${k}</td><td>${DATA[scale][k]}</td></tr>`).join('');
  document.getElementById('activity-body').innerHTML = rows;
}}
select.addEventListener('change', render);
render();
</script>
"""


def main(facebook_dir, transcripts_dir, output_file):
    day_counts = defaultdict(int)
    load_transcripts(transcripts_dir, day_counts)
    load_facebook_messages(Path(facebook_dir) / 'messages', day_counts)
    load_facebook_posts(Path(facebook_dir) / 'posts/your_posts.json', day_counts)
    week_counts, month_counts, year_counts = aggregate_periods(day_counts)
    data = {
        'day': day_counts,
        'week': week_counts,
        'month': month_counts,
        'year': year_counts,
    }
    html_content = generate_html_header()
    html_content += generate_table_script(data)
    html_content += generate_html_footer()
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate activity summary at various scales.')
    parser.add_argument('facebook_dir', help='Path to extracted Facebook data')
    parser.add_argument('transcripts_dir', help='Path to transcripts directory')
    parser.add_argument('--output', default='content/activity.html', help='Output HTML file')
    args = parser.parse_args()
    main(args.facebook_dir, args.transcripts_dir, args.output)
