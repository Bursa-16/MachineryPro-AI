# MachineryPro AI — Universal Engineering Interoperability Architecture Roadmap

**Document type:** Long-horizon architectural directive
**Scope:** Format ingestion, canonical representation, feature recognition,
CAM/NC interpretation, validation, conversion, and fidelity reporting
**Status:** Architecture definition — no implementation
**Relationship to prior stages:** Stages 3A–3J establish the deterministic
engineering core. This roadmap defines the data-acquisition and
interoperability layer that feeds that core.

---

## 1. Governing Principle

**Manufacturing intelligence must be format-independent.**

MachineryPro AI shall ingest, normalize, analyze, validate, compare,
and convert the widest practical range of engineering formats without
coupling its engineering models to any single vendor representation.

This principle has three corollaries:

1. **No vendor lock-in.** Canonical models are defined by MachineryPro AI,
   not by any CAD/CAM/CAE kernel or exchange format.
2. **No assumption of lossless conversion.** Every pipeline stage must be
   capable of reporting what was preserved, partially preserved, lost,
   inferred, or unsupported.
3. **Ingestion and intelligence are separate layers.** Parsing a file is
   not the same as extracting engineering meaning from it.

---

## 2. Architecture Layers

The universal interoperability pipeline has eight distinct layers.
Each layer has a defined responsibility, defined inputs, and defined
outputs. No layer may skip a layer upstream of it.

