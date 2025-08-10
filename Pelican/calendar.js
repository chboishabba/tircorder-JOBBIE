// Basic calendar colouring utility
// intensities should be a mapping of ISO date strings to numbers 0..1
// Example usage:
//   applyCalendarColors(document.getElementById('calendar'), {'2024-05-06': 1, ...});

function applyCalendarColors(container, intensities, baseColor = '0,0,128') {
    Object.entries(intensities).forEach(([day, intensity]) => {
        const cell = container.querySelector(`[data-day="${day}"]`);
        if (!cell) return;
        if (intensity === 0) {
            cell.style.backgroundColor = 'white';
        } else {
            cell.style.backgroundColor = `rgba(${baseColor}, ${intensity})`;
        }
    });
}

// Render a single day's timeline as a vertical bar where each segment
// represents a minute or second. `segments` can be either an array of counts
// (for frequency mode) or a mapping of app name to arrays of counts (for app
// mode). Pass `pxPerStep` to explicitly control pixel height of each step (e.g.
// `1` for 1px per minute/second).
function renderDayTimeline(
    container,
    segments,
    { colorBy = 'frequency', colorMap = {}, baseColor = '0,0,128', pxPerStep = null } = {}
) {
    const stepCount = Array.isArray(segments)
        ? segments.length
        : (segments[Object.keys(segments)[0]] || []).length;
    if (!stepCount) return;

    const height = pxPerStep ? stepCount * pxPerStep : container.clientHeight;
    const pixelsPerStep = height / stepCount;
    container.innerHTML = '';
    container.style.position = 'relative';
    container.style.height = height + 'px';

    if (colorBy === 'app') {
        Object.entries(segments).forEach(([app, arr]) => {
            arr.forEach((val, idx) => {
                if (!val) return;
                const div = document.createElement('div');
                div.style.position = 'absolute';
                div.style.top = (idx * pixelsPerStep) + 'px';
                div.style.height = pixelsPerStep + 'px';
                div.style.width = '100%';
                div.style.backgroundColor = colorMap[app] || 'navy';
                container.appendChild(div);
            });
        });
    } else {
        const maxVal = Math.max(...segments) || 1;
        segments.forEach((val, idx) => {
            if (!val) return;
            const div = document.createElement('div');
            div.style.position = 'absolute';
            div.style.top = (idx * pixelsPerStep) + 'px';
            div.style.height = pixelsPerStep + 'px';
            div.style.width = '100%';
            div.style.backgroundColor = `rgba(${baseColor}, ${val / maxVal})`;
            container.appendChild(div);
        });
    }
}

// expose globally
window.applyCalendarColors = applyCalendarColors;
window.renderDayTimeline = renderDayTimeline;
