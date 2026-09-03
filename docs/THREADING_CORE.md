# MachineryPro AI — Deterministic Threading & Tapping Engineering Core

**Stage:** 3E
**Status:** Closed
**Scope:** Basic deterministic thread geometry, synchronized feed, and threading time

---

## 1. Scope

Stage 3E establishes the deterministic threading and tapping engineering core. It provides basic thread geometry (lead/pitch/starts), synchronized feed relationships, effective travel, machining time, and revolution count for simple thread operations.

Stage 3E does NOT implement a standards database, thread tolerance classes, thread strength calculations, or any process beyond basic deterministic geometry and kinematics.

---

## 2. Engineering Authority

Deterministic engineering calculations are authoritative. Stage 3E contains no LLM calls, no AI dependency, no probabilistic logic, no external APIs, no hidden constants. All results are reproducible.

---

## 3. Terminology

| Term | Definition |
|------|-----------|
| **Pitch** | Axial distance between adjacent thread crests (mm/rev for single-start) |
| **Lead** | Axial advance per one spindle revolution (mm/rev) |
| **Number of starts** | Thread start count; single-start: lead = pitch; multi-start: lead = pitch × starts |
| **Thread length** | Nominal axial length of threaded engagement |
| **Effective travel** | Total axial feed distance including explicit approach and overtravel allowances |
| **Synchronized feed** | Feed rate locked to spindle: Vf = n × lead (mandatory for rigid tapping) |

---

## 4. Supported Calculations

### 4.1 Lead from Pitch
**Function:** `lead_from_pitch(pitch, number_of_starts=1)`
**Formula:** lead = pitch × starts
**Inputs:** pitch (mm/rev, > 0), starts (int, > 0)
**Output:** lead (mm/rev)

### 4.2 Pitch from Lead
**Function:** `pitch_from_lead(lead, number_of_starts=1)`
**Formula:** pitch = lead / starts
**Inputs:** lead (mm/rev, > 0), starts (int, > 0)
**Output:** pitch (mm/rev)

### 4.3 Threads per mm
**Function:** `threads_per_mm(pitch)`
**Formula:** 1 / pitch
**Inputs:** pitch (mm/rev, > 0)
**Output:** dimensionless scalar

### 4.4 Thread Feed Rate
**Function:** `thread_feed_rate(spindle_speed, lead)`
**Formula:** Vf = n × lead — composed via Stage 3A `feed_rate_from_rpm_feed_per_rev`
**Inputs:** n (rpm), lead (mm/rev)
**Output:** Vf (mm/min)

### 4.5 Spindle Speed from Thread Feed
**Function:** `spindle_speed_from_thread_feed(feed_rate, lead)`
**Formula:** n = Vf / lead
**Inputs:** Vf (mm/min), lead (mm/rev, > 0)
**Output:** n (rpm)

### 4.6 Effective Threading Travel
**Function:** `effective_threading_travel(thread_length, approach?, overtravel?)`
**Formula:** L_eff = length + approach + overtravel
**Inputs:** all in mm, allowances optional and explicit
**Output:** L_eff (mm)

### 4.7 Threading Machining Time
**Function:** `threading_machining_time(spindle_speed, lead, thread_length, ...)`
**Formula:** t = L_eff / (n × lead) — composed from Stage 3A
**Inputs:** n (rpm), lead (mm/rev), length (mm), optional allowances
**Output:** t (min)

### 4.8 Threading Revolutions
**Function:** `threading_revolutions(effective_travel, lead)`
**Formula:** revs = L_eff / lead (may be fractional — no silent rounding)
**Inputs:** L_eff (mm), lead (mm/rev, > 0)
**Output:** dimensionless

---

## 5. Tapping Synchronization

For single-start rigid tapping, lead equals pitch:

**Vf = n × pitch**

The feed rate is physically synchronized to the spindle. Any mismatch between Vf, n, and pitch/lead is a kinematic error (rule R-2410).

---

## 6. Threading Rules

### Calculation Rules (R-2401..R-2405)

| Rule ID | Purpose |
|---------|---------|
| R-2401 | Lead from pitch |
| R-2402 | Pitch from lead |
| R-2403 | Thread feed rate |
| R-2404 | Threading machining time |
| R-2405 | Threading revolutions |

### Validation Rules (R-2410..R-2413)

| Rule ID | Purpose | Classification | Severity |
|---------|---------|---------------|----------|
| R-2410 | Vf = n × lead consistency | PHYSICAL_CONSTRAINT | FAIL |
| R-2411 | Travel >= thread length | PHYSICAL_CONSTRAINT | FAIL |
| R-2412 | Single-start: lead == pitch | PHYSICAL_CONSTRAINT | FAIL |
| R-2413 | Zero thread length warning | PHYSICAL_CONSTRAINT | WARNING |

**Zero arbitrary policy thresholds in Stage 3E.**

---

## 7. Units

| Quantity | Unit | Symbol |
|----------|------|--------|
| Pitch | mm per revolution | mm/rev |
| Lead | mm per revolution | mm/rev |
| Thread length | millimeter | mm |
| Feed rate | mm per minute | mm/min |
| Spindle speed | revolutions per minute | rpm |
| Machining time | minute | min |
| Revolutions | dimensionless | 1 |
| Threads per mm | dimensionless | 1 |

---

## 8. Validation & Exceptions

All functions use `MachiningMathError`. Rejected: negative values, zero denominators, NaN, Infinity, wrong units, boolean start counts.

---

## 9. Determinism

All Stage 3E functions produce identical output for identical input. Decimal arithmetic throughout.

---

## 10. Examples

**Lead:** pitch=1.5 mm/rev, starts=3 → lead=4.5 mm/rev

**Feed:** n=500 rpm, lead=1.5 mm/rev → Vf=750 mm/min

**Time:** n=500, lead=1.5, length=20 mm → Vf=750, t=20/750 ≈ 0.0267 min

**Revolutions:** travel=30 mm, lead=1.5 → 20 revolutions

---

## 11. Non-Goals

Thread strength, bolt preload, tolerance classes (6H/6g), ISO/UN/BSP/NPT standards tables, ACME/trapezoidal geometry, pipe thread taper, thread rolling, tapping torque, thread milling CAM, CNC G-code, helix angle (omitted — no angle unit in domain model), AI recommendations.

---

## 12. Relationship to Previous Stages

| Stage | Scope | Rule IDs |
|-------|-------|----------|
| **3A** | Shared math: speed, feed, MRR, time, power, torque | R-2001..R-2013 |
| **3B** | Turning: external, boring, facing, pass count, volumes | R-2101..R-2114 |
| **3C** | Milling: feed/rev, engagement, milling time/MRR | R-2201..R-2213 |
| **3D** | Drilling: travel, time, hole geometry, drilling MRR | R-2301..R-2313 |
| **3E** | Threading: lead/pitch, synchronized feed, time, revolutions | R-2401..R-2413 |
