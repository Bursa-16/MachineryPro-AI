"""Deterministic in-memory tool catalog (Stage 3G).

Provides registration and lookup of :class:`~backend.domain.tool.Tool`
instances for use as applicability references in empirical cutting-parameter
records.

No production seed data is included.  Every :class:`Tool` must carry
explicit provenance before it can be referenced by authoritative records.

Lookup semantics
----------------
* Exact-ID lookup raises :class:`~backend.empirical.exceptions.EmpiricalDataError`
  when the ID is not found.
* Collection queries return all matching records in deterministic order
  (sorted by ``tool_id``).  Empty result → empty tuple (not an error).
* Duplicate ``tool_id`` is rejected at registration (fail closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.enums import OperationType, ToolType
from backend.domain.tool import Tool
from backend.empirical.exceptions import EmpiricalDataError

__all__ = ["ToolCatalog"]


@dataclass
class ToolCatalog:
    """In-memory catalog of :class:`~backend.domain.tool.Tool` records.

    ``_tools`` is private; all mutation goes through :meth:`register`.
    """

    _tools: dict[str, Tool] = field(default_factory=dict, init=False)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: Tool) -> Tool:
        """Register *tool*; raise on duplicate ``tool_id``.

        Raises:
            TypeError: when *tool* is not a :class:`Tool`.
            EmpiricalDataError: when the ID is already registered.
        """
        if not isinstance(tool, Tool):
            raise TypeError("only Tool instances can be registered")
        if tool.tool_id in self._tools:
            raise EmpiricalDataError(
                f"tool id {tool.tool_id!r} is already registered"
            )
        self._tools[tool.tool_id] = tool
        return tool

    # ------------------------------------------------------------------
    # Exact-ID lookup
    # ------------------------------------------------------------------

    def get(self, tool_id: str) -> Tool:
        """Return the tool with *tool_id*.

        Raises:
            EmpiricalDataError: when the ID is not registered.
        """
        tool = self._tools.get(tool_id)
        if tool is None:
            raise EmpiricalDataError(f"no tool with id {tool_id!r}")
        return tool

    def has(self, tool_id: str) -> bool:
        """True when *tool_id* is registered."""
        return tool_id in self._tools

    # ------------------------------------------------------------------
    # Collection queries
    # ------------------------------------------------------------------

    def find_by_type(self, tool_type: ToolType) -> tuple[Tool, ...]:
        """All tools with the given :class:`ToolType`.

        Returns empty tuple when none match.  Sorted by ``tool_id``.
        """
        return tuple(
            sorted(
                (t for t in self._tools.values() if t.tool_type is tool_type),
                key=lambda t: t.tool_id,
            )
        )

    def find_by_operation(
        self, operation_type: OperationType
    ) -> tuple[Tool, ...]:
        """All tools that support the given :class:`OperationType`.

        Returns empty tuple when none match.  Sorted by ``tool_id``.
        """
        return tuple(
            sorted(
                (
                    t
                    for t in self._tools.values()
                    if operation_type in t.supported_operations
                ),
                key=lambda t: t.tool_id,
            )
        )

    def all(self) -> tuple[Tool, ...]:
        """All registered tools sorted by ``tool_id``."""
        return tuple(sorted(self._tools.values(), key=lambda t: t.tool_id))

    def ids(self) -> tuple[str, ...]:
        """All registered tool IDs in stable registration order."""
        return tuple(self._tools)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        return self.has(tool_id)
