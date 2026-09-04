"""Stage 3H: machine capability validation function tests.

All machine specs used here are synthetic test fixtures.
No real OEM data is used.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import MachineType, OperationType, ProvenanceType, ResultStatus
from backend.domain.machine import Machine
from backend.domain.result import EngineeringResult
from backend.domain.units import Quantity, Unit
from backend.machines.validation import (
    check_feed_rate,
    check_power,
    check_spindle_speed,
    check_torque,
    check_work_envelope_dimension,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Test fixture — not production data",
    )


def _make_full_mill() -> Machine:
    """VMC with all optional limits populated."""
    return Machine(
        machine_id="VMC-001",
        name="Test VMC Full",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("100", Unit.RPM),
        spindle_speed_max=Quantity.of("10000", Unit.RPM),
        spindle_power=Quantity.of("15", Unit.KW),
        spindle_torque=Quantity.of("120", Unit.NM),
        feed_rate_max=Quantity.of("10000", Unit.MM_MIN),
        working_envelope={
            "X": Quantity.of("800", Unit.MM),
            "Y": Quantity.of("500", Unit.MM),
            "Z": Quantity.of("600", Unit.MM),
        },
        provenance=_prov(),
        supported_operations=(OperationType.MILLING, OperationType.DRILLING),
    )


def _make_minimal_mill() -> Machine:
    """VMC with only required fields — no optional limits."""
    return Machine(
        machine_id="VMC-MIN",
        name="Test VMC Minimal",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of("8000", Unit.RPM),
        spindle_power=Quantity.of("7.5", Unit.KW),
        provenance=_prov(),
        supported_operations=(OperationType.MILLING,),
    )


def _is_pass(result: EngineeringResult) -> bool:
    return result.status is ResultStatus.PASS


def _is_fail(result: EngineeringResult) -> bool:
    return result.status is ResultStatus.FAIL


def _is_insufficient(result: EngineeringResult) -> bool:
    return result.status is ResultStatus.INSUFFICIENT_DATA


# ---------------------------------------------------------------------------
# A. Spindle speed (R-2601)
# ---------------------------------------------------------------------------

class TestSpindleSpeedCheck:
    def test_within_range_passes(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        assert _is_pass(result)
        assert result.rule_id == "R-2601"

    def test_at_max_passes(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("10000", Unit.RPM))
        assert _is_pass(result)

    def test_at_min_passes(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("100", Unit.RPM))
        assert _is_pass(result)

    def test_above_max_fails(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("15000", Unit.RPM))
        assert _is_fail(result)
        assert any("10000" in v for v in result.violations)

    def test_below_min_fails(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("50", Unit.RPM))
        assert _is_fail(result)
        assert any("minimum" in v.lower() or "below" in v.lower() for v in result.violations)

    def test_wrong_unit_fails(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("5000", Unit.M_MIN))
        assert _is_fail(result)

    def test_zero_rpm_fails(self) -> None:
        """Zero RPM is physically invalid — validation must FAIL or raise."""
        m = _make_full_mill()
        from backend.domain.exceptions import ValidationError
        from backend.domain.units import UnitError
        try:
            result = check_spindle_speed(m, Quantity.of("0", Unit.RPM))
            # If construction succeeded, validation must produce FAIL
            assert _is_fail(result), f"Expected FAIL for 0 rpm, got {result.status}"
        except (UnitError, ValidationError):
            pass  # Rejection at Quantity level is also acceptable

    def test_margin_in_outputs(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("6000", Unit.RPM))
        assert _is_pass(result)
        assert "margin_rpm" in result.outputs
        assert result.outputs["margin_rpm"].value == Decimal("4000")

    def test_utilization_in_outputs(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        assert _is_pass(result)
        assert "utilization_ratio" in result.outputs
        assert result.outputs["utilization_ratio"].unit is Unit.DIMENSIONLESS

    def test_provenance_in_result(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        assert result.provenance is not None
        assert result.provenance.source_reference is not None

    def test_deterministic_repeatability(self) -> None:
        m = _make_full_mill()
        q = Quantity.of("7500", Unit.RPM)
        r1 = check_spindle_speed(m, q)
        r2 = check_spindle_speed(m, q)
        assert r1.status is r2.status
        assert r1.summary == r2.summary

    def test_result_immutable(self) -> None:
        m = _make_full_mill()
        result = check_spindle_speed(m, Quantity.of("5000", Unit.RPM))
        with pytest.raises((AttributeError, TypeError)):
            result.status = ResultStatus.FAIL  # type: ignore[misc]

    def test_bool_rejected(self) -> None:
        m = _make_full_mill()
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            check_spindle_speed(m, Quantity.of(True, Unit.RPM))

    def test_nan_rejected(self) -> None:
        m = _make_full_mill()
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            check_spindle_speed(m, Quantity.of("nan", Unit.RPM))

    def test_infinity_rejected(self) -> None:
        m = _make_full_mill()
        from backend.domain.units import UnitError
        with pytest.raises(UnitError):
            check_spindle_speed(m, Quantity.of("inf", Unit.RPM))


# ---------------------------------------------------------------------------
# B. Feed rate (R-2602)
# ---------------------------------------------------------------------------

class TestFeedRateCheck:
    def test_within_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_feed_rate(m, Quantity.of("5000", Unit.MM_MIN))
        assert _is_pass(result)
        assert result.rule_id == "R-2602"

    def test_at_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_feed_rate(m, Quantity.of("10000", Unit.MM_MIN))
        assert _is_pass(result)

    def test_above_limit_fails(self) -> None:
        m = _make_full_mill()
        result = check_feed_rate(m, Quantity.of("15000", Unit.MM_MIN))
        assert _is_fail(result)

    def test_missing_feed_limit_insufficient_data(self) -> None:
        """Machine without feed_rate_max → INSUFFICIENT_DATA (fail closed)."""
        m = _make_minimal_mill()
        result = check_feed_rate(m, Quantity.of("3000", Unit.MM_MIN))
        assert _is_insufficient(result)
        assert "feed_rate_max" in result.missing_inputs[0]

    def test_wrong_unit_fails(self) -> None:
        m = _make_full_mill()
        result = check_feed_rate(m, Quantity.of("5000", Unit.M_MIN))
        assert _is_fail(result)

    def test_margin_reported(self) -> None:
        m = _make_full_mill()
        result = check_feed_rate(m, Quantity.of("6000", Unit.MM_MIN))
        assert _is_pass(result)
        assert "margin_mm_min" in result.outputs
        assert result.outputs["margin_mm_min"].value == Decimal("4000")


# ---------------------------------------------------------------------------
# C. Power (R-2603)
# ---------------------------------------------------------------------------

class TestPowerCheck:
    def test_within_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("10", Unit.KW))
        assert _is_pass(result)
        assert result.rule_id == "R-2603"

    def test_at_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("15", Unit.KW))
        assert _is_pass(result)

    def test_above_limit_fails(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("20", Unit.KW))
        assert _is_fail(result)
        assert any("15" in v for v in result.violations)

    def test_power_always_known(self) -> None:
        """spindle_power is required on Machine — always present."""
        m = _make_minimal_mill()
        result = check_power(m, Quantity.of("5", Unit.KW))
        assert _is_pass(result)

    def test_wrong_unit_fails(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("10", Unit.NM))
        assert _is_fail(result)

    def test_no_efficiency_factor(self) -> None:
        """Power check must NOT apply any implicit efficiency derating."""
        m = _make_full_mill()
        # 15 kW at machine, requesting exactly 15 kW → PASS (no derating)
        result = check_power(m, Quantity.of("15", Unit.KW))
        assert _is_pass(result)

    def test_margin_reported(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("10", Unit.KW))
        assert _is_pass(result)
        assert "margin_kw" in result.outputs
        assert result.outputs["margin_kw"].value == Decimal("5")

    def test_decimal_preserved(self) -> None:
        m = _make_full_mill()
        result = check_power(m, Quantity.of("7.5", Unit.KW))
        assert _is_pass(result)
        assert result.outputs["required_power"].value == Decimal("7.5")


# ---------------------------------------------------------------------------
# D. Torque (R-2604)
# ---------------------------------------------------------------------------

class TestTorqueCheck:
    def test_within_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_torque(m, Quantity.of("80", Unit.NM))
        assert _is_pass(result)
        assert result.rule_id == "R-2604"

    def test_at_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_torque(m, Quantity.of("120", Unit.NM))
        assert _is_pass(result)

    def test_above_limit_fails(self) -> None:
        m = _make_full_mill()
        result = check_torque(m, Quantity.of("150", Unit.NM))
        assert _is_fail(result)

    def test_missing_torque_limit_insufficient_data(self) -> None:
        """Machine without spindle_torque → INSUFFICIENT_DATA (fail closed)."""
        m = _make_minimal_mill()
        result = check_torque(m, Quantity.of("50", Unit.NM))
        assert _is_insufficient(result)
        assert "spindle_torque" in result.missing_inputs[0]

    def test_wrong_unit_fails(self) -> None:
        m = _make_full_mill()
        result = check_torque(m, Quantity.of("80", Unit.KW))
        assert _is_fail(result)

    def test_margin_reported(self) -> None:
        m = _make_full_mill()
        result = check_torque(m, Quantity.of("70", Unit.NM))
        assert _is_pass(result)
        assert "margin_nm" in result.outputs
        assert result.outputs["margin_nm"].value == Decimal("50")


# ---------------------------------------------------------------------------
# E. Work envelope (R-2605)
# ---------------------------------------------------------------------------

class TestWorkEnvelopeCheck:
    def test_within_z_passes(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "Z", Quantity.of("400", Unit.MM)
        )
        assert _is_pass(result)
        assert result.rule_id == "R-2605"

    def test_at_z_limit_passes(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "Z", Quantity.of("600", Unit.MM)
        )
        assert _is_pass(result)

    def test_above_z_limit_fails(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "Z", Quantity.of("700", Unit.MM)
        )
        assert _is_fail(result)

    def test_missing_key_insufficient_data(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "W", Quantity.of("100", Unit.MM)
        )
        assert _is_insufficient(result)
        assert "W" in result.missing_inputs[0]

    def test_no_envelope_at_all_insufficient_data(self) -> None:
        m = _make_minimal_mill()  # no working_envelope
        result = check_work_envelope_dimension(
            m, "X", Quantity.of("300", Unit.MM)
        )
        assert _is_insufficient(result)

    def test_unit_mismatch_fails(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "X", Quantity.of("500", Unit.M_MIN)  # wrong unit
        )
        assert _is_fail(result)
        assert any("unit" in v.lower() for v in result.violations)

    def test_margin_reported(self) -> None:
        m = _make_full_mill()
        result = check_work_envelope_dimension(
            m, "X", Quantity.of("500", Unit.MM)
        )
        assert _is_pass(result)
        assert "margin_X" in result.outputs
        assert result.outputs["margin_X"].value == Decimal("300")

    def test_x_y_z_independent(self) -> None:
        m = _make_full_mill()
        rx = check_work_envelope_dimension(m, "X", Quantity.of("600", Unit.MM))
        ry = check_work_envelope_dimension(m, "Y", Quantity.of("400", Unit.MM))
        rz = check_work_envelope_dimension(m, "Z", Quantity.of("500", Unit.MM))
        assert _is_pass(rx) and _is_pass(ry) and _is_pass(rz)


# ---------------------------------------------------------------------------
# F. Cross-integration with Stage 3A formulas
# ---------------------------------------------------------------------------

class TestCrossIntegration:
    def test_spindle_speed_from_formula_then_validate(self) -> None:
        """Calculate n from Vc and D using Stage 3A formula, then validate."""
        from backend.machining.formulas import spindle_speed_from_cutting_speed

        m = _make_full_mill()
        # Vc=200 m/min, D=10mm → n ≈ 6366 rpm — within 10000 rpm limit
        n = spindle_speed_from_cutting_speed(
            Quantity.of("200", Unit.M_MIN),
            Quantity.of("10", Unit.MM),
        )
        result = check_spindle_speed(m, n)
        assert _is_pass(result), (
            f"Calculated RPM {n.value} should be within machine limit 10000 rpm"
        )

    def test_high_cutting_speed_exceeds_limit(self) -> None:
        """Very high Vc can produce an RPM beyond machine limit."""
        from backend.machining.formulas import spindle_speed_from_cutting_speed

        m = _make_full_mill()
        # Vc=800 m/min, D=10mm → n ≈ 25465 rpm — exceeds 10000 rpm
        n = spindle_speed_from_cutting_speed(
            Quantity.of("800", Unit.M_MIN),
            Quantity.of("10", Unit.MM),
        )
        result = check_spindle_speed(m, n)
        assert _is_fail(result), (
            f"Calculated RPM {n.value} should exceed machine limit 10000 rpm"
        )

    def test_feed_rate_from_formula_then_validate(self) -> None:
        """Calculate Vf from formulas, then validate against feed limit."""
        from backend.machining.formulas import (
            feed_rate_from_rpm_tooth_feed,
            spindle_speed_from_cutting_speed,
        )

        m = _make_full_mill()
        n = spindle_speed_from_cutting_speed(
            Quantity.of("150", Unit.M_MIN),
            Quantity.of("20", Unit.MM),
        )
        vf = feed_rate_from_rpm_tooth_feed(
            n,
            4,
            Quantity.of("0.1", Unit.MM_TOOTH),
        )
        result = check_feed_rate(m, vf)
        # n ≈ 2387 rpm; vf ≈ 955 mm/min — well within 10000 mm/min
        assert _is_pass(result)

    def test_no_recommendation_implicit(self) -> None:
        """Validation returns PASS or FAIL — no automatic selection or ranking."""
        m1 = _make_full_mill()
        m2 = Machine(
            machine_id="VMC-002",
            name="Larger VMC",
            machine_type=MachineType.MILL,
            axis_count=4,
            spindle_speed_min=Quantity.of("50", Unit.RPM),
            spindle_speed_max=Quantity.of("18000", Unit.RPM),
            spindle_power=Quantity.of("22", Unit.KW),
            provenance=_prov(),
            supported_operations=(OperationType.MILLING,),
        )
        q = Quantity.of("12000", Unit.RPM)
        r1 = check_spindle_speed(m1, q)
        r2 = check_spindle_speed(m2, q)
        # VMC-001 fails (max 10000), VMC-002 passes (max 18000)
        # The code returns separate results — never picks one
        assert _is_fail(r1)
        assert _is_pass(r2)
        # No automatic selection — both results are independent
        assert r1.rule_id == r2.rule_id == "R-2601"
