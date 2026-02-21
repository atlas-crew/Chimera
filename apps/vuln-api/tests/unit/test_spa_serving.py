"""
Tests for SPA (Single Page Application) serving from web_dist/.

Covers two modes:
1. API-only mode  — web_dist/index.html absent → demo template on /
2. SPA mode       — web_dist/index.html present → React app on /, catch-all routing
"""

import os
import shutil
import textwrap

import pytest

from app import create_app


WEB_DIST_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'web_dist')


@pytest.fixture
def spa_files(tmp_path):
    """Populate web_dist/ with a fake SPA for testing, clean up after."""
    index_html = os.path.join(WEB_DIST_DIR, 'index.html')
    assets_dir = os.path.join(WEB_DIST_DIR, 'assets')

    os.makedirs(assets_dir, exist_ok=True)

    with open(index_html, 'w') as f:
        f.write('<html><body>SPA Root</body></html>')

    js_file = os.path.join(assets_dir, 'main.js')
    with open(js_file, 'w') as f:
        f.write('console.log("spa");')

    css_file = os.path.join(assets_dir, 'style.css')
    with open(css_file, 'w') as f:
        f.write('body { margin: 0; }')

    yield {
        'index': index_html,
        'js': js_file,
        'css': css_file,
        'assets_dir': assets_dir,
    }

    # Cleanup: remove generated files but preserve .gitkeep
    for path in [js_file, css_file, index_html]:
        if os.path.exists(path):
            os.remove(path)
    if os.path.isdir(assets_dir):
        shutil.rmtree(assets_dir)


# ============================================================================
# API-only mode (default — no web_dist/index.html)
# ============================================================================

class TestApiOnlyMode:
    """When web_dist/index.html is absent, Flask serves the demo template."""

    def test_root_returns_demo_template(self, client):
        """/ should return the demo page template, not a 404."""
        resp = client.get('/')
        assert resp.status_code == 200
        # Demo template contains HTML (not JSON)
        assert b'<!DOCTYPE html>' in resp.data or b'<html' in resp.data

    def test_healthz_works(self, client):
        """/healthz should always work regardless of SPA mode."""
        resp = client.get('/healthz')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'

    def test_unknown_spa_path_returns_404(self, client):
        """Non-API paths like /healthcare should 404 in API-only mode."""
        resp = client.get('/banking')
        assert resp.status_code == 404


# ============================================================================
# SPA mode (web_dist/index.html present)
# ============================================================================

class TestSpaMode:
    """When web_dist/index.html exists, Flask serves the SPA with catch-all."""

    @pytest.fixture(autouse=True)
    def spa_app(self, spa_files):
        """Create a fresh app with SPA files in place."""
        self._app = create_app()
        self._app.config['TESTING'] = True
        self._client = self._app.test_client()

    @property
    def client(self):
        return self._client

    def test_root_serves_spa_index(self):
        """/ should serve the SPA index.html."""
        resp = self.client.get('/')
        assert resp.status_code == 200
        assert b'SPA Root' in resp.data

    def test_static_asset_served(self):
        """/assets/main.js should serve the actual JS file."""
        resp = self.client.get('/assets/main.js')
        assert resp.status_code == 200
        assert b'console.log' in resp.data

    def test_css_asset_served(self):
        """/assets/style.css should serve the actual CSS file."""
        resp = self.client.get('/assets/style.css')
        assert resp.status_code == 200
        assert b'margin' in resp.data

    def test_client_route_returns_index(self):
        """Client-side routes like /banking should return index.html."""
        resp = self.client.get('/banking')
        assert resp.status_code == 200
        assert b'SPA Root' in resp.data

    def test_deep_client_route_returns_index(self):
        """Deep routes like /healthcare/patients should return index.html."""
        resp = self.client.get('/healthcare/patients')
        assert resp.status_code == 200
        assert b'SPA Root' in resp.data

    def test_api_route_returns_json_404(self):
        """API routes should return JSON 404, not index.html."""
        resp = self.client.get('/api/v1/nonexistent')
        assert resp.status_code == 404
        data = resp.get_json()
        assert 'error' in data

    def test_healthz_still_works(self):
        """/healthz should still work in SPA mode."""
        resp = self.client.get('/healthz')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'

    def test_spa_csp_allows_inline_styles(self):
        """SPA responses should have relaxed CSP for Tailwind."""
        resp = self.client.get('/')
        csp = resp.headers.get('Content-Security-Policy', '')
        assert "'unsafe-inline'" in csp

    def test_api_csp_strict(self):
        """API responses should keep strict CSP (no unsafe-inline in style-src)."""
        resp = self.client.get('/api/v1/auth/login', method='GET')
        csp = resp.headers.get('Content-Security-Policy', '')
        # style-src portion should NOT have unsafe-inline
        if 'style-src' in csp:
            style_part = csp.split('style-src')[1].split(';')[0]
            assert 'unsafe-inline' not in style_part
