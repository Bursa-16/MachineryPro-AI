"""Stage 3I: DFM EngineeringRule wrapper tests."""

from __future__ import annotations

from backend.core.rules.base import EngineeringRule
from backend.dfm.rules import (
    AggregateFeasibilityRule,
    CornerRadiusToolRule,
    DepthDiameterRatioRule,
    HoleToolDiameterRule,
    MachineCapabilityCompositionRule,
    PocketAccessRule,
    ProcessFeatureCompatRule,
    SlotWidthToolRule,
    foundational_dfm_rules,
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
from backend.domain.tool import Tool
from backend.domain.units import Quantity, Unit
from backend.machines.validation import check_spindle_speed


def _prov() -> Provenance:
    return Provenance(source_type=ProvenanceType.USER_INPUT, source_reference="test")


def _hole(d: str = "10") -> Feature:
    return Feature(
        feature_id="F-H", part_id="P-1",
        feature_type=FeatureType.HOLE, provenance=_prov(),
        dimensions={"diameter": Quantity.of(d, Unit.MM)},
    )


def _drill(d: str = "10") -> Tool:
    return Tool(
        tool_id="T-D", tool_type=ToolType.DRILL,
        diameter=Quantity.of(d, Unit.MM), cutting_edge_count=2,
        provenance=_prov(), supported_operations=(OperationType.DRILLING,),
    )


def _machine() -> Machine:
    return Machine(
        machine_id="M-T", name="Test",
        machine_type=MachineType.MILL, axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of("10000", Unit.RPM),
        spindle_power=Quantity.of("15", Unit.KW),
        provenance=_prov(),
        supported_operations=(OperationType.MILLING,),
    )


class TestRuleIdentity:
    def test_rule_ids(self) -> None:
        assert HoleToolDiameterRule.rule_id == "R-2701"
        assert CornerRadiusToolRule.rule_id == "R-2702"
        assert SlotWidthToolRule.rule_id == "R-2703"
        assert PocketAccessRule.rule_id == "R-2704"
        assert ProcessFeatureCompatRule.rule_id == "R-2705"
        assert DepthDiameterRatioRule.rule_id == "R-2706"
        assert MachineCapabilityCompositionRule.rule_id == "R-2710"
        assert AggregateFeasibilityRule.rule_id == "R-2712"

    def test_all_are_engineering_rules(self) -> None:
        for rule in foundational_dfm_rules():
            assert isinstance(rule, EngineeringRule)

    def test_rule_ids_unique(self) -> None:
        ids = [r.rule_id for r in foundational_dfm_rules()]
        assert len(ids) == len(set(ids))

    def test_count(self) -> None:
        assert len(foundational_dfm_rules()) == 8


class TestMissingInputsFailClosed:
    def test_hole_tool_missing_feature(self) -> None:
        rule = HoleToolDiameterRule()
        result = rule.evaluate({"tool": _drill()})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_hole_tool_missing_tool(self) -> None:
        rule = HoleToolDiameterRule()
        result = rule.evaluate({"feature": _hole()})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_process_feature_missing_both(self) -> None:
        rule = ProcessFeatureCompatRule()
        result = rule.evaluate({})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_depth_ratio_missing_feature(self) -> None:
        rule = DepthDiameterRatioRule()
        result = rule.evaluate({})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_machine_composition_missing(self) -> None:
        rule = MachineCapabilityCompositionRule()
        result = rule.evaluate({})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_aggregate_missing_results(self) -> None:
        rule = AggregateFeasibilityRule()
        result = rule.evaluate({})
        assert result.status is ResultStatus.INSUFFICIENT_DATA


class TestRulesDelegateCorrectly:
    def test_hole_tool_pass(self) -> None:
        rule = HoleToolDiameterRule()
        result = rule.evaluate({"feature": _hole("10"), "tool": _drill("10")})
        assert result.status is ResultStatus.PASS

    def test_process_feature_pass(self) -> None:
        rule = ProcessFeatureCompatRule()
        result = rule.evaluate({
            "feature": _hole(),
            "operation_type": OperationType.DRILLING,
        })
        assert result.status is ResultStatus.PASS

    def test_depth_ratio_warning_no_limit(self) -> None:
        rule = DepthDiameterRatioRule()
        feat = Feature(
            feature_id="F-H", part_id="P-1",
            feature_type=FeatureType.HOLE, provenance=_prov(),
            dimensions={
                "diameter": Quantity.of("10", Unit.MM),
                "depth": Quantity.of("50", Unit.MM),
            },
        )
        result = rule.evaluate({"feature": feat})
        assert result.status is ResultStatus.WARNING

    def test_aggregate_pass(self) -> None:
        rule = AggregateFeasibilityRule()
        from backend.dfm.validation import (
            check_hole_tool_diameter,
            check_process_feature_compatibility,
        )
        r1 = check_hole_tool_diameter(_hole(), _drill())
        r2 = check_process_feature_compatibility(_hole(), OperationType.DRILLING)
        result = rule.evaluate({"results": [r1, r2]})
        assert result.status is ResultStatus.PASS

    def test_machine_composition_pass(self) -> None:
        rule = MachineCapabilityCompositionRule()
        m = _machine()
        machine_r = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        result = rule.evaluate({"machine_result": machine_r})
        assert result.status is ResultStatus.PASS
