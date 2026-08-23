# Stage 0 Discovery Report (archived)

**Root inspected:** `d:\makina_ogrenmesi\Machinery_ AI` (path contains a space — known
cross-platform risk). Method: recursive READ-ONLY listing + extension/size/duplicate analysis +
content reading of all text documents. Performed 2026-08-22.

## Inventory (verified)

```text
Machinery_ AI\
├── Machinery_Article\        395 files
│   └── Ders Notları\          69 PDFs (handbooks/course notes)
└── Progamlar\                  7 files (reports; typo of "Programlar")
```

472 files · ~1.59 GB (1,594,505,769 B) · 0 empty folders · no git repo · no cache dirs.

| Ext | Count | Note |
|---|---|---|
| .pdf | 457 | articles + handbooks |
| .docx | 7 | report renders + 3 manuscripts |
| .md | 4 | research/platform reports |
| .doc | 1 | genetic-programming Ra paper |
| .xml | 1 | YÖK thesis metadata (coated-tool wear, Inconel 625/AISI 304 milling parameter grid) |
| .PNG | 1 | DergiPark ordering screenshot |
| .crdownload | 1 | 108 MB incomplete download — junk candidate |

**Zero source code, zero notebooks, zero CSV/Excel, zero CAD files, zero configs, zero databases.**

Duplicates: ≥68 files carry `(n)` suffixes; largest byte-identical groups ×6/×5/×4/×4/×4.
Off-topic: `Progamlar\deep-research-report (9).md` (meta-science publishing report).

## Reusable assets

| Asset | Role |
|---|---|
| `Talasli_Imalat_Zeka_Platformu_Arastirma_Raporu.md` (879 lines) | de-facto product charter (11 disciplines, MVP = STEP AP242/PDF → 3-axis prismatic → DFM/process/tool/parameters/quote; deterministic-authoritative principle; independent from TorqPro) |
| `Talasli_Imalat_Manufacturing_Intelligence_Platform_Raporu.md` | de-facto architecture (CAD→Profitability chain, competitor matrix, Faz 0–12 roadmap, no-CAM-kernel decision) |
| `Talasli_Imalat_Bilimsel_Makaleler_ve_Problem_Literaturu.md` | grounding-layer blueprint (curated CIRP/IJMTM/ASME bibliography ↔ problem families) |
| 457-article corpus + handbooks | formula mining + future RAG grounding |

## Domain classification highlights

Strong: Knowledge Base, Reports/Documentation. Source-material level: cutting parameters,
surface roughness (future ML), tool wear/life (future ML), materials/machinability, machine
selection, CNC/CAM topics, defect taxonomy. Concept-only: fixture, costing, scheduling,
CAD/drawing intelligence, GD&T, inspection.

## Verdicts

- Software assessment: **documentation + reference-corpus repository; no software.**
- AI assessment: A) deterministic core first (authoritative); B) AI-assisted drafting/RAG with
  citations (justified target); C) ML predictions = future capabilities with scientific grounding
  but **no training data locally**.

STAGE_0_DISCOVERY_STATUS: GO

Reasons: documented product definition already exists; rich relevant corpus; greenfield start
(no legacy debt); hygiene issues catalogued and deferrable.

RECOMMENDED_STAGE_1_SCOPE: skeleton (backend packages core/knowledge/machining/materials/
tooling/machines/process_planning/cutting_parameters/quality/costing/ai), README, pyproject,
.gitignore, tests smoke, docs (charter/architecture/rule-registry/governance/this archive),
scripts (catalog_literature.py, dedup_report.py), config/app.yaml — creating files only, no
moves/deletes/git.
