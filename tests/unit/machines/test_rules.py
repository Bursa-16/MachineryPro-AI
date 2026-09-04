"""Stage 3H: EngineeringRule wrapper tests (R-2601 – R-2605).

Verifies that the rule wrappers honour the EngineeringRule contract:
- missing inputs → INSUFFICIENT_DATA (fail closed)
- valid inputs → delegate to validation functions
- rule IDs are correct and unique
"""

from __future__ import annotations

from backend.core.rules.base import EngineeringRule
from backend.domain.base import Provenance
from backend.domain.enums import MachineType, OperationType, ProvenanceType, ResultStatus
from backend.domain.machine import Machine
from backend.domain.units import Quantity, Unit
from backend.machines.rules import (
    FeedRateCapabilityRule,
    PowerCapabilityRule,
    SpindleSpeedCapabilityRule,
    TorqueCapabilityRule,
    WorkEnvelopeCapabilityRule,
    foundational_machine_rules,
)


def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Test fixture — not production data",
    )


def _make_full_mill() -> Machine:
    return Machine(
        machine_id="RULE-TEST-001",
        name="Rule Test VMC",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of("10000", Unit.RPM),
        spindle_power=Quantity.of("15", Unit.KW),
        spindle_torque=Quantity.of("100", Unit.NM),
        feed_rate_max=Quantity.of("8000", Unit.MM_MIN),
        working_envelope={
            "Z": Quantity.of("500", Unit.MM),
        },
        provenance=_prov(),
        supported_operations=(OperationType.MILLING,),
    )


class TestRuleIdentity:
    def test_rule_ids_correct(self) -> None:
        assert SpindleSpeedCapabilityRule.rule_id == "R-2601"
        assert FeedRateCapabilityRule.rule_id == "R-2602"
        assert PowerCapabilityRule.rule_id == "R-2603"
        assert TorqueCapabilityRule.rule_id == "R-2604"
        assert WorkEnvelopeCapabilityRule.rule_id == "R-2605"

    def test_all_are_engineering_rules(self) -> None:
        for rule_cls in (
            SpindleSpeedCapabilityRule,
            FeedRateCapabilityRule,
            PowerCapabilityRule,
            TorqueCapabilityRule,
            WorkEnvelopeCapabilityRule,
        ):
            assert issubclass(rule_cls, EngineeringRule)

    def test_rule_ids_unique(self) -> None:
        rules = foundational_machine_rules()
        ids = [r.rule_id for r in rules]
        assert len(ids) == len(set(ids))

    def test_foundational_machine_rules_count(self) -> None:
        assert len(foundational_machine_rules()) == 5


class TestMissingInputsFailClosed:
    """Missing any required input → INSUFFICIENT_DATA."""

    def test_spindle_missing_machine(self) -> None:
        rule = SpindleSpeedCapabilityRule()
        result = rule.evaluate({"requested_rpm": Quantity.of("5000", Unit.RPM)})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_spindle_missing_rpm(self) -> None:
        rule = SpindleSpeedCapabilityRule()
        result = rule.evaluate({"machine": _make_full_mill()})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_feed_missing_machine(self) -> None:
        rule = FeedRateCapabilityRule()
        result = rule.evaluate({"requested_feed_rate": Quantity.of("3000", Unit.MM_MIN)})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_power_missing_required_power(self) -> None:
        rule = PowerCapabilityRule()
        result = rule.evaluate({"machine": _make_full_mill()})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_torque_missing_machine(self) -> None:
        rule = TorqueCapabilityRule()
        result = rule.evaluate({"required_torque": Quantity.of("50", Unit.NM)})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_envelope_missing_all(self) -> None:
        rule = WorkEnvelopeCapabilityRule()
        result = rule.evaluate({})
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_envelope_missing_dimension_key(self) -> None:
        rule = WorkEnvelopeCapabilityRule()
        result = rule.evaluate({
            "machine": _make_full_mill(),
            "requested_value": Quantity.of("200", Unit.MM),
        })
        assert result.status is ResultStatus.INSUFFICIENT_DATA


class TestRulesDelegate:
    """Rule wrappers return the same results as the raw validation functions."""

    def test_spindle_pass(self) -> None:
        rule = SpindleSpeedCapabilityRule()
        m = _make_full_mill()
        result = rule.evaluate({
            "machine": m,
            "requested_rpm": Quantity.of("5000", Unit.RPM),
        })
        assert result.status is ResultStatus.PASS
        assert result.rule_id == "R-2601"

    def test_spindle_fail(self) -> None:
        rule = SpindleSpeedCapabilityRule()
        m = _make_full_mill()
        result = rule.evaluate({
            "machine": m,
            "requested_rpm": Quantity.of("20000", Unit.RPM),
        })
        assert result.status is ResultStatus.FAIL

    def test_power_pass(self) -> None:
        rule = PowerCapabilityRule()
        result = rule.evaluate({
            "machine": _make_full_mill(),
            "required_power": Quantity.of("10", Unit.KW),
        })
        assert result.status is ResultStatus.PASS
        assert result.rule_id == "R-2603"

    def test_torque_insufficient_when_none(self) -> None:
        from backend.domain.machine import Machine
        minimal = Machine(
            machine_id="MINIMAL",
            name="Minimal",
            machine_type=MachineType.MILL,
            axis_count=3,
            spindle_speed_min=Quantity.of("50", Unit.RPM),
            spindle_speed_max=Quantity.of("8000", Unit.RPM),
            spindle_power=Quantity.of("7.5", Unit.KW),
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )
        rule = TorqueCapabilityRule()
        result = rule.evaluate({
            "machine": minimal,
            "required_torque": Quantity.of("50", Unit.NM),
        })
        assert result.status is ResultStatus.INSUFFICIENT_DATA

    def test_envelope_pass(self) -> None:
        rule = WorkEnvelopeCapabilityRule()
        result = rule.evaluate({
            "machine": _make_full_mill(),
            "dimension_key": "Z",
            "requested_value": Quantity.of("300", Unit.MM),
        })
        assert result.status is ResultStatus.PASS
        assert result.rule_id == "R-2605"

    def test_envelope_insufficient_missing_key(self) -> None:
        rule = WorkEnvelopeCapabilityRule()
        result = rule.evaluate({
            "machine": _make_full_mill(),
            "dimension_key": "W",  # not in envelope
            "requested_value": Quantity.of("100", Unit.MM),
        })
        assert result.status is ResultStatus.INSUFFICIENT_DATA


class TestRuleProvenance:
    def test_result_carries_provenance(self) -> None:
        rule = SpindleSpeedCapabilityRule()
        result = rule.evaluate({
            "machine": _make_full_mill(),
            "requested_rpm": Quantity.of("5000", Unit.RPM),
        })
        assert result.provenance is not None
        assert result.provenance.source_reference is not None
