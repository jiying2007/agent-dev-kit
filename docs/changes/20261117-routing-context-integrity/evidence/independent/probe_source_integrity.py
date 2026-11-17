"""Independent audit inventory, formatter, and same-read cache verification."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit import phase_context, skill_relationships
from agent_dev_kit.model import Manifest, ManifestError

ROOT = Path("/workspace/scratch/d417066aafa8/agent-dev-kit")
BASE = "6d902f721f560f02883516e809fbd93a326405b6"
AUDIT = Path("/workspace/scratch/d417066aafa8/audit-skills/skills-audit.json")


def base_bytes(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def inventory():
    audit = json.loads(AUDIT.read_bytes())
    manifest = json.loads(base_bytes("manifest.json"))
    expected = {row["name"]: row["path"] for section in ("skills", "optional_skills") for row in manifest[section]}
    actual = {row["skill_id"]: row["path"] for row in audit["skills"]}
    checks = []
    references = []
    for row in audit["skills"]:
        for entry in (row, *row["direct_references"]):
            raw = base_bytes(entry["path"])
            checks.append({"path": entry["path"], "matches_baseline": hashlib.sha256(raw).hexdigest() == entry["sha256"],
                           "bytes_match": len(raw) == entry["bytes"]})
        references.extend(entry["path"] for entry in row["direct_references"])
    return {"skill_count": len(actual), "row_count": len(audit["skills"]), "manifest_exact": expected == actual,
            "direct_reference_count": len(references), "unique_direct_reference_count": len(set(references)),
            "conclusions_complete": all(row["decision"] and row["rationale"].strip() for row in audit["skills"]),
            "digests_verified": len(checks), "all_digest_checks_pass": all(x["matches_baseline"] and x["bytes_match"] for x in checks),
            "failed_checks": [x for x in checks if not x["matches_baseline"] or not x["bytes_match"]]}


def formatter():
    old = ast.parse(base_bytes("src/agent_dev_kit/_matcher_kernel.py"))
    new = ast.parse((ROOT / "src/agent_dev_kit/matcher.py").read_bytes())
    old_fn = next(x for x in old.body if isinstance(x, ast.FunctionDef) and x.name == "format_result")
    new_fn = next(x for x in new.body if isinstance(x, ast.FunctionDef) and x.name == "_kernel_format_result")
    old_fn.name = new_fn.name
    return {"formatter_ast_unchanged_except_name": ast.dump(old_fn) == ast.dump(new_fn)}


def same_read(module):
    with tempfile.TemporaryDirectory(prefix="adk-independent-cache-") as directory:
        local = Path(directory)
        source = local / module._CONTRACT
        schema = local / module._CONTRACT_SCHEMA
        source.parent.mkdir(parents=True)
        schema.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((ROOT / module._CONTRACT).read_bytes())
        schema.write_bytes((ROOT / module._CONTRACT_SCHEMA).read_bytes())
        original = source.read_bytes()
        before = source.stat()
        changed = original.replace(b'/v2"', b'/v9"', 1)
        reads = []
        original_read = Path.read_bytes

        def mutate_after_read(path):
            raw = original_read(path)
            if path == source:
                reads.append(hashlib.sha256(raw).hexdigest())
                if len(reads) == 1:
                    source.write_bytes(changed)
                    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
            return raw

        manifest = Manifest(local, {}, local / "manifest.json")
        with patch.object(Path, "read_bytes", mutate_after_read):
            value, digest = module._contract(manifest)
        stale_rejected = False
        try:
            module._contract(manifest)
        except ManifestError:
            stale_rejected = True
        return {"module": module.__name__, "contract_reads": len(reads),
                "parsed_schema": value["schema_version"], "digest_matches_parsed_bytes": digest == hashlib.sha256(original).hexdigest(),
                "disk_changed_after_read": source.read_bytes() == changed,
                "size_and_mtime_preserved": source.stat().st_size == before.st_size and source.stat().st_mtime_ns == before.st_mtime_ns,
                "next_read_rejects_new_invalid_content": stale_rejected}


if __name__ == "__main__":
    print(json.dumps({"observed_at": datetime.now(UTC).isoformat(), "baseline": BASE,
                      "inventory": inventory(), "formatter": formatter(),
                      "cache_same_read": [same_read(phase_context), same_read(skill_relationships)],
                      "fixed_inputs_unchanged": {
                          path: base_bytes(path) == (ROOT / path).read_bytes()
                          for path in ("manifests/profile_context_ratchets.json", "tests/fixtures/software_m5_eval_tasks.jsonl")
                      }}, ensure_ascii=False, indent=2))
