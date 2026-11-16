"""Source-template invariants and timestamp design cases, not model evaluation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / (
    "optional-skills/adk-skill-composition-governance/references/adk-skill-lifecycle.md"
)
INCIDENT = ROOT / "optional-skills/adk-incident-rca-report/SKILL.md"


class OptionalTemplateInvariantTests(unittest.TestCase):
    def test_blank_creation_gate_cannot_predeclare_success(self) -> None:
        section = LIFECYCLE.read_text(encoding="utf-8").split(
            "## Creation Gate\n", 1
        )[1].split("\n## ", 1)[0]
        rows = [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in section.splitlines()
            if line.startswith("| ")
        ]
        self.assertEqual(rows[0], ["Gate", "Decision", "Evidence"])
        data = [row for row in rows[1:] if row[0] != "---"]
        self.assertTrue(data, "the creation checklist must not disappear")
        self.assertEqual(len({row[0] for row in data}), len(data))
        for gate, decision, evidence in data:
            with self.subTest(gate=gate):
                self.assertTrue(decision, "unknown work needs an explicit state")
                if not evidence:
                    self.assertNotIn(
                        decision.casefold(), {"pass", "passed", "accepted", "ready"},
                        "a blank template is not an observed successful review",
                    )

    def test_incident_output_preserves_distinct_clock_fields(self) -> None:
        section = INCIDENT.read_text(encoding="utf-8").split(
            "## Report\n", 1
        )[1].split("\n## ", 1)[0]
        template = re.search(r"```md\n(.*?)\n```", section, re.DOTALL)
        self.assertIsNotNone(template)
        fields = set(re.findall(r"[a-z]+(?:_[a-z]+)+", template.group(1)))
        self.assertTrue(
            {"event_time", "observed_time", "clock_uncertainty"} <= fields,
            "the output template must not collapse event and collection clocks",
        )
        self.assertIn("timezone", template.group(1))
        self.assertIn("evidence", template.group(1).lower())


class IncidentTimelineDesignCaseTests(unittest.TestCase):
    """Executable arithmetic for authored cases; no Skill/host success claim."""

    def test_late_observation_reverses_event_order_across_timezones(self) -> None:
        records = [
            {
                "id": "fault", "event_time": "2026-11-16T12:00:10+08:00",
                "observed_time": "2026-11-16T04:01:30+00:00",
            },
            {
                "id": "deployment", "event_time": "2026-11-16T04:00:40+00:00",
                "observed_time": "2026-11-16T04:00:41+00:00",
            },
        ]
        event_order = sorted(records, key=lambda row: datetime.fromisoformat(row["event_time"]))
        observed_order = sorted(
            records, key=lambda row: datetime.fromisoformat(row["observed_time"])
        )
        self.assertEqual([row["id"] for row in event_order], ["fault", "deployment"])
        self.assertEqual([row["id"] for row in observed_order], ["deployment", "fault"])
        fault = datetime.fromisoformat(records[0]["event_time"]).astimezone(timezone.utc)
        deployed = datetime.fromisoformat(records[1]["event_time"])
        self.assertEqual((deployed - fault).total_seconds(), 30)

    def test_clock_uncertainty_cannot_be_erased_by_timezone_conversion(self) -> None:
        fault = datetime.fromisoformat("2026-11-16T12:00:10+08:00")
        deployed = datetime.fromisoformat("2026-11-16T04:00:40+00:00")
        uncertainty = timedelta(seconds=45)
        self.assertLess(fault - uncertainty, deployed)
        self.assertGreater(fault + uncertainty, deployed)
        # The authored case admits both orders; UTC conversion alone cannot select one.


if __name__ == "__main__":
    unittest.main()
