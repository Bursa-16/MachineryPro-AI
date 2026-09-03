# MachineryPro AI — Deterministic Reaming & Boring Engineering Core

**Stage:** 3F
**Status:** Closed
**Scope:** Shared hole-finishing geometry, reaming, and boring deterministic calculations

---

## 1. Scope

Stage 3F establishes deterministic engineering calculations for reaming and boring operations using a shared hole-finishing geometry model. Both operations enlarge a pre-existing hole from an initial diameter to a final diameter using concentric cylindrical annular geometry.

---

## 2. Engineering Authority

Deterministic calculations are authoritative. No LLM, no AI, no empirical constants, no silent defaults. All results are reproducible.

---

## 3. Terminology

| Term | Definition |
|------|-----------|
| **Initial diameter** | Pre-hole diameter before the finishing operation (> 0) |
| **Final diameter** | Finished diameter after reaming or boring (>= initial) |
| **Diametral stock** | D_final − D_initial (total diameter change) |
| **Radial stock** | (D_final − D_initial) / 2 (depth of cut per side) |
| **Operation length** | Nominal axial length of the ream or bore |
| **Effective travel** | Operation length + explicit approach + overtravel |
| **Reaming** | Finishing of a drilled hole to precise diameter using a reamer |
| **Boring** | Enlargement of a hole using a single-point boring tool/bar |

---

## 4. Shared Geometry

Both reaming and boring use identical annular geometry:

- **Diametral stock:** D_final − D_initial
- **Radial stock:** (D_final − D_initial) / 2
- **Annular area:** π/4 × (D_final² − D_initial²)
- **Annular volume:** π/4 × (D_final² − D_initial²) × length
- **Annular MRR:** π/4 × (D_final² − D_initial²) × Vf

The relationship `diametral = 2 × radial` is always enforced.

---

## 5. Reaming Calculations

Reaming uses the shared functions with reamer-specific context:
- Spindle speed: reuse Stage 3A `spindle_speed_from_cutting_speed`
- Feed rate: reuse Stage 3A `feed_rate_from_rpm_feed_per_rev`
- Time: `hole_finishing_machining_time` (composed from Stage 3A)
- Stock: `diametral_stock`, `radial_stock`
- Volume: `annular_volume`
- MRR: `hole_finishing_mrr`

---

## 6. Boring Calculations

Boring uses the same shared functions. The reference diameter for spindle speed is explicitly chosen by the caller (final bore diameter or user-supplied). Stage 3F does not hide this choice.

---

## 7. Rules

### Calculation Rules (R-2501..R-2505)

| Rule ID | Purpose |
|---------|---------|
| R-2501 | Diametral stock |
| R-2502 | Radial stock |
| R-2503 | Annular volume |
| R-2504 | Hole-finishing MRR |
| R-2505 | Machining time |

### Validation Rules (R-2510..R-2514)

| Rule ID | Purpose | Classification | Severity |
|---------|---------|---------------|----------|
| R-2510 | D_final >= D_initial | PHYSICAL_CONSTRAINT | FAIL |
| R-2511 | diametral == 2 × radial | PHYSICAL_CONSTRAINT | FAIL |
| R-2512 | travel >= operation length | PHYSICAL_CONSTRAINT | FAIL |
| R-2513 | Zero stock warning | PHYSICAL_CONSTRAINT | WARNING |
| R-2514 | MRR consistency | PHYSICAL_CONSTRAINT | FAIL |

**Zero arbitrary policy thresholds.**

---

## 8. Units

| Quantity | Unit |
|----------|------|
| Diameters | mm |
| Stock | mm |
| Length/travel | mm |
| Feed per rev | mm/rev |
| Feed rate | mm/min |
| Spindle speed | rpm |
| Area | dimensionless (mm²) |
| Volume | mm³ |
| MRR | mm³/min |
| Time | min |

---

## 9. Validation & Exceptions

Uses `MachiningMathError`. Rejects: reversed diameters, negative values, zero denominators, NaN, Infinity, wrong units.

---

## 10. Determinism

All functions produce identical output for identical input. Decimal arithmetic throughout.

---

## 11. Examples

**Stock:** D_i=9.8, D_f=10.0 → diametral=0.2 mm, radial=0.1 mm

**Volume:** D_i=9.8, D_f=10.0, L=30 → V = π/4 × (100−96.04) × 30 ≈ 93.3 mm³

**Time:** n=500, f=0.4 → Vf=200; L=30 → t=0.15 min

---

## 12. Non-Goals

Tolerance prediction, IT grades, ISO 286 fits, cylindricity, roundness, surface roughness, reamer expansion, tool wear, boring bar deflection, chatter, fine-boring compensation, thermal growth, tool offsets, spindle runout, stock allowance recommendations, multi-pass optimization, CNC cycles, tool/machine selection, AI.

---

## 13. Relationship to Previous Stages

| Stage | Scope | Rule IDs |
|-------|-------|----------|
| **3A** | Shared math | R-2001..R-2013 |
| **3B** | Turning | R-2101..R-2114 |
| **3C** | Milling | R-2201..R-2213 |
| **3D** | Drilling | R-2301..R-2313 |
| **3E** | Threading | R-2401..R-2413 |
| **3F** | Hole finishing (reaming & boring) | R-2501..R-2514 |
