# Accessibility

We are committed to building interfaces that everyone can use. Our minimum commitments include:

- Follow the [Web Content Accessibility Guidelines](https://www.w3.org/WAI/standards-guidelines/wcag/) 2.1 at the AA level.
- Provide text alternatives for non-text content, including transcripts for audio.
- Maintain keyboard navigability and logical focus order.
- Preserve sufficient color contrast and responsive layouts.
- Continue testing with assistive technologies and incorporate user feedback.

## Current status

The generated timeline page uses semantic HTML elements such as `<header>`, `<main>`, `<section>` and `<audio>`, and exposes text transcripts for audio clips. A skip-navigation link and respect for reduced-motion preferences improve keyboard and screen‑reader navigation. Timeline items now behave as an ARIA list with left and right arrow key support, though additional announcements for dynamically displayed content are still needed.

## Implemented accessibility features

- Semantic landmarks (`<header>`, `<main>`, `<section>`) structure content.
- Skip-navigation link allows keyboard users to bypass repetitive header content and moves focus to the main region for screen-reader clarity.
- 3D timeline effects are disabled when the user prefers reduced motion.
- Audio clips include `<audio>` players paired with text transcripts.
- Timeline items form an ARIA list and support left/right arrow-key navigation.
- Labels expose expanded/collapsed state and receive visible focus outlines.
- Layouts respond to different screen sizes while preserving color contrast.

## Accessibility TODO

- Extend ARIA roles and labels to remaining interactive controls.
- Provide visible focus styles and announce dynamic updates with `aria-live`.
- Automate audits with tools like axe-core and Lighthouse.
- Expand manual testing with screen readers and alternate input devices.

## Accessibility on the Web in 2025

Despite progress, accessibility remains a major challenge on the wider web. The
[2025 WebAIM Million report](https://webaim.org/projects/million/) continues to
find that **over 90% of popular sites fail basic WCAG tests**. This reinforces
the importance of treating accessibility as a first-class requirement.

We will update this document as our work evolves.
