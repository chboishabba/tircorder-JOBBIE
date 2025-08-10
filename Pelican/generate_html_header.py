def generate_html_header():
    """Return the opening HTML for the timeline with accessibility features."""

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Audio Recordings Timeline</title>
        <link rel="stylesheet" href="styles.css">
        <script src="scripts.js" defer></script>
    </head>
    <body>
        <a class="skip-link" href="#main-content">Skip to main content</a>
        <header>
            <h1>Audio Recordings Timeline</h1>
        </header>
        <main id="main-content" tabindex="-1">
            <section id="timeline">
                <h2>Timeline</h2>
                <p id="timeline-instructions" class="sr-only">
                    Use left and right arrow keys to navigate between timeline items.
                    Press Enter to toggle audio details.
                </p>
                <div class="timeline-container" role="list" aria-describedby="timeline-instructions">
    """
