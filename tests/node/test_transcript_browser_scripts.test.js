const test = require("node:test");
const assert = require("node:assert/strict");

const transcriptUi = require("../../Pelican/scripts.js");

test("parseSrtTimestamp parses valid SRT timestamps", () => {
    assert.equal(transcriptUi.parseSrtTimestamp("00:00:05,500"), 5.5);
    assert.equal(transcriptUi.parseSrtTimestamp("01:02:03,004"), 3723.004);
    assert.equal(transcriptUi.parseSrtTimestamp("not-a-timestamp"), null);
});

test("renderTranscriptLines highlights exactly one active cue", () => {
    const lines = [
        "00:00:00,000 --> 00:00:01,000 first",
        "00:00:01,001 --> 00:00:02,000 second",
        "plain text",
    ];

    const state = transcriptUi.renderTranscriptLines(lines, 1.5);
    assert.equal(state.activeLineIndex, 1);
    assert.equal((state.html.match(/class="highlight"/g) || []).length, 1);
    assert.match(state.html, /second/);
});

test("renderCueButtons emits seek targets and active cue class", () => {
    const lines = [
        "00:00:00,000 --> 00:00:01,000 first",
        "00:00:01,250 --> 00:00:02,000 second",
        "not a cue",
    ];

    const html = transcriptUi.renderCueButtons(lines, 1.3);
    assert.match(html, /class="transcript-cue highlight"/);
    assert.match(html, /data-start="1.250"/);
    assert.equal((html.match(/class="transcript-cue/g) || []).length, 2);
});

test("seekAudioToTime sets currentTime for valid cue starts", () => {
    const audio = { currentTime: 0 };
    const changed = transcriptUi.seekAudioToTime(audio, 4.25);
    assert.equal(changed, true);
    assert.equal(audio.currentTime, 4.25);
    assert.equal(transcriptUi.seekAudioToTime(audio, Number.NaN), false);
    assert.equal(audio.currentTime, 4.25);
});

test("handleTranscriptCueClick seeks audio from clicked cue", () => {
    let prevented = false;
    const audio = { currentTime: 0 };
    const cueButton = {
        getAttribute(name) {
            return name === "data-start" ? "2.750" : null;
        },
    };
    const event = {
        preventDefault() {
            prevented = true;
        },
        target: {
            closest(selector) {
                assert.equal(selector, ".transcript-cue");
                return cueButton;
            },
        },
    };

    const changed = transcriptUi.handleTranscriptCueClick(event, audio);
    assert.equal(changed, true);
    assert.equal(prevented, true);
    assert.equal(audio.currentTime, 2.75);
});

test("updateTranscriptHighlight updates cue list for transcript containers", () => {
    const transcript = {
        textContent: "00:00:00,000 --> 00:00:01,000 first\n00:00:01,000 --> 00:00:02,000 second",
        innerHTML: "",
    };
    const transcriptDisplay = { innerHTML: "" };

    transcriptUi.updateTranscriptHighlight(transcript, transcriptDisplay, 0.4);
    assert.match(transcript.innerHTML, /class="highlight"/);
    assert.match(transcriptDisplay.innerHTML, /class="transcript-cue highlight"/);
    assert.match(transcriptDisplay.innerHTML, /data-start="0.000"/);
});
