"""Stage 3J: process-plan validation tests.

Includes a full cross-stage synthetic workflow (Stage 3A → 3H → 3I → 3J).
All fixtures are synthetic test data — no production routing data.
"""

from __future__ import annotations

from backend.cutting_parameters.models import (
    ApplicabilityScope,
    CuttingParameterRecord,
    EvidenceStatus,
    ParameterType,
    QuantityRange,
)
from backend.domain.base import Provenance
from backend.domain.enums import (
    FeatureType,
    IsoMaterialGroup,
    MachineType,
    OperationType,
    ProvenanceType,
    ResultStatus,
    ToolMaterial,
    ToolType,
)
from backend.domain.feature import Feature
from backend.domain.machine import Machine
from backend.domain.result import EngineeringResult
from backend.domain.tool import Tool
from backend.domain.units import Quantity, Unit
from backend.process_planning.models import PlanStatus, ProcessPlanStep
from backend.process_planning.validation import (
    aggregate_plan_status,
    aggregate_step_status,
    validate_acyclic,
    validate_predecessors,
    validate_sequence_indexes,
    validate_step_completeness,
    validate_step_dfm,
    validate_step_empirical_records,
    validate_step_ids,
    validate_step_machine_capability,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.USER_INPUT, source_reference="test fixture"
    )


def _mfr_prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Fixture catalogue §1",
    )


def _step(
    step_id: str = "S-001",
    sequence_index: int = 0,
    **kwargs,
) -> ProcessPlanStep:
    defaults = dict(step_id=step_id, sequence_index=sequence_index)
    defaults.update(kwargs)
    return ProcessPlanStep(**defaults)


def _hole_feature(d_mm: str = "10") -> Feature:
    return Feature(
        feature_id="F-H",
        part_id="P-1",
        feature_type=FeatureType.HOLE,
        provenance=_prov(),
        dimensions={"diameter": Quantity.of(d_mm, Unit.MM)},
    )


def _drill(d_mm: str = "10") -> Tool:
    return Tool(
        tool_id="T-DRILL",
        tool_type=ToolType.DRILL,
        diameter=Quantity.of(d_mm, Unit.MM),
        cutting_edge_count=2,
        provenance=_prov(),
        supported_operations=(OperationType.DRILLING,),
    )


def _machine(rpm_max: str = "10000") -> Machine:
    return Machine(
        machine_id="M-001",
        name="Test VMC",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of(rpm_max, Unit.RPM),
        spindle_power=Quantity.of("15", Unit.KW),
        feed_rate_max=Quantity.of("8000", Unit.MM_MIN),
        provenance=_prov(),
        supported_operations=(OperationType.MILLING, OperationType.DRILLING),
    )


def _auth_vc_record() -> CuttingParameterRecord:
    return CuttingParameterRecord(
        record_id="CP-VC-001",
        parameter_type=ParameterType.CUTTING_SPEED,
        value_range=QuantityRange(
            min_value=Quantity.of("80", Unit.M_MIN),
            max_value=Quantity.of("120", Unit.M_MIN),
        ),
        applicability=ApplicabilityScope(
            operation_type=OperationType.DRILLING,
            iso_material_group=IsoMaterialGroup.P,
            tool_material=ToolMaterial.CARBIDE,
        ),
        provenance=_mfr_prov(),
        evidence_status=EvidenceStatus.AUTHORITATIVE,
    )


def _unver_record() -> CuttingParameterRecord:
    return CuttingParameterRecord(
        record_id="CP-UNVER-001",
        parameter_type=ParameterType.CUTTING_SPEED,
        value_range=QuantityRange(
            min_value=Quantity.of("50", Unit.M_MIN),
            max_value=Quantity.of("80", Unit.M_MIN),
        ),
        applicability=ApplicabilityScope(),
        provenance=Provenance(
            source_type=ProvenanceType.UNKNOWN, source_reference=None
        ),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )


