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
    const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;
    if (prefersReducedMotion || !supports3d()) {
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
    const skipLink = document.querySelector('.skip-link');
    if (skipLink) {
        skipLink.addEventListener('click', function(event) {
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                event.preventDefault();
                mainContent.focus();
            }
        });
    }

    const timelineItems = document.querySelectorAll(".timeline-item");

    timelineItems.forEach((item, index) => {
        const label = item.querySelector(".label");
        const audioPlayer = item.querySelector(".audio-player");
        const audio = audioPlayer.querySelector("audio");
        const source = audio.querySelector("source");
        const transcript = audioPlayer.querySelector("pre");
        const transcriptDisplay = audioPlayer.querySelector(".transcript-display");

        const playerId = `player-${index}`;
        audioPlayer.id = playerId;
        label.setAttribute("role", "button");
        label.setAttribute("aria-controls", playerId);
        label.setAttribute("aria-expanded", "false");

        label.addEventListener("click", function(event) {
            event.preventDefault();
            const isExpanded = label.getAttribute("aria-expanded") === "true";
            if (isExpanded) {
                audioPlayer.style.display = "none";
                label.setAttribute("aria-expanded", "false");
            } else {
                audioPlayer.style.display = "block";
                label.setAttribute("aria-expanded", "true");
                if (!audio.src) {
                    audio.src = source.getAttribute("data-src");
                }
            }
        });

        label.addEventListener("keydown", function(event) {
            if (event.key === "ArrowRight") {
                event.preventDefault();
                const next = timelineItems[index + 1];
                if (next) {
                    next.querySelector(".label").focus();
                }
            } else if (event.key === "ArrowLeft") {
                event.preventDefault();
                const prev = timelineItems[index - 1];
                if (prev) {
                    prev.querySelector(".label").focus();
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

