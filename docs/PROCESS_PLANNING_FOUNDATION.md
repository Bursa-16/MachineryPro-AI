# MachineryPro AI — Deterministic Process Planning Foundation

**Stage:** 3J
**Status:** Implemented
**Rule ID range:** R-2801 – R-2810

---

## 1. Purpose

Stage 3J establishes the data contracts and validation layer for explicit,
traceable, human-reviewable process plans.

It answers:

> **Given explicit feature, operation, tool, machine, and empirical parameter
> assignments, are they mutually compatible and do they collectively constitute
> a valid machining step?**

Stage 3J does NOT generate plans.  All engineering decisions are explicit
caller inputs.  Stage 3J validates them.

---

## 2. Engineering Authority

```
DETERMINISTIC MACHINING MATH (Stages 3A–3F) = AUTHORITATIVE
EMPIRICAL ENGINEERING DATA (Stage 3G)        = SOURCE-BOUNDED INPUT
MACHINE CAPABILITY (Stage 3H)                = EXPLICIT CONSTRAINTS
DFM FEASIBILITY (Stage 3I)                   = GEOMETRIC / PROCESS CHECKS
PROCESS PLAN (Stage 3J)                      = VALIDATED EXPLICIT DECISIONS
AI                                           = ADVISORY ONLY
```

---

## 3. Relationship to Stages 3A–3I

| Stage | Adds |
|---|---|
| 3A–3F | Machining math: RPM, feed, MRR, time, power, torque |
| 3G | Empirical data contracts: records, provenance, authority |
| 3H | Machine capability: RPM, feed, power, torque, envelope |
| 3I | DFM/feasibility: geometry, process-feature compatibility |
| **3J** | **Process plan: explicit assignments + composed validation** |

Stage 3J composes R-2806 (DFM, from 3I) and R-2807 (machine, from 3H) into
a single step-level validation workflow.  No logic from earlier stages is
duplicated.

---

## 4. Process Plan

`ProcessPlan` — an immutable, ordered, traceable collection of steps.

| Field | Type | Purpose |
|---|---|---|
| `plan_id` | str | Stable unique identifier |
| `part_id` | str | The part this plan applies to |
| `steps` | tuple[ProcessPlanStep] | Ordered steps (sorted by sequence_index) |
| `engineering_status` | PlanStatus | Aggregate engineering validity |
| `review_status` | ReviewStatus | Human review state (independent) |
| `provenance` | Provenance | Who created this plan |
| `notes` | str \| None | Optional notes |

`plan.ordered_steps` always returns steps sorted by `sequence_index`
(deterministic).

---

## 5. Process Plan Step

`ProcessPlanStep` — one explicit manufacturing step.

| Field | Type | Required? | Notes |
|---|---|---|---|
| `step_id` | str | Yes | Unique within the plan |
| `sequence_index` | int (≥ 0) | Yes | Ordering position |
| `feature_id` | str \| None | Caller decision | Required for DFM/geometry checks |
| `operation_type` | OperationType \| None | Caller decision | Required for process-feature compatibility |
| `tool_id` | str \| None | Caller decision | Required for geometry checks |
| `machine_id` | str \| None | Caller decision | Required for capability validation |
| `parameter_record_ids` | tuple[str] | Caller decision | IDs of CuttingParameterRecord instances |
| `predecessor_step_ids` | tuple[str] | Caller decision | Must reference existing step IDs |
| `engineering_status` | PlanStatus | Set after validation | VALIDATED / INCOMPLETE / INVALID |
| `review_status` | ReviewStatus | Human lifecycle | NOT_REVIEWED / APPROVED / REJECTED |

---

## 6. Explicit Assignments

Stage 3J validates only what the caller explicitly supplies.  Nothing is
inferred, defaulted, or selected automatically.

| Assignment | Stage 3J behaviour |
|---|---|
| Operation type | Must be an OperationType enum value if supplied |
| Tool | Referenced by ID; geometry validated if tool object supplied |
| Machine | Referenced by ID; capability validated if machine object supplied |
| Empirical records | Authority-checked via Stage 3G `is_usable_for_authority()` |

**No assignment is ever chosen automatically.**

---

## 7. Sequencing

Steps are ordered by `sequence_index` (integer, ≥ 0).  Duplicate sequence
indexes are rejected (R-2802).  The plan sorts steps deterministically by
`sequence_index` during build.

No optimisation, no automatic reordering.

---

## 8. Dependencies

`predecessor_step_ids` declares explicit ordering dependencies.

