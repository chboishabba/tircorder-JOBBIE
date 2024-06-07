# generate_content.py
from jinja2 import Template

template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Audio Recordings</title>
    <style>
        /* Add your CSS here */
    </style>
</head>
<body>
    <h1>Audio Recordings Timeline</h1>
    <div id="timeline">
        {% for audio, transcript in matches %}
            <div class="recording" data-audio="{{ audio }}" data-transcript="{{ transcript }}">
                {{ audio }}
            </div>
        {% endfor %}
    </div>
    <h2>Dangling Files</h2>
    <h3>Audio without Transcripts</h3>
    <ul>
        {% for audio in dangling_audio %}
            <li>{{ audio }}</li>
        {% endfor %}
    </ul>
    <h3>Transcripts without Audio</h3>
    <ul>
        {% for transcript in dangling_transcripts %}
            <li>{{ transcript }}</li>
        {% endfor %}
    </ul>
    <script>
        /* Add your JavaScript here */
    </script>
</body>
</html>
""")

output = template.render(
    matches=matches,
    dangling_audio=dangling_audio,
    dangling_transcripts=dangling_transcripts
)

with open('content/timeline.html', 'w') as f:
    f.write(output)
 
