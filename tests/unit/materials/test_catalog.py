"""Stage 3G: MaterialCatalog tests."""

from __future__ import annotations

import pytest

from backend.domain.base import Provenance
from backend.domain.enums import IsoMaterialGroup, MaterialFamily, ProvenanceType
from backend.domain.material import Material
from backend.empirical.exceptions import EmpiricalDataError
from backend.materials.catalog import MaterialCatalog


def _prov() -> Provenance:
    return Provenance(
        source_type=ProvenanceType.MATERIAL_STANDARD,
        source_reference="ISO 683-1:2016",
    )


def _make_steel(mat_id: str = "MAT-STEEL-001") -> Material:
    return Material(
        material_id=mat_id,
        designation="C45",
        material_family=MaterialFamily.STEEL,
        provenance=_prov(),
        standard="EN 10083-2",
    )


def _make_aluminum(mat_id: str = "MAT-AL-001") -> Material:
    return Material(
        material_id=mat_id,
        designation="6061-T6",
        material_family=MaterialFamily.ALUMINUM,
        provenance=_prov(),
    )


class TestMaterialCatalog:
    def test_register_and_get(self) -> None:
        catalog = MaterialCatalog()
        mat = _make_steel()
        catalog.register(mat)
        assert catalog.get("MAT-STEEL-001") is mat

    def test_get_missing_raises(self) -> None:
        catalog = MaterialCatalog()
        with pytest.raises(EmpiricalDataError, match="MAT-GHOST"):
            catalog.get("MAT-GHOST")

    def test_duplicate_id_rejected(self) -> None:
        catalog = MaterialCatalog()
        catalog.register(_make_steel("MAT-001"))
        with pytest.raises(EmpiricalDataError, match="MAT-001"):
            catalog.register(_make_steel("MAT-001"))

    def test_non_material_rejected(self) -> None:
        catalog = MaterialCatalog()
        with pytest.raises(TypeError):
            catalog.register("not-a-material")  # type: ignore[arg-type]

    def test_has(self) -> None:
        catalog = MaterialCatalog()
        catalog.register(_make_steel())
        assert catalog.has("MAT-STEEL-001") is True
        assert catalog.has("MISSING") is False

    def test_len(self) -> None:
        catalog = MaterialCatalog()
        assert len(catalog) == 0
        catalog.register(_make_steel())
        assert len(catalog) == 1

    def test_find_by_family(self) -> None:
        catalog = MaterialCatalog()
        catalog.register(_make_steel("S-001"))
        catalog.register(_make_aluminum("A-001"))
        steels = catalog.find_by_family(MaterialFamily.STEEL)
        alums = catalog.find_by_family(MaterialFamily.ALUMINUM)
        assert len(steels) == 1 and steels[0].material_id == "S-001"
        assert len(alums) == 1 and alums[0].material_id == "A-001"

    def test_find_by_family_empty(self) -> None:
        catalog = MaterialCatalog()
        assert catalog.find_by_family(MaterialFamily.TITANIUM) == ()

    def test_find_by_iso_group(self) -> None:
        """ISO group stored in machinability_metadata."""
        catalog = MaterialCatalog()
        mat = Material(
            material_id="MAT-P-001",
            designation="C45",
            material_family=MaterialFamily.STEEL,
            provenance=_prov(),
            machinability_metadata={"iso_material_group": "P"},
        )
        catalog.register(mat)
        p_group = catalog.find_by_iso_group(IsoMaterialGroup.P)
        n_group = catalog.find_by_iso_group(IsoMaterialGroup.N)
        assert len(p_group) == 1
        assert p_group[0].material_id == "MAT-P-001"
        assert n_group == ()

    def test_all_sorted_by_id(self) -> None:
        catalog = MaterialCatalog()
        catalog.register(_make_steel("Z-001"))
        catalog.register(_make_steel("A-001"))
        all_mats = catalog.all()
        assert [m.material_id for m in all_mats] == ["A-001", "Z-001"]

    def test_contains_operator(self) -> None:
        catalog = MaterialCatalog()
        catalog.register(_make_steel())
        assert "MAT-STEEL-001" in catalog
        assert "NOPE" not in catalog

    def test_empty_catalog_all(self) -> None:
        catalog = MaterialCatalog()
        assert catalog.all() == ()
