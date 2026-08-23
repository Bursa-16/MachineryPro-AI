"""AI-assisted engineering layer.

Target capabilities grounded in the Stage 0 corpus: retrieval-augmented
answers over curated literature, process-plan/tool suggestions as DRAFTS,
defect-family diagnosis, natural-language engineering assistant.

Boundary conditions (non-negotiable):
    * AI output is advisory; it never silently alters a validated result.
    * Every AI answer must carry citations into the registered corpus.
    * Fail closed: without sufficient grounding the assistant must say so.
"""
