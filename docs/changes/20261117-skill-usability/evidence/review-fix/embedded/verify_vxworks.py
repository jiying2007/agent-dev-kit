"""U06 review fix: four production-matcher cases and the existing eight ratchets."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest
from agent_dev_kit.profile_context_footprint import enforce_profile_ratchet

phase = sys.argv[1]
if phase not in ("red", "green"):
    raise SystemExit("phase must be red or green")
skill = ROOT / "skills/adk-rtos-task-design/SKILL.md"
raw = skill.read_bytes()
manifest = Manifest.load(ROOT)
cases = [
    ("vxworks-existing-positive", "请为 VxWorks 做任务设计", True),
    ("freertos-existing-positive", "请为 FreeRTOS 做实时任务设计。", True),
    ("sales-negative", "请做一个季度销售团队任务设计。", False),
    ("no-rtos-negative", "项目没有 RTOS；请评估裸机主循环任务设计。", False),
]
routes = []
for identity, prompt, expected in cases:
    result = match_text(manifest, prompt)
    selected = result.get("match") is True and result.get("skill") == "adk-rtos-task-design"
    passed = selected == expected and result.get("mutation_permission") == "deny"
    routes.append(dict(id=identity, prompt=prompt, expect_selected=expected,
                       actual=result, passed=passed))
ratchets = [enforce_profile_ratchet(manifest, name) for name in sorted(manifest.data["profiles"])]
assert len(ratchets) == 8
policy = ROOT / "manifests/profile_context_ratchets.json"
record = dict(
    phase=phase, observed_at=datetime.now(timezone.utc).isoformat(),
    skill_path=str(skill), skill_sha256=hashlib.sha256(raw).hexdigest(), skill_bytes=len(raw),
    implicit_context_line=next(line for line in raw.decode().splitlines() if line.startswith("implicit_context:")),
    routes=routes, route_passed=sum(row["passed"] for row in routes),
    ratchet_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(), ratchets=ratchets,
    native_runtime_evidence="not-run", live_device_evidence="not-run",
)
(OUT / f"{phase}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(dict(phase=phase, routes=f"{record['route_passed']}/4",
                      failures=[row["id"] for row in routes if not row["passed"]],
                      ratchets={row["profile"]: row["status"] for row in ratchets}), ensure_ascii=False))
raise SystemExit(0 if all(row["passed"] for row in routes)
                 and all(row["status"] == "pass" for row in ratchets) else 1)
