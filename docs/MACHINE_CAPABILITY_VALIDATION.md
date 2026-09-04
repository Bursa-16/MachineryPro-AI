# MachineryPro AI — Machine Capability Validation Foundation

**Stage:** 3H
**Status:** Implemented
**Rule ID range:** R-2601 – R-2605

---

## 1. Purpose

Stage 3H answers one deterministic engineering question:

> **Can this machine safely and explicitly support this requested machining condition?**

It validates a single engineering value (e.g. requested spindle speed, required
power) against explicit machine capability limits.  It does not recommend
machines, rank machines, or optimise utilisation.

---

## 2. Authority Model

```
DETERMINISTIC MACHINING MATH (Stages 3A–3F)
= AUTHORITATIVE

EMPIRICAL ENGINEERING DATA (Stage 3G)
= SOURCE-BOUNDED AUTHORITATIVE INPUT

MACHINE CAPABILITY DATA (Stage 3H)
= EXPLICIT MACHINE CONSTRAINTS
  (machine.spindle_speed_max, machine.spindle_power, etc.)

AI
= ADVISORY ONLY — never overrides any of the above
```

Machine limits are **constraints**, never recommendations.  A check that
returns PASS confirms feasibility — it does not imply the condition is
optimal.

---

## 3. Relationship to Stages 3A–3G

| Stage | Adds |
|---|---|
| 3A | Machining math: n, Vf, MRR, t, P, T (pure formulas) |
| 3B | Turning geometry |
| 3C | Milling geometry |
| 3D | Drilling geometry |
| 3E | Threading geometry |
| 3F | Hole finishing geometry |
| 3G | Empirical data contracts: records, provenance, registry |
| **3H** | **Machine capability validation: feasibility checks against explicit limits** |

Stage 3H does not replace or bypass earlier stages.  A typical workflow:

1. Calculate spindle speed using Stage 3A (`spindle_speed_from_cutting_speed`).
2. Validate the calculated speed against the target machine using Stage 3H
   (`check_spindle_speed`).

---

## 4. Machine Model Reuse

Stage 3H reuses the existing
:class:`~backend.domain.machine.Machine` domain entity without modification.

The Machine entity carries:

| Field | Type | Required? | Stage 3H use |
|---|---|---|---|
| `machine_id` | str | Yes | Identification in results |
| `spindle_speed_min` | Quantity (rpm) | Yes | Lower RPM bound (R-2601) |
| `spindle_speed_max` | Quantity (rpm) | Yes | Upper RPM bound (R-2601) |
| `spindle_power` | Quantity (kW) | Yes | Power limit (R-2603) |
| `spindle_torque` | Quantity (Nm) | Optional | Torque limit (R-2604) — INSUFFICIENT_DATA if None |
| `feed_rate_max` | Quantity (mm/min) | Optional | Feed limit (R-2602) — INSUFFICIENT_DATA if None |
| `working_envelope` | Mapping[str, Quantity] | Optional | Axis limits (R-2605) |

**No new machine model was created.**

---

## 5. Machine Catalog

`MachineCatalog` is a deterministic in-memory registry.

```python
from backend.machines.catalog import MachineCatalog

catalog = MachineCatalog()
catalog.register(machine)       # raises EmpiricalDataError on duplicate ID
machine = catalog.get("M-001") # raises EmpiricalDataError if not found
catalog.all()                   # sorted by machine_id (deterministic)
```

No production machine data is included.  No OEM specs.  No web-scraped
catalog entries.

---

## 6. Supported Capability Checks

| Rule | Function | Validates | Limit field | INSUFFICIENT_DATA when |
|---|---|---|---|---|
| R-2601 | `check_spindle_speed` | requested_rpm ∈ [min, max] | `spindle_speed_min/max` | never (always present) |
| R-2602 | `check_feed_rate` | requested_feed_rate ≤ max | `feed_rate_max` | `feed_rate_max is None` |
| R-2603 | `check_power` | required_power ≤ spindle_power | `spindle_power` | never (always present) |
| R-2604 | `check_torque` | required_torque ≤ spindle_torque | `spindle_torque` | `spindle_torque is None` |
| R-2605 | `check_work_envelope_dimension` | requested ≤ envelope[key] | `working_envelope[key]` | key absent from envelope |

**Not implemented (domain model does not support these fields):**

- Tool/holder diameter or length envelope — `Tool` and `Machine` do not have
  a joined holder-compatibility model.  Deferred.
- Axis travel asymmetry — `working_envelope` stores one value per key; signed
  travel limits are not supported.

---

## 7. Result Semantics

Every capability check returns an `EngineeringResult` with:

