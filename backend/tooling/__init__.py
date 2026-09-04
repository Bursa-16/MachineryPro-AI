"""Cutting-tool and insert registry (Stage 3G).

Stage 0 finding: no vendor catalog data exists locally; schema-first
development until licensed data sources are acquired.

Stage 3G adds the deterministic in-memory catalog and lookup layer.
No production seed data is included.
"""

from backend.tooling.catalog import ToolCatalog

__all__ = ["ToolCatalog"]
