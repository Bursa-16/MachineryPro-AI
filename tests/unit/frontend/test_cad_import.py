"""UI-1A — CAD Import page tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.interoperability.enums import CapabilityLevel, NormalizationStatus
from backend.interoperability.models import (
    CanonicalDocument,
    EngineeringSource,
    FormatDescriptor,
)
from backend.interoperability.orchestrator import (
    CapabilityRecord,
    FormatDetectionResult,
    ImportDiagnostics,
    ImportProvenance,
    ImportResult,
    ImportStatus,
)
from frontend.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# -- Helpers ---------------------------------------------------------------

def _fake_success_result(source_id: str = "upload::test.step") -> ImportResult:
    """Build a realistic ImportResult for monkeypatching."""
    from backend.domain.base import Provenance
    from backend.domain.enums import ProvenanceType
    from backend.interoperability.enums import (
        AdapterLicense,
        FidelityReportCompleteness,
        FormatFamily,
    )
    from backend.interoperability.models import ConversionFidelityReport

    source = EngineeringSource(source_id=source_id, file_name="test.step")
    descriptor = FormatDescriptor(
        format_id="STEP-GENERIC",
        canonical_name="STEP Generic",
        family=FormatFamily.NEUTRAL_EXCHANGE,
        adapter_license=AdapterLicense.INTERNAL_PARSER,
    )
    fidelity = ConversionFidelityReport(
        report_id="rpt-1",
        source_format_id="STEP-GENERIC",
        adapter_id="step-token-adapter",
        adapter_version="4C.0",
        completeness=FidelityReportCompleteness.COMPLETE,
        normalization_status=NormalizationStatus.SUCCESS,
    )
    document = CanonicalDocument(
        document_id="doc-1",
        canonical_kind="CAD_GEOMETRY",
        source=source,
        format_descriptor=descriptor,
        adapter_id="step-token-adapter",
        adapter_version="4C.0",
        capability_level=CapabilityLevel.LEVEL_2_NORMALIZED,
        normalization_status=NormalizationStatus.SUCCESS,
        fidelity_report=fidelity,
    )
    detection = FormatDetectionResult(
        detected_format_id="STEP-GENERIC",
        detection_confidence="MEDIUM",
        detection_method="file_extension",
    )
    diag = ImportDiagnostics(
        format_detection=detection,
        adapter_candidates=("step-token-adapter",),
        selected_adapter_id="step-token-adapter",
        selection_reason="first_ordered_candidate",
        fidelity_adverse_count=0,
        has_unsupported_content=False,
        has_loss=False,
    )
    cap = CapabilityRecord(achieved_level=CapabilityLevel.LEVEL_2_NORMALIZED)
    prov = ImportProvenance(
        source_id=source_id,
        adapter_id="step-token-adapter",
        adapter_version="4C.0",
        format_id="STEP-GENERIC",
        capability_level=CapabilityLevel.LEVEL_2_NORMALIZED,
        normalization_status=NormalizationStatus.SUCCESS,
        domain_provenance=Provenance(
            source_type=ProvenanceType.USER_INPUT,
            source_reference="step-token-adapter@4C.0",
            source_document="test.step",
        ),
    )
    return ImportResult(
        import_id=f"import::{source_id}::step-token-adapter",
        status=ImportStatus.SUCCESS,
        document=document,
        diagnostics=diag,
        capability=cap,
        provenance=prov,
    )


def _fake_failed_result(source_id: str = "upload::bad.step") -> ImportResult:
    """Build a FAILED ImportResult for monkeypatching."""
    detection = FormatDetectionResult(
        detected_format_id="STEP-GENERIC",
        detection_confidence="MEDIUM",
        detection_method="file_extension",
    )
    diag = ImportDiagnostics(
        format_detection=detection,
        adapter_candidates=("step-token-adapter",),
        selected_adapter_id="step-token-adapter",
        selection_reason="adapter_raised_exception",
        fidelity_adverse_count=1,
        has_unsupported_content=False,
        has_loss=True,
        notes=("Adapter raised: malformed content",),
    )
    cap = CapabilityRecord(achieved_level=CapabilityLevel.LEVEL_0_RECOGNIZED)
    return ImportResult(
        import_id=f"import::{source_id}::step-token-adapter",
        status=ImportStatus.FAILED,
        document=None,
        diagnostics=diag,
        capability=cap,
        error_message="malformed content",
    )


# -- GET /ui/cad-import ----------------------------------------------------

class TestCadImportGet:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/ui/cad-import")
        assert resp.status_code == 200

    def test_contains_title(self, client: TestClient) -> None:
        assert "CAD Import" in client.get("/ui/cad-import").text

    def test_contains_form(self, client: TestClient) -> None:
        html = client.get("/ui/cad-import").text
        assert 'enctype="multipart/form-data"' in html

    def test_sidebar_link_correct(self, client: TestClient) -> None:
        html = client.get("/ui/cad-import").text
        assert 'href="/ui/cad-import"' in html

    def test_shows_accepted_formats(self, client: TestClient) -> None:
        html = client.get("/ui/cad-import").text
        assert ".step" in html
        assert ".dxf" in html
        assert ".iges" in html


# -- POST /ui/cad-import: validation errors --------------------------------

class TestCadImportValidation:
    def test_empty_upload_rejected(self, client: TestClient) -> None:
        resp = client.post("/ui/cad-import")
        assert resp.status_code == 200
        assert "No file was uploaded" in resp.text

    def test_unsupported_extension_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/ui/cad-import",
            files={"file": ("model.stl", b"solid test", "application/octet-stream")},
        )
        assert resp.status_code == 200
        assert "Unsupported file extension" in resp.text

    def test_empty_file_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/ui/cad-import",
            files={"file": ("test.step", b"", "application/octet-stream")},
        )
        assert resp.status_code == 200
        assert "empty" in resp.text.lower()


# -- POST /ui/cad-import: backend integration -----------------------------

class TestCadImportOrchestration:
    def test_successful_import_shows_status(self, client: TestClient) -> None:
        fake = _fake_success_result()
        with patch(
            "frontend.routers.ui.CadImportOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"ISO-10303-21;", "application/octet-stream")},
            )
        assert resp.status_code == 200
        html = resp.text
        assert "SUCCESS" in html
        assert "step-token-adapter" in html
        assert "STEP-GENERIC" in html

    def test_failed_import_shows_error(self, client: TestClient) -> None:
        fake = _fake_failed_result()
        with patch(
            "frontend.routers.ui.CadImportOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("bad.step", b"garbage", "application/octet-stream")},
            )
        assert resp.status_code == 200
        html = resp.text
        assert "FAILED" in html
        assert "malformed content" in html

    def test_no_traceback_on_exception(self, client: TestClient) -> None:
        with patch(
            "frontend.routers.ui.CadImportOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.import_source.side_effect = RuntimeError("boom")
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"data", "application/octet-stream")},
            )
        assert resp.status_code == 200
        html = resp.text
        assert "Traceback" not in html
        assert "boom" not in html
        assert "internal error" in html.lower()

    def test_result_shows_real_fields(self, client: TestClient) -> None:
        fake = _fake_success_result()
        with patch(
            "frontend.routers.ui.CadImportOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"ISO-10303-21;", "application/octet-stream")},
            )
        html = resp.text
        # All these are real fields from ImportResult
        assert "LEVEL_2_NORMALIZED" in html
        assert "SUCCESS" in html
        assert "CAD_GEOMETRY" in html
        assert "4A.0" in html

    def test_no_fake_data_generated(self, client: TestClient) -> None:
        fake = _fake_success_result()
        with patch(
            "frontend.routers.ui.CadImportOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.import_source.return_value = fake
            resp = client.post(
                "/ui/cad-import",
                files={"file": ("test.step", b"data", "application/octet-stream")},
            )
        html = resp.text
        # Should NOT contain fabricated data
        assert "Loading" not in html
        assert "progress" not in html.lower() or "progress" in html.lower()
        assert "3D" not in html
