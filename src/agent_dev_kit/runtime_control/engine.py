"""5.x compatibility facade for :mod:`agent_dev_kit.execution_policy.engine`.

New code must import the canonical implementation from ``execution_policy``.
This module intentionally contains no decision-engine implementation.
"""

from ..execution_policy.engine import *  # noqa: F403
