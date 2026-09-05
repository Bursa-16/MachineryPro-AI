
# MachineryPro AI — Canonical Geometry / Topology Model

> **Stage 4B — vendor-neutral canonical geometry and topology schemas.**
>
> This document defines the deterministic, immutable, vendor-neutral data
> models that all future format adapters (STEP, IGES, Parasolid, ACIS, native
> CAD, DXF, STL, etc.) populate. Stage 4B is **representation only** — no
> parser, no geometry kernel, no tessellation, no Boolean operations, no
> manufacturing-feature recognition.

## 1. Purpose

The Stage 4A Universal Engineering Interoperability Foundation (UEIF)
defines the envelope into which engineering data flows:

```
SOURCE FILE
    ↓
FormatAdapter (Stage 4B+)
    ↓
Canonical Engineering Representation (CER)   ← Stage 4A
    ↓
Canonical Geometry / Topology                ← Stage 4B
    ↓
Canonical Topology                           ← Stage 4B
    ↓
Semantic Normalization (Stage 4D+)
    ↓
Manufacturing Feature Recognition (Stage 4D+)
    ↓
MachineryPro domain Feature
    ↓
DFM / Process Planning / CAM / / Validation
```

Stage 4B introduces:

* A **canonical geometry model** — point, vector, bounding box, curve,
  surface, geometry container.
* A **canonical topology model** — vertex, edge, loop, face, shell, body,
  transform, topology container.
* **Reference integrity** — every topology reference is validated against
  the referenced class.
* **Source traceability** — every entity carries an optional
  `source_entity_ref` (string) that links back to a Stage 4A
  `CanonicalEntityRef` or adapter-specific source identity.
* **Determinism** — frozen dataclasses, normalized iterables, sorted
  iteration, no hidden state.

## 2. Relationship to CER

The Stage 4A `CanonicalDocument` carries `entity_refs: tuple[CanonicalEntityRef, ...]`
which provide a stable, typed reference mechanism for entities that did not yet
have explicit schemas at Stage 4A. Stage 4B populates the actual entity
classes (curves, surfaces, vertices, edges, loops, faces, shells, bodies)
referenced by those `CanonicalEntityRef` instances.

Stage 4B does **not** mutate `CanonicalDocument`. The two layers compose:

```python
from backend.interoperability import (
    CanonicalDocument,
    CanonicalTopology,
    CanonicalEntityRef,
)

# Stage 4A envelope:
document = CanonicalDocument(
    document_id="DOC-001",
    canonical_kind="CAD_GEOMETRY",
    source=...,
    format_descriptor=...,
    adapter_id="occt-step",
    adapter_version="1.0.0",
    capability_level=CapabilityLevel.LEVEL_2_NORMALIZED,
    normalization_status=NormalizationStatus.SUCCESS,
    entity_refs=(
        CanonicalEntityRef(entity_id="B1", entity_kind="CanonicalBody"),
        CanonicalEntityRef(entity_id="F0", entity_kind="CanonicalFace"),
    ),
)

# Stage 4B payload (not stored inside the document):
topology = CanonicalTopology(
    topology_id="T1",
    bodies=(CanonicalBody("B1", BodyType.SOLID, ("SH1",)),),
    ...
)
```

## 3. Geometry vs Topology

Geometry and topology are **kept distinct**:

| Concern | Owns | Stage 4B module |
|---|---|---|
| **Geometry** | mathematical shape description | `geometry.py` |
| **Topology** | connectivity / adjacency / containment | `topology.py` |

A `CanonicalTopology` references geometry via stable IDs (`curve_id`,
`surface_id`) but never embeds full geometric objects inside its topology
entities. A topology entity that needs a point (e.g. `CanonicalVertex`)
embeds a `CanonicalPoint3D` (geometry) directly because the point is
*intrinsic* to the vertex.

## 4. Units

Every coordinate carries an explicit `Quantity` (Decimal value + `Unit`).
The canonical length units accepted by Stage 4B are:

* `Unit.MM` — millimetres.
* `Unit.M` — metres.

Mixing length units across the three coordinates of a single point, or
across the corners of a bounding box, is rejected at construction.

Direction vectors are dimensionless (`Unit.DIMENSIONLESS`) to keep
direction and position semantically distinct. `CanonicalVector3D` rejects
length-unit components.

There is **no implicit unit conversion**. Two coordinates are equal only
when both value and unit are identical.

## 5. Canonical Points / Vectors

### `CanonicalPoint3D`

An immutable 3D position with explicit length-units on every coordinate.

```python
CanonicalPoint3D(
    x=Quantity.of(1, "mm"),
    y=Quantity.of(2, "mm"),
    z=Quantity.of(3, "mm"),
)
```

* All three coordinates must share a single length unit.
* `point_id`, `source_entity_ref`, `metadata` are optional.
* `metadata` is an immutable `MappingProxyType`.

### `CanonicalVector3D`

An immutable 3D *directional* vector with dimensionless components.

