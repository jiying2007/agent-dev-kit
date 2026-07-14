"""Deterministic caller-supplied target smoke fixture.

This fixture validates the smoke harness contract only.  It is deliberately not
accepted as evidence that a real external runtime discovered or loaded assets.
"""

from __future__ import annotations

import os
from pathlib import Path


root = Path(os.environ["ADK_TARGET_ROOT"])
target = os.environ["ADK_TARGET"]
stage = os.environ["ADK_TARGET_SMOKE_STAGE"]

if not root.is_dir():
    raise SystemExit("target root is missing")

skills = list(root.glob("skills/*/SKILL.md"))
agents = list(root.glob("agents/*.md"))
if target == "hermes-agent" and agents:
    raise SystemExit("Hermes smoke tree unexpectedly contains agents")
if not skills:
    raise SystemExit("smoke tree contains no native skills")

if stage == "discovery":
    raise SystemExit(0)
if stage == "load":
    if "description:" not in skills[0].read_text(encoding="utf-8"):
        raise SystemExit("skill frontmatter has no description")
    raise SystemExit(0)
if stage == "trigger":
    if "#" not in skills[0].read_text(encoding="utf-8"):
        raise SystemExit("skill body is missing")
    raise SystemExit(0)
if stage == "permission":
    if target != "hermes-agent" and not agents:
        raise SystemExit("permission smoke requires a native agent")
    raise SystemExit(0)
raise SystemExit("unknown smoke stage")
