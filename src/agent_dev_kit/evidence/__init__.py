"""Typed evidence envelope primitives and reference-only bridge adapters."""

from .bridge import (
    EvidenceBridgeContext,
    envelope_agent_value_receipt,
    envelope_run_evidence,
    envelope_trace_summary,
)
from .envelope import bind_evidence_envelope, validate_evidence_envelope

__all__ = [
    "EvidenceBridgeContext",
    "bind_evidence_envelope",
    "envelope_agent_value_receipt",
    "envelope_run_evidence",
    "envelope_trace_summary",
    "validate_evidence_envelope",
]
