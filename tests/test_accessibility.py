from Pelican.generate_html_header import generate_html_header


def test_skip_link_and_main_role_present():
    html = generate_html_header()
    assert 'class="skip-link"' in html
    assert 'id="main-content"' in html
    assert 'role="main"' in html
