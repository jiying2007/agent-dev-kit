"""Direct-target runtime adapter contracts.

The presence of this package defines a Python SPI only. It does not certify any
runtime. Native conformance remains governed by ``adk-target-contract/v2`` and
its runtime evidence receipts.
"""

from .adapter import (
    CONFORMANCE_CAPABILITIES,
    AdapterContext,
    AdapterOperation,
    AdapterPlan,
    AdapterResult,
    RuntimeAdapter,
)

__all__ = [
    "CONFORMANCE_CAPABILITIES",
    "AdapterContext",
    "AdapterOperation",
    "AdapterPlan",
    "AdapterResult",
    "RuntimeAdapter",
]
