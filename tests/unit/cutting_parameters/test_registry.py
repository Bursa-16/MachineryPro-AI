"""Stage 3G: CuttingParameterRegistry tests.

Covers: registration, exact-ID lookup, collection queries, conflict
preservation, deterministic ordering, fail-closed behaviors.
"""

from __future__ import annotations

import pytest

from backend.cutting_parameters.models import (
    ApplicabilityScope,
    CuttingParameterRecord,
    EvidenceStatus,
    ParameterType,
    QuantityRange,
)
from backend.cutting_parameters.registry import CuttingParameterRegistry
from backend.cutting_parameters.validation import require_authoritative
from backend.domain.base import Provenance
from backend.domain.enums import IsoMaterialGroup, OperationType, ProvenanceType
from backend.domain.units import Quantity, Unit
from backend.empirical.exceptions import EmpiricalDataError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prov(ref: str = "test-source") -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference=ref,
    )


def _vc_record(
    record_id: str, lo: str = "150", hi: str = "250", **kwargs
) -> CuttingParameterRecord:
    defaults = dict(
        record_id=record_id,
        parameter_type=ParameterType.CUTTING_SPEED,
        value_range=QuantityRange(
            min_value=Quantity.of(lo, Unit.M_MIN),
            max_value=Quantity.of(hi, Unit.M_MIN),
        ),
        applicability=ApplicabilityScope(operation_type=OperationType.TURNING),
        provenance=_prov(),
        evidence_status=EvidenceStatus.AUTHORITATIVE,
    )
    defaults.update(kwargs)
    return CuttingParameterRecord(**defaults)


