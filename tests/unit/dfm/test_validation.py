"""Stage 3I: DFM / process-feasibility validation tests.

All feature dimensions, tool diameters, and machine specs used here are
synthetic test fixtures.  No production engineering recommendations.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from backend.dfm.validation import (
    aggregate_feasibility,
    check_corner_radius_tool,
    check_depth_diameter_ratio,
    check_hole_tool_diameter,
    check_pocket_access,
    check_process_feature_compatibility,
    check_slot_width_tool,
    compose_machine_result,
)
from backend.domain.base import Provenance
from backend.domain.enums import (
    FeatureType,
    MachineType,
    OperationType,
    ProvenanceType,
    ResultStatus,
    ToolType,
)
from backend.domain.feature import Feature
from backend.domain.machine import Machine
from backend.domain.result import EngineeringResult
from backend.domain.tool import Tool
from backend.domain.units import Quantity, Unit
from backend.machines.validation import check_spindle_speed

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.USER_INPUT,
        source_reference="test fixture",
    )


def _hole(d_mm: str, depth_mm: str | None = None, fid: str = "F-HOLE-001") -> Feature:
    dims: dict[str, Quantity] = {
        "diameter": Quantity.of(d_mm, Unit.MM),
    }
    if depth_mm is not None:
        dims["depth"] = Quantity.of(depth_mm, Unit.MM)
    return Feature(
        feature_id=fid,
        part_id="P-001",
        feature_type=FeatureType.HOLE,
        provenance=_prov(),
        dimensions=dims,
    )


def _pocket(
    opening_mm: str | None = None,
    depth_mm: str | None = None,
    corner_r_mm: str | None = None,
    fid: str = "F-POCKET-001",
) -> Feature:
    dims: dict[str, Quantity] = {}
    if opening_mm is not None:
        dims["opening_width"] = Quantity.of(opening_mm, Unit.MM)
    if depth_mm is not None:
        dims["depth"] = Quantity.of(depth_mm, Unit.MM)
    if corner_r_mm is not None:
        dims["corner_radius"] = Quantity.of(corner_r_mm, Unit.MM)
    return Feature(
        feature_id=fid,
        part_id="P-001",
        feature_type=FeatureType.POCKET,
        provenance=_prov(),
        dimensions=dims,
    )


def _slot(
    width_mm: str | None = None, depth_mm: str | None = None, fid: str = "F-SLOT-001"
) -> Feature:
    dims: dict[str, Quantity] = {}
    if width_mm is not None:
        dims["width"] = Quantity.of(width_mm, Unit.MM)
    if depth_mm is not None:
        dims["depth"] = Quantity.of(depth_mm, Unit.MM)
    return Feature(
        feature_id=fid,
        part_id="P-001",
        feature_type=FeatureType.SLOT,
        provenance=_prov(),
        dimensions=dims,
    )


def _drill(d_mm: str = "10", tid: str = "T-DRILL-001") -> Tool:
    return Tool(
        tool_id=tid,
        tool_type=ToolType.DRILL,
        diameter=Quantity.of(d_mm, Unit.MM),
        cutting_edge_count=2,
        provenance=_prov(),
        supported_operations=(OperationType.DRILLING,),
    )


def _endmill(d_mm: str = "10", tid: str = "T-MILL-001") -> Tool:
    return Tool(
        tool_id=tid,
        tool_type=ToolType.END_MILL,
        diameter=Quantity.of(d_mm, Unit.MM),
        cutting_edge_count=4,
        provenance=_prov(),
        supported_operations=(OperationType.MILLING,),
    )


def _machine(
    rpm_max: str = "10000",
    power_kw: str = "15",
    torque_nm: str | None = None,
    feed_max: str | None = None,
    mid: str = "M-001",
) -> Machine:
    return Machine(
        machine_id=mid,
        name="Test VMC",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of(rpm_max, Unit.RPM),
        spindle_power=Quantity.of(power_kw, Unit.KW),
        spindle_torque=Quantity.of(torque_nm, Unit.NM) if torque_nm else None,
        feed_rate_max=Quantity.of(feed_max, Unit.MM_MIN) if feed_max else None,
        provenance=_prov(),
        supported_operations=(OperationType.MILLING, OperationType.DRILLING),
    )


def _is_pass(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.PASS


def _is_fail(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.FAIL


def _is_insufficient(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.INSUFFICIENT_DATA


def _is_warning(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.WARNING


# ---------------------------------------------------------------------------
# A. R-2701 — Hole / tool diameter compatibility
# ---------------------------------------------------------------------------

class TestHoleToolDiameter:
    def test_exact_match_passes(self) -> None:
        result = check_hole_tool_diameter(_hole("10"), _drill("10"))
        assert _is_pass(result) and result.rule_id == "R-2701"

    def test_tool_smaller_fails(self) -> None:
        result = check_hole_tool_diameter(_hole("10"), _drill("8"))
        assert _is_fail(result)

    def test_tool_larger_fails(self) -> None:
        result = check_hole_tool_diameter(_hole("10"), _drill("12"))
        assert _is_fail(result)

    def test_missing_hole_diameter_insufficient(self) -> None:
        feat = Feature(
            feature_id="F-001", part_id="P-001",
            feature_type=FeatureType.HOLE, provenance=_prov(),
        )
        result = check_hole_tool_diameter(feat, _drill("10"))
        assert _is_insufficient(result)

    def test_wrong_feature_type_fails(self) -> None:
        slot = _slot("10")
        result = check_hole_tool_diameter(slot, _drill("10"))
        assert _is_fail(result)

    def test_decimal_preserved(self) -> None:
        result = check_hole_tool_diameter(_hole("12.5"), _drill("12.5"))
        assert _is_pass(result)
        assert result.outputs["hole_diameter"].value == Decimal("12.5")

    def test_outputs_present(self) -> None:
        result = check_hole_tool_diameter(_hole("10"), _drill("10"))
        assert "hole_diameter" in result.outputs
        assert "tool_diameter" in result.outputs

    def test_immutable_result(self) -> None:
        result = check_hole_tool_diameter(_hole("10"), _drill("10"))
        with pytest.raises((AttributeError, TypeError)):
            result.status = ResultStatus.FAIL  # type: ignore[misc]

    def test_deterministic(self) -> None:
        r1 = check_hole_tool_diameter(_hole("10"), _drill("10"))
        r2 = check_hole_tool_diameter(_hole("10"), _drill("10"))
        assert r1.status is r2.status and r1.summary == r2.summary

    def test_bool_rejected(self) -> None:
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            _hole_bad = Feature(
                feature_id="F-X", part_id="P-001",
                feature_type=FeatureType.HOLE, provenance=_prov(),
                dimensions={"diameter": Quantity.of(True, Unit.MM)},
            )

    def test_nan_rejected(self) -> None:
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            Feature(
                feature_id="F-X", part_id="P-001",
                feature_type=FeatureType.HOLE, provenance=_prov(),
                dimensions={"diameter": Quantity.of("nan", Unit.MM)},
            )

    def test_zero_diameter_rejected(self) -> None:
        """A zero-diameter hole is physically invalid."""
        # Quantity.of("0") succeeds; validation function must catch it
        feat = Feature(
            feature_id="F-X", part_id="P-001",
            feature_type=FeatureType.HOLE, provenance=_prov(),
            dimensions={"diameter": Quantity.of("0", Unit.MM)},
        )
        result = check_hole_tool_diameter(feat, _drill("10"))
        assert _is_fail(result)


# ---------------------------------------------------------------------------
# B. R-2702 — Internal corner radius vs milling tool radius
# ---------------------------------------------------------------------------

class TestCornerRadiusTool:
    def test_tool_radius_equal_to_corner_passes(self) -> None:
        # tool D=10 → radius=5; corner_radius=5 → exactly at limit
        feat = _pocket(corner_r_mm="5")
        result = check_corner_radius_tool(feat, _endmill("10"))
        assert _is_pass(result) and result.rule_id == "R-2702"

    def test_tool_radius_smaller_passes(self) -> None:
        feat = _pocket(corner_r_mm="8")
        result = check_corner_radius_tool(feat, _endmill("10"))  # radius=5, corner=8
        assert _is_pass(result)

    def test_tool_radius_larger_fails(self) -> None:
        feat = _pocket(corner_r_mm="3")
        result = check_corner_radius_tool(feat, _endmill("10"))  # radius=5 > corner=3
        assert _is_fail(result)

    def test_missing_corner_radius_insufficient(self) -> None:
        result = check_corner_radius_tool(_pocket(), _endmill("10"))
        assert _is_insufficient(result)

    def test_corner_clearance_in_outputs(self) -> None:
        feat = _pocket(corner_r_mm="8")
        result = check_corner_radius_tool(feat, _endmill("10"))
        assert _is_pass(result)
        assert "corner_clearance_mm" in result.outputs
        assert result.outputs["corner_clearance_mm"].value == Decimal("3")

    def test_tool_radius_computed_correctly(self) -> None:
        feat = _pocket(corner_r_mm="6")
        result = check_corner_radius_tool(feat, _endmill("12"))  # radius=6 == corner=6
        assert _is_pass(result)
        assert result.outputs["tool_radius"].value == Decimal("6")


# ---------------------------------------------------------------------------
# C. R-2703 — Slot width vs tool diameter
# ---------------------------------------------------------------------------

class TestSlotWidthTool:
    def test_tool_diameter_equal_passes(self) -> None:
        result = check_slot_width_tool(_slot("10"), _endmill("10"))
        assert _is_pass(result) and result.rule_id == "R-2703"

    def test_tool_smaller_passes(self) -> None:
        result = check_slot_width_tool(_slot("12"), _endmill("10"))
        assert _is_pass(result)

    def test_tool_larger_fails(self) -> None:
        result = check_slot_width_tool(_slot("8"), _endmill("10"))
        assert _is_fail(result)

    def test_missing_width_insufficient(self) -> None:
        result = check_slot_width_tool(_slot(), _endmill("10"))
        assert _is_insufficient(result)

    def test_wrong_feature_type_fails(self) -> None:
        result = check_slot_width_tool(_hole("10"), _endmill("10"))
        assert _is_fail(result)

    def test_margin_in_outputs(self) -> None:
        result = check_slot_width_tool(_slot("15"), _endmill("10"))
        assert _is_pass(result)
        assert "width_clearance_mm" in result.outputs
        assert result.outputs["width_clearance_mm"].value == Decimal("5")


# ---------------------------------------------------------------------------
# D. R-2704 — Pocket access
# ---------------------------------------------------------------------------

class TestPocketAccess:
    def test_tool_fits_passes(self) -> None:
        result = check_pocket_access(_pocket(opening_mm="20"), _endmill("10"))
        assert _is_pass(result) and result.rule_id == "R-2704"

    def test_tool_exactly_fits_passes(self) -> None:
        result = check_pocket_access(_pocket(opening_mm="10"), _endmill("10"))
        assert _is_pass(result)

    def test_tool_too_large_fails(self) -> None:
        result = check_pocket_access(_pocket(opening_mm="8"), _endmill("10"))
        assert _is_fail(result)

    def test_missing_opening_insufficient(self) -> None:
        result = check_pocket_access(_pocket(), _endmill("10"))
        assert _is_insufficient(result)

    def test_wrong_feature_type_fails(self) -> None:
        result = check_pocket_access(_slot("20"), _endmill("10"))
        assert _is_fail(result)

    def test_access_margin_in_outputs(self) -> None:
        result = check_pocket_access(_pocket(opening_mm="20"), _endmill("10"))
        assert _is_pass(result)
        assert "access_margin_mm" in result.outputs
        assert result.outputs["access_margin_mm"].value == Decimal("10")


# ---------------------------------------------------------------------------
# E. R-2705 — Process–feature compatibility
# ---------------------------------------------------------------------------

class TestProcessFeatureCompat:
    def test_drilling_hole_passes(self) -> None:
        result = check_process_feature_compatibility(
            _hole("10"), OperationType.DRILLING
        )
        assert _is_pass(result) and result.rule_id == "R-2705"

    def test_drilling_pocket_fails(self) -> None:
        result = check_process_feature_compatibility(
            _pocket(), OperationType.DRILLING
        )
        assert _is_fail(result)

    def test_milling_slot_passes(self) -> None:
        result = check_process_feature_compatibility(
            _slot("10"), OperationType.MILLING
        )
        assert _is_pass(result)

    def test_milling_hole_fails(self) -> None:
        result = check_process_feature_compatibility(
            _hole("10"), OperationType.MILLING
        )
        assert _is_fail(result)

    def test_reaming_hole_passes(self) -> None:
        result = check_process_feature_compatibility(
            _hole("10"), OperationType.REAMING
        )
        assert _is_pass(result)

    def test_tapping_hole_passes(self) -> None:
        result = check_process_feature_compatibility(
            _hole("10"), OperationType.TAPPING
        )
        assert _is_pass(result)

    def test_unknown_operation_insufficient(self) -> None:
        result = check_process_feature_compatibility(
            _hole("10"), OperationType.OTHER
        )
        assert _is_insufficient(result)

    def test_deterministic(self) -> None:
        r1 = check_process_feature_compatibility(_hole("10"), OperationType.DRILLING)
        r2 = check_process_feature_compatibility(_hole("10"), OperationType.DRILLING)
        assert r1.status is r2.status


# ---------------------------------------------------------------------------
# F. R-2706 — Depth / diameter ratio
# ---------------------------------------------------------------------------

class TestDepthDiameterRatio:
    def test_calculates_ratio_warning_without_limit(self) -> None:
        feat = _hole("10", depth_mm="50")
        result = check_depth_diameter_ratio(feat)
        assert _is_warning(result) and result.rule_id == "R-2706"
        assert "depth_diameter_ratio" in result.outputs
        assert result.outputs["depth_diameter_ratio"].value == Decimal("5.0000")

    def test_pass_with_explicit_limit_within(self) -> None:
        feat = _hole("10", depth_mm="30")  # ratio = 3
        result = check_depth_diameter_ratio(feat, explicit_limit=Decimal("5"))
        assert _is_pass(result)
        assert "ratio_margin" in result.outputs

    def test_fail_with_explicit_limit_exceeded(self) -> None:
        feat = _hole("10", depth_mm="60")  # ratio = 6
        result = check_depth_diameter_ratio(feat, explicit_limit=Decimal("5"))
        assert _is_fail(result)

    def test_at_exact_limit_passes(self) -> None:
        feat = _hole("10", depth_mm="50")  # ratio = 5
        result = check_depth_diameter_ratio(feat, explicit_limit=Decimal("5"))
        assert _is_pass(result)

    def test_missing_depth_insufficient(self) -> None:
        result = check_depth_diameter_ratio(_hole("10"))  # no depth
        assert _is_insufficient(result)

    def test_missing_both_insufficient(self) -> None:
        feat = Feature(
            feature_id="F-X", part_id="P-001",
            feature_type=FeatureType.HOLE, provenance=_prov(),
        )
        result = check_depth_diameter_ratio(feat)
        assert _is_insufficient(result)

    def test_uses_width_for_slot(self) -> None:
        feat = _slot(width_mm="8", depth_mm="40")  # ratio = 5
        result = check_depth_diameter_ratio(feat)
        assert _is_warning(result)
        assert result.outputs["depth_diameter_ratio"].value == Decimal("5.0000")

    def test_zero_limit_rejected(self) -> None:
        feat = _hole("10", depth_mm="30")
        result = check_depth_diameter_ratio(feat, explicit_limit=Decimal("0"))
        assert _is_fail(result)

    def test_no_arbitrary_threshold_without_limit(self) -> None:
        """Without explicit_limit, even extreme ratios are only WARNING."""
        feat = _hole("1", depth_mm="1000")  # ratio = 1000 — extreme
        result = check_depth_diameter_ratio(feat)
        assert _is_warning(result), "Without limit, must return WARNING not FAIL"


# ---------------------------------------------------------------------------
# G. R-2710 — Machine capability composition
# ---------------------------------------------------------------------------

class TestMachineCapabilityComposition:
    def test_pass_machine_result_gives_pass(self) -> None:
        m = _machine()
        machine_result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        result = compose_machine_result(machine_result)
        assert _is_pass(result) and result.rule_id == "R-2710"

    def test_fail_machine_result_gives_fail(self) -> None:
        m = _machine()
        machine_result = check_spindle_speed(m, Quantity.of("20000", Unit.RPM))
        result = compose_machine_result(machine_result)
        assert _is_fail(result)
        assert len(result.violations) > 0

    def test_insufficient_machine_result_gives_insufficient(self) -> None:
        from backend.machines.validation import check_torque
        m = _machine()  # no torque limit
        machine_result = check_torque(m, Quantity.of("50", Unit.NM))
        result = compose_machine_result(machine_result)
        assert _is_insufficient(result)

    def test_machine_outputs_preserved(self) -> None:
        m = _machine()
        machine_result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        result = compose_machine_result(machine_result)
        assert _is_pass(result)
        # Machine outputs should be propagated
        assert len(result.outputs) > 0


# ---------------------------------------------------------------------------
# H. R-2712 — Aggregate feasibility
# ---------------------------------------------------------------------------

class TestAggregateFeasibility:
    def test_all_pass_gives_pass(self) -> None:
        r1 = check_hole_tool_diameter(_hole("10"), _drill("10"))
        r2 = check_process_feature_compatibility(_hole("10"), OperationType.DRILLING)
        agg = aggregate_feasibility((r1, r2))
        assert _is_pass(agg) and agg.rule_id == "R-2712"

    def test_any_fail_gives_fail(self) -> None:
        r_pass = check_hole_tool_diameter(_hole("10"), _drill("10"))
        r_fail = check_hole_tool_diameter(_hole("10"), _drill("12"))
        agg = aggregate_feasibility((r_pass, r_fail))
        assert _is_fail(agg)

    def test_insufficient_without_fail_gives_insufficient(self) -> None:
        r_pass = check_hole_tool_diameter(_hole("10"), _drill("10"))
        r_insuf = check_depth_diameter_ratio(_hole("10"))  # missing depth
        agg = aggregate_feasibility((r_pass, r_insuf))
        assert _is_insufficient(agg)

    def test_fail_overrides_insufficient(self) -> None:
        r_fail = check_hole_tool_diameter(_hole("10"), _drill("8"))
        r_insuf = check_depth_diameter_ratio(_hole("10"))
        agg = aggregate_feasibility((r_fail, r_insuf))
        assert _is_fail(agg)

    def test_warning_without_fail_or_insufficient(self) -> None:
        r_pass = check_hole_tool_diameter(_hole("10"), _drill("10"))
        r_warn = check_depth_diameter_ratio(_hole("10", depth_mm="50"))
        agg = aggregate_feasibility((r_pass, r_warn))
        assert _is_warning(agg)

    def test_empty_results_insufficient(self) -> None:
        agg = aggregate_feasibility(())
        assert _is_insufficient(agg)

    def test_partial_info_cannot_pass(self) -> None:
        """Partial information must not produce PASS."""
        r_insuf = check_depth_diameter_ratio(_hole("10"))
        agg = aggregate_feasibility((r_insuf,))
        assert not _is_pass(agg)

    def test_violations_collected(self) -> None:
        r1 = check_hole_tool_diameter(_hole("10"), _drill("8"))
        r2 = check_slot_width_tool(_slot("5"), _endmill("10"))
        agg = aggregate_feasibility((r1, r2))
        assert _is_fail(agg)
        assert len(agg.violations) == 2

    def test_deterministic(self) -> None:
        results = (
            check_hole_tool_diameter(_hole("10"), _drill("10")),
            check_process_feature_compatibility(_hole("10"), OperationType.DRILLING),
        )
        a1 = aggregate_feasibility(results)
        a2 = aggregate_feasibility(results)
        assert a1.status is a2.status and a1.summary == a2.summary


# ---------------------------------------------------------------------------
# I. Cross-stage integration
# ---------------------------------------------------------------------------

class TestCrossStageIntegration:
    """Full deterministic workflow spanning Stages 3A, 3H, and 3I."""

    def test_full_workflow_pass(self) -> None:
        """
        1. Stage 3A: compute spindle speed from Vc and D.
        2. Stage 3H: validate RPM against machine limit.
        3. Stage 3I: check hole/tool diameter compatibility.
        4. Stage 3I: compose machine result.
        5. Stage 3I: aggregate feasibility → PASS.
        """
        from backend.machining.formulas import spindle_speed_from_cutting_speed

        m = _machine(rpm_max="10000")

        # Stage 3A
        n = spindle_speed_from_cutting_speed(
            Quantity.of("100", Unit.M_MIN),
            Quantity.of("10", Unit.MM),
        )
        # n ≈ 3183 rpm — within 10000 rpm

        # Stage 3H
        machine_r = check_spindle_speed(m, n)
        assert _is_pass(machine_r)

        # Stage 3I geometry
        hole_r = check_hole_tool_diameter(_hole("10"), _drill("10"))
        assert _is_pass(hole_r)

        proc_r = check_process_feature_compatibility(
            _hole("10"), OperationType.DRILLING
        )
        assert _is_pass(proc_r)

        machine_composed = compose_machine_result(machine_r)

        # Stage 3I aggregate
        agg = aggregate_feasibility((hole_r, proc_r, machine_composed))
        assert _is_pass(agg), (
            f"Expected aggregate PASS, got {agg.status}: {agg.violations}"
        )

    def test_full_workflow_machine_fail_propagates(self) -> None:
        """Machine failure propagates through composition to aggregate FAIL."""
        from backend.machining.formulas import spindle_speed_from_cutting_speed

        m = _machine(rpm_max="2000")  # tight limit

        # Stage 3A — computes n = ~3183 rpm > 2000
        n = spindle_speed_from_cutting_speed(
            Quantity.of("100", Unit.M_MIN),
            Quantity.of("10", Unit.MM),
        )

        # Stage 3H — should FAIL
        machine_r = check_spindle_speed(m, n)
        assert _is_fail(machine_r)

        # Geometry checks pass
        hole_r = check_hole_tool_diameter(_hole("10"), _drill("10"))
        proc_r = check_process_feature_compatibility(
            _hole("10"), OperationType.DRILLING
        )

        machine_composed = compose_machine_result(machine_r)

        agg = aggregate_feasibility((hole_r, proc_r, machine_composed))
        assert _is_fail(agg), "Machine FAIL must propagate to aggregate FAIL"

    def test_no_recommendation_made(self) -> None:
        """Validation returns PASS or FAIL — never recommends a tool or machine."""
        r1 = check_hole_tool_diameter(_hole("10"), _drill("8"))
        r2 = check_hole_tool_diameter(_hole("10"), _drill("12"))
        # Both fail — but the code does not select a better tool
        assert _is_fail(r1)
        assert _is_fail(r2)
        assert r1.rule_id == r2.rule_id == "R-2701"
