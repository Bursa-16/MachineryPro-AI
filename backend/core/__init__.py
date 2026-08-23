"""Core engineering primitives: unit handling, validation and the fail-closed
policy engine.

Every deterministic result must be reproducible from registered rules and
inputs; on missing/invalid data the system must fail closed (refuse to answer)
rather than guess.
"""
