# Rule Registry — config/rules

This directory is the **declarative metadata home** for engineering rules
(per docs/ENGINEERING_RULE_REGISTRY.md and docs/SYSTEM_ARCHITECTURE.md).

Stage 2 status: **intentionally empty of machining knowledge tables.** The
Stage 2 registry is code-level only (`backend/core/rules/`); no YAML rule
files are loaded or executed yet.

When this directory is populated in a later stage it will contain **declarative
metadata only**:

* rule identity, version, description, domain;
* required-input names;
* declarative constants/limits with a cited source reference.

The following are **never allowed** in this directory or its loaders:

* executable code (`eval`, `exec`, dynamic Python-from-YAML);
* hidden engineering thresholds without provenance;
* literature/AI-derived values promoted to authority without review.