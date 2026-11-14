"""Source-only portfolio and target-boundary regression. No host model is invoked."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/evals/skill-portfolio-audit-20261114.md"
CASES = ROOT / "tests/fixtures/skill_portfolio_quality_cases.json"


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class SkillPortfolioQualityTests(unittest.TestCase):
    def test_65_manifest_skills_have_one_frozen_source_audit_row(self) -> None:
        manifest = json.loads(source("manifest.json"))
        expected = [(e["name"], "core" if i == 0 else "optional", e["category"])
                    for i, section in enumerate(("skills", "optional_skills"))
                    for e in manifest[section]]
        self.assertEqual(len(expected), 65)
        ledger = LEDGER.read_text(encoding="utf-8")
        pattern = (r"^\|\s*\d+\s*\| `([a-z0-9-]+)` \| "
                   r"(core|optional) / ([a-z_]+) \| "
                   r"(改进（候选）|保持本轮不变) \| .+ \| `([a-f0-9]{12})` \|$")
        matches = re.findall(pattern, ledger, re.MULTILINE)
        self.assertEqual(len(matches), 65)
        self.assertEqual([(x[0], x[1], x[2]) for x in matches], expected)
        self.assertEqual(sum(x[3] == "改进（候选）" for x in matches), 11)
        self.assertIn("not-measured", ledger)
        self.assertIn("不是", ledger)

    def test_external_fetch_untrusted_url_and_redirect_denials(self) -> None:
        s = source("optional-skills/adk-data-fetch/adk-fetch-url-content/SKILL.md")
        for marker in ("SSRF", "DNS rebinding", "loopback", "private", "link-local",
                       "重定向", "HTTP(S)", "robots.txt", "最大响应字节",
                       "不可信数据", "Cookie", "认证头"):
            # "Cookie" uses case-sensitive example only where present.
            self.assertIn(marker.lower(), s.lower())
        parent = source("optional-skills/adk-data-fetch/SKILL.md")
        self.assertIn("已安装", parent)
        self.assertIn("权限", parent)
        self.assertIn("凭证", parent)

    def test_imap_read_does_not_imply_mailbox_mutation(self) -> None:
        s = source("optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md")
        for marker in ("EXAMINE", "BODY.PEEK", "UID", "STORE/COPY/MOVE/EXPUNGE",
                       "not-verified", "只读", "凭证", "认证失败"):
            self.assertIn(marker, s)

    def test_supply_chain_has_readonly_and_install_boundaries(self) -> None:
        s = source("optional-skills/adk-security-supply-chain/SKILL.md")
        for marker in ("source-only intake", "adoption preflight",
                       "install / runtime readiness", "SBOM", "CVE",
                       "not-scanned / reason / owner", "needs-fix"):
            self.assertIn(marker, s)

    def test_embedded_tool_and_fake_register_example_gates(self) -> None:
        protocol = source("skills/adk-protocol-stack-integration/SKILL.md")
        unit = source("skills/adk-unit-test-embedded/SKILL.md")
        regs = source("skills/adk-register-map-design/SKILL.md")
        perf = source("skills/adk-performance-profiling-embedded/SKILL.md")
        cmake = source("skills/adk-cmake-cross-build/SKILL.md")
        self.assertIn("tcpdump", protocol)
        self.assertIn("not-tested", protocol)
        self.assertIn("权限", protocol)
        for marker in ("needs-hil", "host-unit", "compile-only", "SIL", "HIL", "mock"):
            self.assertIn(marker, unit)
        for marker in ("EXAMPLE_PERIPHERAL", "base_address: null",
                       "reset_value: null", "datasheet/errata"):
            self.assertIn(marker, regs)
        self.assertNotIn("base_address: 0x40020000", regs)
        for marker in ("linux-embedded", "mcu-rtos", "mcu-baremetal", "not-measured"):
            self.assertIn(marker, perf)
        self.assertIn("--parallel <resource-budget>", cmake)
        self.assertIn("只清理任务自有构建目录", cmake)

    def test_composition_light_mode_does_not_downgrade_risk(self) -> None:
        skill = source("optional-skills/adk-skill-composition-governance/SKILL.md")
        self.assertIn("collision-only", skill)
        self.assertIn("composition-change", skill)
        self.assertIn("near-miss", skill)
        self.assertIn("权限", skill)
        flaky = source("optional-skills/adk-test-flakiness-triage/SKILL.md")
        self.assertIn("quarantine", flaky)
        self.assertIn("owner", flaky)
        self.assertIn("不能把被隔离测试计为 PASS", flaky)

    def test_scenarios_are_unmeasured_hypotheses(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "adk-skill-portfolio-method-cases/v1")
        self.assertEqual(data["behavior_status"], "not-measured")
        self.assertGreaterEqual(len(data["cases"]), 12)
        ids = [x["id"] for x in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in data["cases"]:
            for key in ("id", "input", "expected", "forbidden"):
                self.assertTrue(item[key].strip(), (item["id"], key))


if __name__ == "__main__":
    unittest.main()
