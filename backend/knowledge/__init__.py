"""Knowledge layer: literature ingestion, indexing and provenance.

Maps the pre-existing corpus inventoried in Stage 0 (``Machinery_Article/``,
``Progamlar/`` reports, handbook PDFs) into a searchable, citation-tracked
knowledge base used for grounding rules and later RAG answers.
Source files are read-only; all derived artifacts live under ``data/``.
"""
