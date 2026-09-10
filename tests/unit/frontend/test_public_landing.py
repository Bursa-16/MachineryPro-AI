"""PUBLIC-0A — Public landing page tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frontend.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


@pytest.fixture()
def landing(client: TestClient) -> str:
    return client.get("/").text


# -- Route behavior --------------------------------------------------------

class TestRoutes:
    def test_root_returns_200(self, client: TestClient) -> None:
        assert client.get("/").status_code == 200

    def test_root_is_landing(self, landing: str) -> None:
        assert "Manufacturing engineering intelligence" in landing.lower() or \
               "manufacturing engineering" in landing.lower()

    def test_workspace_still_works(self, client: TestClient) -> None:
        resp = client.get("/ui/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_app_redirects_to_workspace(self, client: TestClient) -> None:
        resp = client.get("/app")
        assert resp.status_code == 302
        assert resp.headers["location"] == "/ui/"

    def test_cad_import_still_works(self, client: TestClient) -> None:
        assert client.get("/ui/cad-import").status_code == 200


# -- Landing content -------------------------------------------------------

class TestLandingContent:
    def test_machineryproai_title(self, landing: str) -> None:
        assert "MachineryPro AI" in landing

    def test_start_cta(self, landing: str) -> None:
        assert "Start MachineryPro AI" in landing

    def test_request_demo_cta(self, landing: str) -> None:
        assert "Request Demo" in landing

    def test_workflow_section(self, landing: str) -> None:
        assert "how-it-works" in landing

    def test_step_format(self, landing: str) -> None:
        assert "STEP" in landing or "STP" in landing

    def test_iges_format(self, landing: str) -> None:
        assert "IGES" in landing or "IGS" in landing

    def test_dxf_format(self, landing: str) -> None:
        assert "DXF" in landing

    def test_deterministic_vs_ai_section(self, landing: str) -> None:
        assert "mp-card--calc" in landing
        assert "mp-card--ai" in landing

    def test_ai_clearly_labelled(self, landing: str) -> None:
        assert "AI Assisted" in landing or "AI Advisory" in landing


# -- Pricing ---------------------------------------------------------------

class TestPricing:
    def test_starter_tier(self, landing: str) -> None:
        assert "Starter" in landing

    def test_professional_tier(self, landing: str) -> None:
        assert "Professional" in landing

    def test_enterprise_tier(self, landing: str) -> None:
        assert "Enterprise" in landing

    def test_pricing_tbd(self, landing: str) -> None:
        assert "TBD" in landing


# -- No fabricated content -------------------------------------------------

class TestNoFabrication:
    def test_no_fake_testimonials(self, landing: str) -> None:
        for word in ["testimonial", "customer said", "client quote"]:
            assert word.lower() not in landing.lower()

    def test_no_fake_logos(self, landing: str) -> None:
        assert "customer-logo" not in landing.lower()


# -- FAQ -------------------------------------------------------------------

class TestFAQ:
    def test_faq_section_exists(self, landing: str) -> None:
        assert "Frequently Asked Questions" in landing

    def test_faq_cad_formats(self, landing: str) -> None:
        assert "STEP" in landing
        assert "IGES" in landing
        assert "DXF" in landing

    def test_faq_no_native_cad_claimed(self, landing: str) -> None:
        assert "CATIA" not in landing or "not currently supported" in landing


# -- SEO -------------------------------------------------------------------

class TestSEO:
    def test_title_tag(self, landing: str) -> None:
        assert "<title>" in landing
        assert "MachineryPro AI" in landing

    def test_meta_description(self, landing: str) -> None:
        assert 'name="description"' in landing

    def test_og_title(self, landing: str) -> None:
        assert 'og:title' in landing
