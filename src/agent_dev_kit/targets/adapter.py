"""Typed SPI for direct target runtime adapters.

This module deliberately separates *adapter shape* from *conformance status*.
Implementing :class:`RuntimeAdapter` does not imply native verification.  A
target becomes runtime-conformance-certified only through the existing
``adk-target-contract/v2`` receipt and trust policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol, Sequence, runtime_checkable

CONFORMANCE_CAPABILITIES = frozenset(
    {
        "discovery",
        "load",
        "trigger",
        "permission",
        "resume",
        "cancel",
        "rollback",
        "trace",
    }
)

OperationKind = Literal["read", "write", "execute", "network"]
AdapterStatus = Literal["pass", "fail", "blocked", "unsupported", "unknown"]


@dataclass(frozen=True, slots=True)
class AdapterContext:
    """Immutable execution context supplied by the ADK control plane."""

    target: str
    workspace: Path
    dry_run: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AdapterOperation:
    """One planned side effect or observation.

    ``description`` is intentionally human-readable.  Runtime-specific opaque
    payloads remain adapter-owned and must not be treated as conformance
    evidence unless emitted through ``collect_evidence``.
    """

    kind: OperationKind
    description: str
    resource: str | None = None


@dataclass(frozen=True, slots=True)
class AdapterPlan:
    """Read-before-write plan returned before installation or mutation."""

    target: str
    operations: tuple[AdapterOperation, ...] = ()
    required_capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """Normalized adapter result without making a certification claim."""

    status: AdapterStatus
    summary: str
    details: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status == "pass"


@runtime_checkable
class RuntimeAdapter(Protocol):
    """Protocol implemented by a direct runtime target adapter.

    The method set covers lifecycle operations needed by ADK control and the
    eight conformance capabilities already defined by target-contract/v2.
    Adapters must remain fail-closed: unsupported operations return an explicit
    ``unsupported``/``blocked`` result rather than silently succeeding.
    """

    adapter_id: str
    target: str

    def detect(self, context: AdapterContext) -> AdapterResult: ...

    def version(self, context: AdapterContext) -> AdapterResult: ...

    def plan(self, context: AdapterContext) -> AdapterPlan: ...

    def export(self, context: AdapterContext, plan: AdapterPlan) -> AdapterResult: ...

    def install(self, context: AdapterContext, plan: AdapterPlan) -> AdapterResult: ...

    def discover(self, context: AdapterContext) -> AdapterResult: ...

    def load(self, context: AdapterContext) -> AdapterResult: ...

    def trigger(self, context: AdapterContext) -> AdapterResult: ...

    def resume(self, context: AdapterContext) -> AdapterResult: ...

    def cancel(self, context: AdapterContext) -> AdapterResult: ...

    def rollback(self, context: AdapterContext) -> AdapterResult: ...

    def health(self, context: AdapterContext) -> AdapterResult: ...

    def collect_evidence(
        self,
        context: AdapterContext,
        *,
        capabilities: Sequence[str],
    ) -> AdapterResult: ...
