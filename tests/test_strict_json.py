from __future__ import annotations

import tempfile
import unittest
import json
import os
import stat
import io
import tarfile
from unittest import mock
from pathlib import Path

from agent_dev_kit.strict_json import StrictJSONError, loads, read
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.campaign_model import _load_json_object
from agent_dev_kit.effect_campaign_materializer import _load_effect_plan
from agent_dev_kit.agent_value_contracts import _load_json as load_value_contract
from agent_dev_kit.agent_value_trust import _json_object as load_trust_registry
from agent_dev_kit.native_campaign_contract import _load_json as load_native_campaign
from agent_dev_kit.evaluation_runtime import load_tasks, _load_effect_inputs
from agent_dev_kit.target_contracts import (_json_object as load_target_object,
                                          load_target_contract, _validate_native_conformance_evidence)
from agent_dev_kit.distribution import promotion_evidence
from agent_dev_kit.distribution.release_contract import _canonical_manifest_sha256, validate_release_artifact
from release_archive_fixture import release_fixture


class StrictJSONTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX symlink")
    def test_real_target_loader_rejects_in_root_leaf_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifests").mkdir()
            (root / "manifests" / "target-contract.schema.json").write_text("{}")
            regular = root / "regular.json"
            regular.write_text("{}")
            link = root / "contract.json"
            link.symlink_to(regular)
            manifest = mock.Mock(root=root)
            manifest.target.return_value = {"contract": "contract.json"}
            with self.assertRaisesRegex(ManifestError, "must not be a symlink"):
                load_target_contract(manifest, "probe")

    def test_native_receipt_is_bounded_before_digest_or_trust(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "schemas").mkdir()
            (root / "schemas" / "native-target-conformance-receipt-v2.schema.json").write_text("{}")
            path = root / "receipt.json"
            path.write_bytes(b" " * (4 * 1024 * 1024) + b"{}")
            adapter = {"conformance": {"level": "runtime", "runtime_version": "test",
                       "evidence": [{"target": "probe", "runtime_version": "test",
                                     "path": "receipt.json", "sha256": "0" * 64}]},
                       "conformance_trust_policy": {"enabled": True,
                          "trusted_authorities": ["test"], "verification_backend": "test"}}
            trust = mock.Mock()
            with mock.patch("agent_dev_kit.target_contracts._native_contract_digest", return_value="0" * 64), \
                 mock.patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read")):
                with self.assertRaisesRegex(ManifestError, "invalid JSON"):
                    _validate_native_conformance_evidence(mock.Mock(root=root), "probe", adapter, {}, trust)
            trust.assert_not_called()

    def test_real_archive_reader_rejects_duplicate_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "agent-dev-kit-7.0.0.tar.gz"
            release, members = release_fixture()
            source = dict(members)["manifest.json"]
            release_raw = json.dumps(release).encode()
            cases = ((source, release_raw, True),
                     (b'{"version":"invalid","version":"7.0.0"}', release_raw, False),
                     (source, b'{"release_eligible":true,' + release_raw[1:], False),
                     (source, b'{"extra":NaN,' + release_raw[1:], False))
            for source_raw, raw, valid in cases:
                with tarfile.open(artifact, "w:gz") as archive:
                    for name, payload in members + [("release-manifest.json", raw)]:
                        if name in ("manifest.json", "source/manifest.json"):
                            payload = source_raw
                        info = tarfile.TarInfo(name)
                        info.size = len(payload)
                        archive.addfile(info, io.BytesIO(payload))
                if valid:
                    self.assertEqual("pass", validate_release_artifact(artifact)["status"])
                else:
                    with self.subTest(raw=raw, source=source_raw), self.assertRaises(ValueError):
                        validate_release_artifact(artifact)

    def test_target_and_promotion_consumers_reject_ambiguous_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.json"
            for raw in ('{"status":"fail","status":"pass"}',
                        '{"status":"fail","\\u0073tatus":"pass"}',
                        '{"nested":{"x":1,"x":2}}', '{"x":NaN}',
                        '{"x":1e999}', "[" * 65 + "0" + "]" * 65,
                        "[]", b"\xff"):
                path.write_bytes(raw.encode() if isinstance(raw, str) else raw)
                with self.subTest(raw=raw), self.assertRaises(ManifestError):
                    load_target_object(path, "target receipt")
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    promotion_evidence._load_release_contract(path)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    _canonical_manifest_sha256(path.read_bytes())

    def test_harness_mcp_config_rejects_duplicate_keys_and_nonfinite_numbers(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools

        canonical = Path(__file__).resolve().parents[1] / "manifests/harness_readiness_contracts.json"
        contract = load_readiness_contract(canonical)
        ambiguous = (
            '{"mcpServers":{"danger":{"headers":{"token":"test-literal"}}},'
            '"mcpServers":{"clean":{"command":"npx","args":["safe-package@1.2.3"]}}}',
            '{"mcpServers":{"clean":{"command":"npx","command":"node"}}}',
            '{"mcpServers":{"clean":{"args":[NaN]}}}',
            '{"mcpServers":{"clean":{"args":[1e999]}}}',
            '{"mcpServers":{"clean":{"args":["\\uD800"]}}}',
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / ".mcp.json"
            for raw in ambiguous:
                with self.subTest(raw=raw[:75]):
                    source.write_text(raw, encoding="utf-8")
                    index = RepositoryIndex(root, contract)
                    status, _evidence, blockers = _evaluate_tools(index, contract)
                    self.assertEqual("needs-review", status)
                    self.assertIn("invalid_mcp_json", {b["code"] for b in blockers})
                    self.assertNotIn("test-literal", str(blockers))
            source.write_text(
                '{"mcpServers":{"clean":{"command":"npx","args":["safe-package@1.2.3"]}}}',
                encoding="utf-8",
            )
            status, _evidence, blockers = _evaluate_tools(RepositoryIndex(root, contract), contract)
            self.assertEqual("partial", status)
            self.assertNotIn("invalid_mcp_json", {b["code"] for b in blockers})

    def test_harness_mcp_cli_credentials_and_opaque_report_refs(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools

        root_dir = Path(__file__).resolve().parents[1]
        contract = load_readiness_contract(root_dir / "manifests/harness_readiness_contracts.json")
        metadata = {"dimensions": {"tool_and_permission_boundary": {
            "permission_boundary": {"read_only": True, "approval_required": True,
                                    "credential_source": "environment-variable"}}}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/security.md").write_text(
                "read-only approval credential environment variable", encoding="utf-8"
            )
            config = root / ".mcp.json"

            def evaluate(name, server):
                config.write_text(json.dumps({"mcpServers": {name: server}}), encoding="utf-8")
                return _evaluate_tools(RepositoryIndex(root, contract), contract, metadata)

            status, _refs, blockers = evaluate(
                "demo", {"command": "npx", "args": ["safe-package@1.2.3"]}
            )
            self.assertEqual("pass", status, blockers)
            bad = (
                ["safe-package@1.2.3", "--token=demo_value"],
                ["safe-package@1.2.3", "--api-key", "demo_value"],
                ["safe-package@1.2.3", "--header=Authorization: Bearer demo_value"],
                ["safe-package@1.2.3", "TOKEN=demo_value"],
                ["safe-package@1.2.3", "--env=TOKEN=demo_value"],
                ["safe-package@1.2.3", "node script --api-key demo_value"],
                ["safe-package@1.2.3", "-H", "Authorization: Bearer demo_value"],
            )
            for args in bad:
                with self.subTest(bad=args):
                    status, _refs, blockers = evaluate(
                        "sk-demo_marker", {"command": "npx", "args": args}
                    )
                    self.assertEqual("blocked", status)
                    self.assertIn("hardcoded_mcp_secret", {b["code"] for b in blockers})
                    self.assertNotIn("demo_value", str(blockers))
                    self.assertNotIn("sk-demo_marker", str(blockers))
                    self.assertTrue(any(
                        "#mcpServers[0].args[" in b["evidence_ref"]
                        for b in blockers if b["code"] == "hardcoded_mcp_secret"
                    ))
            ref = "$" + "{DEMO_TOKEN}"
            for args in (
                ["safe-package@1.2.3", "--token=" + ref],
                ["safe-package@1.2.3", "--token", ref],
                ["safe-package@1.2.3", "--header=Authorization: Bearer " + ref],
            ):
                with self.subTest(safe=args):
                    status, _refs, blockers = evaluate(
                        "demo", {"command": "npx", "args": args}
                    )
                    self.assertEqual("pass", status, blockers)
            for args in (["safe-package@1.2.3", "--token"],
                         ["safe-package@1.2.3", "--token", "--other"],
                         ["safe-package@1.2.3", 42]):
                with self.subTest(invalid=args):
                    status, _refs, blockers = evaluate("demo", {"command": "npx", "args": args})
                    self.assertEqual("needs-review", status, blockers)
                    self.assertIn("invalid_mcp_command_args", {b["code"] for b in blockers})
            for server in (
                {"command": "npx", "args": ["unpinned-package"]},
                {"command": "npx", "args": ["safe-package@1.2.3"],
                 "headers": {"private-token-demo_value": "demo_value"}},
            ):
                with self.subTest(redaction=server):
                    status, _refs, blockers = evaluate("sk-demo_marker", server)
                    self.assertIn(status, ("blocked", "needs-review"))
                    self.assertNotIn("sk-demo_marker", str(blockers))
                    self.assertNotIn("demo_value", str(blockers))
                    self.assertTrue(any("mcpServers[0]" in b["evidence_ref"] for b in blockers))

    def test_harness_mcp_sensitive_aliases_and_header_value_semantics(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools, _sensitive_key

        root_dir = Path(__file__).resolve().parents[1]
        contract = load_readiness_contract(root_dir / "manifests/harness_readiness_contracts.json")
        fragments = contract["mcp"]["sensitive_key_fragments"]
        for key in ("private-token-demo_value", "apiKey", "prefix_API_KEY_suffix",
                    "accessToken", "x-auth", "myCredentialValue"):
            self.assertTrue(_sensitive_key(key, fragments), key)
        for key in ("tokenizer", "command", "name", "mcpServers"):
            self.assertFalse(_sensitive_key(key, fragments), key)

        metadata = {"dimensions": {"tool_and_permission_boundary": {
            "permission_boundary": {"read_only": True, "approval_required": True,
                                    "credential_source": "environment-variable"}}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs/security.md").write_text(
                "read-only approval credential environment variable", encoding="utf-8"
            )
            config = root / ".mcp.json"

            def inspect(server):
                config.write_text(json.dumps({"mcpServers": {"sk-test_opaque": server}}),
                                  encoding="utf-8")
                return _evaluate_tools(RepositoryIndex(root, contract), contract, metadata)

            for headers in (
                {"private-token-demo_value": "demo_value"},
                {"prefix_api_key_suffix": "demo_value"},
                {"X-Auth": "Bearer demo_value"},
                {"X-Custom": "Bearer demo_value"},
                {"X-Custom": "Basic demo_value"},
            ):
                with self.subTest(headers=headers):
                    status, _refs, blockers = inspect(
                        {"command": "npx", "args": ["safe-package@1.2.3"], "headers": headers}
                    )
                    self.assertEqual("blocked", status, blockers)
                    self.assertIn("hardcoded_mcp_secret", {b["code"] for b in blockers})
                    self.assertNotIn("demo_value", str(blockers))
                    self.assertNotIn("sk-test_opaque", str(blockers))

            ref = "$" + "{DEMO_TOKEN}"
            for headers in (
                {"X-Auth": "Bearer " + ref},
                {"X-Auth": "Basic " + ref},
                {"private-token-demo_value": ref},
            ):
                with self.subTest(safe=headers):
                    status, _refs, blockers = inspect(
                        {"command": "npx", "args": ["safe-package@1.2.3"], "headers": headers}
                    )
                    self.assertEqual("pass", status, blockers)

            for arg in ("-token demo_value", "--token demo_value",
                        "--header=Authorization: Basic demo_value"):
                with self.subTest(arg=arg):
                    status, _refs, blockers = inspect(
                        {"command": "npx", "args": ["safe-package@1.2.3", arg]}
                    )
                    self.assertEqual("blocked", status, blockers)
                    self.assertNotIn("demo_value", str(blockers))

            for arg in ("--token=", "-token=", "--api-key:"):
                with self.subTest(missing=arg):
                    status, _refs, blockers = inspect(
                        {"command": "npx", "args": ["safe-package@1.2.3", arg]}
                    )
                    self.assertEqual("needs-review", status, blockers)
                    self.assertIn("invalid_mcp_command_args",
                                  {b["code"] for b in blockers})

    def test_harness_mcp_http_urls_and_indirect_env_credentials(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools
        policy = load_readiness_contract(
            Path(__file__).resolve().parents[1] / "manifests/harness_readiness_contracts.json"
        )
        metadata = {"dimensions": {"tool_and_permission_boundary": {
            "permission_boundary": {"read_only": True, "approval_required": True,
                                    "credential_source": "environment-variable"}}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs/security.md").write_text(
                "MCP read-only approval credential environment variable", encoding="utf-8"
            )
            config = root / "mcp.json"

            def check(server):
                config.write_text(json.dumps({"mcpServers": {"sk-opaque_name": server}}),
                                  encoding="utf-8")
                return _evaluate_tools(RepositoryIndex(root, policy), policy, metadata)

            for url in (
                "https://example.test/mcp?access_token=demo_value",
                "https://example.test/mcp?Authorization=Bearer%20demo_value",
                "https://user:demo_value@example.test/mcp",
                "https://example.test/mcp?APP_OPTIONS=TOKEN%3Ddemo_value",
            ):
                with self.subTest(url=url):
                    status, _evidence, blockers = check({"type": "http", "url": url})
                    self.assertEqual("blocked", status, blockers)
                    self.assertIn("hardcoded_mcp_secret", {b["code"] for b in blockers})
                    self.assertNotIn("demo_value", str(blockers))
                    self.assertNotIn("sk-opaque_name", str(blockers))

            ref = "$" + "{DEMO_TOKEN}"
            for url in ("https://example.test/mcp",
                        "https://example.test/mcp?access_token=" + ref):
                with self.subTest(safe_url=url):
                    status, _evidence, blockers = check({"type": "http", "url": url})
                    self.assertEqual("pass", status, blockers)

            for value in ("TOKEN=demo_value", "Authorization: Bearer demo_value"):
                with self.subTest(env_value=value):
                    server = {"command": "npx", "args": ["safe-package@1.2.3"],
                              "env": {"APP_OPTIONS": value}}
                    status, _evidence, blockers = check(server)
                    self.assertEqual("blocked", status, blockers)
                    self.assertNotIn("demo_value", str(blockers))

            for value in ("TOKEN=" + ref, "Authorization: Bearer " + ref):
                with self.subTest(safe_env=value):
                    status, _evidence, blockers = check(
                        {"command": "npx", "args": ["safe-package@1.2.3"],
                         "env": {"APP_OPTIONS": value}}
                    )
                    self.assertEqual("pass", status, blockers)

            for server in (
                {"command": ["npx", "--token=demo_value"],
                 "args": ["safe-package@1.2.3"]},
                {"command": "npx", "args": ["safe-package@1.2.3"],
                 "env": {"APP_OPTIONS": ["TOKEN=demo_value"]}},
                {"command": "npx", "args": ["safe-package@1.2.3"],
                 "headers": {"X-Other": ["Bearer demo_value"]}},
                {"type": "http", "url": ["https://example.test/mcp"]},
                {"type": "http", "url": "not a URL"},
            ):
                with self.subTest(invalid=server):
                    status, _evidence, blockers = check(server)
                    self.assertEqual("needs-review", status, blockers)
                    self.assertTrue(
                        {"invalid_mcp_command", "invalid_mcp_security_fields",
                         "invalid_mcp_url"} & {b["code"] for b in blockers}
                    )
                    self.assertNotIn("demo_value", str(blockers))

    def test_harness_mcp_url_userinfo_ports_and_unsafe_config_index(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools

        contract = load_readiness_contract(
            Path(__file__).resolve().parents[1] / "manifests/harness_readiness_contracts.json"
        )
        metadata = {"dimensions": {"tool_and_permission_boundary": {
            "permission_boundary": {"read_only": True, "approval_required": True,
                                    "credential_source": "environment-variable"}}}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs/security.md").write_text(
                "MCP read-only approval credential environment variable", encoding="utf-8"
            )
            config = root / ".mcp.json"

            def evaluate(value):
                config.write_text(json.dumps({"mcpServers": {"demo": value}}),
                                  encoding="utf-8")
                return _evaluate_tools(RepositoryIndex(root, contract), contract, metadata)

            for url in (
                "https://token%3Ddemo_value:%24%7BDEMO_PWD%7D@example.test/mcp",
                "https://user:demo_value@example.test/mcp",
                "https://%24%7BDEMO_USER%7D:demo_value@example.test/mcp",
                "https://token%3Ddemo_value:demo_value@example.test/mcp",
            ):
                with self.subTest(credential=url):
                    status, _evidence, blockers = evaluate({"type": "http", "url": url})
                    self.assertNotEqual("pass", status, blockers)
                    self.assertNotIn("demo_value", str(blockers))
            for url in (
                "https://example.test:badport/mcp",
                "https://example.test:99999/mcp",
                "https://example.test:0/mcp",
                "file:///tmp/mcp",
                "https://user@example.test/mcp",
                "https://user:%24%7BDEMO_PWD%7D@example.test/mcp",
            ):
                with self.subTest(malformed=url):
                    status, _evidence, blockers = evaluate({"type": "http", "url": url})
                    self.assertEqual("needs-review", status, blockers)
                    self.assertIn("invalid_mcp_url", {b["code"] for b in blockers})
            safe = "https://%24%7BDEMO_USER%7D:%24%7BDEMO_PWD%7D@example.test/mcp"
            status, _evidence, blockers = evaluate({"type": "http", "url": safe})
            self.assertEqual("pass", status, blockers)

            # Unsafe declarations may not silently disappear and cause N/A.
            config.unlink()
            regular = root / "receipt.json"
            regular.write_text('{"mcpServers": {}}', encoding="utf-8")
            config.symlink_to(regular)
            index = RepositoryIndex(root, contract)
            self.assertIn(".mcp.json", index.unsafe_mcp_configs)
            status, _evidence, blockers = _evaluate_tools(index, contract, metadata)
            self.assertEqual("needs-review", status, blockers)
            self.assertIn("unsafe_mcp_config", {b["code"] for b in blockers})
            config.unlink()

            if hasattr(os, "mkfifo"):
                os.mkfifo(config)
                index = RepositoryIndex(root, contract)
                status, _evidence, blockers = _evaluate_tools(index, contract, metadata)
                self.assertEqual("needs-review", status, blockers)
                self.assertIn("unsafe_mcp_config", {b["code"] for b in blockers})
                config.unlink()
            config.mkdir()
            index = RepositoryIndex(root, contract)
            status, _evidence, blockers = _evaluate_tools(index, contract, metadata)
            self.assertEqual("needs-review", status, blockers)
            self.assertIn("unsafe_mcp_config", {b["code"] for b in blockers})

    def test_harness_rejects_ambiguous_url_authorities_and_empty_credentials(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract
        from agent_dev_kit.readiness_tools import _evaluate_tools

        contract = load_readiness_contract(
            Path(__file__).resolve().parents[1] / "manifests/harness_readiness_contracts.json"
        )
        metadata = {"dimensions": {"tool_and_permission_boundary": {
            "permission_boundary": {"read_only": True, "approval_required": True,
                                    "credential_source": "environment-variable"}}}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "security.md").write_text(
                "MCP read-only approval credential environment variable",
                encoding="utf-8",
            )
            config = root / "mcp.json"

            def evaluate(url):
                config.write_text(json.dumps({"mcpServers": {"demo": {
                    "type": "http", "url": url}}}), encoding="utf-8")
                return _evaluate_tools(RepositoryIndex(root, contract), contract, metadata)

            for url in (
                r"https://example.test\foo/mcp",
                "https://example.test%5cfoo/mcp",
                "https://example.test%2ffoo/mcp",
                "https://example.test/mcp?access_token=",
                "https://example.test/mcp?access_token",
                "https://example.test/mcp?Authorization=",
                "https://example.test/mcp#access_token=",
                "https://%24%7BDEMO_USER%7D:@example.test/mcp",
                "https://:%24%7BDEMO_PWD%7D@example.test/mcp",
                "https://example.test/mcp?access_token=%ZZ",
            ):
                with self.subTest(malformed=url):
                    status, _evidence, blockers = evaluate(url)
                    self.assertEqual("needs-review", status, blockers)
                    self.assertIn("invalid_mcp_url", {b["code"] for b in blockers})
                    self.assertNotIn("access_token=", str(blockers))

            managed = "$" + "{DEMO_TOKEN}"
            for url in (
                "https://example.test/mcp",
                "https://example.test/mcp?access_token=" + managed,
                "https://example.test/mcp#access_token=" + managed,
                "https://%24%7BDEMO_USER%7D:%24%7BDEMO_PWD%7D@example.test/mcp",
            ):
                with self.subTest(valid=url):
                    status, _evidence, blockers = evaluate(url)
                    self.assertEqual("pass", status, blockers)

    def test_harness_index_reads_one_bounded_regular_descriptor(self):
        from agent_dev_kit.readiness_evidence import RepositoryIndex, load_readiness_contract

        canonical = Path(__file__).resolve().parents[1] / "manifests/harness_readiness_contracts.json"
        contract = load_readiness_contract(canonical)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / "work"
            directory.mkdir()
            source = directory / "notes.md"
            source.write_text("safe\n", encoding="utf-8")
            index = RepositoryIndex(root, contract)
            # Reject a separate read_text() call, which is not descriptor-bound.
            with mock.patch.object(Path, "read_text", side_effect=AssertionError("unbounded text read")):
                self.assertEqual("safe\n", index.read_text("work/notes.md"))

            over = root / "large.md"
            over.write_text("ok", encoding="utf-8")
            index = RepositoryIndex(root, contract)
            over.write_bytes(b"x" * (index.max_file_bytes + 1))
            self.assertIsNone(index.read_text("large.md"))

            replaced = root / "replaced.md"
            replaced.write_text("initial\n", encoding="utf-8")
            index = RepositoryIndex(root, contract)
            if hasattr(os, "mkfifo"):
                replaced.unlink()
                os.mkfifo(replaced)
                self.assertIsNone(index.read_text("replaced.md"))

            aliased_dir = root / "symlinked"
            aliased_dir.mkdir()
            nested = aliased_dir / "owned.json"
            nested.write_text("safe", encoding="utf-8")
            index = RepositoryIndex(root, contract)
            original = root / "real"
            aliased_dir.rename(original)
            aliased_dir.symlink_to(original, target_is_directory=True)
            self.assertIsNone(index.read_text("symlinked/owned.json"))

    def test_harness_contract_loader_rejects_ambiguous_unbounded_and_alias_inputs(self):
        from agent_dev_kit.readiness_evidence import (
            ReadinessContractError, load_readiness_contract,
        )
        root = Path(__file__).resolve().parents[1]
        canonical = root / "manifests" / "harness_readiness_contracts.json"
        self.assertEqual("1.0.0", load_readiness_contract(canonical)["schema_version"])
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            path = workspace / "contract.json"
            for raw in (
                b'{"schema_version":"1.0.0","schema_version":"2.0.0"}',
                b'{"verification":{"max_age_days":30,"max_age_days":0}}',
                b'{"review":NaN}',
                b'{"review":1e999}',
                b'{"review":"\\ud800"}',
                b'{"review":0}' + b" " * (256 * 1024),
            ):
                with self.subTest(raw=raw[:70]):
                    path.write_bytes(raw)
                    with self.assertRaises(ReadinessContractError):
                        load_readiness_contract(path)
            path.write_bytes(canonical.read_bytes())
            self.assertEqual("1.0.0", load_readiness_contract(path)["schema_version"])
            if os.name == "posix":
                leaf = workspace / "leaf.json"
                leaf.symlink_to(path)
                parent = workspace / "aliased-dir"
                parent.symlink_to(workspace, target_is_directory=True)
                for unsafe in (leaf, parent / path.name):
                    with self.subTest(unsafe=unsafe.name), self.assertRaisesRegex(
                        ReadinessContractError, "symlink"
                    ):
                        load_readiness_contract(unsafe)
                if hasattr(os, "mkfifo"):
                    fifo = workspace / "input.fifo"
                    os.mkfifo(fifo)
                    with self.assertRaises(ReadinessContractError):
                        load_readiness_contract(fifo)

    def test_target_and_promotion_file_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.json"
            path.write_bytes(b" " * (4 * 1024 * 1024) + b"{}")
            with self.assertRaises(ManifestError):
                load_target_object(path, "target receipt")
            with self.assertRaisesRegex(StrictJSONError, "byte budget"):
                promotion_evidence._load_release_contract(path)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW") and hasattr(os, "mkfifo"), "POSIX file boundaries")
    def test_target_and_promotion_reject_links_and_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            regular = root / "regular.json"
            regular.write_text('{"schema":"adk-release-artifact-contract-set/v1",'
                               '"artifacts":[{"status":"pass"}]}')
            link = root / "link.json"
            link.symlink_to(regular)
            fifo = root / "fifo.json"
            os.mkfifo(fifo)
            for path in (link, fifo):
                with self.subTest(path=path), self.assertRaises(ManifestError):
                    load_target_object(path, "target receipt")
                with self.subTest(path=path), self.assertRaises(StrictJSONError):
                    promotion_evidence._load_release_contract(path)
                self.assertEqual(1, promotion_evidence._main(["validate", str(path)]))

    def test_promotion_validation_rejects_duplicate_claim_before_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.json"
            path.write_text('{"ci":{"static_security":"failure","static_security":"success"}}')
            with mock.patch.object(promotion_evidence, "validate_promotion_evidence") as validator:
                self.assertEqual(1, promotion_evidence._main(["validate", str(path)]))
                validator.assert_not_called()

    def test_promotion_publication_preserves_sorted_bytes_and_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "evidence.json"
            evidence = {"z": 1, "a": {"valid": True}}
            args = ["generate", "--release-contract", str(root / "contract.json"),
                    "--out", str(output), "--contract-result", "success",
                    "--regression-result", "success", "--static-security-result", "success",
                    "--deterministic-result", "success"]
            with mock.patch.object(promotion_evidence, "build_promotion_evidence", return_value=evidence):
                self.assertEqual(0, promotion_evidence._main(args))
                expected = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode()
                self.assertEqual(expected, output.read_bytes())
                self.assertEqual(evidence, read(output, regular_only=True))
                if os.name == "posix":
                    self.assertEqual(0o644, stat.S_IMODE(output.stat().st_mode))
                with mock.patch.object(promotion_evidence, "write_text_atomic", side_effect=OSError("probe")):
                    self.assertEqual(1, promotion_evidence._main(args))
                self.assertEqual(expected, output.read_bytes())
            self.assertEqual([output], list(root.iterdir()))

    @unittest.skipUnless(os.name == "posix", "POSIX symlink")
    def test_promotion_publication_rejects_output_link_without_touching_referent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sentinel = root / "sentinel"
            sentinel.write_bytes(b"SENTINEL")
            link = root / "evidence.json"
            link.symlink_to(sentinel)
            args = ["generate", "--release-contract", str(root / "contract.json"),
                    "--out", str(link), "--contract-result", "success",
                    "--regression-result", "success", "--static-security-result", "success",
                    "--deterministic-result", "success"]
            with mock.patch.object(promotion_evidence, "build_promotion_evidence", return_value={"valid": True}):
                self.assertEqual(1, promotion_evidence._main(args))
            self.assertTrue(link.is_symlink())
            self.assertEqual(b"SENTINEL", sentinel.read_bytes())

    def test_legal_json_and_string_brackets(self):
        self.assertEqual({"name": "[\\\"]", "x": [1, 2.5]}, loads('{"name":"[\\\\\\\"]","x":[1,2.5]}'))
        self.assertEqual([1, True, None], loads(b"[1,true,null]"))

    def test_unicode_scalar_values_reject_lone_surrogates(self):
        for raw in (
            r'"\ud800"', r'"\udc00"', r'"\ud800\ud800"',
            r'{"\ud800":1}', r'{"nested":[{"value":"\udc00"}]}',
            r'{"x":"\ud83dX"}',
        ):
            for source in (raw, raw.encode("ascii")):
                with self.subTest(source=raw), self.assertRaisesRegex(
                    StrictJSONError, "invalid Unicode scalar"
                ):
                    loads(source)
        self.assertEqual(
            {"😀": ["😀", "中文"]},
            loads(r'{"\ud83d\ude00":["\ud83d\ude00","中文"]}'),
        )
        self.assertEqual(
            {"literal": r"\uD800"},
            loads(r'{"literal":"\\uD800"}'),
        )
        with mock.patch(
            "agent_dev_kit.strict_json._scalar_guard",
            side_effect=AssertionError("ordinary JSON should not need Unicode tree scan"),
        ):
            self.assertEqual({"name": "中文"}, loads('{"name":"中文"}'))

    def test_ambiguity_nonfinite_and_budgets(self):
        for raw in ('{"x":1,"x":2}', '{"x":1,"\\u0078":2}',
                    '{"a":{"x":1,"x":2}}', 'NaN', 'Infinity', '-Infinity', '1e999'):
            with self.subTest(raw=raw), self.assertRaises(StrictJSONError):
                loads(raw)
        with self.assertRaisesRegex(StrictJSONError, "byte budget"):
            loads('{"x":1}', max_bytes=2)
        with self.assertRaisesRegex(StrictJSONError, "nesting budget"):
            loads("[" * 65 + "0" + "]" * 65)
        with self.assertRaises(StrictJSONError):
            loads(b"\xff")
        with self.assertRaises(StrictJSONError):
            loads("{}", max_bytes=True)

    def test_errors_do_not_echo_keys_values_or_paths(self):
        try:
            loads('{"private-marker":"secret-value","private-marker":0}')
        except StrictJSONError as exc:
            self.assertNotIn("private-marker", str(exc))
            self.assertNotIn("secret-value", str(exc))
        else:
            self.fail("duplicate keys accepted")

    def test_bounded_file_read_and_real_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "manifest.json"
            path.write_text('{"version":"x","version":"y"}')
            with self.assertRaisesRegex(StrictJSONError, "byte budget"):
                read(path, max_bytes=4)
            with self.assertRaises(ManifestError):
                Manifest.load(root)
            with self.assertRaises(ManifestError):
                _load_json_object(path, "campaign plan")
            with self.assertRaises(ManifestError):
                _load_effect_plan(path)
            with self.assertRaises(ManifestError):
                load_value_contract(path, "receipt")
            with self.assertRaises(ManifestError):
                load_trust_registry(path, limit=1024, label="trust registry")
            with self.assertRaises(ManifestError):
                load_native_campaign(path, "native receipt")

    def test_task_and_effect_jsonl_consumers_reject_nonfinite_and_depth(self):
        import json
        task = {"id": "case", "category": "test", "prompt": "test", "expected_skill": "adk-test-strategy", "expected_safe": True}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "tasks.jsonl"
            prefix = json.dumps(task)[:-1]
            for value in ("NaN", "Infinity", "1e999", "[" * 65 + "0" + "]" * 65):
                path.write_text(prefix + ',"extra":' + value + "}\n")
                with self.subTest(value=value), self.assertRaises(ManifestError):
                    load_tasks(path)
                with self.subTest(value=value), self.assertRaises(ManifestError):
                    _load_effect_inputs(path)


if __name__ == "__main__":
    unittest.main()
