# MachineryPro AI — Deterministic Milling Engineering Core

**Stage:** 3C
**Status:** Closed
**Scope:** Deterministic milling-specific calculations and engineering rules

---

## 1. Scope

Stage 3C establishes the deterministic milling engineering core for MachineryPro AI. It provides milling-specific calculations and validation rules that compose with the shared Stage 3A formula foundation.

Stage 3C does NOT duplicate universal formulas already provided by Stage 3A. Instead, it reuses them via explicit composition and adds milling-specific functions.

---

## 2. Engineering Authority

Deterministic engineering calculations are authoritative. Stage 3C contains no LLM calls, no AI provider calls, no probabilistic calculations, no external API dependency. All results are reproducible.

---

## 3. Supported Calculations

### 3.1 Feed Per Revolution (Milling Context)

**Function:** `feed_per_rev_from_tooth_feed(tooth_count, feed_per_tooth)`
**Formula:** f_rev = z × fz
**Inputs:** z (positive integer), fz (mm/tooth, >= 0)
**Output:** f_rev (mm/rev)
**Authority:** MILLING_SPECIFIC
**Source:** Milling kinematics

### 3.2 Radial Engagement Ratio

**Function:** `radial_engagement_ratio(radial_width, tool_diameter)`
**Formula:** ae_ratio = ae / D
**Inputs:** ae (mm, >= 0), D (mm, > 0)
**Output:** dimensionless ratio
**Authority:** MILLING_SPECIFIC
**Source:** Milling geometry

### 3.3 Axial Engagement Ratio

**Function:** `axial_engagement_ratio(axial_depth, tool_diameter)`
**Formula:** ap_ratio = ap / D
**Inputs:** ap (mm, >= 0), D (mm, > 0)
**Output:** dimensionless ratio
**Authority:** MILLING_SPECIFIC
**Source:** Milling geometry

### 3.4 Milling Machining Time

**Function:** `milling_machining_time(spindle_speed, tooth_count, feed_per_tooth, cutting_distance)`
**Formula:** t = L / (n × z × fz) — composed from Stage 3A `feed_rate_from_rpm_tooth_feed` and `machining_time_from_distance_feed_rate`
**Inputs:** n (rpm), z (int), fz (mm/tooth), L (mm)
**Output:** t (min)
**Authority:** COMPOSED_FROM_STAGE_3A
**Assumptions:** Does NOT include approach, retract, rapid, or tool-change time.

### 3.5 Milling MRR

**Function:** `milling_mrr(axial_depth, radial_width, spindle_speed, tooth_count, feed_per_tooth)`
**Formula:** Q = ap × ae × (n × z × fz) — composed from Stage 3A `feed_rate_from_rpm_tooth_feed` and `milling_material_removal_rate`
**Inputs:** ap (mm), ae (mm), n (rpm), z (int), fz (mm/tooth)
**Output:** Q (mm³/min)
**Authority:** COMPOSED_FROM_STAGE_3A

---

## 4. Milling Rules

### Calculation Rules (R-2201..R-2205)

| Rule ID | Purpose | Classification |
|---------|---------|---------------|
| R-2201 | Feed per revolution from tooth feed | DETERMINISTIC |
| R-2202 | Radial engagement ratio | DETERMINISTIC |
| R-2203 | Axial engagement ratio | DETERMINISTIC |
| R-2204 | Milling machining time | DETERMINISTIC (composed) |
| R-2205 | Milling MRR | DETERMINISTIC (composed) |

### Validation Rules (R-2210..R-2213)

| Rule ID | Purpose | Classification | Severity |
|---------|---------|---------------|----------|
| R-2210 | ae > D rejection | PHYSICAL_CONSTRAINT | FAIL |
| R-2211 | ap/D > 2.0 warning | ENGINEERING_POLICY_THRESHOLD | WARNING |
| R-2212 | Vf = n×z×fz consistency check | PHYSICAL_CONSTRAINT | FAIL |
| R-2213 | Zero engagement (ap=0 and ae=0) warning | PHYSICAL_CONSTRAINT | WARNING |

---

## 5. Units

| Quantity | Unit | Symbol |
|----------|------|--------|
| Tool diameter | millimeter | mm |
| Axial depth of cut | millimeter | mm |
| Radial width of cut | millimeter | mm |
| Cutting distance | millimeter | mm |
| Feed per tooth | mm per tooth | mm/tooth |
| Feed per revolution | mm per revolution | mm/rev |
| Feed rate | mm per minute | mm/min |
| Spindle speed | revolutions per minute | rpm |
| Material removal rate | cubic mm per minute | mm³/min |
| Machining time | minute | min |
| Engagement ratio | dimensionless | 1 |

---

## 6. Validation & Exceptions

All milling functions use `MachiningMathError` (Stage 3A exception hierarchy).

Rejected inputs: negative physical dimensions, zero tool diameter, non-integer or non-positive tooth count, boolean values as integer arguments, NaN, Infinity, wrong unit types.

---

## 7. Determinism

Every Stage 3C function produces identical output for identical input. No randomness, no external state, no side effects. Decimal arithmetic throughout.

---

## 8. Examples

**Feed per revolution:**
z=4, fz=0.1 mm/tooth → f_rev = 0.4 mm/rev

**Radial engagement ratio:**
ae=10 mm, D=20 mm → ae/D = 0.5

**Milling machining time:**
n=1000 rpm, z=4, fz=0.1 mm/tooth, L=200 mm → Vf=400 mm/min, t=0.5 min

**Milling MRR:**
ap=2 mm, ae=10 mm, n=1000 rpm, z=4, fz=0.1 mm/tooth → Vf=400 mm/min, Q=8000 mm³/min

---

## 9. Non-Goals

Stage 3C does NOT implement:

- CAM toolpath generation
- CAPP / process planning
- Feature recognition
- DFM analysis
- Chatter prediction or stability analysis
- Tool wear prediction
- Tool catalog recommendations
- Automatic parameter optimization
- AI authority over calculations
- Chip thinning correction
- Ball-nose effective diameter
- Trochoidal engagement geometry
- Surface roughness prediction
- Cutting force coefficients
- Specific cutting force (Kc) values

---

## 10. Relationship to Stage 3A and Stage 3B

| Stage | Scope | Rule IDs |
|-------|-------|----------|
| **3A** | Shared deterministic math foundation: spindle speed, feed (turning & milling), MRR, machining time, power, torque | R-2001..R-2013 |
| **3B** | Turning process core: external turning, boring, facing, pass count, turning volumes, turning MRR, turning time | R-2101..R-2114 |
| **3C** | Milling process core: feed per rev, engagement ratios, milling time (composed), milling MRR (composed), milling validation rules | R-2201..R-2213 |

Stage 3C reuses Stage 3A formulas via explicit import and composition. It does not duplicate universal calculations.
