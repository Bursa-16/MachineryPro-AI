# Data Governance & Source Policy

**Status:** Stage 1 deliverable. Derived from Stage 0 findings (publisher-PDF corpus,
licensing exposure, duplicate hygiene).

## Corpus classification

| Material | Handling |
|---|---|
| Publisher PDFs (`1-s2.0-*`, DergiPark DOI names, Wear 2025 set) | **Internal grounding/reference only.** No redistribution, bundling or sublicense in any product build. Kept out of git by `.gitignore`. |
| Handbooks & course notes (`Ders Notları`) | Same internal-only treatment until license status is verified. |
| Thesis XML / PNG screenshot | Reference metadata; same policy. |
| Project-generated catalogs (`data/*.csv`) | Trackable — they contain index/metadata only, not copyrighted content. |

## Extraction provenance rule (mandatory)

Any value extracted from the corpus into a registry must record: source file SHA-256
(from `data/literature_catalog.csv`), page/table locator, extraction date, extractor identity
and verification status. Unverified values remain `draft` and cannot feed approved rules.

## Cleanup policy

Duplicates and junk (`*.crdownload`, `(n)` copies) are **reported only**
(`scripts/dedup_report.py`). Deletion or movement requires explicit, per-group human approval.
Nothing is auto-cleaned.

## Folder integrity

`Machinery_Article/`, `Progamlar/` and loose root documents are read-only for all project code
and scripts. Scripts may read them; nothing writes into them.

## Privacy & future data

No personal or customer production data exists at Stage 0. Before any shop-floor/CNC data
ingestion is enabled (Phase 8+), retention periods and access control must be defined here.