```
┌───────────────────────────────────────────────────────────────────────┐
│  LAYER 0 — NATIVE / OPEN ENGINEERING FORMAT                           │
│  STEP · IGES · DXF · DWG · SolidWorks · NX · CATIA · G-code · PDF   │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 1 — FORMAT ADAPTER / PARSER                                    │
│  Format-specific reader. Outputs raw in-memory representation.        │
│  No semantic interpretation. Fails closed on corrupt/unsupported data.│
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 2 — CANONICAL ENGINEERING REPRESENTATION (CER)                 │
│  Vendor-neutral intermediate models. Geometry, topology, PMI,         │
│  assemblies, CAM operations, NC motion — all in MachineryPro-defined  │
│  canonical schemas. No manufacturing intelligence yet.                │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 3 — RECOGNITION / SEMANTIC NORMALIZATION                       │
│  Feature recognition from B-rep. PMI/GD&T parsing. Operation         │
│  sequencing from CAM. Tool/holder identification. NC code analysis.   │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 4 — MACHINERYPRO DOMAIN MODELS                                 │
│  Feature · Material · MachiningParameters · Operation · Tool ·        │
│  Machine · ProcessPlan · CuttingParameterRecord (Stages 3A–3J)        │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 5 — DETERMINISTIC ENGINEERING ANALYSIS                         │
│  Stage 3A–3J rules: RPM, feed, MRR, power, DFM, machine capability,  │
│  process planning, empirical data validation                          │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 6 — VALIDATION / COMPARISON                                    │
│  Cross-format comparison (CAD vs CAM vs NC). As-designed vs           │
│  as-planned vs as-manufactured analysis.                              │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  LAYER 7 — EXPORT / CONVERSION + FIDELITY REPORT                     │
│  Write to target format. Record what was preserved, lost, inferred.   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Canonical Engineering Representation (CER) — Model Hierarchy

The CER is the central architectural innovation. It is a set of
MachineryPro-defined, vendor-neutral intermediate schemas that sit between
raw file parsers and the downstream manufacturing-domain models.

### 3.1 Canonical Geometry Model

Represents 3D geometric entities without kernel dependency.

**Scope:**
- Primitive surfaces: plane, cylinder, cone, sphere, torus
- Free-form surfaces: NURBS (control points, weights, knot vectors, degree)
- Procedural: extrude, revolve, sweep, loft (where recoverable from B-rep)
- 2D profiles: polylines, arcs, splines, ellipses

**Key fields:** entity_id, entity_type, bounding_box, surface_type,
parametric_data, approximation_tessellation, tolerance, provenance

**NOT in scope here:** topology (how surfaces are connected), PMI, or
feature semantics.

### 3.2 Canonical Topology Model

Represents the B-rep shell structure: how geometric entities are connected.

**Scope:**
- Solid, shell, face, edge, vertex hierarchy
- Face orientation, edge sense, loop (outer/inner)
- Manifold/non-manifold flags
- Topological genus

**Key fields:** topology_id, solid_id, faces, edges, vertices, loops,
manifold_status, genus, provenance

**Dependency:** Canonical Geometry Model

### 3.3 Canonical Assembly Model

Represents part-assembly relationships: instances, transforms, constraints.

**Scope:**
- Component instances with rigid-body transforms (4×4 matrix)
- Named configurations
- Assembly constraints (mate, flush, coincident — where recoverable)
- Hierarchy depth

**Key fields:** assembly_id, component_instances, transforms, constraints,
hierarchy, configuration, provenance

**Dependency:** Canonical Geometry + Topology Models

### 3.4 Canonical Manufacturing Feature Model

Represents recognized machining features as engineering entities, distinct
from raw B-rep topology.

**Scope:**
- Hole (blind, through, stepped, countersunk, counterbored)
- Pocket (open, blind, island)
- Slot (open, closed, T-slot, dovetail)
- Boss, pad, rib
- Planar face
- Cylindrical surface (external, internal)
- Thread (internal, external — pitch, form, depth)
- Fillet, chamfer
- Groove, undercut

**Key fields:** feature_id, feature_class, sub_type, nominal_dimensions,
tolerances, surface_finish, access_directions, prerequisite_features,
recognition_confidence, provenance

**Downstream:** Maps to MachineryPro `Feature` (domain/feature.py)
**Dependency:** Canonical Topology Model + Recognition Engine (Layer 3)

### 3.5 Canonical PMI / GD&T Model

Represents product manufacturing information: tolerances, datums,
surface finish, weld symbols, notes.

**Scope:**
- GD&T callouts (flatness, cylindricity, true position, runout, etc.)
- Dimensional tolerances (bilateral, unilateral, limit)
- Datum references and datum feature symbols
- Surface finish callouts (Ra, Rz, Rmax)
- Weld symbols
- Notes and flags

**Key fields:** pmi_id, pmi_type, referenced_geometry_ids, datum_refs,
tolerance_value, unit, zone_type, modifier, surface_finish, provenance

**Source formats:** STEP AP242 PMI, native CAD PMI, PDF annotation extraction

### 3.6 Canonical Drawing Model

Represents 2D engineering drawings and their semantic content.

**Scope:**
- View layout (front, top, side, isometric, section, detail)
- Dimension annotations with values and units
- Title block fields (part number, revision, material, approval)
- BOM / parts list
- Notes

**Key fields:** drawing_id, views, dimensions, annotations, title_block,
revision, bom, notes, source_format, provenance

**Source formats:** DXF, DWG, PDF, TIFF, raster (OCR pipeline for raster)

### 3.7 Canonical CAM Model

Represents a CAM program's declared manufacturing intent: operations,
sequences, tool selections, and strategies — independent of the CAM
software that created it.

**Scope:**
- Operation type (rough, semi-finish, finish, drill, tap, etc.)
- Operation parameters (Vc, f, ap, ae, fz, coolant)
- Tool assignment and geometry
- Holder assignment
- Work coordinate system / setup datum
- Operation sequence
- Strategy name (adaptive, trochoidal, pencil, parallel, etc.)

**Key fields:** cam_program_id, operations[], tool_library[], wcs[],
setups[], strategy_metadata, source_cam_system, provenance

**Source:** NX CAM, Mastercam, PowerMill, hyperMILL, Fusion Manufacturing,
SolidCAM, ESPRIT, GibbsCAM

**Downstream:** Maps to MachineryPro `ProcessPlan` + `ProcessPlanStep`

### 3.8 Canonical Setup Model

Represents physical workpiece orientation and fixturing intent for one
machine setup.

**Scope:**
- Setup datum and work coordinate system
- Clamping / fixturing description
- Accessible feature set in this setup
- Operation sequence within setup
- Part orientation relative to machine axes

**Key fields:** setup_id, datum_id, wcs, fixture_description,
accessible_feature_ids, operation_sequence, orientation_matrix, provenance

**Dependency:** Canonical Manufacturing Feature Model + Canonical CAM Model

### 3.9 Canonical Tool / Holder Model

Represents a cutting tool and its holder as a combined assembly with
standardized geometric and material attributes. Independent of any
tool library vendor.

**Scope:**
- Tool type (end mill, drill, turning insert, tap, etc.)
- Cutting geometry (diameter, flute count, helix angle, corner radius, etc.)
- Holder type (collet, hydraulic, shrink fit, boring bar)
- Overall assembly gauge length, stick-out
- Material / coating / grade
- Manufacturer reference (optional)

**Key fields:** tool_assembly_id, tool_type, cutting_diameter_mm,
flute_count, cutting_length_mm, holder_type, gauge_length_mm,
tool_material, coating, grade, manufacturer_ref, provenance

**Downstream:** Enriches MachineryPro `Tool` (domain/tool.py)

### 3.10 Canonical Toolpath Model

Represents the actual cutter motion as a sequence of machining moves,
independent of NC dialect.

**Scope:**
- Motion segments (linear, arc, helical, rapid, plunge)
- Feed/speed at each segment or change point
- Cutter compensation state
- Approach and retract moves
- Tool-change events
- Spindle events (speed, direction, CSS mode)

**Key fields:** toolpath_id, operation_id, segments[], tool_assembly_id,
wcs_id, total_time_estimate, provenance

**Dependency:** Canonical Tool Model + Canonical Setup Model
**Source:** NC file back-calculation, CAM native output

### 3.11 Canonical NC Model

Represents the parsed content of an NC program at the semantic level
(not raw G-code text).

**Scope:**
- Tool calls and tool numbers
- Spindle speed and feed commands
- Canned cycles (G81 drill, G83 peck, G84 tap, etc.)
- Work offset calls (G54–G59)
- Coordinate mode (G90/G91, G17/G18/G19)
- Compensation (G41/G42/G43)
- Modal state machine

**Key fields:** nc_program_id, dialect_detected, tool_calls[],
spindle_events[], feed_events[], motion_segments[], cycles[],
wcs_calls[], modal_state_log, provenance

**Source:** G-code, NC, TAP, CNC files; controller-dialect adapter normalizes
Fanuc/Siemens/Heidenhain/Mazatrol/Okuma/Haas/Mitsubishi/Fagor variations

### 3.12 Canonical CAE Result Model

Represents engineering analysis results in format-neutral form.

**Scope:**
- FEA stress/strain fields on geometry
- Modal analysis (natural frequencies, mode shapes)
- Thermal analysis (temperature distribution)
- Fatigue life predictions
- Contact pressure

**Key fields:** cae_result_id, analysis_type, referenced_geometry_ids,
field_data[], units, solver_metadata, convergence_info, provenance

**Source:** Ansys .rst, Abaqus .odb, Nastran .op2/BDF, LS-DYNA d3plot
**Note:** CAE ingestion is lower priority than CAD/CAM/NC for manufacturing
intelligence. Include schema now; implementation deferred to Stage 4M+.

### 3.13 Conversion Fidelity Model

Records what was preserved, lost, or degraded during any format
translation or normalization step.

**Scope (per entity or per conversion step):**
- PRESERVED: data was transferred without loss
- PARTIALLY_PRESERVED: data transferred with degradation (e.g., NURBS
  downgraded to tessellation)
- LOST: data present in source, absent in output
- UNSUPPORTED: data type not handled by the adapter
- INFERRED: value was not in source; reconstructed from context
- RECONSTRUCTED: geometry repaired or gap-filled
- DOWNGRADED: semantic content reduced (e.g., exact tolerance → approximate)

**Key fields:** fidelity_report_id, source_format, target_format,
source_entity_count, item_reports[], overall_score, conversion_timestamp,
adapter_version, provenance

---

## 4. Format Adapter Architecture

### 4.1 Adapter Interface

Every format adapter implements a common interface:

```
FormatAdapter
  .can_read(file_path) → bool
  .read(file_path, options) → ParseResult
  .can_write(canonical_model, target_format) → bool
  .write(canonical_model, file_path, options) → WriteResult + FidelityReport
  .metadata() → AdapterMetadata (format, version, capability_level)
