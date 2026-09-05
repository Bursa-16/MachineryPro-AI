"""Stage 3J: ProcessPlanBuilder tests."""

from __future__ import annotations

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import ProvenanceType
from backend.domain.exceptions import ValidationError
from backend.process_planning.builder import ProcessPlanBuilder
from backend.process_planning.models import PlanStatus, ProcessPlanStep


def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.USER_INPUT, source_reference="test"
    )


def _step(step_id: str = "S-001", seq: int = 0) -> ProcessPlanStep:
    return ProcessPlanStep(step_id=step_id, sequence_index=seq)


class TestProcessPlanBuilder:
    def test_builds_empty_plan(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        plan = builder.build()
        assert plan.plan_id == "PP-001"
        assert len(plan.steps) == 0
        assert plan.engineering_status is PlanStatus.INCOMPLETE

    def test_builds_single_step_plan(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(_step("S-001", 0))
        plan = builder.build()
        assert len(plan.steps) == 1

    def test_steps_sorted_by_sequence_index(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(_step("S-003", 2))
        builder.add_step(_step("S-001", 0))
        builder.add_step(_step("S-002", 1))
        plan = builder.build()
        assert [s.sequence_index for s in plan.steps] == [0, 1, 2]

    def test_duplicate_step_id_gives_invalid_plan(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(_step("S-001", 0))
        builder.add_step(_step("S-001", 1))  # duplicate ID
        plan = builder.build()
        assert plan.engineering_status is PlanStatus.INVALID

    def test_duplicate_sequence_index_gives_invalid_plan(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(_step("S-001", 0))
        builder.add_step(_step("S-002", 0))  # duplicate sequence
        plan = builder.build()
        assert plan.engineering_status is PlanStatus.INVALID

    def test_cycle_gives_invalid_plan(self) -> None:
        s1 = ProcessPlanStep(step_id="S-001", sequence_index=0,
                             predecessor_step_ids=("S-002",))
        s2 = ProcessPlanStep(step_id="S-002", sequence_index=1,
                             predecessor_step_ids=("S-001",))
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(s1)
        builder.add_step(s2)
        plan = builder.build()
        assert plan.engineering_status is PlanStatus.INVALID

    def test_non_step_rejected(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        with pytest.raises(ValidationError):
            builder.add_step("not-a-step")  # type: ignore[arg-type]

    def test_builder_not_reusable(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.build()
        with pytest.raises(RuntimeError):
            builder.build()

    def test_add_step_after_build_rejected(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.build()
        with pytest.raises(RuntimeError):
            builder.add_step(_step())

    def test_step_count(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        assert builder.step_count() == 0
        builder.add_step(_step("S-001", 0))
        assert builder.step_count() == 1

    def test_plan_immutable(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        plan = builder.build()
        with pytest.raises((AttributeError, TypeError)):
            plan.plan_id = "MUTATED"  # type: ignore[misc]

    def test_validated_steps_give_validated_plan(self) -> None:
        s = ProcessPlanStep(step_id="S-001", sequence_index=0,
                            engineering_status=PlanStatus.VALIDATED)
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(s)
        plan = builder.build()
        assert plan.engineering_status is PlanStatus.VALIDATED

    def test_incomplete_step_gives_incomplete_plan(self) -> None:
        s = ProcessPlanStep(step_id="S-001", sequence_index=0,
                            engineering_status=PlanStatus.INCOMPLETE)
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        builder.add_step(s)
        plan = builder.build()
        assert plan.engineering_status is PlanStatus.INCOMPLETE

    def test_method_chaining(self) -> None:
        builder = ProcessPlanBuilder("PP-001", "PART-001", _prov())
        plan = (
            builder
            .add_step(_step("S-001", 0))
            .add_step(_step("S-002", 1))
            .build()
        )
        assert len(plan.steps) == 2

    def test_deterministic_build(self) -> None:
        """Same steps always produce same plan structure."""
        def make_plan():
            b = ProcessPlanBuilder("PP-001", "PART-001", _prov())
            b.add_step(_step("S-002", 1))
            b.add_step(_step("S-001", 0))
            return b.build()

        p1 = make_plan()
        p2 = make_plan()
        assert [s.step_id for s in p1.steps] == [s.step_id for s in p2.steps]
