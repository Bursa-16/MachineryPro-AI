"""Stage 3H: MachineCatalog tests."""

from __future__ import annotations

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import MachineType, OperationType, ProvenanceType
from backend.domain.machine import Machine
from backend.domain.units import Quantity, Unit
from backend.empirical.exceptions import EmpiricalDataError
from backend.machines.catalog import MachineCatalog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Fixture machine — test only",
    )


def _make_mill(machine_id: str = "MILL-001") -> Machine:
    return Machine(
        machine_id=machine_id,
        name="Test VMC",
        machine_type=MachineType.MILL,
        axis_count=3,
        spindle_speed_min=Quantity.of("50", Unit.RPM),
        spindle_speed_max=Quantity.of("12000", Unit.RPM),
        spindle_power=Quantity.of("15", Unit.KW),
        provenance=_prov(),
        supported_operations=(OperationType.MILLING, OperationType.DRILLING),
    )


def _make_lathe(machine_id: str = "LATHE-001") -> Machine:
    return Machine(
        machine_id=machine_id,
        name="Test CNC Lathe",
        machine_type=MachineType.LATHE,
        axis_count=2,
        spindle_speed_min=Quantity.of("30", Unit.RPM),
        spindle_speed_max=Quantity.of("5000", Unit.RPM),
        spindle_power=Quantity.of("11", Unit.KW),
        spindle_torque=Quantity.of("200", Unit.NM),
        feed_rate_max=Quantity.of("8000", Unit.MM_MIN),
        provenance=_prov(),
        supported_operations=(OperationType.TURNING, OperationType.FACING),
    )


# ---------------------------------------------------------------------------
# A. Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_and_get(self) -> None:
        catalog = MachineCatalog()
        machine = _make_mill()
        result = catalog.register(machine)
        assert result is machine
        assert catalog.get("MILL-001") is machine

    def test_duplicate_id_rejected(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-001"))
        with pytest.raises(EmpiricalDataError, match="M-001"):
            catalog.register(_make_mill("M-001"))

    def test_non_machine_rejected(self) -> None:
        catalog = MachineCatalog()
        with pytest.raises(TypeError):
            catalog.register("not-a-machine")  # type: ignore[arg-type]

    def test_empty_catalog_length(self) -> None:
        catalog = MachineCatalog()
        assert len(catalog) == 0

    def test_length_increments(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-001"))
        catalog.register(_make_lathe("L-001"))
        assert len(catalog) == 2

    def test_contains(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill())
        assert "MILL-001" in catalog
        assert "MISSING" not in catalog

    def test_has(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill())
        assert catalog.has("MILL-001") is True
        assert catalog.has("NOPE") is False


# ---------------------------------------------------------------------------
# B. Lookup
# ---------------------------------------------------------------------------

class TestLookup:
    def test_get_existing(self) -> None:
        catalog = MachineCatalog()
        m = _make_lathe()
        catalog.register(m)
        assert catalog.get("LATHE-001") is m

    def test_get_missing_raises(self) -> None:
        catalog = MachineCatalog()
        with pytest.raises(EmpiricalDataError, match="GHOST"):
            catalog.get("GHOST")


# ---------------------------------------------------------------------------
# C. Collection queries
# ---------------------------------------------------------------------------

class TestCollectionQueries:
    def test_find_by_type(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-001"))
        catalog.register(_make_lathe("L-001"))
        mills = catalog.find_by_type(MachineType.MILL)
        lathes = catalog.find_by_type(MachineType.LATHE)
        assert len(mills) == 1 and mills[0].machine_id == "M-001"
        assert len(lathes) == 1 and lathes[0].machine_id == "L-001"

    def test_find_by_type_empty(self) -> None:
        catalog = MachineCatalog()
        assert catalog.find_by_type(MachineType.GRINDER) == ()

    def test_find_by_operation(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-001"))
        catalog.register(_make_lathe("L-001"))
        turning = catalog.find_by_operation(OperationType.TURNING)
        milling = catalog.find_by_operation(OperationType.MILLING)
        assert len(turning) == 1 and turning[0].machine_id == "L-001"
        assert len(milling) == 1 and milling[0].machine_id == "M-001"

    def test_find_by_operation_empty(self) -> None:
        catalog = MachineCatalog()
        assert catalog.find_by_operation(OperationType.GRINDING) == ()

    def test_all_sorted_by_id(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("Z-MILL"))
        catalog.register(_make_lathe("A-LATHE"))
        all_machines = catalog.all()
        assert [m.machine_id for m in all_machines] == ["A-LATHE", "Z-MILL"]

    def test_deterministic_ordering_repeated(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-003"))
        catalog.register(_make_mill("M-001"))
        catalog.register(_make_mill("M-002"))
        r1 = catalog.all()
        r2 = catalog.all()
        assert [m.machine_id for m in r1] == [m.machine_id for m in r2]

    def test_empty_all(self) -> None:
        assert MachineCatalog().all() == ()

    def test_ids(self) -> None:
        catalog = MachineCatalog()
        catalog.register(_make_mill("M-001"))
        catalog.register(_make_lathe("L-001"))
        assert "M-001" in catalog.ids()
        assert "L-001" in catalog.ids()
