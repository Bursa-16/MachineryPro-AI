# MachineryPro AI — Deterministic Drilling Engineering Core

**Stage:** 3D
**Status:** Closed
**Scope:** Deterministic drilling-specific calculations and engineering rules

---

## 1. Scope

Stage 3D establishes the deterministic drilling engineering core. It provides drilling-specific geometry, time, volume, and MRR calculations that compose with the shared Stage 3A formula foundation.

Stage 3D covers solid circular twist-drill operations only. It does NOT cover trepanning, gun drilling, annular cutters, reaming, boring, or tapping.

---

## 2. Engineering Authority

Deterministic engineering calculations are authoritative. Stage 3D contains no LLM calls, no AI dependency, no probabilistic logic, no external API calls. All results are reproducible.

---

## 3. Supported Calculations

### 3.1 Effective Drilling Travel

**Function:** `effective_drilling_travel(hole_depth, approach_allowance?, breakthrough_allowance?)`
**Formula:** L_eff = depth + approach + breakthrough
**Inputs:** depth (mm, >= 0), approach (mm, >= 0, optional), breakthrough (mm, >= 0, optional)
**Output:** L_eff (mm)
**Authority:** DRILLING_SPECIFIC
**Assumptions:** All allowances are explicit. No automatic drill-point calculation.

### 3.2 Drilling Machining Time

**Function:** `drilling_machining_time(spindle_speed, feed_per_rev, hole_depth, ...)`
**Formula:** t = L_eff / (n × f) — composed from Stage 3A
**Inputs:** n (rpm), f (mm/rev), depth (mm), optional allowances (mm)
**Output:** t (min)
**Authority:** COMPOSED_FROM_STAGE_3A

### 3.3 Hole Cross-Sectional Area

**Function:** `hole_cross_sectional_area(diameter)`
**Formula:** A = π × D² / 4
**Inputs:** D (mm, > 0)
**Output:** A (dimensionless — mm² semantically; see note)
**Authority:** DRILLING_SPECIFIC
**Note:** Domain model does not yet include MM2 unit; value stored as DIMENSIONLESS with mm² semantics.

### 3.4 Cylindrical Hole Volume

**Function:** `cylindrical_hole_volume(diameter, depth)`
**Formula:** V = (π × D² / 4) × depth
**Inputs:** D (mm, > 0), depth (mm, >= 0)
**Output:** V (mm³)
**Authority:** DRILLING_SPECIFIC

### 3.5 Drilling MRR

**Function:** `drilling_mrr(diameter, feed_rate)`
**Formula:** Q = (π × D² / 4) × Vf
**Inputs:** D (mm, > 0), Vf (mm/min, >= 0)
**Output:** Q (mm³/min)
**Authority:** DRILLING_SPECIFIC
**Constraint:** Solid circular drill only.

---

## 4. Drilling Geometry

**Hole depth** is the nominal axial depth of the finished hole.

**Effective feed travel** includes hole depth plus any explicit allowances (approach, breakthrough). No hidden drill-tip geometry is applied automatically.

**Circular solid-drill assumption:** All area, volume, and MRR calculations assume a full-diameter circular drill creating a cylindrical hole. These formulas are NOT valid for annular cutters, trepanning, or partial-engagement operations.

---

## 5. Rules

### Calculation Rules (R-2301..R-2305)

| Rule ID | Purpose | Classification |
|---------|---------|---------------|
| R-2301 | Effective drilling travel | DETERMINISTIC |
| R-2302 | Drilling machining time | DETERMINISTIC (composed) |
| R-2303 | Hole cross-sectional area | DETERMINISTIC |
| R-2304 | Cylindrical hole volume | DETERMINISTIC |
| R-2305 | Drilling MRR | DETERMINISTIC |

### Validation Rules (R-2310..R-2313)

| Rule ID | Purpose | Classification | Severity |
|---------|---------|---------------|----------|
| R-2310 | Vf = n × f consistency | PHYSICAL_CONSTRAINT | FAIL |
| R-2311 | Effective travel >= hole depth | PHYSICAL_CONSTRAINT | FAIL |
| R-2312 | Zero depth warning | PHYSICAL_CONSTRAINT | WARNING |
| R-2313 | L/D > 10 deep-hole warning | ENGINEERING_POLICY_THRESHOLD | WARNING |

---

## 6. Units

| Quantity | Unit | Symbol |
|----------|------|--------|
| Diameter | millimeter | mm |
| Depth | millimeter | mm |
| Feed per revolution | mm per revolution | mm/rev |
| Feed rate | mm per minute | mm/min |
| Spindle speed | revolutions per minute | rpm |
| Cross-sectional area | mm² (as DIMENSIONLESS) | — |
| Volume | cubic mm | mm³ |
| Material removal rate | cubic mm per minute | mm³/min |
| Machining time | minute | min |
| Depth/diameter ratio | dimensionless | 1 |

---

## 7. Validation & Exceptions

All drilling functions use `MachiningMathError` (Stage 3A exception hierarchy).

Rejected inputs: negative dimensions, zero diameter, NaN, Infinity, wrong units, boolean values as integer arguments.

---

## 8. Determinism

Every Stage 3D function produces identical output for identical input. No randomness, no external state, no side effects. Decimal arithmetic throughout.

---

## 9. Examples

**Effective travel:** depth=30 mm, approach=2 mm, breakthrough=3 mm → L_eff = 35 mm

**Drilling time:** n=1000 rpm, f=0.2 mm/rev, depth=30 mm → Vf=200 mm/min, t=0.15 min

**Hole area:** D=10 mm → A = 25π ≈ 78.54 mm²

**Volume:** D=10 mm, depth=30 mm → V = 750π ≈ 2356.2 mm³

**Drilling MRR:** D=10 mm, Vf=200 mm/min → Q = 5000π ≈ 15708 mm³/min

---

## 10. Non-Goals

Stage 3D does NOT implement: peck drilling, chip evacuation, coolant recommendation, deep-hole drilling dynamics, gun drilling, drill wander, deflection, burr prediction, thrust force models, drilling temperature, tool wear prediction, surface roughness, runout, CNC canned cycles, tapping, reaming, boring, CAM, CAPP, DFM, AI authority.

---

## 11. Relationship to Stages 3A/3B/3C

| Stage | Scope | Rule IDs |
|-------|-------|----------|
| **3A** | Shared deterministic math: spindle speed, feed, MRR, time, power, torque | R-2001..R-2013 |
| **3B** | Turning core: external turning, boring, facing, pass count, volumes | R-2101..R-2114 |
| **3C** | Milling core: feed/rev, engagement ratios, milling time/MRR, validation | R-2201..R-2213 |
| **3D** | Drilling core: effective travel, drilling time, hole geometry, drilling MRR | R-2301..R-2313 |

Stage 3D reuses Stage 3A `feed_rate_from_rpm_feed_per_rev` and `machining_time_from_distance_feed_rate` via composition. No Stage 3A formulas are duplicated.
