# MachineryPro AI — DFM / Process Feasibility Foundation

**Stage:** 3I
**Status:** Implemented
**Rule ID range:** R-2701 – R-2712

---

## 1. Purpose

Stage 3I answers:

> **Is this feature geometrically and physically compatible with this
> process condition, given this tool and machine?**

It provides deterministic, traceable feasibility checks over explicit
part-feature and process inputs.  No CAD parsing, no automatic process
planning, no AI.

---

## 2. Engineering Authority

```
DETERMINISTIC ENGINEERING MATH (Stages 3A–3F)
= AUTHORITATIVE

EMPIRICAL ENGINEERING DATA (Stage 3G)
= SOURCE-BOUNDED AUTHORITATIVE INPUT

MACHINE CAPABILITY (Stage 3H)
= EXPLICIT MACHINE CONSTRAINTS

DFM / FEASIBILITY (Stage 3I)
= DETERMINISTIC RULE EVALUATION OVER EXPLICIT INPUTS

AI = ADVISORY ONLY — never overrides any of the above
```

No DFM conclusion may come from hidden assumptions.

---

## 3. Relationship to Stages 3A–3H

| Stage | Adds |
|---|---|
| 3A | Machining math: n, Vf, MRR, t, P, T |
| 3B–3F | Turning / milling / drilling / threading / hole-finishing geometry |
| 3G | Empirical data contracts: records, provenance |
| 3H | Machine capability: RPM, feed, power, torque, envelope checks |
| **3I** | **DFM / process feasibility: geometry + process–feature compatibility + machine composition + aggregate** |

Stage 3I does not replace or modify any earlier stage.  It composes their
results and adds geometry compatibility checks.

---

## 4. Feature Inputs

Stage 3I reuses the existing `Feature` domain entity unchanged.

Key `Feature` fields used:

| Field | Type | Used for |
|---|---|---|
| `feature_type` | `FeatureType` | Process–feature compatibility (R-2705) |
| `dimensions["diameter"]` | Quantity (mm) | Hole checks (R-2701, R-2706) |
| `dimensions["depth"]` | Quantity (mm) | Depth/diameter ratio (R-2706) |
| `dimensions["corner_radius"]` | Quantity (mm) | Corner check (R-2702) |
| `dimensions["width"]` | Quantity (mm) | Slot check (R-2703), depth/diameter fallback |
| `dimensions["opening_width"]` | Quantity (mm) | Pocket access (R-2704) |

All dimension keys are caller-supplied.  Missing keys → INSUFFICIENT_DATA (fail closed).

---

## 5. Tool / Geometry Compatibility

Stage 3I reuses the existing `Tool` domain entity.  `Tool.diameter` (in mm) is
the only tool field used by Stage 3I checks.

All geometry checks are pure physics — not empirical thresholds:

| Check | Rule | Condition | Physics |
|---|---|---|---|
| Hole / drill | R-2701 | `tool.diameter == hole_diameter` | A drill must match the hole |
| Corner radius | R-2702 | `tool.diameter/2 ≤ corner_radius` | A tool cannot machine a tighter corner |
| Slot width | R-2703 | `tool.diameter ≤ slot_width` | A tool must physically fit in the slot |
| Pocket access | R-2704 | `tool.diameter ≤ opening_width` | A tool must enter the pocket |

---

## 6. Machine Capability Composition

Stage 3I does not re-implement machine capability checks.  It composes
Stage 3H results via `compose_machine_result` (R-2710):

```python
# Stage 3H
machine_result = check_spindle_speed(machine, calculated_rpm)

# Stage 3I wraps it
dfm_machine = compose_machine_result(machine_result)
# → PASS / FAIL / INSUFFICIENT_DATA / WARNING, rule_id R-2710
```

The Stage 3H result is preserved with all outputs and violations intact.

---

## 7. Empirical Capability Inputs

Stage 3I may accept an explicit empirical capability limit (e.g. a
depth/diameter threshold from a governed empirical record).  The caller
must resolve any ambiguity from the Stage 3G registry before passing the
limit — Stage 3I does not query or rank empirical records automatically.

Example: `check_depth_diameter_ratio(feature, explicit_limit=Decimal("5"))`.

Without `explicit_limit`, the ratio is calculated and returned as a WARNING
for the caller to evaluate.  No arbitrary threshold is hard-coded.

---

## 8. Supported Feasibility Checks

| Rule | Function | Description |
|---|---|---|
| R-2701 | `check_hole_tool_diameter` | Drill diameter == hole diameter |
| R-2702 | `check_corner_radius_tool` | Tool radius ≤ internal corner radius |
| R-2703 | `check_slot_width_tool` | Tool diameter ≤ slot width |
| R-2704 | `check_pocket_access` | Tool diameter ≤ pocket opening |
| R-2705 | `check_process_feature_compatibility` | Operation type compatible with feature type |
| R-2706 | `check_depth_diameter_ratio` | Calculate ratio; validate against explicit limit |
| R-2710 | `compose_machine_result` | Wrap Stage 3H result in DFM envelope |
| R-2712 | `aggregate_feasibility` | Combine all results into one status |

