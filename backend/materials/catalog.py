"""Deterministic in-memory material catalog (Stage 3G).

Provides registration and lookup of
:class:`~backend.domain.material.Material` instances for use as
applicability references in empirical cutting-parameter records.

No production seed data is included.  Every :class:`Material` admitted to
the catalog must carry explicit provenance before it can be referenced by
authoritative empirical records.

Lookup semantics
----------------
* Exact-ID lookup raises :class:`~backend.empirical.exceptions.EmpiricalDataError`
  when the ID is not found.
* Collection queries return all matching records in deterministic order
  (sorted by ``material_id``).  Empty result → empty tuple (not an error).
* Duplicate ``material_id`` is rejected at registration (fail closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.enums import IsoMaterialGroup, MaterialFamily
from backend.domain.material import Material
from backend.empirical.exceptions import EmpiricalDataError

__all__ = ["MaterialCatalog"]


@dataclass
class MaterialCatalog:
    """In-memory catalog of :class:`~backend.domain.material.Material` records.

    ``_materials`` is private; all mutation goes through :meth:`register`.
    """

    _materials: dict[str, Material] = field(default_factory=dict, init=False)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, material: Material) -> Material:
        """Register *material*; raise on duplicate ``material_id``.

        Raises:
            TypeError: when *material* is not a :class:`Material`.
            EmpiricalDataError: when the ID is already registered.
        """
        if not isinstance(material, Material):
            raise TypeError("only Material instances can be registered")
        if material.material_id in self._materials:
            raise EmpiricalDataError(
                f"material id {material.material_id!r} is already registered"
            )
        self._materials[material.material_id] = material
        return material

    # ------------------------------------------------------------------
    # Exact-ID lookup
    # ------------------------------------------------------------------

    def get(self, material_id: str) -> Material:
        """Return the material with *material_id*.

        Raises:
            EmpiricalDataError: when the ID is not registered.
        """
        material = self._materials.get(material_id)
        if material is None:
            raise EmpiricalDataError(
                f"no material with id {material_id!r}"
            )
        return material

    def has(self, material_id: str) -> bool:
        """True when *material_id* is registered."""
        return material_id in self._materials

    # ------------------------------------------------------------------
    # Collection queries
    # ------------------------------------------------------------------

    def find_by_family(
        self, family: MaterialFamily
    ) -> tuple[Material, ...]:
        """All materials with the given :class:`MaterialFamily`.

        Returns an empty tuple when none match.  Sorted by ``material_id``.
        """
        return tuple(
            sorted(
                (m for m in self._materials.values() if m.material_family is family),
                key=lambda m: m.material_id,
            )
        )

    def find_by_iso_group(
        self, iso_group: IsoMaterialGroup
    ) -> tuple[Material, ...]:
        """All materials tagged with the given ISO material group.

        The ISO group is stored in ``material.machinability_metadata`` under
        the key ``"iso_material_group"`` as a string matching the
        :class:`~backend.domain.enums.IsoMaterialGroup` value.

        This is a soft convention for Stage 3G: a full ISO-group model is
        deferred to a later stage.  Returns an empty tuple when none match.
        Sorted by ``material_id``.
        """
        target = iso_group.value
        return tuple(
            sorted(
                (
                    m
                    for m in self._materials.values()
                    if m.machinability_metadata.get("iso_material_group") == target
                ),
                key=lambda m: m.material_id,
            )
        )

    def all(self) -> tuple[Material, ...]:
        """All registered materials sorted by ``material_id``."""
        return tuple(sorted(self._materials.values(), key=lambda m: m.material_id))

    def ids(self) -> tuple[str, ...]:
        """All registered material IDs in stable registration order."""
        return tuple(self._materials)

    def __len__(self) -> int:
        return len(self._materials)

    def __contains__(self, material_id: str) -> bool:
        return self.has(material_id)
