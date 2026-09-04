# MachineryPro AI — Empirical Engineering Data Foundation

**Stage:** 3G
**Status:** Implemented
**Rule ID range:** n/a (data foundation — no additional EngineeringRule instances)

---

## 1. Purpose

Stage 3G establishes the authoritative **data contracts** for empirical
machining information entering MachineryPro AI.

Its purpose is to define *how* empirical engineering data is structured,
validated, and stored — not to populate a production database of cutting
speeds, feeds, or material properties.

Stage 3G answers:

- What fields must a cutting-parameter record carry?
- What provenance is required for authoritative status?
- How are applicability and scope expressed?
- How are conflicting sources handled?
- How are lookups performed deterministically?
- What happens when data is missing or unsourced?

---

## 2. Relationship to the Deterministic Engineering Core

```
┌──────────────────────────────────────────────────────────┐
│  Stages 3A – 3F: DETERMINISTIC PHYSICS / KINEMATICS      │
│  n = 1000·Vc/(π·D)   Vf = z·fz·n   MRR = ap·ae·Vf       │
│  AUTHORITATIVE — no empirical constants required          │
└──────────────────────────┬───────────────────────────────┘
                           │ needs Vc, fz, ap inputs
┌──────────────────────────▼───────────────────────────────┐
│  Stage 3G: EMPIRICAL DATA FOUNDATION                      │
│  CuttingParameterRecord  QuantityRange  ApplicabilityScope│
│  Provenance  EvidenceStatus  CuttingParameterRegistry     │
│  SOURCE-BOUNDED AUTHORITATIVE (only when provenance valid)│
└──────────────────────────────────────────────────────────┘
                           │ advisory only — never overrides
┌──────────────────────────▼───────────────────────────────┐
│  Future: AI ADVISORY LAYER                                │
│  NEVER authoritative without Stage 3G provenance          │
└──────────────────────────────────────────────────────────┘
```

Stages 3A–3F **calculate** from explicit inputs.
Stage 3G **governs** the empirical inputs those calculations may receive.

A cutting-speed recommendation from Stage 3G is only as trustworthy as
its provenance.  A deterministic formula from Stage 3A is authoritative
by mathematical construction.  These are different things and must remain
separate.

---

## 3. Authority Model

```
AUTHORITATIVE:    deterministic physics (Stages 3A–3F)
SOURCE-BOUNDED:   empirical data with valid Provenance + EvidenceStatus
ADVISORY ONLY:    AI output — never overrides either of the above
```

The following can NEVER elevate a value to authoritative status:

- An LLM generated it.
- It appears in an unsourced training document.
- It resembles an industry norm.
- It is numerically plausible.
- It exists in a CAM tutorial or textbook example.

Only explicit, machine-readable Provenance + an appropriate EvidenceStatus
creates source-bounded authority.

---

## 4. Empirical Record Model

### `CuttingParameterRecord`

The core empirical unit.  Represents one engineering parameter observation
or approved data entry.

| Field | Type | Required | Purpose |
|---|---|---|---|
| `record_id` | `str` | Yes | Stable unique identifier within the catalog |
| `parameter_type` | `ParameterType` | Yes | Controlled parameter identity |
| `value_range` | `QuantityRange` | Yes | Unit-safe min/max value |
| `applicability` | `ApplicabilityScope` | Yes | Explicit engineering context |
| `provenance` | `Provenance` | Yes | Source traceability |
| `evidence_status` | `EvidenceStatus` | Yes | Authority classification |
| `notes` | `str | None` | No | Limitations, caveats |

All records are **frozen** (immutable once constructed).
Provenance is permanently bound to the value — no stripping path exists.

---

## 5. Parameter Identity

`ParameterType` is a controlled vocabulary.  Only parameter types whose
units and semantics are unambiguous within the `Unit` model are defined.

| ParameterType | Canonical Unit | Engineering symbol |
|---|---|---|
| `CUTTING_SPEED` | `m/min` | Vc |
| `FEED_PER_TOOTH` | `mm/tooth` | fz |
| `FEED_PER_REV` | `mm/rev` | f |
| `AXIAL_DEPTH_OF_CUT` | `mm` | ap |
| `RADIAL_ENGAGEMENT` | `mm` | ae |
| `SPECIFIC_CUTTING_FORCE` | `MPa` | Kc1.1 (1 MPa = 1 N/mm²) |
| `TOOL_LIFE_CONSTANT` | `m/min` | Taylor C |
| `TOOL_LIFE_EXPONENT` | `dimensionless` | Taylor n |

A record with the wrong unit for its parameter type is rejected at
construction.

---

## 6. Units and Ranges

### `QuantityRange`

An immutable, inclusive range `[min_value, max_value]`.

- Both bounds carry the same `Unit` (validated at construction).
- `min_value.value <= max_value.value` is enforced.
- `NaN` and `Infinity` are rejected by `Quantity`.
- `bool` arguments are rejected by `_to_decimal`.
- A point value is expressed as a range where min == max.
- No implicit conversion of a range to a midpoint.

### Unit policy

