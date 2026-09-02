"""Stage 2 unit tests: deterministic rule framework (backend.core.rules).

Scope is deliberately limited to the *existing* rule contract:

  * rule registry duplicate-id rejection
  * unknown rule lookup
  * deterministic rule evaluation
  * missing required input -> INSUFFICIENT_DATA (fail closed)
  * positive-dimensions rule (R-1001)
  * spindle RPM range rule (R-1002)
  * tool-diameter range rule (R-1003)

No machining domain data is introduced here.
"""
from __future__ import annotations

import pytest

from backend.core.rules import (
    RuleRegistry,
    foundational_rules,
    missing_input_names,
)
from backend.core.rules.foundational import (
    PositiveDimensionalValueRule,
    RequiredInputCompletenessRule,
    SpindleRpmRangeRule,
    ToolDiameterRangeRule,
)
from backend.domain import Quantity, ResultStatus
from backend.domain.exceptions import (
    DuplicateRuleError,
    RuleNotFoundError,
)


# --------------------------------------------------------------------- #
# Registry behavior
# --------------------------------------------------------------------- #
def test_registry_can_hold_all_foundational_rules() -> None:
    registry = RuleRegistry()
    for rule in foundational_rules():
        registry.register(rule)
    assert len(registry) == 4
    assert "R-1001" in registry
    assert "R-1002" in registry


def test_registry_get_returns_registered_rule() -> None:
    registry = RuleRegistry()
    rule = SpindleRpmRangeRule()
    registry.register(rule)
    assert registry.get("R-1002") is rule


def test_registry_rejects_duplicate_rule_id() -> None:
    registry = RuleRegistry()
    registry.register(PositiveDimensionalValueRule())
    with pytest.raises(DuplicateRuleError):
        registry.register(PositiveDimensionalValueRule())  # same R-1001 id


def test_registry_unknown_lookup_raises() -> None:
    registry = RuleRegistry()
    with pytest.raises(RuleNotFoundError):
        registry.get("R-9999")


# --------------------------------------------------------------------- #
# Fail-closed: missing input -> INSUFFICIENT_DATA (never silently PASS)
# --------------------------------------------------------------------- #
def test_missing_input_names_reports_absent_and_none() -> None:
    rule = PositiveDimensionalValueRule()
    assert missing_input_names(rule, {}) == ("value",)
    assert missing_input_names(rule, {"value": None}) == ("value",)


def test_missing_required_input_is_insufficient_data() -> None:
    rule = PositiveDimensionalValueRule()
    result = rule.evaluate({})
    assert result.status is ResultStatus.INSUFFICIENT_DATA
    assert result.missing_inputs == ("value",)


# --------------------------------------------------------------------- #
# Deterministic evaluation
# --------------------------------------------------------------------- #
def test_positive_dimension_rule_pass() -> None:
    rule = PositiveDimensionalValueRule()
    result = rule.evaluate({"value": Quantity.of(10, "mm")})
    assert result.status is ResultStatus.PASS
    assert result.outputs["value"] == Quantity.of(10, "mm")


def test_positive_dimension_rule_zero_rejected() -> None:
    rule = PositiveDimensionalValueRule()
    result = rule.evaluate({"value": Quantity.of(0, "mm")})
    assert result.status is ResultStatus.FAIL


def test_positive_dimension_rule_non_quantity_rejected() -> None:
    rule = PositiveDimensionalValueRule()
    result = rule.evaluate({"value": 10})  # bare int is not a Quantity
    assert result.status is ResultStatus.FAIL


def test_spindle_rpm_range_rule_pass() -> None:
    rule = SpindleRpmRangeRule()
    result = rule.evaluate(
        {
            "spindle_speed": Quantity.of(5000, "rpm"),
            "speed_min": Quantity.of(50, "rpm"),
            "speed_max": Quantity.of(15000, "rpm"),
        }
    )
    assert result.status is ResultStatus.PASS
    assert result.outputs["spindle_speed"] == Quantity.of(5000, "rpm")


def test_spindle_rpm_range_rule_outside_range_fails() -> None:
    rule = SpindleRpmRangeRule()
    result = rule.evaluate(
        {
            "spindle_speed": Quantity.of(20000, "rpm"),
            "speed_min": Quantity.of(50, "rpm"),
            "speed_max": Quantity.of(15000, "rpm"),
        }
    )
    assert result.status is ResultStatus.FAIL


def test_spindle_rpm_range_rule_unit_mismatch_fails() -> None:
    rule = SpindleRpmRangeRule()
    result = rule.evaluate(
        {
            "spindle_speed": Quantity.of(5000, "rpm"),
            "speed_min": Quantity.of(50, "rpm"),
            "speed_max": Quantity.of(0.015, "m/min"),  # wrong unit
        }
    )
    assert result.status is ResultStatus.FAIL


def test_spindle_rpm_range_rule_inverted_range_fails() -> None:
    rule = SpindleRpmRangeRule()
    result = rule.evaluate(
        {
            "spindle_speed": Quantity.of(1000, "rpm"),
            "speed_min": Quantity.of(15000, "rpm"),
            "speed_max": Quantity.of(50, "rpm"),  # min > max
        }
    )
    assert result.status is ResultStatus.FAIL


def test_tool_diameter_range_rule_pass() -> None:
    rule = ToolDiameterRangeRule()
    result = rule.evaluate(
        {
            "tool_diameter": Quantity.of(10, "mm"),
            "diameter_min": Quantity.of(6, "mm"),
            "diameter_max": Quantity.of(12, "mm"),
        }
    )
    assert result.status is ResultStatus.PASS
    assert result.outputs["tool_diameter"] == Quantity.of(10, "mm")


def test_tool_diameter_range_rule_exceeds_max_fails() -> None:
    rule = ToolDiameterRangeRule()
    result = rule.evaluate(
        {
            "tool_diameter": Quantity.of(20, "mm"),
            "diameter_min": Quantity.of(6, "mm"),
            "diameter_max": Quantity.of(12, "mm"),
        }
    )
    assert result.status is ResultStatus.FAIL


def test_required_input_completeness_rule_pass() -> None:
    rule = RequiredInputCompletenessRule()
    result = rule.evaluate(
        {
            "expected": ("speed_min", "speed_max"),
            "speed_min": Quantity.of(50, "rpm"),
            "speed_max": Quantity.of(15000, "rpm"),
        }
    )
    assert result.status is ResultStatus.PASS
