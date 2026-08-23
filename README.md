# Machinery AI

**Deterministic-first machining intelligence platform** — from CAD/drawing understanding through
process planning, tool & parameter selection, quality and costing, with AI used as an
explainable, citation-forced assistant rather than an autonomous decision maker.

> **Core principle** (from the Stage 0 product-definition reports):
> Deterministic engineering calculations, verified rules and approved data are authoritative.
> AI is used to understand geometry, generate alternatives, surface gaps and explain results.
> AI may never silently alter a validated engineering result or replace the responsible engineer.

## Project status

| Stage | Scope | Status |
|---|---|---|
| 0 | Discovery | ✅ Done — see `docs/STAGE_0_DISCOVERY_REPORT.md` |
| 1 | Repository / Foundation | 🔨 Current |
| 2 | Engineering Domain Model + Rule Registry | ⬜ |
| 3 | Deterministic Machining Core | ⬜ |
| 4 | Process Planning MVP | ⬜ |
| 5 | CAD / Drawing Intelligence | ⬜ |
| 6 | Tool & Machine Intelligence | ⬜ |
| 7 | Quality / Inspection Intelligence | ⬜ |
| 8 | AI Integration (RAG over curated corpus) | ⬜ |
| 9 | UI / API Integration | ⬜ |
| 10 | Validation / Release | ⬜ |

## Repository layout

```text
backend/            Domain packages (core, knowledge, machining, materials, tooling,
                    machines, process_planning, cutting_parameters, quality,
                    costing, ai)
frontend/           UI (planned, Stage 9)
data/               Generated catalogs and future datasets
  raw/              Future measured/experimental data
  extracted/        Structured data mined from literature
docs/               Product charter, architecture, rule registry, governance
scripts/            Read-only corpus utilities (catalog, dedup report)
config/             Application configuration
tests/              Test suite (pytest-compatible)

Machinery_Article/  PRE-EXISTING SOURCE MATERIAL — read-only, never modified
Progamlar/          PRE-EXISTING SOURCE MATERIAL — read-only, never modified
```

## Source material policy

The pre-existing corpus (457 machining PDFs, handbooks, reports, thesis metadata — ~1.59 GB,
472 files inventoried in the Stage 0 report) is treated as **read-only reference material**.
Project code never writes into those folders. Publisher-supplied PDFs are used for internal
grounding only and must not be redistributed — see `docs/DATA_GOVERNANCE.md`.

## Quickstart

```bash
# create an environment (any Python >= 3.11)
python -m venv .venv
.venv\Scripts\activate           # Windows

# install dev tools (optional, for tests/linting)
pip install -e ".[dev]"

# run the smoke test
pytest                            # or: python tests/test_smoke.py

# catalog the literature corpus (read-only, writes data/literature_catalog.csv)
python scripts/catalog_literature.py

# duplicate report (report-only, deletes nothing)
python scripts/dedup_report.py
```
