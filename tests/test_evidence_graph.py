from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_dev_kit.evidence_graph import load_contract, validate_graph
from agent_dev_kit.model import ManifestError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = load_contract(ROOT / "manifests" / "evidence_graph_contracts.json")
AS_OF = datetime(2026, 8, 30, 23, 59, tzinfo=timezone.utc)


def node(evidence_root: Path, node_id: str, node_type: str, layer: str, attributes: dict | None = None) -> dict:
    subject_relative = Path("subjects") / "{}.json".format(node_id)
    subject_path = evidence_root / subject_relative
    subject_path.parent.mkdir(parents=True, exist_ok=True)
    subject_path.write_text(
        json.dumps({"schema_version": "test-subject/v1", "subject_id": node_id}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    subject_digest = hashlib.sha256(subject_path.read_bytes()).hexdigest()
    relative = Path("evidence") / "{}.json".format(node_id)
    path = evidence_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    claim = {
        "schema_version": "adk-evidence-node-claim/v1",
        "node_id": node_id,
        "node_type": node_type,
        "evidence_layer": layer,
        "subject_ref": {
            "ref": "ref:{}".format(subject_digest),
            "path": subject_relative.as_posix(),
            "sha256": subject_digest,
        },
        "generated_at": "2026-08-30T00:00:00Z",
        "raw_content_stored": False,
    }
    path.write_text(json.dumps(claim, sort_keys=True) + "\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "node_id": node_id,
        "node_type": node_type,
        "content_sha256": digest,
        "evidence_ref": {"ref": "ref:{}".format(digest), "path": relative.as_posix(), "sha256": digest},
        "evidence_layer": layer,
        "owner": "agent-dev-kit",
        "verified_at": "2026-08-30T00:00:00Z",
        "expires_at": None,
        "sensitivity": "team-internal",
        "retention": "keep-provenance",
        "attributes": attributes or {},
    }


def graph(evidence_root: Path) -> dict:
    outcome_metrics = {
        "task_success": True,
        "first_pass_success": False,
        "human_interventions": 1,
        "elapsed_ms": 1200,
        "input_tokens": 100,
        "output_tokens": 20,
        "tool_calls": 2,
        "wrong_skill": False,
        "abstained": False,
    }
    nodes = [
        node(evidence_root, "source-1", "source", "source"),
        node(evidence_root, "decision-1", "decision", "source"),
        node(evidence_root, "asset-1", "asset", "source"),
        node(evidence_root, "bundle-1", "bundle", "test"),
        node(evidence_root, "runtime-1", "runtime", "runtime"),
        node(evidence_root, "trace-1", "trace", "runtime"),
        node(evidence_root, "outcome-1", "outcome", "runtime", outcome_metrics),
        node(evidence_root, "release-1", "release", "runtime"),
        node(evidence_root, "rollback-1", "rollback", "runtime"),
    ]
    edges = [
        {"from": "source-1", "to": "decision-1", "relation": "informs"},
        {"from": "decision-1", "to": "asset-1", "relation": "authorizes"},
        {"from": "asset-1", "to": "bundle-1", "relation": "compiled-into"},
        {"from": "bundle-1", "to": "runtime-1", "relation": "loaded-by"},
        {"from": "runtime-1", "to": "trace-1", "relation": "emits"},
        {"from": "trace-1", "to": "outcome-1", "relation": "evaluated-as"},
        {"from": "outcome-1", "to": "release-1", "relation": "supports"},
        {"from": "release-1", "to": "rollback-1", "relation": "rehearsed-with"},
    ]
    return {
        "schema_version": "adk-evidence-graph/v1",
        "graph_id": "release-evidence-graph",
        "graph_kind": "release-evidence",
        "generated_at": "2026-08-30T00:00:00Z",
        "nodes": nodes,
        "edges": edges,
        "raw_content_stored": False,
    }


class EvidenceGraphTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.evidence_root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, value: dict, contract: dict | None = None) -> dict:
        return validate_graph(value, contract or CONTRACT, self.evidence_root, as_of=AS_OF)

    def test_valid_graph_is_hashed_sanitized_and_file_bound(self) -> None:
        result = self.validate(graph(self.evidence_root))
        self.assertEqual("pass", result["status"])
        self.assertEqual(9, result["node_count"])
        self.assertEqual(8, result["edge_count"])
        self.assertEqual(64, len(result["graph_sha256"]))
        self.assertFalse(result["raw_content_stored"])

    def test_graph_structure_sensitive_values_and_raw_content_fail_closed(self) -> None:
        dangling = graph(self.evidence_root)
        dangling["edges"][0]["to"] = "missing"
        with self.assertRaises(ManifestError):
            self.validate(dangling)

        cycle_contract = copy.deepcopy(CONTRACT)
        cycle_contract["allowed_edges"].append({"from": "rollback", "to": "source", "relation": "restarts"})
        cyclic = graph(self.evidence_root)
        cyclic["edges"].append({"from": "rollback-1", "to": "source-1", "relation": "restarts"})
        with self.assertRaises(ManifestError):
            self.validate(cyclic, cycle_contract)

        raw = graph(self.evidence_root)
        raw["raw_content_stored"] = True
        with self.assertRaises(ManifestError):
            self.validate(raw)

        for secret in (
            "ghp_abcdefghijklmnopqrstuv",
            "github_pat_abcdefghijklmnopqrstuv",
            "sk-abcdefghijklmnop",
            "Bearer abcdefghijklmnop",
            "AKIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
            "raw prompt",
            "tool payload",
        ):
            value = graph(self.evidence_root)
            value["nodes"][0]["owner"] = secret
            with self.subTest(secret=secret), self.assertRaises(ManifestError):
                self.validate(value)

    def test_typed_evidence_reference_and_content_hash_are_required(self) -> None:
        missing = graph(self.evidence_root)
        missing["nodes"][0]["evidence_ref"]["path"] = "evidence/missing.json"
        with self.assertRaises(ManifestError):
            self.validate(missing)

        symlinked = graph(self.evidence_root)
        original = self.evidence_root / symlinked["nodes"][0]["evidence_ref"]["path"]
        link = original.with_name("source-link.json")
        link.symlink_to(original)
        symlinked["nodes"][0]["evidence_ref"]["path"] = link.relative_to(self.evidence_root).as_posix()
        with self.assertRaises(ManifestError):
            self.validate(symlinked)

        wrong_file_hash = graph(self.evidence_root)
        wrong_file_hash["nodes"][0]["evidence_ref"]["sha256"] = "0" * 64
        wrong_file_hash["nodes"][0]["content_sha256"] = "0" * 64
        with self.assertRaises(ManifestError):
            self.validate(wrong_file_hash)

        unbound_content_hash = graph(self.evidence_root)
        unbound_content_hash["nodes"][0]["content_sha256"] = "0" * 64
        with self.assertRaises(ManifestError):
            self.validate(unbound_content_hash)

        free_ref = graph(self.evidence_root)
        free_ref["nodes"][0]["evidence_ref"]["ref"] = "tests/raw-log.txt"
        with self.assertRaises(ManifestError):
            self.validate(free_ref)

        mismatched_opaque_ref = graph(self.evidence_root)
        mismatched_opaque_ref["nodes"][0]["evidence_ref"]["ref"] = "ref:" + "f" * 64
        with self.assertRaises(ManifestError):
            self.validate(mismatched_opaque_ref)

        reused_claim = graph(self.evidence_root)
        source_ref = copy.deepcopy(reused_claim["nodes"][0]["evidence_ref"])
        source_digest = reused_claim["nodes"][0]["content_sha256"]
        for item in reused_claim["nodes"][1:]:
            item["evidence_ref"] = copy.deepcopy(source_ref)
            item["content_sha256"] = source_digest
        with self.assertRaisesRegex(ManifestError, "independent typed claim|identity"):
            self.validate(reused_claim)

    def test_timestamp_and_retention_invariants_fail_closed(self) -> None:
        future_graph = graph(self.evidence_root)
        future_graph["generated_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaises(ManifestError):
            self.validate(future_graph)

        future_verified = graph(self.evidence_root)
        future_verified["nodes"][0]["verified_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaises(ManifestError):
            self.validate(future_verified)

        reversed_time = graph(self.evidence_root)
        reversed_time["nodes"][0]["expires_at"] = "2026-08-29T00:00:00Z"
        with self.assertRaises(ManifestError):
            self.validate(reversed_time)

        expire_without_future = graph(self.evidence_root)
        expire_without_future["nodes"][0]["retention"] = "expire"
        with self.assertRaises(ManifestError):
            self.validate(expire_without_future)

        valid_expire = graph(self.evidence_root)
        valid_expire["nodes"][0]["retention"] = "expire"
        valid_expire["nodes"][0]["expires_at"] = "2026-09-30T00:00:00Z"
        self.assertEqual("pass", self.validate(valid_expire)["status"])

        for retention in ("supersede", "retire"):
            value = graph(self.evidence_root)
            value["nodes"][2]["retention"] = retention
            with self.subTest(retention=retention), self.assertRaises(ManifestError):
                self.validate(value)

        valid_retire = graph(self.evidence_root)
        valid_retire["nodes"][2]["retention"] = "retire"
        valid_retire["nodes"].append(node(self.evidence_root, "retirement-1", "retirement", "runtime"))
        valid_retire["edges"].append(
            {"from": "asset-1", "to": "retirement-1", "relation": "retired-by"}
        )
        self.assertEqual("pass", self.validate(valid_retire)["status"])

        valid_supersede = graph(self.evidence_root)
        valid_supersede["nodes"][7]["retention"] = "supersede"
        valid_supersede["nodes"].append(node(self.evidence_root, "retirement-2", "retirement", "runtime"))
        valid_supersede["edges"].append(
            {"from": "release-1", "to": "retirement-2", "relation": "superseded-by"}
        )
        self.assertEqual("pass", self.validate(valid_supersede)["status"])

    def test_outcome_layer_taxonomy_release_path_and_partial_status(self) -> None:
        missing_metric = graph(self.evidence_root)
        missing_metric["nodes"][6]["attributes"].pop("human_interventions")
        with self.assertRaises(ManifestError):
            self.validate(missing_metric)

        wrong_layer = graph(self.evidence_root)
        wrong_layer["nodes"][0]["evidence_layer"] = "field"
        with self.assertRaises(ManifestError):
            self.validate(wrong_layer)

        disconnected = graph(self.evidence_root)
        disconnected["edges"] = []
        with self.assertRaises(ManifestError):
            self.validate(disconnected)

        partial = graph(self.evidence_root)
        partial["graph_kind"] = "partial"
        partial["nodes"] = partial["nodes"][:1]
        partial["edges"] = []
        self.assertEqual("partial", self.validate(partial)["status"])


if __name__ == "__main__":
    unittest.main()
