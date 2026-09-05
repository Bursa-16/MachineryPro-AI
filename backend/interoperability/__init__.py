"""Universal Engineering Interoperability Foundation for MachineryPro AI.

Stage 4A — establishes vendor-neutral contracts, data structures, adapter
interfaces, format capability model, source identity model, canonical-document
envelope, and conversion-fidelity semantics required by all future
CAD/CAM/CAE/drawing/PMI/NC ingestion stages.

Product-level interoperability principle (exact statement):

    "MachineryPro AI shall ingest, normalize, analyze, validate, compare and,
    where technically possible, convert the widest practical range of CAD,
    CAM, CAE, drawing, PMI and CNC/NC engineering formats without tying
    manufacturing intelligence to any single vendor format."

Non-negotiable fidelity principle (exact statement):

    "No adapter may silently downgrade engineering semantics. Any loss,
    inference, reconstruction, unsupported semantic, or confidence reduction
    must be explicitly represented in fidelity metadata."

Architecture pipeline::

    SOURCE FILE / ENGINEERING SOURCE
        ↓
    FORMAT ADAPTER / PARSER (Stage 4B+)
        ↓
    CANONICAL ENGINEERING REPRESENTATION (CER)   ← this package
        ↓
    SEMANTIC NORMALIZATION (Stage 4D+)
        ↓
    MACHINERYPRO DOMAIN MODELS (Stages 3A–3J)
        ↓
    DETERMINISTIC ENGINEERING ANALYSIS
        ↓
    VALIDATION / COMPARISON (Stage 4L+)
        ↓
    EXPORT / CONVERSION + FIDELITY REPORT (Stage 4M)

Vendor independence
-------------------
This package imports zero external dependencies beyond the Python stdlib
and the MachineryPro domain layer.  Commercial/native adapters for CATIA,
NX, SolidWorks, Parasolid, Mastercam, etc. are optional plugins; the
core interoperability package functions without them.

Exports
-------
Enums: :class:`FormatFamily`, :class:`AdapterCapability`,
:class:`CapabilityLevel`, :class:`AdapterLicense`, :class:`FidelityClass`,
:class:`FidelityReportCompleteness`, :class:`NormalizationStatus`

Models: :class:`EngineeringSource`, :class:`FormatDescriptor`,
:class:`AdapterMetadata`, :class:`CanonicalEntityRef`,
:class:`FidelityEvent`, :class:`ConversionFidelityReport`,
:class:`CanonicalDocument`

Adapter interface: :class:`FormatAdapter`

Registry: :class:`AdapterRegistry`, :class:`AdapterRegistryError`
"""

from backend.interoperability.adapter import FormatAdapter
from backend.interoperability.enums import (
    AdapterCapability,
    AdapterLicense,
    CapabilityLevel,
    FidelityClass,
    FidelityReportCompleteness,
    FormatFamily,
    NormalizationStatus,
)
from backend.interoperability.models import (
    AdapterMetadata,
    CanonicalDocument,
    CanonicalEntityRef,
    ConversionFidelityReport,
    EngineeringSource,
    FidelityEvent,
    FormatDescriptor,
)
from backend.interoperability.registry import AdapterRegistry, AdapterRegistryError

__all__ = [
    # Enums
    "AdapterCapability",
    "AdapterLicense",
    "CapabilityLevel",
    "FidelityClass",
    "FidelityReportCompleteness",
    "FormatFamily",
    "NormalizationStatus",
    # Models
    "AdapterMetadata",
    "CanonicalDocument",
    "CanonicalEntityRef",
    "ConversionFidelityReport",
    "EngineeringSource",
    "FidelityEvent",
    "FormatDescriptor",
    # Adapter
    "FormatAdapter",
    # Registry
    "AdapterRegistry",
    "AdapterRegistryError",
]
