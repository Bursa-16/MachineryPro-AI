"""UI-MEDIA-0A — Machining visual system tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frontend.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def landing(client: TestClient) -> str:
    return client.get("/").text


@pytest.fixture()
def css(client: TestClient) -> str:
    return client.get("/static/design-system.css").text


@pytest.fixture()
def js(client: TestClient) -> str:
    return client.get("/static/js/machining-visuals.js").text


# -- Visual sections exist -------------------------------------------------

class TestVisualSections:
    def test_hero_visual_container(self, landing: str) -> None:
        assert "mp-hero-visual" in landing

    def test_process_selector_exists(self, landing: str) -> None:
        assert "mp-process-selector" in landing

    def test_milling_tab(self, landing: str) -> None:
        assert 'data-process="milling"' in landing

    def test_turning_tab(self, landing: str) -> None:
        assert 'data-process="turning"' in landing

    def test_drilling_tab(self, landing: str) -> None:
        assert 'data-process="drilling"' in landing

    def test_validation_tab(self, landing: str) -> None:
        assert 'data-process="validation"' in landing


# -- JS contains visual builders -------------------------------------------

class TestVisualBuilders:
    def test_milling_visual(self, js: str) -> None:
        assert "buildMillingVisual" in js

    def test_turning_visual(self, js: str) -> None:
        assert "buildTurningVisual" in js

    def test_drilling_visual(self, js: str) -> None:
        assert "buildDrillingVisual" in js

    def test_validation_visual(self, js: str) -> None:
        assert "buildValidationVisual" in js

    def test_hero_visual(self, js: str) -> None:
        assert "buildHeroVisual" in js


# -- No paid/external asset URLs -------------------------------------------

class TestAssetPolicy:
    def test_no_stock_image_urls(self, landing: str) -> None:
        forbidden = ["shutterstock", "gettyimages", "istockphoto", "stock.adobe",
                      "dreamstime", "depositphotos", "123rf"]
        for domain in forbidden:
            assert domain not in landing.lower()

    def test_no_google_images(self, landing: str) -> None:
        assert "images.google" not in landing.lower()

    def test_no_youtube_embeds(self, landing: str) -> None:
        assert "youtube.com/embed" not in landing.lower()

    def test_no_unverified_img_src(self, landing: str) -> None:
        # Only /static/ or data: URIs are acceptable
        import re
        srcs = re.findall(r'src=["\']([^"\']+)["\']', landing)
        for s in srcs:
            if s.startswith("/static/") or s.startswith("data:"):
                continue
            allowed_cdns = ("cdn.tailwindcss", "unpkg.com", "fonts.googleapis", "fonts.gstatic")
            if any(cdn in s for cdn in allowed_cdns):
                continue
            pytest.fail(f"Unverified external src: {s}")

    def test_js_has_no_external_urls(self, js: str) -> None:
        # SVG namespace (http://www.w3.org/2000/svg) is required, not an external asset
        filtered = js.replace("http://www.w3.org/2000/svg", "")
        assert "http://" not in filtered
        assert "https://" not in filtered


# -- Reduced motion --------------------------------------------------------

class TestReducedMotion:
    def test_css_reduced_motion(self, css: str) -> None:
        assert "prefers-reduced-motion" in css

    def test_js_reduced_motion(self, js: str) -> None:
        assert "prefers-reduced-motion" in js


# -- Interaction states ----------------------------------------------------

class TestInteractionStates:
    def test_btn_active_state(self, css: str) -> None:
        assert ".mp-btn:active" in css

    def test_btn_disabled_state(self, css: str) -> None:
        assert ".mp-btn:disabled" in css or ".mp-btn[disabled]" in css

    def test_process_tab_active_class(self, css: str) -> None:
        assert ".mp-process-tab--active" in css

    def test_process_tab_focus(self, css: str) -> None:
        assert ".mp-process-tab:focus-visible" in css


# -- No regression ---------------------------------------------------------

class TestNoRegression:
    def test_landing_loads(self, client: TestClient) -> None:
        assert client.get("/").status_code == 200

    def test_workspace_loads(self, client: TestClient) -> None:
        assert client.get("/ui/").status_code == 200

    def test_cad_import_loads(self, client: TestClient) -> None:
        assert client.get("/ui/cad-import").status_code == 200

    def test_health_ok(self, client: TestClient) -> None:
        assert client.get("/health").json()["status"] == "ok"

    def test_app_title(self) -> None:
        assert app.title == "MachineryPro AI"
