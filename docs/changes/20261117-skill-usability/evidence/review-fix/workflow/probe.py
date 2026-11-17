"""Replay independent-review OTA regressions without overwriting the first T3b evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit._matcher_kernel import (
    _active_phrase_matches, _frontmatter, _implicit_context_matches, _routing_ir, _routing_markers,
)
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


def main() -> None:
    phase = sys.argv[1]
    if phase not in ("red", "green"):
        raise SystemExit("phase must be red or green")
    manifest = Manifest.load(ROOT)
    frontmatter = _frontmatter(ROOT / "skills/adk-production-field-readiness/SKILL.md")
    broad = dict(frontmatter)
    broad["implicit_context"] = [phrase.replace("OTA升级/OTA回滚/OTA验收", "OTA")
                                 for phrase in frontmatter["implicit_context"]]
    markers = _routing_markers(_routing_ir(manifest))
    prompts = (
        "评估嵌入式设备 OTA 的断电恢复、回滚和上线 readiness",
        "请只读检查 OTA 签名和回滚验证证据",
        "Review OTA firmware rollback readiness",
        "帮我设计设备状态机，不涉及量产或OTA",
        "不涉及量产、OTA和RMA；请检查数据库回滚方案",
        "不涉及量产，只读评估 OTA 回滚",
        "文档示例：`OTA`；请检查数据库回滚方案",
    )
    rows = []
    for prompt in prompts:
        rows.append({
            "prompt": prompt,
            "route": match_text(manifest, prompt),
            "candidate_domain_eligible": _implicit_context_matches(frontmatter, prompt, markers),
            "with_bare_ota_domain_eligible": _implicit_context_matches(broad, prompt, markers),
            "global_local_polarity_unchanged": _active_phrase_matches(
                prompt, "量产/OTA/RMA", (*markers, "非", "不涉及", "not", "non-")),
        })
    result = {
        "phase": phase,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output([RTK, "bypass", "git", "rev-parse", "HEAD"],
                                         cwd=ROOT, text=True).strip(),
        "manifest_version": manifest.data.get("version"),
        "frontmatter_context": frontmatter["implicit_context"],
        "rows": rows,
        "boundary": "Source routing and eligibility only; no live runtime or device evidence",
    }
    (OUT / f"{phase}-probes.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