All numeric engineering values use `Quantity` (Decimal + Unit).  No bare
floats.  No free-form unit strings for controlled-vocabulary units.

---

## 7. Process Applicability

`ApplicabilityScope.operation_type` accepts `OperationType` enum values
(reusing the existing domain enum):

`TURNING · FACING · MILLING · DRILLING · BORING · REAMING · TAPPING ·
THREADING · GRINDING · DEBURRING · INSPECTION · HEAT_TREATMENT · OTHER`

A `None` operation type means "not specified by the source" — not "applies
to all processes".  Callers should treat it as a partial match.

---

## 8. Material Applicability

`ApplicabilityScope.iso_material_group` accepts `IsoMaterialGroup` values
(new enum added in Stage 3G):

| Group | Meaning |
|---|---|
| `P` | Steel |
| `M` | Stainless steel |
| `K` | Cast iron |
| `N` | Non-ferrous (aluminium, copper alloys, etc.) |
| `S` | Superalloys, titanium |
| `H` | Hardened steel |

Records can also be associated with specific `Material` instances via the
`MaterialCatalog`.  ISO group is stored in
`material.machinability_metadata["iso_material_group"]` as a convention
for Stage 3G; a full ISO group model is deferred.

Production seed data in the `MaterialCatalog` is **zero** at Stage 3G.

---

## 9. Tool Applicability

`ApplicabilityScope` accepts `ToolMaterial` (new enum, Stage 3G) and
`ToolType` (existing enum).

| ToolMaterial | Meaning |
|---|---|
| `HSS` | High-speed steel |
| `carbide` | Cemented carbide |
| `cermet` | Cermet |
| `ceramic` | Ceramic |
| `CBN` | Cubic boron nitride |
| `PCD` | Polycrystalline diamond |

Specific `Tool` instances are managed by `ToolCatalog`.
Production seed data is **zero** at Stage 3G.

---

## 10. Provenance

Every `CuttingParameterRecord` carries a `Provenance` instance (reusing
the existing domain model).

Required fields for authoritative use:

- `source_type`: must be in `ACCEPTABLE_AUTHORITATIVE_SOURCE_TYPES`
  (`MANUFACTURER_DATA`, `MATERIAL_STANDARD`, `ENGINEERING_STANDARD`,
  `LITERATURE`, `HISTORICAL_PROCESS_DATA`, `USER_INPUT`).
- `source_reference`: must be non-None (identifies the exact document,
  table, page).

Explicitly **rejected** source types for authoritative records:
`AI_SUGGESTION`, `UNKNOWN`.

---

## 11. Evidence Classification

`EvidenceStatus` is an engineering classification — not a probability.

| Status | Meaning | Authoritative? |
|---|---|---|
| `AUTHORITATIVE` | Primary source (manufacturer bulletin, standard, experiment) | Yes |
| `EXPERIMENTAL` | Internal experiment, pending review | Yes |
| `REFERENCE_ONLY` | Secondary source (textbook, training material) | No |
| `UNVERIFIED` | Source not confirmed | No |

`is_authoritative` is `True` only when:
1. `evidence_status` ∈ {`AUTHORITATIVE`, `EXPERIMENTAL`}, AND
2. `provenance.source_reference` is not None.

`require_authoritative()` raises `EmpiricalDataError` when these
conditions are not met.

---

## 12. Validation

All validation runs in `__post_init__`; no silent coercion.

Key validation rules:

- `record_id` must be a non-empty string.
- `parameter_type` must be a `ParameterType`.
- `value_range.unit` must match `PARAMETER_CANONICAL_UNIT[parameter_type]`.
- `applicability` must be an `ApplicabilityScope`.
- `provenance` must be a `Provenance`.
- `evidence_status` must be an `EvidenceStatus`.
- AUTHORITATIVE/EXPERIMENTAL status requires `source_reference` → fails closed.
- `bool` arguments are rejected by `_to_decimal` in `Quantity`.

---

## 13. Lookup Semantics

`CuttingParameterRegistry.get(record_id)`:
- Found → returns the record.
- Not found → raises `EmpiricalDataError`.

`CuttingParameterRegistry.find(scope=…, parameter_type=…, evidence_status=…)`:
- Returns **all** matching records sorted by `record_id`.
- Zero matches → returns empty tuple (not an error).
- `None` filter → not applied (matches all).

`find_authoritative(…)`: same as `find`, filtered to `is_authoritative == True`.

---

## 14. Multiple Matches and Conflicts

When a query matches multiple records:

- All matching records are returned in deterministic order.
- No automatic selection.
- No ranking.
- No averaging.
- The caller decides how to handle multiple results.

Example: Source A says Vc = 180–220 m/min; Source B says Vc = 240–280 m/min
for the same scope.  Both records are returned.  The caller sees both
provenances and decides.

---

## 15. Duplicate Semantics

Two records are **exact duplicates** when they share the same `record_id`.
The registry rejects duplicate IDs at registration.

Two records with **different IDs but the same scope and values** from
different sources are **distinct records** and are both preserved.  This is
the correct handling of agreeing sources.