```python
v = CanonicalVector3D(0, 0, 1)  # dimensionless unit vector along z
assert v.is_zero is False
```

* Vectors are **not** positions; positions are **not** vectors.
* `is_zero` is a property; there is no automatic normalization.
* Components are dimensionless; passing a length-unit `Quantity` is rejected.

## 6. Curves

`CanonicalCurve` is the immutable descriptor for a canonical curve. Curves are
not evaluated; Stage 4B stores the canonical data future evaluators may
consume.

| Curve type | Required canonical data | Optional canonical data |
|---|---|---|
| `LINE` | — | `origin`, `direction` |
| `CIRCLE` | — | `center`, `axis`, `radius` |
| `ARC` | — | `center`, `axis`, `radius` |
| `ELLIPSE` | — | `center`, `axis`, `major_radius`, `minor_radius` |
| `BSPLINE` | — | `degree`, `control_points`, `knots` |
| `NURBS` | — | `degree`, `control_points`, `knots`, `weights` |
| `POLYLINE` | — | — |
| `UNKNOWN` | — | — |

`radius`, `major_radius`, `minor_radius` must be strictly positive when
known; zero and negative values are rejected.

## 7. Surfaces

`CanonicalSurface` is the immutable descriptor for a canonical surface.
Surfaces are not evaluated; Stage 4B stores the canonical data.

| Surface type | Required canonical data | Optional canonical data |
|---|---|---|
| `PLANE` | — | `origin`, `normal` |
| `CYLINDER` | — | `origin`, `axis`, `radius` |
| `CONE` | — | `origin`, `axis`, `semi_angle` |
| `SPHERE` | — | `center`, `radius` |
| `TORUS` | — | `center`, `axis`, `major_radius`, `minor_radius` |
| `NURBS` | — | `degree`, `control_points`, `knots`, `weights` |
| `BSPLINE` | — | `degree`, `control_points`, `knots` |
| `REVOLUTION` | — | `axis` |
| `EXTRUSION` | — | `axis` |
| `OFFSET` | — | `normal` |
| `UNKNOWN` | — | — |

A `CYLINDER` is **not** automatically a manufacturing hole, bore, boss, or
turned diameter. See §23 — Manufacturing semantics.

## 8. Vertices

`CanonicalVertex` is the 0D topological vertex positioned by a
`CanonicalPoint3D`.

```python
CanonicalVertex(vertex_id="V1", point=CanonicalPoint3D(...))
```

* Immutable; non-empty `vertex_id`.
* `metadata` is an immutable `MappingProxyType`.

## 9. Edges

`CanonicalEdge` is the 1D topological edge connecting two vertices and bound
to a curve.

```python
CanonicalEdge(
    edge_id="E1",
    start_vertex_id="V0",
    end_vertex_id="V1",
    curve_id="C0",
    orientation=Orientation.FORWARD,
)
```

* `start_vertex_id` and `end_vertex_id` must be **distinct**.
* `curve_id` is referenced by the topology container, not embedded.
* References are validated by `CanonicalTopology`.

## 10. Loops

`CanonicalLoop` is an ordered closed chain of edges bounding a face.

* `edge_ids` must contain **at least 3** entries.
* `edge_ids` order is preserved verbatim (topology semantics).
* Duplicate edge references within the same loop are rejected.
* `loop_type` is `OUTER`, `INNER`, or `UNKNOWN`.

## 11. Faces

`CanonicalFace` is the 2D topological face bound to a surface and one or
more loops.

* `boundary_loop_ids` must contain at least one loop reference.
* Loop order is preserved verbatim; the first loop is typically the outer
  boundary but the topology container does NOT rely on that ordering.
* Duplicate loop references within the same face are rejected.

## 12. Shells

`CanonicalShell` is a connected set of faces.

* `face_ids` must contain at least one face reference.
* `closure` is `OPEN`, `CLOSED`, or `UNKNOWN`.
* **`UNKNOWN` is the default and the fail-closed stance.**
* Closure is **never inferred** from face count or arrangement.

## 13. Bodies

`CanonicalBody` is the top-level topological body composed of one or more
shells.

* `body_type` is `SOLID`, `SHEET`, `WIRE`, `COMPOUND`, or `UNKNOWN`.
* A `SOLID` body should only be declared `SOLID` when the adapter knows the
  shell(s) form a watertight volume.
* `bounding_box` and `transform` are optional.

## 14. Bounding Boxes

`BoundingBox3D` is a deterministic axis-aligned bounding box.

* Min and max corners share a single length unit.
* `min_x <= max_x`, `min_y <= max_y`, `min_z <= max_z`.
* `min == max` is permitted (degenerate / flat box).
* Properties expose `size_x`, `size_y`, `size_z` as `Quantity` values.

No oriented bounding box in Stage 4B.

## 15. Orientation

`Orientation` is the vendor-neutral orientation enum.

