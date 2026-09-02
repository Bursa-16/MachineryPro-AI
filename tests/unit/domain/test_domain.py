"""Stage 2 unit tests: Machinery AI engineering domain model.

Boundary cases and fail-closed behavior are first-class here.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from backend.domain import (
    CoolantMode,
    EngineeringResult,
    Feature,
    FeatureType,
    Machine,
    MachineType,
    MachiningParameters,
    Material,
    MaterialFamily,
    Operation,
    OperationType,
    Part,
    Provenance,
    ProvenanceType,
    Quantity,
    ResultStatus,
    Tool,
    ToolType,
    Unit,
    UnitError,
    ValidationError,
)


def _prov(source_type: ProvenanceType = ProvenanceType.USER_INPUT) -> Provenance:
    return Provenance(
        source_type=source_type,
        source_reference="ref-1",
        source_document="doc-1",
        page_section="p.3",
    )


def _valid_part(**overrides) -> Part:
    values = dict(
        part_id="P-1",
        name="Bracket",
        revision="A",
        material_id="MAT-1",
        quantity=5,
        provenance=_prov(),
    )
    values.update(overrides)
    return Part(**values)


def test_valid_part_construction() -> None:
    part = _valid_part()
    assert part.part_id == "P-1"
    assert part.quantity == 5
    assert part.unit_system == "METRIC"
    assert part.schema_version == "1"


def test_part_normalizes_whitespace_and_strips() -> None:
    part = _valid_part(part_id="  P-2  ", name="  Cap  ")
    assert part.part_id == "P-2"
    assert part.name == "Cap"


def test_part_invalid_quantity_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        _valid_part(quantity=0)


def test_part_invalid_quantity_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        _valid_part(quantity=-3)


def test_part_invalid_quantity_float_rejected() -> None:
    with pytest.raises(ValidationError):
        _valid_part(quantity=2.5)


def test_part_empty_identity_rejected() -> None:
    with pytest.raises(ValidationError):
        _valid_part(part_id="   ")


def test_part_is_frozen() -> None:
    part = _valid_part()
    with pytest.raises(Exception):
        part.part_id = "other"  # type: ignore[misc]


# --------------------------------------------------------------------- #
# Quantity / units
# --------------------------------------------------------------------- #
def test_quantity_explicit_unit() -> None:
    quantity = Quantity.of(20, "mm")
    assert quantity.is_positive()
    assert quantity.unit is Unit.MM
    assert str(quantity) == "20 mm"


def test_quantity_negative_representable_but_not_positive() -> None:
    quantity = Quantity.of(-5, "mm")
    assert not quantity.is_positive()


def test_quantity_invalid_numeric_rejected() -> None:
    with pytest.raises(UnitError):
        Quantity.of("not-a-number", "mm")


def test_quantity_nan_rejected() -> None:
    with pytest.raises(UnitError):
        Quantity.of("NaN", "mm")


def test_quantity_unknown_symbol_rejected() -> None:
    with pytest.raises(UnitError):
        Quantity.of("1", "furlong")


def test_no_implicit_unit_conversion() -> None:
    mm = Quantity.of(1000, "mm")
    m = Quantity.of(1, "m")
    with pytest.raises(ValidationError):
        mm.require_same_unit(m, context="compare")


def test_require_same_unit_ok_for_identical() -> None:
    Quantity.of(1, "mm").require_same_unit(Quantity.of(2, "mm"))


# --------------------------------------------------------------------- #
# Feature / operation / parameters
# --------------------------------------------------------------------- #
def test_feature_type_enum_members() -> None:
    expected = {
        "hole",
        "pocket",
        "slot",
        "planar_face",
        "cylindrical_surface",
        "thread",
        "chamfer",
        "fillet",
        "groove",
        "freeform_surface",
        "unknown",
    }
    assert {feature.value for feature in FeatureType} == expected


def test_valid_feature_construction() -> None:
    feature = Feature(
        feature_id="F-1",
        part_id="P-1",
        feature_type=FeatureType.HOLE,
        provenance=_prov(ProvenanceType.DRAWING),
        dimensions={"diameter": Quantity.of(10, "mm")},
        tolerance_refs=("tol-1",),
        surface_finish=Quantity.of(3.2, "Ra_um"),
    )
    assert feature.feature_id == "F-1"
    assert feature.surface_finish is not None
    assert feature.surface_finish.unit is Unit.RA_UM


def test_feature_dimensions_wrong_type_rejected() -> None:
    with pytest.raises(ValidationError):
        Feature(
            feature_id="F-1",
            part_id="P-1",
            feature_type=FeatureType.HOLE,
            provenance=_prov(),
            dimensions={"d": 10},  # type: ignore[dict-item]
        )


def test_operation_empty_refs_allowed() -> None:
    operation = Operation(
        operation_id="OP-1",
        part_id="P-1",
        operation_type=OperationType.DRILLING,
        sequence_index=1,
        provenance=_prov(),
    )
    assert operation.feature_ids == ()
    assert operation.tool_ids == ()
    assert operation.machine_id is None


def test_operation_rejects_zero_sequence_index() -> None:
    with pytest.raises(ValidationError):
        Operation(
            operation_id="OP-9",
            part_id="P-1",
            operation_type=OperationType.DRILLING,
            sequence_index=0,
            provenance=_prov(),
        )


def test_machining_parameters_optionality() -> None:
    params = MachiningParameters()
    assert params.cutting_speed is None
    assert params.coolant_mode is None
    params2 = MachiningParameters(
        cutting_speed=Quantity.of(150, "m/min"),
        coolant_mode=CoolantMode.FLOOD,
    )
    assert params2.cutting_speed is not None
    assert params2.coolant_mode is CoolantMode.FLOOD


def test_machining_parameters_zero_feed_rejected() -> None:
    with pytest.raises(ValidationError):
        MachiningParameters(feed_per_tooth=Quantity.of(0, "mm/tooth"))


# --------------------------------------------------------------------- #
# Tool / machine constraint validation
# --------------------------------------------------------------------- #
def test_valid_tool_construction() -> None:
    tool = Tool(
        tool_id="T-1",
        tool_type=ToolType.END_MILL,
        diameter=Quantity.of(10, "mm"),
        cutting_edge_count=4,
        provenance=_prov(ProvenanceType.MANUFACTURER_DATA),
        supported_operations=(OperationType.MILLING,),
    )
    assert tool.cutting_edge_count == 4


def test_tool_zero_diameter_rejected() -> None:
    with pytest.raises(ValidationError):
        Tool(
            tool_id="T-1",
            tool_type=ToolType.END_MILL,
            diameter=Quantity.of(0, "mm"),
            cutting_edge_count=4,
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )


def test_tool_edge_count_positive_enforced() -> None:
    with pytest.raises(ValidationError):
        Tool(
            tool_id="T-1",
            tool_type=ToolType.END_MILL,
            diameter=Quantity.of(10, "mm"),
            cutting_edge_count=0,
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )


def test_tool_supported_operations_required() -> None:
    with pytest.raises(ValidationError):
        Tool(
            tool_id="T-1",
            tool_type=ToolType.END_MILL,
            diameter=Quantity.of(10, "mm"),
            cutting_edge_count=4,
            provenance=_prov(),
            supported_operations=(),
        )


def test_valid_machine_construction() -> None:
    machine = Machine(
        machine_id="M-1",
        name="VMC-3",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of(50, "rpm"),
        spindle_speed_max=Quantity.of(15000, "rpm"),
        spindle_power=Quantity.of(15, "kW"),
        provenance=_prov(ProvenanceType.MANUFACTURER_DATA),
        supported_operations=(OperationType.MILLING,),
    )
    assert machine.spindle_speed_max.value == 15000


def test_machine_inverted_speed_range_rejected() -> None:
    with pytest.raises(ValidationError):
        Machine(
            machine_id="M-1",
            name="VMC",
            machine_type=MachineType.MILL,
            axis_count=3,
            spindle_speed_min=Quantity.of(15000, "rpm"),
            spindle_speed_max=Quantity.of(50, "rpm"),
            spindle_power=Quantity.of(15, "kW"),
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )


def test_machine_wrong_power_unit_rejected() -> None:
    with pytest.raises(ValidationError):
        Machine(
            machine_id="M-1",
            name="VMC",
            machine_type=MachineType.MILL,
            axis_count=3,
            spindle_speed_min=Quantity.of(50, "rpm"),
            spindle_speed_max=Quantity.of(15000, "rpm"),
            spindle_power=Quantity.of(15, "Nm"),
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )


def test_machine_zero_power_rejected() -> None:
    with pytest.raises(ValidationError):
        Machine(
            machine_id="M-1",
            name="VMC",
            machine_type=MachineType.MILL,
            axis_count=3,
            spindle_speed_min=Quantity.of(50, "rpm"),
            spindle_speed_max=Quantity.of(15000, "rpm"),
            spindle_power=Quantity.of(0, "kW"),
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )


# --------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------- #
def test_provenance_ai_remains_identifiable() -> None:
    ai = _prov(ProvenanceType.AI_SUGGESTION)
    assert ai.is_ai_suggestion
    authority = _prov(ProvenanceType.MATERIAL_STANDARD)
    assert not authority.is_ai_suggestion


def test_provenance_confidence_bounds() -> None:
    Provenance(source_type=ProvenanceType.LITERATURE, confidence=0.5)
    with pytest.raises(ValidationError):
        Provenance(source_type=ProvenanceType.LITERATURE, confidence=1.5)


def test_provenance_accepts_timestamp() -> None:
    stamp = datetime(2026, 8, 1, tzinfo=timezone.utc)
    prov = Provenance(
        source_type=ProvenanceType.HISTORICAL_PROCESS_DATA, timestamp=stamp
    )
    assert prov.timestamp == stamp


# --------------------------------------------------------------------- #
# Material: unknown != zero
# --------------------------------------------------------------------- #
def test_material_unknown_remains_none() -> None:
    material = Material(
        material_id="MAT-1",
        designation="EN AW-6082 T6",
        material_family=MaterialFamily.ALUMINUM,
        provenance=_prov(ProvenanceType.MATERIAL_STANDARD),
    )
    assert material.density is None
    assert material.tensile_strength is None
    assert material.hardness is None


def test_material_wrong_density_unit_rejected() -> None:
    with pytest.raises(ValidationError):
        Material(
            material_id="MAT-1",
            designation="Steel",
            material_family=MaterialFamily.STEEL,
            provenance=_prov(),
            density=Quantity.of(7.85, "MPa"),
        )


def test_material_known_properties_stored() -> None:
    material = Material(
        material_id="MAT-1",
        designation="S275JR",
        material_family=MaterialFamily.STEEL,
        provenance=_prov(ProvenanceType.MATERIAL_STANDARD),
        density=Quantity.of(7850, "kg/m3"),
        tensile_strength=Quantity.of(410, "MPa"),
    )
    assert material.density is not None
    assert material.tensile_strength is not None


# --------------------------------------------------------------------- #
# EngineeringResult statuses
# --------------------------------------------------------------------- #
def _success_result() -> EngineeringResult:
    return EngineeringResult(
        result_id="R1.result",
        rule_id="R-1001",
        rule_version="1.0.0",
        status=ResultStatus.PASS,
        provenance=_prov(ProvenanceType.DETERMINISTIC_CALCULATION),
        outputs={"value": Quantity.of(5, "mm")},
    )


def test_result_pass_valid() -> None:
    assert _success_result().status is ResultStatus.PASS


def test_result_fail_requires_violations() -> None:
    with pytest.raises(ValidationError):
        EngineeringResult(
            result_id="x",
            rule_id="R",
            rule_version="1",
            status=ResultStatus.FAIL,
            provenance=_prov(),
        )


def test_result_warning_requires_warnings() -> None:
    with pytest.raises(ValidationError):
        EngineeringResult(
            result_id="x",
            rule_id="R",
            rule_version="1",
            status=ResultStatus.WARNING,
            provenance=_prov(),
        )


def test_result_insufficient_data_requires_missing() -> None:
    with pytest.raises(ValidationError):
        EngineeringResult(
            result_id="x",
            rule_id="R",
            rule_version="1",
            status=ResultStatus.INSUFFICIENT_DATA,
            provenance=_prov(),
        )


def test_result_pass_rejects_violations_and_missing() -> None:
    with pytest.raises(ValidationError):
        EngineeringResult(
            result_id="x",
            rule_id="R",
            rule_version="1",
            status=ResultStatus.PASS,
            provenance=_prov(),
            violations=("boom",),
        )


# --------------------------------------------------------------------- #
# Serialization-friendly behavior
# --------------------------------------------------------------------- #
def test_part_as_dict_is_json_safe() -> None:
    document = json.dumps(_valid_part().as_dict())
    assert "P-1" in document
    assert "provenance" in document
    assert isinstance(json.loads(document), dict)


def test_quantity_serializes_decimal_to_str() -> None:
    feature = Feature(
        feature_id="F-1",
        part_id="P-1",
        feature_type=FeatureType.HOLE,
        provenance=_prov(),
        dimensions={"diameter": Quantity.of(10, "mm")},
    )
    rendered = feature.as_dict()
    assert rendered["dimensions"]["diameter"] == "10"