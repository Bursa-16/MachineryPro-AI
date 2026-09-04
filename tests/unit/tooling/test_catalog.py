"""Stage 3G: ToolCatalog tests."""

from __future__ import annotations

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import OperationType, ProvenanceType, ToolType
from backend.domain.tool import Tool
from backend.domain.units import Quantity, Unit
from backend.empirical.exceptions import EmpiricalDataError
from backend.tooling.catalog import ToolCatalog


def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Sandvik Catalogue 2023 p.88",
    )


def _make_insert(tool_id: str = "TOOL-INSERT-001") -> Tool:
    return Tool(
        tool_id=tool_id,
        tool_type=ToolType.TURNING_INSERT,
        diameter=Quantity.of("12", Unit.MM),
        cutting_edge_count=4,
        provenance=_prov(),
        supported_operations=(OperationType.TURNING,),
    )


def _make_drill(tool_id: str = "TOOL-DRILL-001") -> Tool:
    return Tool(
        tool_id=tool_id,
        tool_type=ToolType.DRILL,
        diameter=Quantity.of("10", Unit.MM),
        cutting_edge_count=2,
        provenance=_prov(),
        supported_operations=(OperationType.DRILLING,),
    )


class TestToolCatalog:
    def test_register_and_get(self) -> None:
        catalog = ToolCatalog()
        tool = _make_insert()
        catalog.register(tool)
        assert catalog.get("TOOL-INSERT-001") is tool

    def test_get_missing_raises(self) -> None:
        catalog = ToolCatalog()
        with pytest.raises(EmpiricalDataError, match="TOOL-GHOST"):
            catalog.get("TOOL-GHOST")

    def test_duplicate_id_rejected(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert("T-001"))
        with pytest.raises(EmpiricalDataError, match="T-001"):
            catalog.register(_make_insert("T-001"))

    def test_non_tool_rejected(self) -> None:
        catalog = ToolCatalog()
        with pytest.raises(TypeError):
            catalog.register({"tool_id": "X"})  # type: ignore[arg-type]

    def test_has(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert())
        assert catalog.has("TOOL-INSERT-001") is True
        assert catalog.has("MISSING") is False

    def test_len(self) -> None:
        catalog = ToolCatalog()
        assert len(catalog) == 0
        catalog.register(_make_insert())
        assert len(catalog) == 1

    def test_find_by_type(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert("I-001"))
        catalog.register(_make_drill("D-001"))
        inserts = catalog.find_by_type(ToolType.TURNING_INSERT)
        drills = catalog.find_by_type(ToolType.DRILL)
        assert len(inserts) == 1 and inserts[0].tool_id == "I-001"
        assert len(drills) == 1 and drills[0].tool_id == "D-001"

    def test_find_by_type_empty(self) -> None:
        catalog = ToolCatalog()
        assert catalog.find_by_type(ToolType.REAMER) == ()

    def test_find_by_operation(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert("I-001"))
        catalog.register(_make_drill("D-001"))
        turning_tools = catalog.find_by_operation(OperationType.TURNING)
        milling_tools = catalog.find_by_operation(OperationType.MILLING)
        assert len(turning_tools) == 1 and turning_tools[0].tool_id == "I-001"
        assert milling_tools == ()

    def test_all_sorted_by_id(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert("Z-TOOL"))
        catalog.register(_make_drill("A-TOOL"))
        all_tools = catalog.all()
        assert [t.tool_id for t in all_tools] == ["A-TOOL", "Z-TOOL"]

    def test_contains_operator(self) -> None:
        catalog = ToolCatalog()
        catalog.register(_make_insert())
        assert "TOOL-INSERT-001" in catalog
        assert "NOPE" not in catalog

    def test_empty_catalog_all(self) -> None:
        catalog = ToolCatalog()
        assert catalog.all() == ()
