"""Preferred public namespace for ADK execution-policy decisions.

ADK is not a runtime. The canonical implementation lives in this package.
The historical :mod:`agent_dev_kit.runtime_control` namespace remains a 5.x
compatibility facade and re-exports these exact objects.
"""

from .engine import (
    DECISION_SCHEMA,
    DECISION_SCHEMA_V2,
    EVENT_SCHEMA,
    POLICY_SCHEMA,
    POLICY_SCHEMA_V2,
    STATE_SCHEMA,
    RuntimeControlError,
    evaluate,
    goal_intake_attestation_sha256,
    reduce_events,
    validate_policy,
)

__all__ = [
    "DECISION_SCHEMA",
    "DECISION_SCHEMA_V2",
    "EVENT_SCHEMA",
    "POLICY_SCHEMA",
    "POLICY_SCHEMA_V2",
    "STATE_SCHEMA",
    "RuntimeControlError",
    "evaluate",
    "goal_intake_attestation_sha256",
    "reduce_events",
    "validate_policy",
]