| Field | Content |
|---|---|
| `rule_id` | e.g. `"R-2601"` |
| `rule_version` | `"1.0.0"` |
| `status` | `PASS` / `FAIL` / `INSUFFICIENT_DATA` |
| `provenance` | deterministic provenance (source_type = DETERMINISTIC_CALCULATION) |
| `outputs` | requested value, machine limit, margin, utilisation ratio (on PASS) |
| `violations` | human-readable failure description (on FAIL) |
| `missing_inputs` | which limit was absent (on INSUFFICIENT_DATA) |
| `summary` | one-line plain-language summary |

**`PASS` does not mean recommended.**  It means the condition is within the
machine's declared limits.

---

## 8. Fail-Closed Behavior

| Condition | Result |
|---|---|
| `machine.spindle_torque is None` and torque check requested | `INSUFFICIENT_DATA` |
| `machine.feed_rate_max is None` and feed check requested | `INSUFFICIENT_DATA` |
| Envelope key absent from `machine.working_envelope` | `INSUFFICIENT_DATA` |
| Wrong unit on any input quantity | `FAIL` |
| `NaN` or `Infinity` on any input | rejected by `Quantity` constructor |
| `bool` passed as numeric | rejected by `Quantity` constructor |
| Required rule input missing (None) | `INSUFFICIENT_DATA` (base `EngineeringRule.evaluate`) |

**An unknown limit is never treated as "no constraint".**

---

## 9. Missing Capability Data

A machine that does not declare a limit is not assumed to have an infinite
one.  Missing data forces `INSUFFICIENT_DATA`.

Example:

```python
# Machine with no spindle_torque declared
result = check_torque(machine, required_torque)
# → INSUFFICIENT_DATA, missing_inputs=("machine.spindle_torque",)
```

If a machine's torque limit has not been measured, the validation is
impossible — fail closed.

---

## 10. Capability Margin

On `PASS`, the outputs include:

- **margin** = `limit − requested` (in the same unit as the limit).
- **utilization_ratio** = `requested / limit` (dimensionless, 4 d.p.).

These are diagnostic outputs only.  No traffic-light thresholds, no scoring,
no automatic selection based on margin size.

Example: `requested_rpm = 6000`, `spindle_speed_max = 10000` →
`margin_rpm = 4000 rpm`, `utilization_ratio = 0.6000`.

---

## 11. Determinism

Every validation function:

- Takes identical inputs → always produces identical outputs.
- Uses `Decimal` arithmetic — no binary float.
- Returns frozen `EngineeringResult` — immutable.
- Does not mutate the `Machine` or any input argument.
- Has no hidden state.

---

## 12. Examples

### Check spindle speed from a Stage 3A calculation

```python
from backend.machining.formulas import spindle_speed_from_cutting_speed
from backend.machines.validation import check_spindle_speed
from backend.domain.units import Quantity, Unit

# Stage 3A: compute spindle speed
n = spindle_speed_from_cutting_speed(
    Quantity.of("200", Unit.M_MIN),  # Vc
    Quantity.of("10", Unit.MM),      # D
)
# n ≈ 6366 rpm

# Stage 3H: validate against machine
result = check_spindle_speed(machine, n)
# result.status → PASS if machine supports 6366 rpm
# result.outputs["margin_rpm"] → headroom below max RPM
# result.outputs["utilization_ratio"] → n / max_rpm
```

### Check power without implicit efficiency

```python
from backend.machines.validation import check_power

# Caller supplies required power including any efficiency calculation
result = check_power(machine, Quantity.of("12.5", Unit.KW))
# No efficiency factor is applied inside check_power.
# If derated power is wanted, the caller computes: required = raw / efficiency
```

### Fail-closed missing torque limit

```python
result = check_torque(minimal_machine, Quantity.of("80", Unit.NM))
# minimal_machine.spindle_torque is None
# result.status → INSUFFICIENT_DATA
# result.missing_inputs → ("machine.spindle_torque",)
```

---

## 13. Non-Goals

Stage 3H does NOT implement:

- Machine recommendation or ranking
- Capacity planning or OEE
- Scheduling or APS
- Machine utilisation optimisation
- Shop-floor connectivity (MTConnect, OPC UA)
- Real-time spindle load
- Tool changer or fixture compatibility
- Post-processor selection
- CAM / CAPP / DFM / costing
- AI recommendation, ML, RAG
- Vendor machine database

---

## 14. Future Machine Selection / Scheduling

Stage 3H provides the building block.  Future stages may build on it:

| Future stage | Uses Stage 3H by… |
|---|---|
| Process planning (CAPP) | Checking each candidate machine against process requirements |
| Cost model | Using cycle-time calculation with validated parameters |
| Machine selection | Filtering machines to those that pass all Stage 3H checks |
| Scheduling (APS) | Validating job-machine compatibility before assignment |

Machine selection and ranking belong AFTER feasibility is established.
Stage 3H is the feasibility layer only.
