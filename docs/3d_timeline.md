# 3D Timeline Axis Priorities

The 3D timeline models how interactions move across platforms and contacts over time. The axes are ordered by importance:

- **X – Platform**: The horizontal axis distinguishes the medium or platform used (e.g., phone, email, social media). Grouping by platform helps analyze cross-channel behavior.
- **Y – Time**: The vertical axis tracks chronological sequence so trends and gaps become clear.
- **Z – Contact**: The depth axis separates individual contacts, allowing focused review of each relationship.

## Rationale

Prioritizing platforms on the X-axis keeps similar media aligned, while a vertical time axis communicates progression at a glance. Using depth for contacts allows simultaneous comparison of different relationships without losing temporal context.

## Style Conventions for Axis Emphasis

- Refer to axes in uppercase followed by a colon, e.g., `X:`.
- Bold axis letters when mentioned in prose (e.g., **X**, **Y**, **Z**).
- Color suggestions: X = blue, Y = green, Z = red. Ensure colors meet high-contrast guidelines for accessibility.

## Accessibility

- Provide text descriptions and alt text for any 3D visualizations.
- Offer keyboard navigation and logical reading order for assistive technologies.
- Choose color palettes with sufficient contrast and avoid relying solely on color to convey meaning.

## Fallback for Non‑3D Environments

- Supply a 2D view using **X** for platform and **Y** for time, encoding contacts through color, icons, or grouping.
- When graphics are unavailable, present a chronological table grouped by contact.
- Implement graceful degradation so environments lacking WebGL or 3D support default to the 2D or textual representations automatically.