Two records with **different values for the same scope** from different
sources are **conflicting records**.  Both are preserved; neither is
automatically preferred.

---

## 16. Fail-Closed Behavior

| Condition | Behavior |
|---|---|
| Missing `record_id` | `ValidationError` at construction |
| Wrong unit for parameter type | `ValidationError` at construction |
| `min_value > max_value` | `ValidationError` at construction |
| AUTHORITATIVE + no `source_reference` | `ValidationError` at construction |
| `AI_SUGGESTION` provenance | `EmpiricalDataError` from `require_authoritative` |
| Exact-ID lookup, not found | `EmpiricalDataError` |
| Duplicate ID registration | `EmpiricalDataError` |
| `NaN` or `Infinity` in quantity | `UnitError` |
| `bool` passed as numeric | `UnitError` |

No silent defaults.  No silent fallbacks.  Unknown is `None`, not zero.

---

## 17. CAM Source Material Policy

The `CAM/` directory contains Turkish-language educational documents
(Mastercam training notes, a CAM learning guide, and a CAM overview report).

These documents:
- Contain indicative parameter tables explicitly labelled as
  *"yaklaşık aralıklardır"* (approximate ranges) and *"sadece örnek"*
  (examples only).
- Cite unidentified sources (e.g., "[66]" without full reference).
- Are pedagogical in nature — they explain formulas, not provide
  calibration data.

**Policy:**

> CAM tutorial and example values are NEVER production seeds.
> They are useful as test fixtures only when clearly labelled as such.

The worked example from SRC-002 §6.2 (Vc = 250 m/min, fz = 0.05 mm/tooth
for Ø10 carbide end mill in an unspecified material) appears in some test
files clearly marked as a test fixture, not a recommendation.

---

## 18. Examples

All examples below use clearly synthetic or test-fixture data.

### Constructing a test record (fixture, NOT production data)

```python
from backend.cutting_parameters.models import (
    ApplicabilityScope, CuttingParameterRecord, EvidenceStatus,
    ParameterType, QuantityRange,
)
from backend.cutting_parameters.registry import CuttingParameterRegistry
from backend.domain.base import Provenance
from backend.domain.enums import (
    IsoMaterialGroup, OperationType, ProvenanceType, ToolMaterial,
)
from backend.domain.units import Quantity, Unit

# Build a record — requires real provenance for authoritative status
record = CuttingParameterRecord(
    record_id="VC-P-TURN-CARBIDE-001",
    parameter_type=ParameterType.CUTTING_SPEED,
    value_range=QuantityRange(
        min_value=Quantity.of("200", Unit.M_MIN),
        max_value=Quantity.of("350", Unit.M_MIN),
    ),
    applicability=ApplicabilityScope(
        operation_type=OperationType.TURNING,
        iso_material_group=IsoMaterialGroup.P,
        tool_material=ToolMaterial.CARBIDE,
    ),
    provenance=Provenance(
        source_type=ProvenanceType.MANUFACTURER_DATA,
        source_reference="Sandvik Coromant Turning Catalogue 2023, Table 3.4, p.187",
        source_document="Sandvik Coromant General Catalogue 2023",
    ),
    evidence_status=EvidenceStatus.AUTHORITATIVE,
    notes="Applicable to uncoated ISO P10–P30 grades at flood coolant.",
)

# Register and query
registry = CuttingParameterRegistry()
registry.register(record)

results = registry.find(
    scope=ApplicabilityScope(
        operation_type=OperationType.TURNING,
        iso_material_group=IsoMaterialGroup.P,
    ),
    parameter_type=ParameterType.CUTTING_SPEED,
)
# results: tuple of all matching records — not a single "best" value.
# Multiple sources → multiple records → caller decides.
```

---

## 19. Non-Goals

Stage 3G does NOT implement:

- Production cutting-speed or feed recommendation engine
- Optimization logic
- Machine selection
- Tool selection
- CAM toolpath generation
- CAPP / process planning
- DFM rules
- Cost model
- AI / RAG / LLM integration
- Database persistence (SQLite, PostgreSQL)
- External API endpoints
- Vendor catalog ingestion (Sandvik, Kennametal, Seco, etc.)
- Taylor tool-life equation evaluation
- Kienzle cutting-force model evaluation
- Surface roughness prediction

---

## 20. Future Integration

Stage 3G is the data foundation.  Future stages build on it:

| Stage | Builds on 3G by… |
|---|---|
| 3H | Machine capability validation — checks spindle power, rpm limits |
| 4 | Parameter recommendation — deterministically retrieves records from 3G to suggest Vc/fz |
| 5 | DFM — uses material and process scope from 3G for DFM checks |
| 6 | CAPP — generates process plans using 3G parameter records |
| 7 | Cost model — uses 3G Vc/fz/MRR records to compute cycle time |
| 8 | AI advisory — uses 3G provenance contracts to distinguish authoritative from advisory |

---

## Stage 3G Rule ID Range

Stage 3G adds no `EngineeringRule` instances.  It is a data-layer stage.
The next `EngineeringRule` block begins at Stage 3H (rule IDs TBD).
