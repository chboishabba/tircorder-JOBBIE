def generate_html_header():
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
        <a href="#main-content" class="skip-link">Skip to main content</a>
        <header>
            <h1>Audio Recordings Timeline</h1>
        </header>
        <main id="main-content" role="main">
            <section id="timeline">
                <h2>Timeline</h2>
                <div class="timeline-container">
    """