def _is_pass(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.PASS


def _is_fail(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.FAIL


def _is_insuf(r: EngineeringResult) -> bool:
    return r.status is ResultStatus.INSUFFICIENT_DATA


# ---------------------------------------------------------------------------
# A. R-2801 — Step ID uniqueness
# ---------------------------------------------------------------------------

class TestStepIds:
    def test_unique_ids_pass(self) -> None:
        steps = (_step("S-001", 0), _step("S-002", 1))
        result = validate_step_ids(steps)
        assert _is_pass(result) and result.rule_id == "R-2801"

    def test_duplicate_ids_fail(self) -> None:
        steps = (_step("S-001", 0), _step("S-001", 1))
        result = validate_step_ids(steps)
        assert _is_fail(result)
        assert any("S-001" in v for v in result.violations)

    def test_empty_steps_pass(self) -> None:
        result = validate_step_ids(())
        assert _is_pass(result)


# ---------------------------------------------------------------------------
# B. R-2802 — Sequence index uniqueness
# ---------------------------------------------------------------------------

class TestSequenceIndexes:
    def test_unique_indexes_pass(self) -> None:
        steps = (_step("S-001", 0), _step("S-002", 1))
        result = validate_sequence_indexes(steps)
        assert _is_pass(result) and result.rule_id == "R-2802"

    def test_duplicate_indexes_fail(self) -> None:
        steps = (_step("S-001", 0), _step("S-002", 0))
        result = validate_sequence_indexes(steps)
        assert _is_fail(result)


# ---------------------------------------------------------------------------
# C. R-2803 — Predecessor existence
# ---------------------------------------------------------------------------

class TestPredecessors:
    def test_valid_predecessors_pass(self) -> None:
        s1 = _step("S-001", 0)
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("S-001",))
        result = validate_predecessors((s1, s2))
        assert _is_pass(result) and result.rule_id == "R-2803"

    def test_missing_predecessor_fails(self) -> None:
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("GHOST",))
        result = validate_predecessors((s2,))
        assert _is_fail(result)

    def test_self_predecessor_fails(self) -> None:
        s = ProcessPlanStep(step_id="S-001", sequence_index=0,
                            predecessor_step_ids=("S-001",))
        result = validate_predecessors((s,))
        assert _is_fail(result)


# ---------------------------------------------------------------------------
# D. R-2804 — Acyclic dependency
# ---------------------------------------------------------------------------

class TestAcyclic:
    def test_no_deps_acyclic(self) -> None:
        result = validate_acyclic((_step("S-001", 0), _step("S-002", 1)))
        assert _is_pass(result) and result.rule_id == "R-2804"

    def test_linear_chain_acyclic(self) -> None:
        s1 = _step("S-001", 0)
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("S-001",))
        result = validate_acyclic((s1, s2))
        assert _is_pass(result)

    def test_cycle_detected(self) -> None:
        s1 = ProcessPlanStep(step_id="S-001", sequence_index=0,
                             predecessor_step_ids=("S-002",))
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("S-001",))
        result = validate_acyclic((s1, s2))
        assert _is_fail(result)

    def test_three_node_cycle(self) -> None:
        s1 = ProcessPlanStep(step_id="S-001", sequence_index=0,
                             predecessor_step_ids=("S-003",))
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("S-001",))
        s3 = ProcessPlanStep(step_id="S-003", sequence_index=2,
                             predecessor_step_ids=("S-002",))
        result = validate_acyclic((s1, s2, s3))
        assert _is_fail(result)

    def test_empty_plan_acyclic(self) -> None:
        result = validate_acyclic(())
        assert _is_pass(result)


# ---------------------------------------------------------------------------
# E. R-2805 — Step completeness
# ---------------------------------------------------------------------------

class TestStepCompleteness:
    def test_complete_step_passes(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            feature_id="F-001", operation_type=OperationType.DRILLING,
            tool_id="T-001", machine_id="M-001",
        )
        result = validate_step_completeness(step)
        assert _is_pass(result) and result.rule_id == "R-2805"

    def test_missing_feature_incomplete(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            operation_type=OperationType.DRILLING,
            tool_id="T-001", machine_id="M-001",
        )
        result = validate_step_completeness(step)
        assert _is_insuf(result)
        assert "feature_id" in result.missing_inputs[0]

    def test_missing_operation_incomplete(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            feature_id="F-001", tool_id="T-001", machine_id="M-001",
        )
        result = validate_step_completeness(step)
        assert _is_insuf(result)

    def test_missing_tool_incomplete(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            feature_id="F-001", operation_type=OperationType.DRILLING,
            machine_id="M-001",
        )
        result = validate_step_completeness(step)
        assert _is_insuf(result)

    def test_missing_machine_incomplete(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            feature_id="F-001", operation_type=OperationType.DRILLING,
            tool_id="T-001",
        )
        result = validate_step_completeness(step)
        assert _is_insuf(result)

    def test_tool_not_required(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            feature_id="F-001", operation_type=OperationType.DRILLING,
            machine_id="M-001",
        )
        result = validate_step_completeness(step, require_tool=False)
        assert _is_pass(result)