```

`ParseResult` contains:
- raw in-memory representation (format-specific)
- format metadata (version, units, author, etc.)
- warnings and errors
- capability level reached (0–7 per §6)

**No adapter may communicate directly with MachineryPro domain models.**
All adapters write to the Canonical Engineering Representation only.
Domain model population is the responsibility of Layer 3 (recognition
and normalization).

### 4.2 Adapter Registry

A central `FormatAdapterRegistry` manages all registered adapters:

```
FormatAdapterRegistry
  .register(adapter: FormatAdapter) → None
  .detect_format(file_path) → FormatDescriptor | None
  .get_adapter(format_descriptor) → FormatAdapter | None
  .capabilities(format_descriptor) → CapabilityMatrix
```

Format detection uses: file extension, magic bytes, and content sniffing.

### 4.3 Adapter Tiers

**Tier 1 — Native/Open (no licensing cost):**
Implemented directly in MachineryPro AI using open-source parsers.

**Tier 2 — Open Geometry Kernel:**
Implemented via OpenCASCADE (OCCT) — open source LGPL.
Reads STEP, IGES, and B-rep formats through a stable kernel API.

**Tier 3 — Commercial Translation SDK:**
Third-party translation engines (Spatial 3D InterOp, Datakit,
CADfix, Theorem-XE, STEP Tools). Requires licensing.
Integrated as optional plugins; MachineryPro core does not depend on them.

**Tier 4 — Vendor API / SDK:**
Direct API access to CAD/CAM systems (SolidWorks API, NX Open,
CATIA V5/V6 CAA, Creo Toolkit, Inventor API, Fusion API).
Requires vendor license and platform availability.
Integrated as optional platform adapters.

**Tier 5 — External Converter + File Exchange:**
Systems not offering API access are handled via an intermediate conversion
step (e.g., export CATIA to STEP via Datakit, then ingest STEP).
Fidelity loss is documented in the Conversion Fidelity Report.

**Tier 6 — Controller-Specific Parser:**
Custom parsers for NC dialects (Fanuc, Siemens, Heidenhain, etc.).
Normalizes dialect to Canonical NC Model.

---

## 5. Format Support Matrix

### 5.1 CAD / Geometry Formats

| Format | Type | Implementation Method | CER Target | Read | Write | Priority |
|---|---|---|---|---|---|---|
| STEP AP203/AP214 | Open exchange | OpenCASCADE (Tier 2) | Geometry + Topology | ✓ | ✓ | P1 |
| STEP AP242 | Open exchange | OpenCASCADE (Tier 2) | + PMI + Assembly | ✓ | ✓ | P1 |
| IGES | Open exchange | OpenCASCADE (Tier 2) | Geometry + Topology | ✓ | ✓ | P1 |
| DXF R2000–2024 | Open exchange | ezdxf (Tier 1) | Drawing + 2D Geo | ✓ | ✓ | P1 |
| DWG (AutoCAD native) | Proprietary | Open Design Alliance ODA (Tier 3) or Teigha | Drawing + 2D Geo | ✓ | ✓ | P2 |
| STL (ASCII + binary) | Open mesh | numpy-stl / trimesh (Tier 1) | Mesh Geometry | ✓ | ✓ | P1 |
| OBJ | Open mesh | trimesh (Tier 1) | Mesh Geometry | ✓ | ✓ | P2 |
| 3MF | Open mesh | lib3mf / python-3mf (Tier 1) | Mesh + Material | ✓ | ✓ | P2 |
| PLY | Open mesh | trimesh (Tier 1) | Mesh Geometry | ✓ | — | P3 |
| Parasolid X_T / X_B | Proprietary kernel | Siemens Parasolid SDK (Tier 3) or OCCT import | B-Rep Geo+Topo | ✓ | ✓ | P1 |
| ACIS SAT / SAB | Proprietary kernel | Spatial 3D ACIS SDK (Tier 3) or OCCT import | B-Rep Geo+Topo | ✓ | ✓ | P1 |
| SolidWorks .SLDPRT / .SLDASM | Proprietary native | SolidWorks API (Tier 4) or STEP fallback | Full CER | ✓ | — | P2 |
| CATIA V5 .CATPart / .CATProduct | Proprietary native | CATIA CAA V5 SDK (Tier 4) or Datakit (Tier 3) | Full CER | ✓ | — | P2 |
| CATIA V6 / 3DEXPERIENCE | Proprietary native | 3DXML + Dassault SDK (Tier 4) | Full CER | ✓ | — | P3 |
| Siemens NX .prt | Proprietary native | NX Open API (Tier 4) or STEP fallback | Full CER | ✓ | — | P2 |
| Creo Parametric .prt / .asm | Proprietary native | Creo Toolkit (Tier 4) or STEP fallback | Full CER | ✓ | — | P2 |
| Inventor .ipt / .iam | Proprietary native | Inventor API (Tier 4) or STEP fallback | Full CER | ✓ | — | P3 |
| Fusion 360 .f3d / .f3z | Proprietary native | Autodesk Forge / Platform API (Tier 4) | Full CER | ✓ | — | P3 |
| JT (Jupiter Tessellation) | Open ISO 14306 | Open CASCADE or JTML SDK (Tier 3) | Mesh + B-Rep | ✓ | ✓ | P2 |
| VRML / X3D | Open | python-x3d (Tier 1) | Mesh + Visual | ✓ | — | P4 |
| FBX | Proprietary | Autodesk FBX SDK (Tier 3) | Mesh + Scene | ✓ | — | P4 |

### 5.2 Drawing / PMI Formats

| Format | Type | Implementation Method | CER Target | Read | Write | Priority |
|---|---|---|---|---|---|---|
| STEP AP242 PMI | Open standard | OpenCASCADE (Tier 2) | PMI Model | ✓ | ✓ | P1 |
| PDF (vector drawings) | Open | pdfplumber + MarkItDown (Tier 1) | Drawing Model (partial) | ✓ | — | P1 |
| PDF (raster drawings) | Open | OCR pipeline: pdfminer + tesseract (Tier 1) | Drawing Model (inferred) | ✓ | — | P2 |
| DXF (annotated) | Open | ezdxf (Tier 1) | Drawing + PMI | ✓ | ✓ | P1 |
| DWG (annotated) | Proprietary | ODA Teigha (Tier 3) | Drawing + PMI | ✓ | ✓ | P2 |
| TIFF (scanned drawing) | Open raster | Pillow + OCR (Tier 1) | Drawing (inferred) | ✓ | — | P3 |
| PNG / JPG (drawing photos) | Open raster | Pillow + OCR + vision AI (Tier 1 + optional) | Drawing (inferred) | ✓ | — | P3 |
| Native CAD PMI (NX) | Proprietary | NX Open (Tier 4) | PMI Model | ✓ | — | P2 |
| Native CAD PMI (CATIA) | Proprietary | CATIA CAA (Tier 4) | PMI Model | ✓ | — | P2 |
| Native CAD PMI (SolidWorks) | Proprietary | SolidWorks API (Tier 4) | PMI Model | ✓ | — | P2 |
| QIF (Quality Information Framework) | Open XML | Custom parser (Tier 1) | PMI + Metrology | ✓ | ✓ | P2 |

### 5.3 CAM Formats

| System | Format | Implementation Method | CER Target | Read | Write | Priority |
|---|---|---|---|---|---|---|
| Mastercam | .MCAM, .MCX | Mastercam SDK / API (Tier 4) | CAM Model | ✓ | — | P1 |
| Siemens NX CAM | .PRT (CAM data) | NX Open (Tier 4) | CAM Model | ✓ | — | P1 |
| PowerMill | .DCPF / .PMILL | Autodesk PowerMill API (Tier 4) | CAM Model | ✓ | — | P2 |
| hyperMILL | .HMX | OPEN MIND API / import (Tier 4) | CAM Model | ✓ | — | P2 |
| Fusion 360 Manufacturing | .f3d (CAM) | Autodesk Platform API (Tier 4) | CAM Model | ✓ | — | P2 |
| SolidCAM | .SCAM | SolidCAM API (Tier 4) | CAM Model | ✓ | — | P2 |
| ESPRIT | .esp | ESPRIT API / XML export (Tier 4) | CAM Model | ✓ | — | P3 |
| GibbsCAM | .gibbs | Sandvik Coromant / GibbsCAM API (Tier 4) | CAM Model | ✓ | — | P3 |
| Cimatron | .elt | PTG/Cimatron API (Tier 4) | CAM Model | ✓ | — | P3 |
| EdgeCAM | .ppf | Hexagon EdgeCAM API (Tier 4) | CAM Model | ✓ | — | P3 |
| APT / CLDATA | Open standard | Custom parser (Tier 1) | Toolpath Model | ✓ | ✓ | P2 |
| Generic NC post output | Text | Post-processed G-code (normalised) | NC Model | ✓ | — | P1 |

### 5.4 NC / CNC Formats

| Dialect | Format | Implementation Method | CER Target | Priority |
|---|---|---|---|---|
| Generic EIA/ISO G-code | .nc / .tap / .cnc | Custom parser (Tier 1) | NC Model | P1 |
| Fanuc 0i / 30i / 31i / 32i | .nc | Fanuc dialect adapter (Tier 6) | NC Model | P1 |
| Siemens SINUMERIK 840D / 828D | .mpf / .spf | Siemens dialect adapter (Tier 6) | NC Model | P1 |
| Heidenhain iTNC 530 / TNC 640 | .H / .i | Heidenhain dialect adapter (Tier 6) | NC Model | P1 |
| Mazak / Mazatrol Smooth | .eia + conversational | Mazak dialect adapter (Tier 6) | NC Model | P2 |
| Okuma OSP-P300S | .min | Okuma dialect adapter (Tier 6) | NC Model | P2 |
| Haas NGC | .nc | Haas dialect adapter (Tier 6) | NC Model | P2 |
| Mitsubishi M700 / M800 | .nc | Mitsubishi dialect adapter (Tier 6) | NC Model | P2 |
| Fagor 8070 | .nc | Fagor dialect adapter (Tier 6) | NC Model | P3 |
| Brother | .nc | Dialect adapter (Tier 6) | NC Model | P3 |
| NUM | .nc | Dialect adapter (Tier 6) | NC Model | P3 |
| Conversational (Mazatrol) | Proprietary binary | Mazak SDK / Tier 4 if available | NC Model (partial) | P3 |

### 5.5 CAE Formats

| Solver | Format | Implementation Method | CER Target | Priority |
|---|---|---|---|---|
| Ansys Mechanical | .rst / .cdb | pyansys / ansys-mapdl-reader (Tier 1) | CAE Result | P3 |
| Abaqus | .odb / .inp | Abaqus Python API (Tier 4) | CAE Result | P3 |
| Nastran | .op2 / BDF | pyNastran (Tier 1) | CAE Result | P3 |
| LS-DYNA | d3plot | lasso-python (Tier 1) | CAE Result | P4 |
| OpenFOAM | .foam | fluidfoam / vtk (Tier 1) | CAE Result (CFD) | P4 |
| Universal FEA | VTK / XDMF | vtk Python package (Tier 1) | CAE Result | P3 |

---

## 6. Capability Levels

Every format adapter reports the maximum capability level it achieves
for a given file. Levels are cumulative.

| Level | Name | Description |
|---|---|---|
| 0 | FORMAT_RECOGNIZED | File extension and/or magic bytes matched |
| 1 | FILE_PARSED | File opened and raw data structure read without error |
| 2 | DATA_NORMALIZED | Geometry/data placed into Canonical Engineering Representation |
| 3 | SEMANTICS_EXTRACTED | Engineering meaning extracted (features, tolerances, operations) |
| 4 | FEATURES_RECOGNIZED | Manufacturing features identified from geometry/topology |
| 5 | PROCESS_INTERPRETED | CAM operations, setup, toolpath, or NC motion interpreted |
| 6 | VALIDATED | Data validated against MachineryPro engineering models |
| 7 | CONVERTED | Data exported to target format with Fidelity Report |

**Levels 0–2 belong to Layer 1 (adapter/parser).**
**Levels 3–4 belong to Layer 2–3 (CER + recognition).**
**Levels 5–7 belong to Layers 4–7 (domain models through export).**

---

## 7. Conversion Fidelity Strategy

### 7.1 Principle

No format conversion is assumed lossless. Every conversion pipeline step
produces a `ConversionFidelityReport` entry.

### 7.2 Fidelity Classification

| Class | Code | Meaning |
|---|---|---|
| Preserved | P | Data transferred without change or degradation |
| Partially preserved | PP | Data transferred with precision or information loss |
| Lost | L | Data present in source; absent in target |
| Unsupported | U | Data type not handled by this adapter; skipped |
| Inferred | I | Value not in source; reconstructed from context/heuristic |
| Reconstructed | R | Geometry repaired (gap filled, self-intersection removed) |
| Downgraded | D | Semantic content reduced (tolerance → note, B-rep → mesh) |

### 7.3 Fidelity Report Structure

```
ConversionFidelityReport
  .report_id
  .source_format
  .target_format
  .source_entity_count
  .adapter_id
  .adapter_version
  .timestamp
  .item_reports[] → [
      ConversionFidelityItem
        .entity_id
        .entity_type
        .fidelity_class (P/PP/L/U/I/R/D)
        .detail
        .source_value (optional)
        .target_value (optional)
  ]
  .summary_counts → {P: n, PP: n, L: n, U: n, I: n, R: n, D: n}
  .overall_fidelity_score → Decimal [0.0, 1.0]
    (= preserved / total; P + PP weighted separately)
