"""Stage 3G: CuttingParameterRecord and related model tests.

Test fixture values are clearly labeled and come from:
  SRC-002 §6.2 (CAM_Detayli_Ogrenme_Rehberi (1).docx) — pedagogical examples
  Synthetic values — used to exercise model behavior only

NO fixture value in this file represents an authoritative production
cutting recommendation.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from backend.cutting_parameters.models import (
    AUTHORITATIVE_STATUSES,
    PARAMETER_CANONICAL_UNIT,
    ApplicabilityScope,
    CuttingParameterRecord,
    EvidenceStatus,
    ParameterType,
    QuantityRange,
)
from backend.domain.base import Provenance
from backend.domain.enums import (
    CoolantMode,
    IsoMaterialGroup,
    OperationType,
    ProvenanceType,
    ToolMaterial,
    ToolType,
)
from backend.domain.exceptions import ValidationError
from backend.domain.units import Quantity, Unit

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _lit_provenance(ref: str = "test-fixture") -> Provenance:
    """A LITERATURE provenance with a reference — authoritative-eligible."""
    return Provenance(
        source_type=ProvenanceType.LITERATURE,
        source_reference=ref,
        source_document="test fixture document",
    )


def _ai_provenance() -> Provenance:
    """An AI_SUGGESTION provenance — never authoritative."""
    return Provenance(
        source_type=ProvenanceType.AI_SUGGESTION,
        source_reference="model-output",
    )


def _vc_range(lo: str = "150", hi: str = "250") -> QuantityRange:
    return QuantityRange(
        min_value=Quantity.of(lo, Unit.M_MIN),
        max_value=Quantity.of(hi, Unit.M_MIN),
    )


def _base_record(**kwargs) -> CuttingParameterRecord:
    defaults = dict(
        record_id="TEST-001",
        parameter_type=ParameterType.CUTTING_SPEED,
        value_range=_vc_range(),
        applicability=ApplicabilityScope(operation_type=OperationType.TURNING),
        provenance=_lit_provenance(),
        evidence_status=EvidenceStatus.AUTHORITATIVE,
    )
    defaults.update(kwargs)
    return CuttingParameterRecord(**defaults)


# ---------------------------------------------------------------------------
# A. EvidenceStatus
# ---------------------------------------------------------------------------

class TestEvidenceStatus:
    def test_authoritative_statuses_non_empty(self) -> None:
        assert len(AUTHORITATIVE_STATUSES) >= 1

    def test_authoritative_in_authoritative_statuses(self) -> None:
        assert EvidenceStatus.AUTHORITATIVE in AUTHORITATIVE_STATUSES

    def test_unverified_not_in_authoritative_statuses(self) -> None:
        assert EvidenceStatus.UNVERIFIED not in AUTHORITATIVE_STATUSES

    def test_reference_only_not_in_authoritative_statuses(self) -> None:
        assert EvidenceStatus.REFERENCE_ONLY not in AUTHORITATIVE_STATUSES

    def test_all_status_values_are_strings(self) -> None:
        for status in EvidenceStatus:
            assert isinstance(status.value, str)


# ---------------------------------------------------------------------------
# B. ParameterType and canonical units
# ---------------------------------------------------------------------------

class TestParameterType:
    def test_cutting_speed_canonical_unit(self) -> None:
        assert PARAMETER_CANONICAL_UNIT[ParameterType.CUTTING_SPEED] is Unit.M_MIN

    def test_feed_per_tooth_canonical_unit(self) -> None:
        assert PARAMETER_CANONICAL_UNIT[ParameterType.FEED_PER_TOOTH] is Unit.MM_TOOTH

    def test_feed_per_rev_canonical_unit(self) -> None:
        assert PARAMETER_CANONICAL_UNIT[ParameterType.FEED_PER_REV] is Unit.MM_REV

    def test_specific_cutting_force_canonical_unit(self) -> None:
        # Kc1.1 uses MPa (1 MPa == 1 N/mm²)
        assert (
            PARAMETER_CANONICAL_UNIT[ParameterType.SPECIFIC_CUTTING_FORCE]
            is Unit.MPA
        )

    def test_all_parameter_types_have_canonical_unit(self) -> None:
        for pt in ParameterType:
            assert pt in PARAMETER_CANONICAL_UNIT


# ---------------------------------------------------------------------------
# C. QuantityRange
# ---------------------------------------------------------------------------

class TestQuantityRange:
    def test_valid_range(self) -> None:
        qr = QuantityRange(
            min_value=Quantity.of("150", Unit.M_MIN),
            max_value=Quantity.of("250", Unit.M_MIN),
        )
        assert qr.min_value.value == Decimal("150")
        assert qr.max_value.value == Decimal("250")
        assert qr.unit is Unit.M_MIN

    def test_point_range(self) -> None:
        qr = QuantityRange(
            min_value=Quantity.of("200", Unit.M_MIN),
            max_value=Quantity.of("200", Unit.M_MIN),
        )
        assert qr.is_point is True

    def test_non_point_range(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.is_point is False

    def test_min_gt_max_rejected(self) -> None:
        with pytest.raises(ValidationError, match="min_value"):
            QuantityRange(
                min_value=Quantity.of("300", Unit.M_MIN),
                max_value=Quantity.of("200", Unit.M_MIN),
            )

    def test_unit_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="unit"):
            QuantityRange(
                min_value=Quantity.of("150", Unit.M_MIN),
                max_value=Quantity.of("250", Unit.RPM),
            )

    def test_contains_within(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.contains(Quantity.of("200", Unit.M_MIN)) is True

    def test_contains_at_min_boundary(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.contains(Quantity.of("150", Unit.M_MIN)) is True

    def test_contains_at_max_boundary(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.contains(Quantity.of("250", Unit.M_MIN)) is True

    def test_contains_below_min(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.contains(Quantity.of("100", Unit.M_MIN)) is False

    def test_contains_above_max(self) -> None:
        qr = _vc_range("150", "250")
        assert qr.contains(Quantity.of("300", Unit.M_MIN)) is False

    def test_contains_unit_mismatch_raises(self) -> None:
        qr = _vc_range("150", "250")
        with pytest.raises(ValidationError):
            qr.contains(Quantity.of("200", Unit.RPM))

    def test_immutable(self) -> None:
        qr = _vc_range()
        with pytest.raises((AttributeError, TypeError)):
            qr.min_value = Quantity.of("10", Unit.M_MIN)  # type: ignore[misc]

    def test_nan_rejected_by_quantity(self) -> None:
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            Quantity.of("nan", Unit.M_MIN)

    def test_infinity_rejected_by_quantity(self) -> None:
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            Quantity.of("inf", Unit.M_MIN)

    def test_bool_rejected(self) -> None:
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            Quantity.of(True, Unit.M_MIN)

    def test_as_dict_returns_dict(self) -> None:
        qr = _vc_range()
        d = qr.as_dict()
        assert isinstance(d, dict)


# ---------------------------------------------------------------------------
# D. ApplicabilityScope
# ---------------------------------------------------------------------------

class TestApplicabilityScope:
    def test_empty_scope_is_valid(self) -> None:
        scope = ApplicabilityScope()
        assert scope.operation_type is None

    def test_full_scope(self) -> None:
        scope = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
            tool_material=ToolMaterial.CARBIDE,
            tool_type=ToolType.TURNING_INSERT,
            coolant_mode=CoolantMode.FLOOD,
        )
        assert scope.operation_type is OperationType.TURNING

    def test_invalid_operation_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApplicabilityScope(operation_type="turning")  # type: ignore[arg-type]

    def test_invalid_iso_group_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApplicabilityScope(iso_material_group="P")  # type: ignore[arg-type]

    def test_invalid_tool_material_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApplicabilityScope(tool_material="carbide")  # type: ignore[arg-type]

    def test_empty_notes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApplicabilityScope(notes="   ")

    def test_immutable(self) -> None:
        scope = ApplicabilityScope(operation_type=OperationType.MILLING)
        with pytest.raises((AttributeError, TypeError)):
            scope.operation_type = OperationType.TURNING  # type: ignore[misc]

    # Scope matching
    def test_exact_match(self) -> None:
        record_scope = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        query = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        assert record_scope.matches(query) is True

    def test_record_unspecified_field_matches_any_query(self) -> None:
        record_scope = ApplicabilityScope(operation_type=OperationType.TURNING)
        # Record doesn't specify material → matches any material query
        query = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.M,
        )
        assert record_scope.matches(query) is True

    def test_record_specified_field_mismatch(self) -> None:
        record_scope = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        query = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.M,
        )
        assert record_scope.matches(query) is False

    def test_query_none_field_matches_anything(self) -> None:
        record_scope = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        # Query doesn't filter on material
        query = ApplicabilityScope(operation_type=OperationType.TURNING)
        assert record_scope.matches(query) is True

    def test_operation_type_mismatch(self) -> None:
        record_scope = ApplicabilityScope(operation_type=OperationType.TURNING)
        query = ApplicabilityScope(operation_type=OperationType.MILLING)
        assert record_scope.matches(query) is False


# ---------------------------------------------------------------------------
# E. CuttingParameterRecord — construction
# ---------------------------------------------------------------------------

class TestCuttingParameterRecordConstruction:
    def test_valid_authoritative_record(self) -> None:
        record = _base_record()
        assert record.record_id == "TEST-001"
        assert record.parameter_type is ParameterType.CUTTING_SPEED
        assert record.is_authoritative is True

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(record_id="")

    def test_whitespace_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(record_id="   ")

    def test_wrong_parameter_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(parameter_type="CUTTING_SPEED")  # type: ignore[arg-type]

    def test_wrong_unit_for_parameter_type_rejected(self) -> None:
        """Vc must use M_MIN; RPM is wrong."""
        bad_range = QuantityRange(
            min_value=Quantity.of("500", Unit.RPM),
            max_value=Quantity.of("5000", Unit.RPM),
        )
        with pytest.raises(ValidationError, match="unit"):
            _base_record(parameter_type=ParameterType.CUTTING_SPEED, value_range=bad_range)

    def test_wrong_value_range_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(value_range=("150", "250"))  # type: ignore[arg-type]

    def test_wrong_applicability_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(applicability={"operation_type": "turning"})  # type: ignore[arg-type]

    def test_wrong_provenance_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(provenance="source: Sandvik 2023")  # type: ignore[arg-type]

    def test_wrong_evidence_status_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _base_record(evidence_status="AUTHORITATIVE")  # type: ignore[arg-type]

    def test_immutable(self) -> None:
        record = _base_record()
        with pytest.raises((AttributeError, TypeError)):
            record.record_id = "MUTATED"  # type: ignore[misc]

    def test_decimal_value_preserved(self) -> None:
        qr = QuantityRange(
            min_value=Quantity.of("123.456", Unit.M_MIN),
            max_value=Quantity.of("234.567", Unit.M_MIN),
        )
        record = _base_record(value_range=qr)
        assert record.value_range.min_value.value == Decimal("123.456")

    def test_no_float_leakage(self) -> None:
        """Confirm no float appears in the record's value."""
        record = _base_record()
        assert isinstance(record.value_range.min_value.value, Decimal)
        assert isinstance(record.value_range.max_value.value, Decimal)


