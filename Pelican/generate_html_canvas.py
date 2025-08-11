import json
from pathlib import Path
from random import random

# Mapping of communication mediums to fixed z-layer positions
MEDIUM_Z_LAYERS = {
    "transcript": 0.0,
    "facebook_message": 10.0,
    "facebook_post": 20.0,
}

from generate_html_header import generate_html_header
from generate_html_footer import generate_html_footer
from sort_audio_transcript import extract_date


def dummy_tag(text: str) -> str:
    """Return a placeholder tag for the given text."""
    if "gertrude" in text.lower():
        return "Gertrude"
    return "Other"


def dummy_impact(text: str) -> float:
    """Return a placeholder impact score derived from word count."""
    words = len(text.split())
    return max(1.0, min(words / 20.0, 10.0))


def load_transcripts(transcripts_dir, items):
    """Populate ``items`` with transcript entries."""
    for path in Path(transcripts_dir).glob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        ts = extract_date(str(path)).timestamp()
        items.append({"ts": ts, "text": text, "medium": "transcript"})


def load_facebook_messages(messages_dir, items):
    """Load Facebook messages into ``items``."""
    for json_file in Path(messages_dir).rglob("*.json"):
        try:
            data = json.loads(Path(json_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for msg in data.get("messages", []):
            ts = msg.get("timestamp_ms")
            if ts is None:
                continue
            text = msg.get("content") or ""
            items.append({"ts": ts / 1000, "text": text, "medium": "facebook_message"})


def load_facebook_posts(posts_json, items):
    """Load Facebook posts from a JSON export."""
    path = Path(posts_json)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    posts = data.get("posts") or data.get("entries") or []
    for post in posts:
        ts = post.get("timestamp") or post.get("timestamp_ms")
        if ts is None:
            continue
        if isinstance(ts, str):
            try:
                ts = int(ts)
            except ValueError:
                continue
        if ts > 1e12:
            ts /= 1000
        text = ""
        if "data" in post and post["data"]:
            entry = post["data"][0]
            text = (
                entry.get("post") or entry.get("share", {}).get("original_text") or ""
            )
        items.append({"ts": ts, "text": text, "medium": "facebook_post"})


def build_points(items):
    """Build point dictionaries for Three.js rendering."""
    if not items:
        return []
    min_ts = min(i["ts"] for i in items)
    tag_positions = {}
    points = []
    for it in items:
        tag = dummy_tag(it["text"])
        impact = dummy_impact(it["text"])
        tag_positions.setdefault(tag, len(tag_positions) * 10)
        x = (it["ts"] - min_ts) / 86400.0
        y = tag_positions[tag]
        z_layer = MEDIUM_Z_LAYERS.get(it.get("medium"), 0.0)
        color = "#ff5555" if tag == "Gertrude" else "#5555ff"
        points.append(
            {"x": x, "y": y, "z": z_layer, "size": impact / 2, "color": color}
        )
    return points


def generate_canvas_script(points):
    """Generate the HTML/JS snippet for the 3D scene."""
    data_json = json.dumps(points)
    return f"""
            </div>
        </section>
        <section id=\"cloud\">
            <div id=\"scene-container\" style=\"width:100%;height:600px;\"></div>
        </section>
        <script src=\"https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js\"></script>
        <script src=\"https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/examples/js/controls/OrbitControls.js\"></script>
        <script>
        const DATA = {data_json};
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('scene-container').appendChild(renderer.domElement);
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        DATA.forEach(d => {{
            const geo = new THREE.SphereGeometry(d.size, 16, 16);
            const mat = new THREE.MeshBasicMaterial({{color: d.color}});
            const mesh = new THREE.Mesh(geo, mat);
            mesh.position.set(d.x, d.y, d.z);
            scene.add(mesh);
        }});
        camera.position.z = 30;

        // Scroll wheel traverses layers along the Z axis
        window.addEventListener('wheel', (event) => {{
            camera.position.z += event.deltaY * 0.01;
        }});

        function pollGamepad() {{
            const [gp] = navigator.getGamepads();
            if (gp) {{
                const tiltX = gp.axes[2] || 0; // right stick horizontal
                const tiltY = gp.axes[3] || 0; // right stick vertical
                camera.rotation.y -= tiltX * 0.05;
                camera.rotation.x -= tiltY * 0.05;
            }}
        }}

        function animate() {{
            requestAnimationFrame(animate);
            pollGamepad();
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        </script>
    """


def main(facebook_dir, transcripts_dir, output_file):
    """Entry point for generating the 3D bubble visualisation."""
    items = []
    load_transcripts(transcripts_dir, items)
    load_facebook_messages(Path(facebook_dir) / "messages", items)
    load_facebook_posts(Path(facebook_dir) / "posts/your_posts.json", items)
    points = build_points(items)
    html_content = generate_html_header()
    html_content += generate_canvas_script(points)
    html_content += generate_html_footer()
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate 3D canvas of tagged items.")
    parser.add_argument("facebook_dir", help="Path to extracted Facebook data")
    parser.add_argument("transcripts_dir", help="Path to transcripts directory")
    parser.add_argument(
        "--output", default="content/cloud.html", help="Output HTML file"
    )
    args = parser.parse_args()
    main(args.facebook_dir, args.transcripts_dir, args.output)