# ---------------------------------------------------------------------------
# F. R-2806 — DFM validation
# ---------------------------------------------------------------------------

class TestStepDfm:
    def test_matching_hole_drill_passes(self) -> None:
        step = _step(operation_type=OperationType.DRILLING)
        result = validate_step_dfm(step, _hole_feature("10"), _drill("10"))
        assert _is_pass(result) and result.rule_id == "R-2806"

    def test_mismatched_drill_fails(self) -> None:
        step = _step(operation_type=OperationType.DRILLING)
        result = validate_step_dfm(step, _hole_feature("10"), _drill("12"))
        assert _is_fail(result)

    def test_wrong_process_fails(self) -> None:
        step = _step(operation_type=OperationType.MILLING)
        result = validate_step_dfm(step, _hole_feature("10"), _drill("10"))
        assert _is_fail(result)


# ---------------------------------------------------------------------------
# G. R-2807 — Machine capability validation
# ---------------------------------------------------------------------------

class TestStepMachineCapability:
    def test_rpm_within_limit_passes(self) -> None:
        step = _step()
        m = _machine("10000")
        result = validate_step_machine_capability(
            step, m, requested_rpm=Quantity.of("5000", Unit.RPM)
        )
        assert _is_pass(result) and result.rule_id == "R-2807"

    def test_rpm_exceeds_limit_fails(self) -> None:
        step = _step()
        m = _machine("2000")
        result = validate_step_machine_capability(
            step, m, requested_rpm=Quantity.of("5000", Unit.RPM)
        )
        assert _is_fail(result)

    def test_no_inputs_insufficient(self) -> None:
        step = _step()
        m = _machine()
        result = validate_step_machine_capability(step, m)
        assert _is_insuf(result)

    def test_feed_rate_passes(self) -> None:
        step = _step()
        m = _machine()
        result = validate_step_machine_capability(
            step, m,
            requested_feed_rate=Quantity.of("3000", Unit.MM_MIN),
        )
        assert _is_pass(result)

    def test_power_passes(self) -> None:
        step = _step()
        m = _machine()
        result = validate_step_machine_capability(
            step, m, required_power=Quantity.of("10", Unit.KW)
        )
        assert _is_pass(result)


# ---------------------------------------------------------------------------
# H. R-2808 — Empirical record authority
# ---------------------------------------------------------------------------

class TestStepEmpiricalRecords:
    def test_authoritative_record_passes(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            parameter_record_ids=("CP-VC-001",),
        )
        result = validate_step_empirical_records(step, (_auth_vc_record(),))
        assert _is_pass(result) and result.rule_id == "R-2808"

    def test_unverified_record_incomplete(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            parameter_record_ids=("CP-UNVER-001",),
        )
        result = validate_step_empirical_records(step, (_unver_record(),))
        assert _is_insuf(result)

    def test_records_referenced_but_not_supplied(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            parameter_record_ids=("CP-VC-001",),
        )
        result = validate_step_empirical_records(step, ())
        assert _is_insuf(result)

    def test_no_records_required_no_records_passes(self) -> None:
        step = _step()
        result = validate_step_empirical_records(step, ())
        assert _is_pass(result)


# ---------------------------------------------------------------------------
# I. Aggregate step status
# ---------------------------------------------------------------------------