```

### 7.4 Fidelity Gates

The system may define fidelity gates for safety-critical operations:

```
FidelityGate
  .minimum_overall_score: Decimal
  .zero_tolerance_classes: frozenset[FidelityClass]
  .fail_closed_behavior: REJECT | WARN | LOG
```

Example: A manufacturing plan may require `minimum_overall_score >= 0.95`
and `zero_tolerance_classes = {LOST}` for GD&T features. Any conversion
with lost tolerance data is rejected, not silently accepted.

---

## 8. Open-Source vs Commercial Integration Matrix

| Category | Preferred open-source path | Commercial/vendor path | Gap |
|---|---|---|---|
| STEP import/export | python-occ (OCCT) | Spatial 3D InterOp, Datakit | OCCT covers most; commercial covers edge cases |
| IGES import | python-occ (OCCT) | Spatial / CADfix | OCCT adequate for P1 |
| B-Rep kernel (Parasolid) | OCCT approximate import | Siemens Parasolid SDK | Exact Parasolid kernel requires licensing |
| B-Rep kernel (ACIS) | OCCT approximate import | Spatial ACIS SDK | Same gap |
| DXF import/export | ezdxf (MIT) | — | No gap; ezdxf is production-grade |
| DWG import/export | — | ODA Teigha / RealDWG | No open DWG writer without ODA membership |
| SolidWorks native | STEP fallback | SolidWorks API | Native requires SolidWorks license on host |
| CATIA native | STEP fallback | Datakit or CAA SDK | Native requires CATIA/DS license |
| NX native | STEP fallback | NX Open + license | Native requires NX license |
| Creo native | STEP fallback | Creo Toolkit | Native requires Creo license |
| Mastercam CAM | NC output only | Mastercam SDK | SDK requires Mastercam dealer agreement |
| NX CAM | NC output only | NX Open | NX license required |
| PowerMill | NC output only | Autodesk Platform API | API access via Autodesk agreements |
| NC dialects (Fanuc/Siemens/etc.) | Custom parser (Tier 1) | Vendor simulator SDKs | Tier 1 sufficient for read; simulation needs vendor SDK |
| FEA results (Ansys) | pyansys | Ansys Python APIs | pyansys covers common cases |
| FEA results (Abaqus) | — | Abaqus Python API | Abaqus license required for .odb |
| FEA results (Nastran) | pyNastran | MSC Nastran API | pyNastran covers op2/BDF |
| PDF (vector) | pdfplumber, MarkItDown | — | No gap for vector PDF |
| PDF (raster/OCR) | tesseract + Pillow | ABBYY, AWS Textract | Commercial OCR higher accuracy |

---

## 9. Stage-by-Stage Implementation Roadmap

### Dependency order rationale

Geometry must precede topology. Topology must precede feature recognition.
Feature recognition must precede CAM interpretation. NC interpretation
can run in parallel with geometry if no CAD-CAM-NC comparison is needed.

```
Stage 4A — Architecture (this document + domain scaffolding)
    ↓