**Not implemented (no authoritative capability data):**
- Tolerance feasibility (`NOT_IMPLEMENTED_NO_AUTHORITATIVE_CAPABILITY_DATA`)
- Surface finish feasibility (`NOT_IMPLEMENTED_NO_AUTHORITATIVE_CAPABILITY_DATA`)
- Thin-wall threshold (`NOT_IMPLEMENTED_NO_AUTHORITATIVE_CAPABILITY_DATA`)

---

## 9. Aggregate Feasibility

`aggregate_feasibility(results)` — R-2712:

| Condition | Status |
|---|---|
| Any FAIL | FAIL (physical violation is definitive) |
| No FAIL, any INSUFFICIENT_DATA | INSUFFICIENT_DATA |
| No FAIL or INSUFFICIENT_DATA, any WARNING | WARNING |
| All PASS | PASS |
| Empty results | INSUFFICIENT_DATA |

**Partial information can never produce PASS.**

---

## 10. Missing Data / Fail-Closed Behavior

| Missing data | Result |
|---|---|
| `feature.dimensions["diameter"]` absent | INSUFFICIENT_DATA |
| `feature.dimensions["depth"]` absent when needed | INSUFFICIENT_DATA |
| `feature.dimensions["corner_radius"]` absent | INSUFFICIENT_DATA |
| `feature.dimensions["width"]` absent for slot | INSUFFICIENT_DATA |
| `feature.dimensions["opening_width"]` absent for pocket | INSUFFICIENT_DATA |
| `explicit_limit` not supplied to R-2706 | WARNING (calculated, no PASS/FAIL) |
| `operation_type` not in compatibility table | INSUFFICIENT_DATA |
| Machine check not runnable (Stage 3H returns INSUFFICIENT_DATA) | INSUFFICIENT_DATA propagated |

Nothing is silently assumed.  Unknown is INSUFFICIENT_DATA, not PASS.

---

## 11. Units

All geometry dimensions are in `mm`.  Wrong unit → FAIL.

| Quantity | Unit |
|---|---|
| Feature dimensions | mm |
| Tool diameter | mm |
| Depth/diameter ratio | dimensionless |
| Corner clearance | mm |
| Width clearance | mm |
| Access margin | mm |

---

## 12. Determinism

- Pure functions — identical inputs → identical outputs.
- Frozen `EngineeringResult` — immutable once returned.
- No hidden state, no randomness, no network calls, no AI.
- `Decimal` arithmetic for ratio calculations.

---

## 13. Examples

### Full workflow: Stage 3A → Stage 3H → Stage 3I

```python
from backend.machining.formulas import spindle_speed_from_cutting_speed
from backend.machines.validation import check_spindle_speed
from backend.dfm.validation import (
    check_hole_tool_diameter, check_process_feature_compatibility,
    compose_machine_result, aggregate_feasibility,
)

# Stage 3A
n = spindle_speed_from_cutting_speed(
    Quantity.of("100", Unit.M_MIN),
    Quantity.of("10", Unit.MM),
)  # ≈ 3183 rpm

# Stage 3H
machine_r = check_spindle_speed(machine, n)   # PASS if machine supports 3183 rpm

# Stage 3I geometry
hole_r   = check_hole_tool_diameter(hole_feature, drill)
process_r = check_process_feature_compatibility(hole_feature, OperationType.DRILLING)
machine_composed = compose_machine_result(machine_r)

# Stage 3I aggregate
agg = aggregate_feasibility((hole_r, process_r, machine_composed))
# PASS only if ALL three checks passed
```

### Depth/diameter ratio with explicit limit

```python
from decimal import Decimal
result = check_depth_diameter_ratio(feature, explicit_limit=Decimal("5"))
# Explicit limit comes from a governed empirical record — never invented here
```

---

## 14. Non-Goals

Stage 3I does NOT implement:

- Automatic CAD feature recognition
- STEP / PDF drawing interpretation
- Automatic process planning or operation sequencing
- Tool recommendation or tool selection
- Machine recommendation or machine selection
- Fixture design or collision checking
- 3D accessibility analysis
- Tolerance stack analysis
- Surface roughness prediction
- Tool wear, chatter, or vibration analysis
- Cost estimation or scheduling
- AI, ML, RAG, or LLM

---

## 15. Future CAD / CAPP Integration

Stage 3I establishes the feasibility evaluation layer.  Future stages build
on it:

| Future stage | Uses Stage 3I by… |
|---|---|
| CAPP / process planning | Evaluating each candidate operation for feasibility before sequencing |
| Tool selection | First filtering to tools that pass R-2701–R-2704 geometry checks |
| Cost model | Computing cycle time only for feasible conditions |
| CAD integration | Feeding recognised features into Stage 3I checks automatically |
