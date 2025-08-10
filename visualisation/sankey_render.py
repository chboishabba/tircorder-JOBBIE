"""Utilities for rendering Sankey diagrams from accounting flows.

This module relies on Plotly to generate an interactive HTML visualisation.
It expects the ``generate_sankey`` function to supply a list of ``Flow``
objects describing transfers between accounts.  Each account has an associated
``AccountStyle`` that defines its colour and logical depth in the diagram.

Example usage::

    flows = [
        Flow(
            source="Income",
            target="Savings",
            value=1000,
            source_style=AccountStyle(color="#2ca02c", depth=0.0),
            target_style=AccountStyle(color="#1f77b4", depth=0.5),
        ),
    ]
    render_sankey(flows, "out.html")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import plotly.graph_objects as go


@dataclass(frozen=True)
class AccountStyle:
    """Visual properties for an account node."""

    color: str
    depth: float  # Normalised position (0.0-1.0) in the diagram


@dataclass(frozen=True)
class Flow:
    """Represents a transfer between two accounts."""

    source: str
    target: str
    value: float
    source_style: AccountStyle
    target_style: AccountStyle


def render_sankey(flows: Iterable[Flow], output_path: str) -> Path:
    """Render a Sankey diagram to ``output_path``.

    Parameters
    ----------
    flows:
        Iterable of :class:`Flow` objects typically produced by
        ``generate_sankey``.
    output_path:
        Destination file path for the resulting HTML document.

    Returns
    -------
    :class:`~pathlib.Path`
        Path to the generated file.
    """

    flows = list(flows)
    if not flows:
        raise ValueError("No flows provided for rendering")

    labels: List[str] = []
    styles = {}
    for flow in flows:
        for name, style in (
            (flow.source, flow.source_style),
            (flow.target, flow.target_style),
        ):
            if name not in styles:
                styles[name] = style
                labels.append(name)

    label_to_idx = {label: i for i, label in enumerate(labels)}

    node_colors = [styles[label].color for label in labels]
    node_x = [styles[label].depth for label in labels]

    link_source = [label_to_idx[flow.source] for flow in flows]
    link_target = [label_to_idx[flow.target] for flow in flows]
    link_value = [flow.value for flow in flows]
    link_colors = [styles[flow.source].color for flow in flows]

    sankey = go.Sankey(
        node=dict(label=labels, color=node_colors, x=node_x, pad=15, thickness=20),
        link=dict(source=link_source, target=link_target, value=link_value, color=link_colors),
        arrangement="fixed",
    )
    fig = go.Figure(data=[sankey])

    # Generate a responsive HTML snippet suitable for embedding in web pages
    html = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True})
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return path