class TestAggregateStepStatus:
    def test_all_pass_gives_validated(self) -> None:
        from backend.domain.result import success
        r1 = success(result_id="r1", rule_id="R-2801", rule_version="1.0.0",
                     summary="ok")
        r2 = success(result_id="r2", rule_id="R-2802", rule_version="1.0.0",
                     summary="ok")
        assert aggregate_step_status((r1, r2)) is PlanStatus.VALIDATED

    def test_any_fail_gives_invalid(self) -> None:
        from backend.domain.result import failure, success
        r_pass = success(result_id="r1", rule_id="R-2801", rule_version="1.0.0",
                         summary="ok")
        r_fail = failure(result_id="r2", rule_id="R-2802", rule_version="1.0.0",
                         violations=("bad",))
        assert aggregate_step_status((r_pass, r_fail)) is PlanStatus.INVALID

    def test_insufficient_gives_incomplete(self) -> None:
        from backend.domain.result import insufficient_data, success
        r_pass = success(result_id="r1", rule_id="R-2801", rule_version="1.0.0",
                         summary="ok")
        r_ins = insufficient_data(result_id="r2", rule_id="R-2805",
                                  rule_version="1.0.0", missing_inputs=("x",))
        assert aggregate_step_status((r_pass, r_ins)) is PlanStatus.INCOMPLETE

    def test_fail_overrides_incomplete(self) -> None:
        from backend.domain.result import failure, insufficient_data
        r_fail = failure(result_id="r1", rule_id="R-2801", rule_version="1.0.0",
                         violations=("bad",))
        r_ins = insufficient_data(result_id="r2", rule_id="R-2805",
                                  rule_version="1.0.0", missing_inputs=("x",))
        assert aggregate_step_status((r_fail, r_ins)) is PlanStatus.INVALID


# ---------------------------------------------------------------------------
# J. R-2810 — Aggregate plan status
# ---------------------------------------------------------------------------

class TestAggregatePlanStatus:
    def test_all_validated_gives_validated(self) -> None:
        s = ProcessPlanStep(step_id="S-001", sequence_index=0,
                            engineering_status=PlanStatus.VALIDATED)
        status, result = aggregate_plan_status((s,))
        assert status is PlanStatus.VALIDATED and _is_pass(result)

    def test_any_invalid_gives_invalid(self) -> None:
        s1 = ProcessPlanStep(step_id="S-001", sequence_index=0,
                             engineering_status=PlanStatus.VALIDATED)
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             engineering_status=PlanStatus.INVALID)
        status, result = aggregate_plan_status((s1, s2))
        assert status is PlanStatus.INVALID and _is_fail(result)

    def test_incomplete_without_invalid(self) -> None:
        s1 = ProcessPlanStep(step_id="S-001", sequence_index=0,
                             engineering_status=PlanStatus.VALIDATED)
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             engineering_status=PlanStatus.INCOMPLETE)
        status, result = aggregate_plan_status((s1, s2))
        assert status is PlanStatus.INCOMPLETE and _is_insuf(result)

    def test_empty_plan_incomplete(self) -> None:
        status, _ = aggregate_plan_status(())
        assert status is PlanStatus.INCOMPLETE

    def test_partial_data_cannot_validate(self) -> None:
        s = ProcessPlanStep(step_id="S-001", sequence_index=0,
                            engineering_status=PlanStatus.INCOMPLETE)
        status, _ = aggregate_plan_status((s,))
        assert status is not PlanStatus.VALIDATED


# ---------------------------------------------------------------------------
# K. Full cross-stage synthetic workflow (3A → 3H → 3I → 3J)
# ---------------------------------------------------------------------------

