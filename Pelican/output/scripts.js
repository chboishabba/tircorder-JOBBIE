document.addEventListener("DOMContentLoaded", function() {
    const timelineItems = document.querySelectorAll(".timeline-item");

    timelineItems.forEach(item => {
        const audio = item.querySelector("audio");
        const transcript = item.querySelector("pre");

        audio.addEventListener("timeupdate", function() {
            const currentTime = audio.currentTime;
            const lines = transcript.textContent.split('\n');
            let highlighted = false;

            transcript.innerHTML = lines.map(line => {
                const timeMatch = line.match(/\[(\d{2}:\d{2}:\d{2})\]/);
                if (timeMatch) {
                    const timeParts = timeMatch[1].split(':');
                    const timeInSeconds = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
                    if (currentTime >= timeInSeconds && !highlighted) {
                        highlighted = true;
                        return `<span class="highlight">${line}</span>`;
                    }
                }
                return line;
            }).join('\n');
        });
    });
});