# ---------------------------------------------------------------------------
# F. CuttingParameterRecord — authority / provenance
# ---------------------------------------------------------------------------

class TestCuttingParameterRecordAuthority:
    def test_authoritative_with_valid_provenance(self) -> None:
        record = _base_record(
            evidence_status=EvidenceStatus.AUTHORITATIVE,
            provenance=_lit_provenance("Sandvik Catalogue 2023 p.187"),
        )
        assert record.is_authoritative is True

    def test_authoritative_without_source_reference_rejected(self) -> None:
        """AUTHORITATIVE status requires source_reference — fail closed."""
        prov = Provenance(
            source_type=ProvenanceType.LITERATURE,
            source_reference=None,  # missing
        )
        with pytest.raises(ValidationError, match="source_reference"):
            _base_record(evidence_status=EvidenceStatus.AUTHORITATIVE, provenance=prov)

    def test_unverified_does_not_require_source_reference(self) -> None:
        """UNVERIFIED records may lack source_reference (they're not authoritative)."""
        prov = Provenance(
            source_type=ProvenanceType.UNKNOWN,
            source_reference=None,
        )
        record = _base_record(
            evidence_status=EvidenceStatus.UNVERIFIED, provenance=prov
        )
        assert record.is_authoritative is False

    def test_reference_only_is_not_authoritative(self) -> None:
        record = _base_record(
            evidence_status=EvidenceStatus.REFERENCE_ONLY,
            provenance=Provenance(
                source_type=ProvenanceType.LITERATURE,
                source_reference=None,
            ),
        )
        assert record.is_authoritative is False

    def test_experimental_with_source_reference_is_authoritative(self) -> None:
        record = _base_record(
            evidence_status=EvidenceStatus.EXPERIMENTAL,
            provenance=_lit_provenance("Internal test TB-2026-001"),
        )
        assert record.is_authoritative is True

    def test_provenance_permanently_bound(self) -> None:
        """Provenance survives retrieval — no stripping path."""
        prov = _lit_provenance("Kennametal Catalogue 2022 p.44")
        record = _base_record(provenance=prov)
        assert record.provenance.source_reference == "Kennametal Catalogue 2022 p.44"
        assert record.provenance.source_type is ProvenanceType.LITERATURE


