# Engineering Rule Registry — Format & Governance

**Status:** Stage 1 deliverable; registry files themselves are created in Stage 2
(`config/rules/*.yaml`), loaded by `backend.core` in Stage 3. Both platform reports identify
this registry as a founding artifact ("Rule Registry" / "Engineering Rule Registry").

## Purpose

A single authoritative home for engineering constants, equations and limits so that:

- every deterministic result is reproducible from named rules;
- every constant has provenance (source document + locator);
- AI layers can *cite* rules but can never mutate them.

## Rule file format (YAML)

```yaml
rule_id: CUT-TURN-001            # unique, stable, prefixed by domain
title: Turning cutting speed upper limit for validated material/tool pair
domain: machining.turning
status: draft                    # draft -> reviewed -> approved
equation_ref: vc = pi * D * n / 1000   # symbolic reference; implementation lives in code
limits:
  vc_max_m_min: 260              # example only - MUST come from a cited source
valid_for:
  material: {group: P, example: AISI 1040}
  tool: {coating: TiAlN, holder_sign: negative}
source:
  type: article                  # handbook | standard | article | supplier_catalog
  ref_sha256: <sha256 from data/literature_catalog.csv>
  locator: "p. 4, Table 3"
provenance:
  created: 2026-08-22
  author: <identity>
  revision: 1
tests:
  golden_file: tests/golden/CUT-TURN-001.json   # required before approval
```

## Lifecycle

`draft` → `reviewed` → `approved`. **Approved requires ALL of:** equation/unit reference,
explicit limits, validity scope, cited source with SHA-256 + locator, and a pytest golden test.

## Prohibitions

1. No rule without provenance.
2. LLM-generated constants can never reach `approved` without human review against the cited
   source.
3. No silent edits — every change bumps `provenance.revision`.
4. Unverified (`draft`) values may inform drafts/suggestions but never authoritative outputs.

## Testing requirement

Each approved rule ships with golden values executed in CI-style local runs; failures block
release of the affected module.
