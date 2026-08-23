# System Architecture — Machinery AI (v0.1 proposal)

**Status:** Stage 1 proposal, distilled from the Stage 0 platform reports. Items marked
*PROPOSED* are assumptions to confirm in Stage 2 — no local evidence forces them yet.

## 1. Value chain (target product)

CAD/Drawing → Feature Recognition → DFM → Process Planning → Machine Selection → Fixture →
Tool Selection → Cutting Parameters → CAM Strategy → Simulation → Quality Plan → Cost & Quote →
Scheduling → Execution → Monitoring → Actual Cost → Profitability → Continuous Learning

## 2. Layer view

```text
+--------------------------------------------------------------+
| frontend  (PROPOSED web UI, Stage 9)                          |
+--------------------------------------------------------------+
| api       (PROPOSED FastAPI, Stage 9)                         |
+--------------------------------------------------------------+
| domain services: process_planning | cutting_parameters |      |
|   quality | costing | scheduling                              |
+--------------------------------------------------------------+
| registries: materials | tooling | machines | knowledge        |
+--------------------------------------------------------------+
| core: units · validation · fail-closed policy engine          |
+--------------------------------------------------------------+
| ai layer: RAG over curated corpus — ADVISORY ONLY, cites      |
+--------------------------------------------------------------+
```

## 3. Module map ↔ backend packages

| Package | Responsibility | Stage |
|---|---|---|
| `backend.core` | units, validation, fail-closed engine | 2–3 |
| `backend.knowledge` | corpus ingestion/indexing/provenance (`Machinery_Article` read-only) | 2 |
| `backend.machining` | deterministic force/power/time/MRR calculators | 3 |
| `backend.materials` | material registry (schema-first; provenance-gated values) | 2/6 |
| `backend.tooling` | ISO 13399-style tool model | 6 |
| `backend.machines` | machine capability models | 6 |
| `backend.process_planning` | op sequencing drafts + approval gate | 4 |
| `backend.cutting_parameters` | recommendation + limit validation | 3–4 |
| `backend.quality` | inspection planning, Cp/Cpk | 7 |
| `backend.costing` | cycle time, should-cost, quote ledgers | 4+/7 |
| `backend.ai` | RAG assistant, defect diagnosis, NLQ (advisory) | 8 |

## 4. Decision flow (fail-closed)

request → input completeness check *(missing ⇒ refuse with gap list)* → approved-rule lookup →
deterministic calculation → limit validation → result envelope
`{value, unit, rule_id@revision, inputs-hash, citations, approval_state}` → human approval gate.

## 5. AI boundaries

- **A Deterministic Core** (authoritative): machining math, tolerance math, SPC/Cp/Cpk,
  engineering limit checks.
- **B AI-Assisted** (drafts with citations): drawing understanding (needs sample STEP/PDF — none
  exist yet), plan/tool suggestions, defect diagnosis via problem-family taxonomy, NL assistant.
- **C Future ML**: Ra/tool-life/cycle-time prediction, anomaly & load prediction — scientific
  grounding exists locally, training data does not.

## 6. Traceability contract

Every numeric output carries rule/model id + revision, hashed input snapshot, source references
and timestamp. This is the platform's core IP per the architecture report ("traceable
engineering recommendations").

## 7. Open decisions (Stage 2 agenda)

API framework (FastAPI *proposed*) · persistence (SQLite start → PostgreSQL later,
*proposed*) · frontend framework (*TBD Stage 9*) · CAM integration format.
