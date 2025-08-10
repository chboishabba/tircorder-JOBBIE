from visualisation.sankey_render import AccountStyle, Flow, render_sankey


def test_render_sankey_creates_html(tmp_path):
    flows = [
        Flow(
            source="Income",
            target="Savings",
            value=1000,
            source_style=AccountStyle(color="#2ca02c", depth=0.0),
            target_style=AccountStyle(color="#1f77b4", depth=0.5),
        ),
        Flow(
            source="Savings",
            target="Expenses",
            value=500,
            source_style=AccountStyle(color="#1f77b4", depth=0.5),
            target_style=AccountStyle(color="#d62728", depth=1.0),
        ),
    ]
    output_file = tmp_path / "sankey.html"
    render_sankey(flows, str(output_file))
    assert output_file.exists()
    # Basic sanity check on output contents
    text = output_file.read_text()
    # The file should contain an embeddable Plotly div rather than a full HTML page
    assert "<div" in text.lower()
