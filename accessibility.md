# Accessibility

We are committed to building interfaces that everyone can use. Our minimum commitments include:

- Follow the [Web Content Accessibility Guidelines](https://www.w3.org/WAI/standards-guidelines/wcag/) 2.1 at the AA level.
- Provide text alternatives for non-text content, including transcripts for audio.
- Maintain keyboard navigability and logical focus order.
- Preserve sufficient color contrast and responsive layouts.
- Continue testing with assistive technologies and incorporate user feedback.

## Current status

The generated timeline page uses semantic HTML elements such as `<header>`, `<main>`, `<section>` and `<audio>`, and exposes text transcripts for audio clips. However, it currently lacks ARIA attributes, skip-navigation links, and other patterns that help screen‑reader users understand interactive elements. Keyboard focus indicators and announcements for dynamically displayed content also need improvement.

## Implemented accessibility features

- Semantic landmarks (`<header>`, `<main>`, `<section>`) structure content.
- Audio clips include `<audio>` players paired with text transcripts.
- Layouts respond to different screen sizes while preserving color contrast.

## Accessibility TODO

- Add ARIA roles and labels to interactive controls.
- Introduce skip-navigation links for keyboard users.
- Provide visible focus styles and announce dynamic updates with `aria-live`.
- Automate audits with tools like axe-core and Lighthouse.
- Expand manual testing with screen readers and alternate input devices.

## Accessibility on the Web in 2025

Despite progress, accessibility remains a major challenge on the wider web. The
[2025 WebAIM Million report](https://webaim.org/projects/million/) continues to
find that **over 90% of popular sites fail basic WCAG tests**. This reinforces
the importance of treating accessibility as a first-class requirement.

We will update this document as our work evolves.
