(function (globalScope) {
    "use strict";

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function parseSrtTimestamp(timestamp) {
        const match = /^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/.exec(timestamp);
        if (!match) {
            return null;
        }
        const hours = Number.parseInt(match[1], 10);
        const minutes = Number.parseInt(match[2], 10);
        const seconds = Number.parseInt(match[3], 10);
        const millis = Number.parseInt(match[4], 10);
        return hours * 3600 + minutes * 60 + seconds + millis / 1000;
    }

    function parseCueFromLine(line) {
        const matches = String(line).match(/\d{2}:\d{2}:\d{2},\d{3}/g);
        if (!matches || matches.length < 2) {
            return null;
        }
        const start = parseSrtTimestamp(matches[0]);
        const end = parseSrtTimestamp(matches[1]);
        if (start === null || end === null || end < start) {
            return null;
        }
        return { start, end, line: String(line) };
    }

    function renderTranscriptLines(lines, currentTime) {
        let activeLineIndex = -1;
        const htmlLines = lines.map(function (line, index) {
            const cue = parseCueFromLine(line);
            if (
                cue &&
                activeLineIndex === -1 &&
                currentTime >= cue.start &&
                currentTime <= cue.end
            ) {
                activeLineIndex = index;
                return '<span class="highlight">' + escapeHtml(line) + "</span>";
            }
            return escapeHtml(line);
        });
        return { html: htmlLines.join("\n"), activeLineIndex };
    }

    function renderCueButtons(lines, currentTime) {
        return lines
            .map(function (line) {
                const cue = parseCueFromLine(line);
                if (!cue) {
                    return "";
                }
                const activeClass =
                    currentTime >= cue.start && currentTime <= cue.end
                        ? " highlight"
                        : "";
                return (
                    '<button type="button" class="transcript-cue' +
                    activeClass +
                    '" data-start="' +
                    cue.start.toFixed(3) +
                    '">' +
                    escapeHtml(line) +
                    "</button>"
                );
            })
            .filter(Boolean)
            .join("");
    }

    function seekAudioToTime(audio, startSeconds, onSeeked) {
        if (!audio || !Number.isFinite(startSeconds) || startSeconds < 0) {
            return false;
        }
        audio.currentTime = startSeconds;
        if (typeof onSeeked === "function") {
            onSeeked(startSeconds);
        }
        return true;
    }

    function handleTranscriptCueClick(event, audio, onSeeked) {
        const target =
            event &&
            event.target &&
            typeof event.target.closest === "function"
                ? event.target.closest(".transcript-cue")
                : null;
        if (!target) {
            return false;
        }
        if (event && typeof event.preventDefault === "function") {
            event.preventDefault();
        }
        const startValue = Number.parseFloat(target.getAttribute("data-start"));
        return seekAudioToTime(audio, startValue, onSeeked);
    }

    function attachTranscriptSeekHandler(container, audio, onSeeked) {
        if (!container || typeof container.addEventListener !== "function") {
            return;
        }
        if (container.dataset && container.dataset.seekHandlerBound === "true") {
            return;
        }
        if (container.dataset) {
            container.dataset.seekHandlerBound = "true";
        }
        container.addEventListener("click", function (event) {
            handleTranscriptCueClick(event, audio, onSeeked);
        });
    }

    function updateTranscriptHighlight(transcript, transcriptDisplay, currentTime) {
        if (!transcript) {
            return;
        }
        const lines = String(transcript.textContent || "").split("\n");
        const transcriptState = renderTranscriptLines(lines, currentTime);
        transcript.innerHTML = transcriptState.html;
        if (transcriptDisplay) {
            transcriptDisplay.innerHTML = renderCueButtons(lines, currentTime);
        }
    }

    function supports3d() {
        if (typeof window === "undefined" || typeof document === "undefined") {
            return false;
        }
        const css3d =
            !!window.CSS && CSS.supports("transform-style", "preserve-3d");
        let webgl = false;
        try {
            const canvas = document.createElement("canvas");
            webgl = !!(
                window.WebGLRenderingContext &&
                (canvas.getContext("webgl") ||
                    canvas.getContext("experimental-webgl"))
            );
        } catch (e) {
            webgl = false;
        }
        return css3d || webgl;
    }

    function initTimeline3DIfSupported() {
        if (typeof window === "undefined" || typeof document === "undefined") {
            return;
        }
        const prefersReducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;
        if (prefersReducedMotion || !supports3d()) {
            return;
        }

        const script = document.createElement("script");
        script.src = "timeline3d.js";
        script.onload = function () {
            if (typeof window.initTimeline3D === "function") {
                window.initTimeline3D();
            }
        };
        document.body.appendChild(script);
    }

    function bootstrapTimeline(doc) {
        if (!doc) {
            return;
        }

        const skipLink = doc.querySelector(".skip-link");
        if (skipLink) {
            skipLink.addEventListener("click", function (event) {
                const mainContent = doc.getElementById("main-content");
                if (mainContent) {
                    event.preventDefault();
                    mainContent.focus();
                }
            });
        }

        const timelineItems = doc.querySelectorAll(".timeline-item");

        timelineItems.forEach(function (item, index) {
            const label = item.querySelector(".label");
            const audioPlayer = item.querySelector(".audio-player");
            if (!label || !audioPlayer) {
                return;
            }

            const audio = audioPlayer.querySelector("audio");
            const source = audio ? audio.querySelector("source") : null;
            const transcript = audioPlayer.querySelector("pre");
            const transcriptDisplay = audioPlayer.querySelector(
                ".highlight-container, .transcript-display"
            );
            if (!audio || !source || !transcript) {
                return;
            }

            const playerId = "player-" + index;
            audioPlayer.id = playerId;
            label.setAttribute("role", "button");
            label.setAttribute("aria-controls", playerId);
            label.setAttribute("aria-expanded", "false");

            const refreshHighlights = function () {
                updateTranscriptHighlight(
                    transcript,
                    transcriptDisplay,
                    Number(audio.currentTime) || 0
                );
            };

            attachTranscriptSeekHandler(transcriptDisplay, audio, refreshHighlights);

            label.addEventListener("click", function (event) {
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
                    refreshHighlights();
                }
            });

            label.addEventListener("keydown", function (event) {
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
                } else if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    label.click();
                }
            });

            audio.addEventListener("timeupdate", refreshHighlights);
        });

        initTimeline3DIfSupported();
    }

    const api = {
        parseSrtTimestamp,
        parseCueFromLine,
        renderTranscriptLines,
        renderCueButtons,
        seekAudioToTime,
        handleTranscriptCueClick,
        attachTranscriptSeekHandler,
        updateTranscriptHighlight,
        bootstrapTimeline,
        supports3d,
        initTimeline3DIfSupported,
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }
    if (globalScope && typeof globalScope === "object") {
        globalScope.TircorderTranscript = api;
    }

    if (typeof document !== "undefined" && document.addEventListener) {
        document.addEventListener("DOMContentLoaded", function () {
            bootstrapTimeline(document);
        });
    }
})(typeof window !== "undefined" ? window : globalThis);
