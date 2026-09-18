"""Canonical public namespace for ADK execution-policy decisions.

ADK provides policy and gate decisions; it is not an agent runtime.
"""

from .engine import (
    DECISION_SCHEMA_V2,
    EVENT_SCHEMA,
    POLICY_SCHEMA_V2,
    STATE_SCHEMA,
    RuntimeControlError,
    evaluate,
    goal_intake_attestation_sha256,
    reduce_events,
    validate_policy,
)

__all__ = [
    "DECISION_SCHEMA_V2",
    "EVENT_SCHEMA",
    "POLICY_SCHEMA_V2",
    "STATE_SCHEMA",
    "RuntimeControlError",
    "evaluate",
    "goal_intake_attestation_sha256",
    "reduce_events",
    "validate_policy",
]