Validated by:
- R-2803: every predecessor ID must exist in the plan; no self-reference.
- R-2804: the dependency graph must be acyclic (Kahn's algorithm).

Dependency cycles → INVALID.

---

## 9. Feature / Operation Validation

R-2806 composes Stage 3I checks:
- Process–feature type compatibility (R-2705 via Stage 3I)
- Hole/drill diameter (R-2701 via Stage 3I)
- Slot/tool width (R-2703 via Stage 3I)
- Pocket access (R-2704 via Stage 3I)
- Corner radius/tool radius (R-2702 via Stage 3I, when corner_radius is present)

Stage 3I logic is NOT duplicated.

---

## 10. Tool Assignment Validation

Tool geometry compatibility is validated via Stage 3I (R-2806).
The caller supplies both the `Feature` object and the `Tool` object.
Stage 3J passes them to Stage 3I and reports the result.

No tool selection.  No tool recommendation.

---

## 11. Machine Capability Validation

R-2807 composes Stage 3H checks:
- Spindle speed (R-2601 via Stage 3H)
- Feed rate (R-2602 via Stage 3H)
- Power (R-2603 via Stage 3H)
- Torque (R-2604 via Stage 3H)

Only the quantities the caller explicitly supplies are checked.
Stage 3H logic is NOT duplicated.

No machine selection.  No machine recommendation.

---

## 12. Empirical Parameter References

R-2808 validates that every `CuttingParameterRecord` referenced by the
step is authoritative (per Stage 3G `is_usable_for_authority()`).

Unverified records → INCOMPLETE (data exists but lacks authority).
Missing records → INCOMPLETE (data not supplied).

No automatic record selection.  If multiple records match and the caller
has not resolved the ambiguity, Stage 3J cannot determine which is correct.

---

## 13. Deterministic Derived Parameters

The caller may use Stage 3A–3F formulas to compute derived values:

```python
# Stage 3A
n = spindle_speed_from_cutting_speed(Quantity.of("100", Unit.M_MIN),
                                     Quantity.of("10", Unit.MM))
# → passes to Stage 3H via validate_step_machine_capability(step, machine, requested_rpm=n)
```

Stage 3J accepts these as explicit inputs.  No formula is duplicated.

---

## 14. Engineering Status

| Status | Meaning |
|---|---|
| VALIDATED | All mandatory checks explicitly evaluated and passed |
| INCOMPLETE | No failure; required data or validation is missing |
| INVALID | At least one mandatory check failed |

**Partial information can never produce VALIDATED.**

Aggregate hierarchy: `INVALID > INCOMPLETE > VALIDATED`.

---

## 15. Human Review State

`ReviewStatus` is independent of engineering validity:

| Status | Meaning |
|---|---|
| NOT_REVIEWED | No human has reviewed this plan/step |
| APPROVED | A human has approved it |
| REJECTED | A human has rejected it |

A plan may be VALIDATED (engineering) and NOT_REVIEWED (human) simultaneously.
These are orthogonal axes.  No approval workflow, no user management.

---

## 16. Traceability

Every validated step retains references to:
- `feature_id` — the part feature
- `operation_type` — the process
- `tool_id` — the assigned tool
- `machine_id` — the assigned machine
- `parameter_record_ids` — the empirical cutting records
- DFM result (R-2806) — carried in EngineeringResult
- Machine capability result (R-2807) — carried in EngineeringResult
- Engineering status — derived from all check results

The engineering chain is never collapsed into an opaque boolean.

---

## 17. Fail-Closed Behavior

| Condition | Status |
|---|---|
| Missing `feature_id`, `operation_type`, `tool_id`, `machine_id` | INCOMPLETE |
| DFM check fails (geometric violation) | INVALID |
| Machine capability exceeds limit | INVALID |
| Empirical record unverified | INCOMPLETE |
| Empirical record not supplied | INCOMPLETE |
| Duplicate step ID | INVALID |
| Duplicate sequence index | INVALID |
| Dependency cycle | INVALID |
| Missing predecessor reference | INVALID |
| Empty plan | INCOMPLETE |

---

## 18. Synthetic Example

```python
from backend.machining.formulas import spindle_speed_from_cutting_speed
from backend.machines.validation import check_spindle_speed
from backend.process_planning import (
    ProcessPlanStep, ProcessPlanBuilder, PlanStatus,
    validate_step_completeness, validate_step_dfm,
    validate_step_machine_capability, validate_step_empirical_records,
    aggregate_step_status,
)

# Stage 3A: derive RPM
n = spindle_speed_from_cutting_speed(
    Quantity.of("100", Unit.M_MIN), Quantity.of("10", Unit.MM)
)

# Build step (explicit assignments)
step = ProcessPlanStep(
    step_id="S-DRILL-001", sequence_index=0,
    feature_id=hole.feature_id, operation_type=OperationType.DRILLING,
    tool_id=drill.tool_id, machine_id=machine.machine_id,
    parameter_record_ids=(vc_record.record_id,),
)

# Validate
r_complete  = validate_step_completeness(step)
r_dfm       = validate_step_dfm(step, hole, drill)          # Stage 3I
r_machine   = validate_step_machine_capability(step, machine, requested_rpm=n)  # Stage 3H
r_empirical = validate_step_empirical_records(step, (vc_record,))  # Stage 3G

status = aggregate_step_status((r_complete, r_dfm, r_machine, r_empirical))
# → PlanStatus.VALIDATED if all pass

# Set status on step (step is frozen; create a new one)
validated_step = ProcessPlanStep(**{**step.as_dict(), "engineering_status": status})

# Build plan
plan = ProcessPlanBuilder("PP-001", "PART-001", provenance).add_step(validated_step).build()
# plan.engineering_status → PlanStatus.VALIDATED
```

---

## 19. Non-Goals

Stage 3J does NOT implement:

- Automatic process selection or process plan generation
- Tool recommendation or tool selection
- Machine recommendation or machine selection
- Automatic empirical record selection
- Automatic cutting parameter recommendation
- Routing optimisation or setup optimisation
- Fixture design or workholding selection
- Datum planning
- Costing, scheduling, or APS
- CAD parsing, STEP interpretation, or drawing recognition
- CAM, toolpath generation, G-code, or postprocessor
- Simulation, collision checking, or 3D accessibility
- AI, ML, RAG, or LLM

---

## 20. Future CAPP / CAM Integration

Stage 3J is the plan-structure and plan-validation layer.  Future stages:

| Future stage | Builds on 3J by… |
|---|---|
| CAPP | Generating and sequencing steps automatically from feature analysis |
| Setup planning | Grouping steps by machine setup and datum |
| Costing | Computing cycle time from validated step parameters |
| CAM review | Comparing planned parameters to actual CAM toolpath data |
| Scheduling (APS) | Sequencing validated plans across a machine shop |