Stage 4B — Canonical Geometry / Topology Model
    ↓
Stage 4C — STEP / IGES / B-Rep Import (OpenCASCADE)
    ↓
Stage 4D — Manufacturing Feature Recognition Foundation
    ↓ (can run in parallel after 4B)
Stage 4E — PMI / GD&T / Drawing Semantic Model
Stage 4G — Mesh Geometry Foundation (STL / OBJ / 3MF)

Stage 4B → Stage 4F — Native CAD Adapter Framework
(SolidWorks / NX / CATIA / Creo via API or Tier 3 SDK)

Stage 4C + 4D → Stage 4H — Canonical CAM Model
Stage 4H → Stage 4I — Native CAM Adapter Framework

Stage 4A → Stage 4J — Canonical NC / G-code Model and Parser
Stage 4J → Stage 4K — CNC Controller Dialect Adapter Framework

Stage 4B + 4C + 4D + 4H + 4J → Stage 4L — Engineering Conversion Framework
Stage 4L → Stage 4M — Conversion Fidelity / Data-Loss Validation
```

### Stage 4A — Universal Engineering Interoperability Architecture

**Purpose:** Establish the foundational packages, interfaces, and schemas.
No parsers implemented yet. Architecture only.

**Deliverables:**
- `backend/interop/__init__.py` — package scaffold
- `backend/interop/adapter.py` — `FormatAdapter` ABC, `FormatAdapterRegistry`
- `backend/interop/capability.py` — `CapabilityLevel` enum (0–7)
- `backend/interop/cer/__init__.py` — Canonical Engineering Representation package
- `backend/interop/cer/geometry.py` — `CanonicalGeometry` schema
- `backend/interop/cer/topology.py` — `CanonicalTopology` schema
- `backend/interop/cer/assembly.py` — `CanonicalAssembly` schema
- `backend/interop/cer/feature.py` — `CanonicalManufacturingFeature` schema
- `backend/interop/cer/pmi.py` — `CanonicalPMI` schema
- `backend/interop/cer/drawing.py` — `CanonicalDrawing` schema
- `backend/interop/cer/cam.py` — `CanonicalCAMProgram` schema
- `backend/interop/cer/setup.py` — `CanonicalSetup` schema
- `backend/interop/cer/tool.py` — `CanonicalToolAssembly` schema
- `backend/interop/cer/toolpath.py` — `CanonicalToolpath` schema
- `backend/interop/cer/nc.py` — `CanonicalNCProgram` schema
- `backend/interop/cer/cae.py` — `CanonicalCAEResult` schema (stub)
- `backend/interop/fidelity.py` — `ConversionFidelityReport`, `FidelityClass`, `FidelityGate`
- `docs/INTEROPERABILITY_ARCHITECTURE.md`
- Full test suite for all schemas and adapter interface

**Stage 3A–3J impact:** Zero. Architecture packages are additive.

---

### Stage 4B — Canonical Geometry / Topology Model

**Purpose:** Implement the full CER geometry and topology models with
validation, serialization, and deterministic ordering. No file I/O.

**Key models:** `BRepSolid`, `BRepShell`, `BRepFace`, `BRepEdge`,
`BRepVertex`, `NURBSSurface`, `NURBSCurve`, `PrimitiveSurface`

**Tests:** Construct geometry from explicit data; verify immutability,
serialization, bounding-box computation, orientation validation.

---

### Stage 4C — STEP / IGES / B-Rep Import Foundation

**Purpose:** First working file reader. Ingests STEP AP214/AP242 and IGES
via OpenCASCADE Python bindings (pythonocc-core).

**Pipeline:** `.stp` file → OCCT reader → CER Geometry + Topology + Assembly
→ Capability Level 2

**Dependencies:** `pythonocc-core` (LGPL; conda-forge or wheel)

**Deliverables:**
- `backend/interop/adapters/step.py` — `StepAdapter`
- `backend/interop/adapters/iges.py` — `IgesAdapter`
- `backend/interop/occt/bridge.py` — OCCT → CER translation
- Tests: read STEP test files; verify geometry entity count, bounding box,
  topology consistency

---

### Stage 4D — Manufacturing Feature Recognition Foundation

**Purpose:** Recognize machining features from B-Rep topology (holes,
pockets, slots, planar faces, cylindrical surfaces).

**Pipeline:** CER Topology → Feature Recognition Engine → Canonical
Manufacturing Feature → MachineryPro `Feature`

**Methods:**
- Rule-based B-rep pattern matching (production-ready for prismatic features)
- Volumetric delta analysis (optional, computationally intensive)
- ML-assisted classification (future; not in this stage)

**Deliverables:**
- `backend/interop/recognition/feature_recognizer.py`
- `backend/interop/recognition/rules/` — pattern matchers for hole, pocket,
  slot, planar face, cylinder
- Confidence scoring on recognized features
- Link from `CanonicalManufacturingFeature` to MachineryPro `Feature`

---

### Stage 4E — PMI / GD&T / Drawing Semantic Model

**Purpose:** Extract product manufacturing information from STEP AP242 PMI,
DXF annotations, and PDF vector drawings.

**Pipeline (STEP):** STEP AP242 PMI entities → CER PMI Model → tolerance
validation against MachineryPro `Feature`

**Pipeline (PDF/DXF):** Vector text + geometry → dimension extraction →
CER Drawing + PMI → feature tolerance enrichment

---

### Stage 4F — Native CAD Adapter Framework

**Purpose:** Define the plugin framework for commercial CAD adapters.
Implement one reference adapter (SolidWorks via API or STEP fallback).

**Architecture:** `NativeCADAdapter` extends `FormatAdapter`.
Plugin discovery via entry points. Graceful degradation to STEP when
native adapter unavailable.

---

### Stage 4G — Mesh Geometry Foundation

**Purpose:** STL, OBJ, 3MF, JT mesh import. Mesh → CER Mesh Geometry.
Mesh quality analysis (watertight, normals, degenerate faces).

**Dependencies:** `trimesh` (MIT), `numpy-stl`, `lib3mf`

---

### Stage 4H — Canonical CAM Model

**Purpose:** Define the CER CAM model with full schema and validation.
No native CAM system readers yet — use NC output as initial source.

**Pipeline:** Post-processed NC → CAM model inference → `CanonicalCAMProgram`
→ MachineryPro `ProcessPlan`

---

### Stage 4I — Native CAM Adapter Framework

**Purpose:** Plugin framework for native CAM adapters. Reference implementation
via a CAM system that offers API access (e.g., Fusion Manufacturing API or
Mastercam SDK if available).

---

### Stage 4J — Canonical NC / G-code Model and Parser

**Purpose:** First working NC parser. Generic EIA/ISO G-code → Canonical
NC Model. Modal state machine. Canned cycle interpretation.

**Key deliverables:**
- `backend/interop/adapters/nc/generic.py` — generic G-code parser
- Modal state tracker (G17/18/19, G90/91, G40/41/42, G43, etc.)
- Canned cycle decoder (G81, G83, G84, G86, etc.)
- Tool change and spindle event extraction
- `CanonicalNCProgram` population

---

### Stage 4K — CNC Controller Dialect Adapter Framework

**Purpose:** Normalize controller-specific NC dialects to the Canonical
NC Model. Reference implementations: Fanuc, Siemens 840D, Heidenhain.

**Architecture:** `DialectAdapter` extends generic NC parser.
Per-dialect token tables, macro resolvers, and cycle mappings.

---

### Stage 4L — Engineering Conversion Framework

**Purpose:** Bidirectional conversion between formats via CER.
Source → CER → Target. Fidelity tracking throughout.

**Key capabilities:**
- STEP ↔ IGES (via CER Geometry)
- CAD → DXF (via CER Drawing)
- NC dialect A → NC dialect B (via CER NC)
- CAM program → ProcessPlan (via CER CAM)

---

### Stage 4M — Conversion Fidelity / Data-Loss Validation

**Purpose:** Full implementation of `ConversionFidelityReport`. Fidelity
gates. Data-loss registry. Comparison reporting (CAD vs CAM vs NC).

---

## 10. Major Technical Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | **OpenCASCADE Python bindings stability** (`pythonocc-core` lags OCCT releases) | HIGH | Pin OCCT version; maintain conda environment separately; evaluate OCE fork |
| 2 | **Parasolid exact kernel requires Siemens licensing** | HIGH | Tier 3 SDK (Spatial) as alternative; STEP as fallback; document gap explicitly |
| 3 | **Native CAD API availability requires installed CAD system** | HIGH | Plugin model; graceful STEP fallback; never hard-require native adapter |
| 4 | **Feature recognition accuracy** (false positives on complex B-rep) | HIGH | Confidence scoring; human review gate before domain model population; never auto-commit unconfirmed features |
| 5 | **NC dialect variation** (even "Fanuc" varies across generations) | MEDIUM | Dialect version tagging; test corpus from real controllers; extensible token tables |
| 6 | **Conversational NC (Mazatrol)** has no documented public format | HIGH | Treat as proprietary/unsupported until Mazak SDK confirmed; CLDATA as alternative |
| 7 | **Large STEP files** (complex assemblies > 1 GB) | MEDIUM | Streaming parser; lazy loading of B-rep bodies; memory budget configuration |
| 8 | **PDF drawing OCR accuracy** for small tolerances (±0.01) | HIGH | Commercial OCR fallback option; confidence threshold before using extracted values; never silently use low-confidence values |
| 9 | **CATIA V6 / 3DEXPERIENCE** uses cloud-native format (3DXML) — limited open support | HIGH | Datakit commercial adapter; 3DXML reader (XML-based, partially parseable); document as Tier 3 only |
| 10 | **CAM native formats are proprietary binary** — no documented spec | HIGH | All CAM adapters must be Tier 4 (vendor API) or fall back to NC output; no reverse-engineering of binary formats |

---

## 11. Licensing and Vendor Lock-in Risks

| Integration | License Model | Lock-in Risk | Mitigation |
|---|---|---|---|
| OpenCASCADE (OCCT) | LGPL 2.1 | LOW | LGPL allows commercial use; no vendor lock-in |
| pythonocc-core | LGPL | LOW | Same as OCCT |
| ezdxf | MIT | NONE | Permissive |
| trimesh | MIT | NONE | Permissive |
| Siemens Parasolid SDK | Per-seat commercial | HIGH | Treat as optional Tier 3 plugin; STEP fallback always available |
| Spatial 3D InterOp (ACIS) | Per-seat commercial | HIGH | Same pattern |
| ODA Teigha (DWG) | ODA membership + license | MEDIUM | ODA membership is reasonable cost; DXF fallback always available |
| SolidWorks API | SolidWorks license required | HIGH | Plugin only; STEP fallback; never require SolidWorks on server |
| NX Open API | NX license required | HIGH | Plugin only; STEP fallback |
| CATIA CAA SDK | Dassault license required | HIGH | Plugin only; Datakit as Tier 3 alternative |
| Mastercam SDK | Dealer agreement required | HIGH | NC output fallback; plugin only |
| Autodesk Platform API | Autodesk account + credits | MEDIUM | Rate limits; cost per API call; alternative: local Fusion backup |
| Datakit CrossManager | Per-format annual license | MEDIUM | Best-in-class translator; evaluated per format need |
| Theorem-XE | Annual license | MEDIUM | Alternative to Datakit for aerospace formats |
| pyansys | MIT (for readers) | NONE | Ansys solver still requires license for simulation |

**Core rule:** MachineryPro AI's CER and all domain-model logic must compile
and run without any commercial license. Commercial adapters are plugins that
extend capability but are never required for the base system to function.

---

## 12. Recommended First Implementation Stage

**Stage 4A — Universal Engineering Interoperability Architecture**

Rationale:
1. It is pure schema and interface work — no external dependencies required.
2. It establishes the CER package structure that all subsequent stages
   depend on.
3. It can be implemented and tested using only the existing Python stdlib
   and MachineryPro domain models.
4. It causes zero risk to Stages 3A–3J.
5. It produces immediately testable deliverables (schema validation,
   adapter registry, fidelity model).

Stage 4A alone is a complete, mergeable, testable unit of work consistent
with the project's stage discipline.

After 4A is merged, Stage 4B (canonical geometry model) and Stage 4J (NC
parser) can proceed in parallel — 4B requires no external dependencies,
and 4J requires only a custom parser (no licensing issues).

---

## 13. Architecture Constraints Inherited from Stages 3A–3J

The interoperability layer must not violate these:

1. **No float.** All engineering values in CER models that flow into
   MachineryPro domain models must use `Decimal`.
2. **Fail closed.** An unrecognized or partially parsed file must never
   silently produce an incorrect domain model object.
3. **Provenance mandatory.** Every `Feature`, `Material`, or
   `MachiningParameters` object populated from an ingested file must carry
   a `Provenance` that traces to the source file, adapter version, and
   capability level.
4. **Immutable results.** CER models follow the same frozen-dataclass
   convention as domain models.
5. **No AI authority.** ML-assisted feature recognition may suggest
   features at a classified confidence level; a human-review gate or an
   explicit authority upgrade is required before the suggestion becomes
   an authoritative manufacturing feature.
6. **Zero vendor required for core.** The base system must function —
   at Level 0–2 for supported formats — without any commercial SDK.

---

*End of Architecture Roadmap*
*Stage 4A implementation may begin after this document is reviewed and accepted.*
