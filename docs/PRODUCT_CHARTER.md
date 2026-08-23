# Product Charter — Machinery AI

**Status:** Draft v0.1 (Stage 1 deliverable)
**Sources:** `Progamlar\Talasli_Imalat_Zeka_Platformu_Arastirma_Raporu.md`,
`Progamlar\Talasli_Imalat_Manufacturing_Intelligence_Platform_Raporu.md` (Stage 0 inventory).

## 1. Mission

Build an **independent, closed-loop machining intelligence platform** covering the engineering
decision chain from CAD/technical-drawing understanding to profitable delivery. The product is
explicitly *not* a module of any existing system (TorqPro or otherwise); it reuses their proven
principles — deterministic, explainable, traceable, fail-closed — as an independent platform.

## 2. The eleven disciplines on one part record

1. CAD & technical drawing understanding
2. Manufacturability analysis (DFM)
3. Computer-aided process planning (CAPP)
4. Tooling & cutting-parameter engineering
5. Fixture & clamping planning
6. CAM strategy creation & validation
7. Machine capability & finite capacity planning
8. CNC/MES shop-floor data collection
9. Quality planning & result verification
10. Quoting & predicted cost calculation
11. Actual cost, deviation & profitability analysis

The value is the **coupling**: tolerance drives sequence → sequence drives setups → setups drive
fixture/quality cost → machine capacity drives due-date risk → actual cycle time corrects the
next quote.

## 3. MVP scope (first sellable slice)

| Item | Decision |
|---|---|
| Input formats | STEP AP242 + PDF technical drawings |
| Part class | 3-axis prismatic CNC parts |
| Customer segment | Automotive/defense suppliers, high-variety low/medium volume |
| Outputs | DFM risk list, process-plan draft, tool + cutting-parameter suggestion, estimated cycle time, quote draft |
| Guarantee | Every decision carries source + revision; engineer approval required |

## 4. Phase-1 non-goals

- Translating native CAD formats with own code.
- Writing a new CAM kernel or postprocessors (integrate with existing CAM instead).
- Enabling material / heat-treatment suggestions without design requirement + engineer approval.
- Closed-loop optimization (later phase after core validation).

## 5. Governing principles

Deterministic calculations are **authoritative** · Explainable · Traceable · Revision-controlled ·
Human approval gates · Fail-closed on missing/invalid data.

## 6. Key risks and controls (from the research report)

Scope too large → narrow MVP · Wrong CAD/PMI reading → confidence score, overlay, human
verification, fail-closed · Unlicensed catalog/web data → licensed APIs + provenance policy ·
AI hallucination → deterministic engine + rule registry + mandatory sourcing · Post/NC errors →
mature CAM + virtual validation + signed release · Catalog-vs-real-machine gap → site-specific
validated capability models · Estimate/accounting confusion → estimated/planned/actual ledger
separation · Defense-sector security → on-prem option, RBAC, encryption, OT segmentation ·
Per-customer code drift → configuration + rule registry + adapter architecture.

## 7. Open items for Stage 2

Measurable MVP exit criteria (benchmark part set, quoting accuracy target) — deliberately left
undefined until the domain model exists.
