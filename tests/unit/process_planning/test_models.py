"""Stage 3J: ProcessPlanStep and ProcessPlan model tests."""

from __future__ import annotations

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import OperationType, ProvenanceType
from backend.domain.exceptions import ValidationError
from backend.process_planning.models import (
    PlanStatus,
    ProcessPlan,
    ProcessPlanStep,
    ReviewStatus,
)


def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.USER_INPUT, source_reference="test fixture"
    )


def _step(
    step_id: str = "S-001",
    seq: int = 0,
    feature_id: str | None = "F-001",
    op: OperationType | None = OperationType.DRILLING,
    tool_id: str | None = "T-001",
    machine_id: str | None = "M-001",
) -> ProcessPlanStep:
    return ProcessPlanStep(
        step_id=step_id,
        sequence_index=seq,
        feature_id=feature_id,
        operation_type=op,
        tool_id=tool_id,
        machine_id=machine_id,
    )


class TestProcessPlanStep:
    def test_minimal_valid_step(self) -> None:
        step = ProcessPlanStep(step_id="S-001", sequence_index=0)
        assert step.step_id == "S-001"
        assert step.sequence_index == 0
        assert step.engineering_status is PlanStatus.INCOMPLETE

    def test_full_step(self) -> None:
        step = _step()
        assert step.feature_id == "F-001"
        assert step.operation_type is OperationType.DRILLING
        assert step.tool_id == "T-001"
        assert step.machine_id == "M-001"

    def test_empty_step_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="", sequence_index=0)

    def test_whitespace_step_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="   ", sequence_index=0)

    def test_negative_sequence_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="S-001", sequence_index=-1)

    def test_bool_sequence_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="S-001", sequence_index=True)  # type: ignore[arg-type]

    def test_float_sequence_index_rejected(self) -> None:
        with pytest.raises((ValidationError, TypeError)):
            ProcessPlanStep(step_id="S-001", sequence_index=1.5)  # type: ignore[arg-type]

    def test_zero_sequence_index_valid(self) -> None:
        step = ProcessPlanStep(step_id="S-001", sequence_index=0)
        assert step.sequence_index == 0

    def test_invalid_operation_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="S-001", sequence_index=0, operation_type="drilling")  # type: ignore[arg-type]

    def test_empty_tool_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlanStep(step_id="S-001", sequence_index=0, tool_id="")

    def test_immutable(self) -> None:
        step = _step()
        with pytest.raises((AttributeError, TypeError)):
            step.step_id = "MUTATED"  # type: ignore[misc]

    def test_parameter_record_ids_tuple(self) -> None:
        step = ProcessPlanStep(
            step_id="S-001", sequence_index=0,
            parameter_record_ids=("R-001", "R-002"),
        )
        assert step.parameter_record_ids == ("R-001", "R-002")

    def test_predecessor_ids_tuple(self) -> None:
        step = ProcessPlanStep(
            step_id="S-002", sequence_index=1,
            predecessor_step_ids=("S-001",),
        )
        assert step.predecessor_step_ids == ("S-001",)

    def test_engineering_status_default(self) -> None:
        step = ProcessPlanStep(step_id="S-001", sequence_index=0)
        assert step.engineering_status is PlanStatus.INCOMPLETE

    def test_review_status_default(self) -> None:
        step = ProcessPlanStep(step_id="S-001", sequence_index=0)
        assert step.review_status is ReviewStatus.NOT_REVIEWED

    def test_as_dict(self) -> None:
        step = _step()
        d = step.as_dict()
        assert isinstance(d, dict)
        assert "step_id" in d


class TestProcessPlan:
    def test_empty_plan(self) -> None:
        plan = ProcessPlan(
            plan_id="PP-001", part_id="P-001",
            steps=(), engineering_status=PlanStatus.INCOMPLETE,
            provenance=_prov(),
        )
        assert plan.plan_id == "PP-001"
        assert len(plan.steps) == 0

    def test_empty_plan_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlan(
                plan_id="", part_id="P-001",
                steps=(), engineering_status=PlanStatus.INCOMPLETE,
                provenance=_prov(),
            )

    def test_non_step_in_tuple_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProcessPlan(
                plan_id="PP-001", part_id="P-001",
                steps=("not-a-step",),  # type: ignore[arg-type]
                engineering_status=PlanStatus.INCOMPLETE,
                provenance=_prov(),
            )

    def test_ordered_steps(self) -> None:
        s1 = ProcessPlanStep(step_id="S-003", sequence_index=2)
        s2 = ProcessPlanStep(step_id="S-001", sequence_index=0)
        s3 = ProcessPlanStep(step_id="S-002", sequence_index=1)
        plan = ProcessPlan(
            plan_id="PP-001", part_id="P-001",
            steps=(s1, s2, s3),
            engineering_status=PlanStatus.INCOMPLETE,
            provenance=_prov(),
        )
        ordered = plan.ordered_steps
        assert [s.sequence_index for s in ordered] == [0, 1, 2]

    def test_immutable(self) -> None:
        plan = ProcessPlan(
            plan_id="PP-001", part_id="P-001",
            steps=(), engineering_status=PlanStatus.INCOMPLETE,
            provenance=_prov(),
        )
        with pytest.raises((AttributeError, TypeError)):
            plan.plan_id = "MUTATED"  # type: ignore[misc]

    def test_as_dict(self) -> None:
        plan = ProcessPlan(
            plan_id="PP-001", part_id="P-001",
            steps=(_step(),), engineering_status=PlanStatus.INCOMPLETE,
            provenance=_prov(),
        )
        d = plan.as_dict()
        assert isinstance(d, dict)
        assert "plan_id" in d

    def test_deterministic_ordered_steps(self) -> None:
        s1 = ProcessPlanStep(step_id="S-B", sequence_index=1)
        s2 = ProcessPlanStep(step_id="S-A", sequence_index=0)
        plan = ProcessPlan(
            plan_id="PP-001", part_id="P-001",
            steps=(s1, s2),
            engineering_status=PlanStatus.INCOMPLETE,
            provenance=_prov(),
        )
        o1 = plan.ordered_steps
        o2 = plan.ordered_steps
        assert [s.step_id for s in o1] == [s.step_id for s in o2]


class TestPlanStatus:
    def test_invalid_dominates(self) -> None:
        assert PlanStatus.INVALID != PlanStatus.VALIDATED

    def test_all_statuses_are_strings(self) -> None:
        for s in PlanStatus:
            assert isinstance(s.value, str)

    def test_review_status_values(self) -> None:
        assert ReviewStatus.NOT_REVIEWED != ReviewStatus.APPROVED
        assert ReviewStatus.NOT_REVIEWED != ReviewStatus.REJECTED
