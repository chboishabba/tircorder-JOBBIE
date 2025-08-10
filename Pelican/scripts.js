function supports3d() {
    const css3d = !!window.CSS && CSS.supports('transform-style', 'preserve-3d');
    let webgl = false;
    try {
        const canvas = document.createElement('canvas');
        webgl = !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
        webgl = false;
    }
    return css3d || webgl;
}

function initTimeline3DIfSupported() {
    if (!supports3d()) {
        return;
    }

    const script = document.createElement('script');
    script.src = 'timeline3d.js';
    script.onload = function() {
        if (typeof window.initTimeline3D === 'function') {
            window.initTimeline3D();
        }
    };
    document.body.appendChild(script);
}

document.addEventListener("DOMContentLoaded", function() {
    const timelineItems = document.querySelectorAll(".timeline-item");

    timelineItems.forEach(item => {
        const label = item.querySelector(".label");
        const audioPlayer = item.querySelector(".audio-player");
        const audio = audioPlayer.querySelector("audio");
        const source = audio.querySelector("source");
        const transcript = audioPlayer.querySelector("pre");
        const transcriptDisplay = audioPlayer.querySelector(".transcript-display");

        label.addEventListener("click", function(event) {
            event.preventDefault();
            if (audioPlayer.style.display === "block") {
                audioPlayer.style.display = "none";
            } else {
                audioPlayer.style.display = "block";
                if (!audio.src) {
                    audio.src = source.getAttribute("data-src");
                }
            }
        });

        audio.addEventListener("timeupdate", function() {
            const currentTime = audio.currentTime;
            const lines = transcript.textContent.split('\n');
            let highlighted = false;

            transcript.innerHTML = lines.map(line => {
                const timeMatch = line.match(/\d{2}:\d{2}:\d{2},\d{3}/g);
                if (timeMatch) {
                    const [start, end] = timeMatch.map(time => {
                        const [hours, minutes, seconds] = time.split(':');
                        return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseFloat(seconds.replace(',', '.'));
                    });
                    if (currentTime >= start && currentTime <= end && !highlighted) {
                        highlighted = true;
                        return `<span class="highlight">${line}</span>`;
                    }
                }
                return line;
            }).join('\n');

            transcriptDisplay.innerHTML = lines.map(line => {
                const timeMatch = line.match(/\d{2}:\d{2}:\d{2},\d{3}/g);
                if (timeMatch) {
                    const [start, end] = timeMatch.map(time => {
                        const [hours, minutes, seconds] = time.split(':');
                        return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseFloat(seconds.replace(',', '.'));
                    });
                    if (currentTime >= start && currentTime <= end && !highlighted) {
                        highlighted = true;
                        return `<div class="highlight">${line}</div>`;
                    }
                }
                return line;
            }).join('\n');
        });
    });

    initTimeline3DIfSupported();
});

