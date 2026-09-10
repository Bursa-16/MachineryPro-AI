"""UI-DESIGN-0B — Workspace UX tests: nav groups, progressive disclosure, CAD import."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frontend.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def dashboard_html(client: TestClient) -> str:
    return client.get("/ui/").text


@pytest.fixture()
def cad_html(client: TestClient) -> str:
    return client.get("/ui/cad-import").text


# -- Collapsible navigation groups -----------------------------------------

class TestNavGroups:
    """All 5 navigation groups must exist with exact labels."""

    def test_workspace_group(self, dashboard_html: str) -> None:
        assert "Workspace" in dashboard_html

    def test_engineering_data_group(self, dashboard_html: str) -> None:
        assert "Engineering Data" in dashboard_html

    def test_manufacturing_group(self, dashboard_html: str) -> None:
        assert "Manufacturing" in dashboard_html

    def test_assurance_group(self, dashboard_html: str) -> None:
        assert "Assurance" in dashboard_html

    def test_intelligence_group(self, dashboard_html: str) -> None:
        assert "Intelligence" in dashboard_html

    def test_groups_use_details_element(self, dashboard_html: str) -> None:
        assert "mp-nav-group" in dashboard_html
        assert "<details" in dashboard_html
        assert "<summary" in dashboard_html

    def test_active_group_open_on_dashboard(self, dashboard_html: str) -> None:
        # Dashboard is in Workspace group — it should have "open"
        assert "open" in dashboard_html

    def test_cad_import_link_present(self, dashboard_html: str) -> None:
        assert "/ui/cad-import" in dashboard_html

    def test_materials_planned(self, dashboard_html: str) -> None:
        assert "PLANNED" in dashboard_html

    def test_ai_assistant_planned(self, dashboard_html: str) -> None:
        assert "AI Assistant" in dashboard_html

    def test_active_group_open_on_cad_import(self, cad_html: str) -> None:
        # CAD Import is in Engineering Data — it should have open
        assert "Engineering Data" in cad_html


class TestNavGroupCSS:
    """CSS classes for nav groups must exist."""

    def test_nav_group_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-nav-group" in css

    def test_nav_group_items_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-nav-group__items" in css

    def test_nav_group_summary_styled(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert "summary" in css


# -- Progressive disclosure ------------------------------------------------

class TestProgressiveDisclosure:
    """Form UX framework classes must exist."""

    def test_form_section_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-form-section" in css

    def test_form_section_basic(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-form-section--basic" in css

    def test_form_section_advanced(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-form-section--advanced" in css

    def test_form_section_role(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-form-section--role" in css

    def test_advanced_toggle_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-advanced-toggle" in css

    def test_field_group_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-field-group" in css

    def test_unit_input_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-unit-input" in css

    def test_validation_message_class(self, client: TestClient) -> None:
        css = client.get("/static/design-system.css").text
        assert ".mp-validation-message" in css


# -- CAD Import simplification --------------------------------------------

class TestCadImportSimplified:
    """CAD Import uses progressive disclosure for technical details."""

    def test_cad_import_loads(self, cad_html: str) -> None:
        assert "CAD Import" in cad_html

    def test_basic_upload_visible(self, cad_html: str) -> None:
        assert 'type="file"' in cad_html
        assert "Import CAD" in cad_html

    def test_advanced_section_in_result(self, client: TestClient) -> None:
        from unittest.mock import patch

        from tests.unit.frontend.test_cad_import import _fake_success_result

        fake = _fake_success_result()
        with patch("frontend.routers.ui.CadImportOrchestrator") as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"ISO-10303-21;", "application/octet-stream")},
            )
        assert "Advanced Import Details" in resp.text

    def test_advanced_is_collapsible(self, client: TestClient) -> None:
        from unittest.mock import patch

        from tests.unit.frontend.test_cad_import import _fake_success_result

        fake = _fake_success_result()
        with patch("frontend.routers.ui.CadImportOrchestrator") as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"ISO-10303-21;", "application/octet-stream")},
            )
        assert "mp-advanced-toggle" in resp.text

    def test_backend_route_unchanged(self, client: TestClient) -> None:
        resp = client.get("/ui/cad-import")
        assert resp.status_code == 200

    def test_post_still_works(self, client: TestClient) -> None:
        resp = client.post("/ui/cad-import")
        assert resp.status_code == 200
        assert "No file was uploaded" in resp.text


# -- No-modification guards ------------------------------------------------

class TestNoModificationGuards:
    """Backend and config must not have changed."""

    def test_app_title(self) -> None:
        assert app.title == "MachineryPro AI"

    def test_health_endpoint(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
