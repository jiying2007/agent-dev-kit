import unittest
import json
import subprocess
from pathlib import Path
from agent_dev_kit.boundary_rehearsal import mcp_observation, rehearse


class BoundaryRehearsalTests(unittest.TestCase):
    def test_all_declared_fault_cases_and_authority_boundary(self):
        value = rehearse()
        self.assertEqual(value["status"], "pass")
        self.assertEqual(value["passed"], value["total"])
        self.assertGreaterEqual(value["total"], 20)
        self.assertFalse(value["external_effect_performed"])
        self.assertFalse(value["network_called"])
        self.assertFalse(value["release_authorized"])

    def test_stdio_transport_is_bounded_and_stateful_caller_is_checked(self):
        base = dict(server_audience="", token_audience="", principal_id="caller")
        self.assertEqual(mcp_observation("stdio", [], {}, **base)["decision"], "test-observation-valid")
        self.assertEqual(mcp_observation("stdio", ["https://public.test"], {}, **base)["decision"], "deny")
        self.assertEqual(mcp_observation("stdio", [], {}, **base, handle_owner="other")["decision"], "deny")
        self.assertEqual(mcp_observation("unknown", [], {}, **base)["decision"], "deny")

    def test_canonical_cli_from_non_repository_cwd(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(["bash", str(root / "scripts/devkit.sh"), "eval", "boundaries", "--summary-json"],
                                cwd="/tmp", text=True, capture_output=True, check=True, timeout=30)
        value = json.loads(result.stdout)
        self.assertEqual(value["passed"], value["total"])
        self.assertFalse(value["runtime_enabled"])


if __name__ == "__main__":
    unittest.main()
