"""Material engineering registry: grades, properties, machinability classes.

Stage 0 finding: material data exists only inside unstructured article texts.
Registry is schema-first; every populated value must cite document + locator
(page/table) before it may be used by deterministic rules.

Stage 3G adds the deterministic in-memory catalog and lookup layer.
No production seed data is included.
"""

from backend.materials.catalog import MaterialCatalog

__all__ = ["MaterialCatalog"]