# ---------------------------------------------------------------------------
# G. CuttingParameterRecord — scope matching
# ---------------------------------------------------------------------------

class TestCuttingParameterRecordScopeMatching:
    def test_matches_exact_scope(self) -> None:
        record = _base_record(
            applicability=ApplicabilityScope(
                operation_type=OperationType.TURNING,
                iso_material_group=IsoMaterialGroup.P,
            )
        )
        query = ApplicabilityScope(
            operation_type=OperationType.TURNING,
            iso_material_group=IsoMaterialGroup.P,
        )
        assert record.matches_scope(query) is True

    def test_does_not_match_different_operation(self) -> None:
        record = _base_record(
            applicability=ApplicabilityScope(operation_type=OperationType.TURNING)
        )
        query = ApplicabilityScope(operation_type=OperationType.MILLING)
        assert record.matches_scope(query) is False

    def test_unspecified_record_field_matches_any(self) -> None:
        record = _base_record(
            applicability=ApplicabilityScope(operation_type=OperationType.DRILLING)
        )
        query = ApplicabilityScope(
            operation_type=OperationType.DRILLING,
            iso_material_group=IsoMaterialGroup.K,
        )
        assert record.matches_scope(query) is True


# ---------------------------------------------------------------------------
# H. CuttingParameterRecord — different parameter types
# ---------------------------------------------------------------------------