# ---------------------------------------------------------------------------
# A. Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_returns_record(self) -> None:
        registry = CuttingParameterRegistry()
        record = _vc_record("R-001")
        result = registry.register(record)
        assert result is record

    def test_duplicate_id_rejected(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        with pytest.raises(EmpiricalDataError, match="R-001"):
            registry.register(_vc_record("R-001"))

    def test_non_record_type_rejected(self) -> None:
        registry = CuttingParameterRegistry()
        with pytest.raises(TypeError):
            registry.register("not-a-record")  # type: ignore[arg-type]

    def test_empty_registry_has_zero_length(self) -> None:
        registry = CuttingParameterRegistry()
        assert len(registry) == 0

    def test_length_increments_on_register(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        registry.register(_vc_record("R-002"))
        assert len(registry) == 2

    def test_contains_after_register(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        assert "R-001" in registry
        assert "R-999" not in registry


# ---------------------------------------------------------------------------
# B. Exact-ID lookup
# ---------------------------------------------------------------------------

class TestExactLookup:
    def test_get_existing_record(self) -> None:
        registry = CuttingParameterRegistry()
        record = _vc_record("R-001")
        registry.register(record)
        assert registry.get("R-001") is record

    def test_get_missing_raises(self) -> None:
        registry = CuttingParameterRegistry()
        with pytest.raises(EmpiricalDataError, match="R-MISSING"):
            registry.get("R-MISSING")

    def test_has_true_when_present(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        assert registry.has("R-001") is True

    def test_has_false_when_absent(self) -> None:
        registry = CuttingParameterRegistry()
        assert registry.has("R-999") is False


# ---------------------------------------------------------------------------
# C. Collection queries
# ---------------------------------------------------------------------------

class TestCollectionQueries:
    def test_find_empty_returns_empty_tuple(self) -> None:
        registry = CuttingParameterRegistry()
        assert registry.find() == ()

    def test_find_all_no_filters(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        registry.register(_vc_record("R-002"))
        results = registry.find()
        assert len(results) == 2

    def test_find_by_parameter_type(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("VC-001"))
        fpt_record = CuttingParameterRecord(
            record_id="FPT-001",
            parameter_type=ParameterType.FEED_PER_TOOTH,
            value_range=QuantityRange(
                min_value=Quantity.of("0.05", Unit.MM_TOOTH),
                max_value=Quantity.of("0.15", Unit.MM_TOOTH),
            ),
            applicability=ApplicabilityScope(operation_type=OperationType.MILLING),
            provenance=_prov(),
            evidence_status=EvidenceStatus.AUTHORITATIVE,
        )
        registry.register(fpt_record)
        vc_results = registry.find(parameter_type=ParameterType.CUTTING_SPEED)
        fpt_results = registry.find(parameter_type=ParameterType.FEED_PER_TOOTH)
        assert len(vc_results) == 1
        assert vc_results[0].record_id == "VC-001"
        assert len(fpt_results) == 1

    def test_find_by_scope_operation_type(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(
            _vc_record("TURN-001", applicability=ApplicabilityScope(
                operation_type=OperationType.TURNING))
        )
        registry.register(
            _vc_record(
                "MILL-001",
                value_range=QuantityRange(
                    min_value=Quantity.of("100", Unit.M_MIN),
                    max_value=Quantity.of("200", Unit.M_MIN),
                ),
                applicability=ApplicabilityScope(operation_type=OperationType.MILLING),
            )
        )
        turning_results = registry.find(
            scope=ApplicabilityScope(operation_type=OperationType.TURNING)
        )
        assert len(turning_results) == 1
        assert turning_results[0].record_id == "TURN-001"

    def test_find_no_match_returns_empty_tuple(self) -> None:
        """A record scoped specifically to P group does not match an S-group query."""
        registry = CuttingParameterRegistry()
        # Register a record that explicitly specifies ISO group P
        p_record = CuttingParameterRecord(
            record_id="P-ONLY-001",
            parameter_type=ParameterType.CUTTING_SPEED,
            value_range=QuantityRange(
                min_value=Quantity.of("150", Unit.M_MIN),
                max_value=Quantity.of("250", Unit.M_MIN),
            ),
            applicability=ApplicabilityScope(
                operation_type=OperationType.TURNING,
                iso_material_group=IsoMaterialGroup.P,  # explicitly P
            ),
            provenance=_prov(),
            evidence_status=EvidenceStatus.AUTHORITATIVE,
        )
        registry.register(p_record)
        # Query for S group — should not match P group record
        results = registry.find(
            scope=ApplicabilityScope(iso_material_group=IsoMaterialGroup.S)
        )
        assert results == ()

    def test_find_deterministic_ordering(self) -> None:
        """Results must be sorted by record_id regardless of registration order."""
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-003"))
        registry.register(_vc_record("R-001"))
        registry.register(_vc_record("R-002"))
        results = registry.find()
        assert [r.record_id for r in results] == ["R-001", "R-002", "R-003"]

    def test_find_repeatable(self) -> None:
        """Same query always returns same result."""
        registry = CuttingParameterRegistry()
        registry.register(_vc_record("R-001"))
        r1 = registry.find()
        r2 = registry.find()
        assert r1 == r2

    def test_find_by_evidence_status(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(
            _vc_record("AUTH-001", evidence_status=EvidenceStatus.AUTHORITATIVE)
        )
        registry.register(
            _vc_record(
                "UNVER-001",
                evidence_status=EvidenceStatus.UNVERIFIED,
                provenance=Provenance(
                    source_type=ProvenanceType.UNKNOWN,
                    source_reference=None,
                ),
            )
        )
        auth_results = registry.find(evidence_status=EvidenceStatus.AUTHORITATIVE)
        unver_results = registry.find(evidence_status=EvidenceStatus.UNVERIFIED)
        assert len(auth_results) == 1
        assert auth_results[0].record_id == "AUTH-001"
        assert len(unver_results) == 1


# ---------------------------------------------------------------------------
# D. Conflict preservation — multiple sources, different values
# ---------------------------------------------------------------------------

class TestConflictPreservation:
    def test_conflicting_records_both_preserved(self) -> None:
        """
        Source A and Source B disagree on Vc range for the same scope.
        Both must be returned — no automatic merging or selection.

        This fixture uses training-material ranges deliberately labeled as
        test-only (not authoritative recommendations).
        """
        registry = CuttingParameterRegistry()
        scope = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        # Source A: Vc 180–220 m/min
        registry.register(
            CuttingParameterRecord(
                record_id="SRC-A-VC",
                parameter_type=ParameterType.CUTTING_SPEED,
                value_range=QuantityRange(
                    min_value=Quantity.of("180", Unit.M_MIN),
                    max_value=Quantity.of("220", Unit.M_MIN),
                ),
                applicability=scope,
                provenance=Provenance(
                    source_type=ProvenanceType.MANUFACTURER_DATA,
                    source_reference="Source-A Catalogue §3.2",
                ),
                evidence_status=EvidenceStatus.AUTHORITATIVE,
            )
        )
        # Source B: Vc 240–280 m/min (conflict)
        registry.register(
            CuttingParameterRecord(
                record_id="SRC-B-VC",
                parameter_type=ParameterType.CUTTING_SPEED,
                value_range=QuantityRange(
                    min_value=Quantity.of("240", Unit.M_MIN),
                    max_value=Quantity.of("280", Unit.M_MIN),
                ),
                applicability=scope,
                provenance=Provenance(
                    source_type=ProvenanceType.LITERATURE,
                    source_reference="Source-B Handbook p.44",
                ),
                evidence_status=EvidenceStatus.AUTHORITATIVE,
            )
        )
        results = registry.find(
            scope=scope, parameter_type=ParameterType.CUTTING_SPEED
        )
        assert len(results) == 2, "Both conflicting records must be preserved"
        ids = {r.record_id for r in results}
        assert "SRC-A-VC" in ids
        assert "SRC-B-VC" in ids

    def test_no_automatic_averaging(self) -> None:
        """Registry never returns a merged or averaged result."""
        registry = CuttingParameterRegistry()
        scope = ApplicabilityScope(operation_type=OperationType.TURNING)
        registry.register(
            CuttingParameterRecord(
                record_id="LOW-VC",
                parameter_type=ParameterType.CUTTING_SPEED,
                value_range=QuantityRange(
                    min_value=Quantity.of("100", Unit.M_MIN),
                    max_value=Quantity.of("150", Unit.M_MIN),
                ),
                applicability=scope,
                provenance=_prov("ref-1"),
                evidence_status=EvidenceStatus.AUTHORITATIVE,
            )
        )
        registry.register(
            CuttingParameterRecord(
                record_id="HIGH-VC",
                parameter_type=ParameterType.CUTTING_SPEED,
                value_range=QuantityRange(
                    min_value=Quantity.of("300", Unit.M_MIN),
                    max_value=Quantity.of("400", Unit.M_MIN),
                ),
                applicability=scope,
                provenance=_prov("ref-2"),
                evidence_status=EvidenceStatus.AUTHORITATIVE,
            )
        )
        results = registry.find(scope=scope)
        # Two separate records, not an averaged midpoint
        assert len(results) == 2
        values = {r.value_range.min_value.value for r in results}
        from decimal import Decimal
        assert Decimal("100") in values
        assert Decimal("300") in values
        # 200 (average of 100 and 300) must NOT appear
        assert Decimal("200") not in values


# ---------------------------------------------------------------------------
# E. find_authoritative
# ---------------------------------------------------------------------------

class TestFindAuthoritative:
    def test_only_authoritative_returned(self) -> None:
        registry = CuttingParameterRegistry()
        registry.register(
            _vc_record("AUTH", evidence_status=EvidenceStatus.AUTHORITATIVE)
        )
        registry.register(
            _vc_record(
                "UNVER",
                evidence_status=EvidenceStatus.UNVERIFIED,
                provenance=Provenance(
                    source_type=ProvenanceType.UNKNOWN,
                    source_reference=None,
                ),
            )
        )
        results = registry.find_authoritative()
        assert len(results) == 1
        assert results[0].record_id == "AUTH"

    def test_empty_registry_authoritative_empty(self) -> None:
        registry = CuttingParameterRegistry()
        assert registry.find_authoritative() == ()


# ---------------------------------------------------------------------------
# F. Validation gate — require_authoritative
# ---------------------------------------------------------------------------

class TestValidationGate:
    def test_authoritative_passes(self) -> None:
        record = _vc_record("R-AUTH")
        result = require_authoritative(record)
        assert result is record

    def test_ai_provenance_blocked(self) -> None:
        """AI-sourced data must never be admitted as authoritative."""
        prov = Provenance(
            source_type=ProvenanceType.AI_SUGGESTION,
            source_reference="gpt-output-2026",
        )
        # AI_SUGGESTION + AUTHORITATIVE status → rejected at construction
        # because source_reference is present but status would be AUTHORITATIVE.
        # We test via an UNVERIFIED record that has AI provenance.
        record = CuttingParameterRecord(
            record_id="AI-001",
            parameter_type=ParameterType.CUTTING_SPEED,
            value_range=QuantityRange(
                min_value=Quantity.of("200", Unit.M_MIN),
                max_value=Quantity.of("300", Unit.M_MIN),
            ),
            applicability=ApplicabilityScope(operation_type=OperationType.TURNING),
            provenance=prov,
            evidence_status=EvidenceStatus.UNVERIFIED,
        )
        with pytest.raises(EmpiricalDataError, match="not authoritative"):
            require_authoritative(record)

    def test_unverified_status_blocked(self) -> None:
        prov = Provenance(
            source_type=ProvenanceType.UNKNOWN,
            source_reference=None,
        )
        record = _vc_record(
            "UNVER-001",
            evidence_status=EvidenceStatus.UNVERIFIED,
            provenance=prov,
        )
        with pytest.raises(EmpiricalDataError):
            require_authoritative(record)

    def test_reference_only_blocked(self) -> None:
        record = CuttingParameterRecord(
            record_id="REF-001",
            parameter_type=ParameterType.CUTTING_SPEED,
            value_range=_vc_record("_").value_range,
            applicability=ApplicabilityScope(operation_type=OperationType.TURNING),
            provenance=Provenance(
                source_type=ProvenanceType.LITERATURE,
                source_reference=None,
            ),
            evidence_status=EvidenceStatus.REFERENCE_ONLY,
        )
        with pytest.raises(EmpiricalDataError):
            require_authoritative(record)