| Value | Meaning |
|---|---|
| `FORWARD` | traversal direction follows the canonical direction |
| `REVERSED` | traversal direction is opposite the canonical direction |
| `INTERNAL` | internal / inner-side |
| `EXTERNAL` | external / outer-side |
| `UNKNOWN` | caller could not determine |

No OpenCASCADE-specific orientation values are used.

## 16. Source Traceability

Every geometry/topology entity carries an optional `source_entity_ref`
(string). Adapters populate this with a stable identifier of the
corresponding entity in the source file (e.g. `STEP_FACE_42`,
`CATIA_FACE_NAME`,` STL_region_id`).

`source_entity_ref` is **separate** from the canonical Stage 4A
`CanonicalEntityRef.entity_id`. Stage 4A references are used inside the
`CanonicalDocument.entity_refs` collection; Stage 4B
`source_entity_ref` strings are attached to individual geometry/topology
entities to map them to format-specific source identifiers.

Traceability survives normalization.

## 17. Validation

Structural validation is enforced at construction time. Every canonical
model performs:

* Rejection of empty / whitespace-only IDs.
* Rejection of bool, NaN, Infinity as numeric values.
* Type checks against the canonical enum / dataclass types.
* Frozen mutation prevention.

`CanonicalTopology` additionally performs **reference integrity** checks:

| Reference | Must exist in |
|---|---|
| `Edge.start_vertex_id`, `Edge.end_vertex_id` | `vertices` |
| `Edge.curve_id` | `geometry.curves` (when `geometry` provided) |
| `Loop.edge_ids` | `edges` |
| `Face.surface_id` | `geometry.surfaces` (when `geometry` provided) |
| `Face.boundary_loop_ids` | `loops` |
| `Shell.face_ids` | `faces` |
| `Body.shell_ids` | `shells` |

Stage 4B does **not** validate:

* Face-face intersection.
* Manifold proof.
* Watertight-solid proof.
* Boolean validity.
* Geometric tolerance healing.

Those require a geometry kernel and belong to a later stage.

## 18. Determinism

* All models are `@dataclass(frozen=True, slots=True)`.
* Iterables are normalized to tuples.
* Iteration order over collections is by canonical ID (sorted by string).
* Deterministic ordering survives round-tripping through `as_dict()`.
* No random tolerance epsilon.

## 19. Example — Rectangular Solid

The synthetic rectangular-block example used by the test suite:

* 8 vertices (unit cube corners).
* 12 edges (4 bottom, 4 top, 4 vertical).
* 6 planar surfaces.
* 6 outer boundary loops (one per face).
* 6 faces.
* 1 closed shell.
* 1 solid body.

The geometry container holds 12 line curves (one per edge) and 6 plane
surfaces. The topology container references them via stable IDs. All
references are validated.

## 20. Example — Cylindrical Surface

The synthetic cylinder example proves that a `CYLINDER` surface is purely
geometric:

```python
s = CanonicalSurface(
    "cyl_001",
    CanonicalSurfaceType.CYLINDER,
    origin=CanonicalPoint3D(
    x=Quantity.of(0, "mm"),
    y=Quantity.of(0, "mm"),
    z=Quantity.of(0, "mm"),
),
    axis=CanonicalVector3D(0, 0, 1),
    radius=Quantity.of(25, "mm"),
)
assert s.surface_type is CanonicalSurfaceType.CYLINDER
assert s.radius is not None
assert s.radius.value == 25
```

The surface carries no manufacturing role, no hole flag, no boss flag.

## 21. Non-Goals

Stage 4B does NOT implement:

* STEP / IGES / DXF / DWG / Parasolid / ACIS / STL parsing.
* Native CAD adapters.
* OpenCASCADE or any geometry kernel.
* Tessellation / mesh generation.
* Surface intersection / Boolean operations.
* Solid healing.
* Manufacturing-feature recognition (Stage 4D).
* PMI / GD&T.
* Drawing interpretation.
* CAM / NC.
* AI / ML / RAG / LLM.

## 22. Relationship to Stage 4C

Stage 4C is expected to introduce the **STEP / IGES / B-Rep import
foundation** — format-specific adapters that populate Stage 4B canonical
entities from real CAD data. Stage 4B provides the contract those
adapters will fulfil.

Stage 4B does **not** depend on Stage 4C. Adapters may be added incrementally.

## 23. Relationship to Manufacturing Feature Recognition

**A geometric cylinder is not automatically a manufacturing hole.**

`CanonicalSurface(surface_type=CYLINDER)` describes the math; it does not
declare whether the cylinder represents a drilled hole, a turned diameter,
a bore, a boss, or simply a geometric primitive. Manufacturing semantics
are added by the Stage 4D Manufacturing Feature Recognition stage, which
analyses canonical geometry + topology together with context (drawing
notes, PMI, annotations) to produce `MachineryFeature` instances.

Stage 4B explicitly avoids attaching manufacturing classification to
geometry or topology entities. Doing so would corrupt the separation between
vendor-neutral shape description and engineering intent.