class TestCrossStageWorkflow:
    """
    Synthetic workflow:
    1. Stage 3A: compute RPM from Vc and D
    2. Stage 3H: validate RPM against machine
    3. Stage 3I: validate tool/feature geometry and process compatibility
    4. Stage 3J: compose step, validate empirical records, determine status

    No AI involved.  All decisions are explicit.
    """

    def _setup(self):
        """Create all domain objects needed for the workflow."""
        from backend.machining.formulas import spindle_speed_from_cutting_speed

        feature = _hole_feature("10")
        tool = _drill("10")
        machine = _machine("10000")

        vc_record = _auth_vc_record()

        # Stage 3A: compute RPM (Vc = 100 m/min, D = 10 mm → n ≈ 3183 rpm)
        n = spindle_speed_from_cutting_speed(
            Quantity.of("100", Unit.M_MIN),
            Quantity.of("10", Unit.MM),
        )

        return feature, tool, machine, vc_record, n

    def test_full_workflow_validated(self) -> None:
        feature, tool, machine, vc_record, n = self._setup()

        step = ProcessPlanStep(
            step_id="S-DRILL-001",
            sequence_index=0,
            feature_id=feature.feature_id,
            operation_type=OperationType.DRILLING,
            tool_id=tool.tool_id,
            machine_id=machine.machine_id,
            parameter_record_ids=(vc_record.record_id,),
        )

        # R-2805 completeness
        r_complete = validate_step_completeness(step)
        assert _is_pass(r_complete)

        # R-2806 DFM
        r_dfm = validate_step_dfm(step, feature, tool)
        assert _is_pass(r_dfm)

        # R-2807 machine capability
        r_machine = validate_step_machine_capability(
            step, machine, requested_rpm=n
        )
        assert _is_pass(r_machine)

        # R-2808 empirical records
        r_empirical = validate_step_empirical_records(step, (vc_record,))
        assert _is_pass(r_empirical)

        # Aggregate step
        status = aggregate_step_status((r_complete, r_dfm, r_machine, r_empirical))
        assert status is PlanStatus.VALIDATED

    def test_modified_machine_limit_fails(self) -> None:
        """Tight machine RPM limit → machine check fails → step INVALID."""
        feature, tool, _, vc_record, n = self._setup()
        tight_machine = _machine("1000")  # n ≈ 3183 > 1000 → FAIL

        step = ProcessPlanStep(
            step_id="S-DRILL-001",
            sequence_index=0,
            feature_id=feature.feature_id,
            operation_type=OperationType.DRILLING,
            tool_id=tool.tool_id,
            machine_id=tight_machine.machine_id,
            parameter_record_ids=(vc_record.record_id,),
        )

        r_complete = validate_step_completeness(step)
        r_dfm = validate_step_dfm(step, feature, tool)
        r_machine = validate_step_machine_capability(step, tight_machine, requested_rpm=n)
        r_empirical = validate_step_empirical_records(step, (vc_record,))

        assert _is_fail(r_machine)
        status = aggregate_step_status((r_complete, r_dfm, r_machine, r_empirical))
        assert status is PlanStatus.INVALID

    def test_missing_machine_gives_incomplete(self) -> None:
        """Missing machine assignment → step INCOMPLETE."""
        feature, tool, _, vc_record, _ = self._setup()

        step = ProcessPlanStep(
            step_id="S-DRILL-001",
            sequence_index=0,
            feature_id=feature.feature_id,
            operation_type=OperationType.DRILLING,
            tool_id=tool.tool_id,
            # machine_id intentionally absent
            parameter_record_ids=(vc_record.record_id,),
        )

        r_complete = validate_step_completeness(step)  # missing machine → INSUFFICIENT_DATA
        assert _is_insuf(r_complete)
        status = aggregate_step_status((r_complete,))
        assert status is PlanStatus.INCOMPLETE

    def test_unverified_record_gives_incomplete(self) -> None:
        """Unverified empirical record → INCOMPLETE (not VALIDATED)."""
        feature, tool, machine, _, n = self._setup()
        bad_record = _unver_record()

        step = ProcessPlanStep(
            step_id="S-DRILL-001",
            sequence_index=0,
            feature_id=feature.feature_id,
            operation_type=OperationType.DRILLING,
            tool_id=tool.tool_id,
            machine_id=machine.machine_id,
            parameter_record_ids=(bad_record.record_id,),
        )

        r_complete = validate_step_completeness(step)
        r_dfm = validate_step_dfm(step, feature, tool)
        r_machine = validate_step_machine_capability(step, machine, requested_rpm=n)
        r_empirical = validate_step_empirical_records(step, (bad_record,))

        assert _is_insuf(r_empirical)
        status = aggregate_step_status((r_complete, r_dfm, r_machine, r_empirical))
        assert status is PlanStatus.INCOMPLETE

    def test_no_recommendation_made(self) -> None:
        """Validation returns VALIDATED or INCOMPLETE — never selects tool/machine."""
        feature = _hole_feature("10")

        # Two drills — both are presented to the caller, not picked by the system
        drill_a = _drill("10")
        drill_b = _drill("12")

        step_a = _step(step_id="S-A", operation_type=OperationType.DRILLING)
        step_b = _step(step_id="S-B", operation_type=OperationType.DRILLING)

        r_a = validate_step_dfm(step_a, feature, drill_a)
        r_b = validate_step_dfm(step_b, feature, drill_b)

        assert _is_pass(r_a)
        assert _is_fail(r_b)
        # The system does not pick drill_a — the caller sees separate results
        assert r_a.rule_id == r_b.rule_id == "R-2806"