class TestCuttingParameterRecordOtherTypes:
    def test_feed_per_tooth_record(self) -> None:
        qr = QuantityRange(
            min_value=Quantity.of("0.05", Unit.MM_TOOTH),
            max_value=Quantity.of("0.15", Unit.MM_TOOTH),
        )
        record = CuttingParameterRecord(
            record_id="FPT-001",
            parameter_type=ParameterType.FEED_PER_TOOTH,
            value_range=qr,
            applicability=ApplicabilityScope(operation_type=OperationType.MILLING),
            provenance=_lit_provenance("test-ref"),
            evidence_status=EvidenceStatus.AUTHORITATIVE,
        )
        assert record.value_range.unit is Unit.MM_TOOTH

    def test_feed_per_rev_record(self) -> None:
        qr = QuantityRange(
            min_value=Quantity.of("0.2", Unit.MM_REV),
            max_value=Quantity.of("0.5", Unit.MM_REV),
        )
        record = CuttingParameterRecord(
            record_id="FPR-001",
            parameter_type=ParameterType.FEED_PER_REV,
            value_range=qr,
            applicability=ApplicabilityScope(operation_type=OperationType.TURNING),
            provenance=_lit_provenance("test-ref"),
            evidence_status=EvidenceStatus.AUTHORITATIVE,
        )
        assert record.value_range.unit is Unit.MM_REV

    def test_specific_cutting_force_record(self) -> None:
        """Kc1.1 values use MPA (1 MPa == 1 N/mm²)."""
        qr = QuantityRange(
            min_value=Quantity.of("1500", Unit.MPA),
            max_value=Quantity.of("1800", Unit.MPA),
        )
        record = CuttingParameterRecord(
            record_id="KC-001",
            parameter_type=ParameterType.SPECIFIC_CUTTING_FORCE,
            value_range=qr,
            applicability=ApplicabilityScope(
                operation_type=OperationType.MILLING,
                iso_material_group=IsoMaterialGroup.P,
            ),
            provenance=_lit_provenance("Groover 2020 Table 21.2"),
            evidence_status=EvidenceStatus.REFERENCE_ONLY,
        )
        assert record.value_range.unit is Unit.MPA
        assert record.is_authoritative is False


# ---------------------------------------------------------------------------
# I. Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_as_dict_returns_dict(self) -> None:
        record = _base_record()
        d = record.as_dict()
        assert isinstance(d, dict)
        assert "record_id" in d
        assert "parameter_type" in d

    def test_deterministic_serialization(self) -> None:
        record = _base_record()
        d1 = record.as_dict()
        d2 = record.as_dict()
        assert d1 == d2
