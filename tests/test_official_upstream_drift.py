"""Offline, deterministic tests for official upstream Git change detection."""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_dev_kit import official_upstream_drift as audit


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    status = 200

    def __init__(self, content: bytes):
        self.content = io.BytesIO(content)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, length):
        return self.content.read(length)


class FakeOpener:
    def __init__(self, content: bytes):
        self.content = content
        self.requests = []

    def open(self, request, timeout=10):
        self.requests.append((request.full_url, request.get_method(), timeout))
        return FakeResponse(self.content)


class OfficialDriftTests(unittest.TestCase):
    def setUp(self):
        self.config = audit.load_config(ROOT / "manifests/official_upstream_git_pins.json")
        self.exact = {x["repository"]: x["reviewed_sha"] for x in self.config["sources"]}

    def test_exact_pins_pass_without_network(self):
        value = audit.check_sources(self.config, lambda repository: self.exact[repository])
        self.assertEqual("pass", value["status"])
        self.assertTrue(all(row["state"] == "unchanged" for row in value["sources"]))
        self.assertIn("not-doc-content", value["claims"])

    def test_commit_drift_is_reported_but_never_auto_accepted(self):
        new_sha = "f" * 40
        value = audit.check_sources(
            self.config,
            lambda repository: new_sha if repository == "openai/plugins" else self.exact[repository],
        )
        self.assertEqual("drift", value["status"])
        by_id = {row["id"]: row for row in value["sources"]}
        self.assertEqual("drift", by_id["openai-plugins-examples"]["state"])
        self.assertEqual(self.exact["openai/plugins"], by_id["openai-plugins-examples"]["reviewed_sha"])

    def test_network_failure_is_not_green_or_source_change(self):
        def unavailable(_repository):
            raise OSError("offline")
        value = audit.check_sources(self.config, unavailable)
        self.assertEqual("fail", value["status"])
        self.assertEqual({"unavailable"}, {row["state"] for row in value["sources"]})

    def test_untrusted_repo_and_invalid_response_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unreviewed upstream"):
            audit.fetch_head("other/repository")
        for content in (b"{}", b'{"sha":"bad"}', b'{"sha":"f","sha":"a"}',
                        b'{"sha":NaN}', b" " * (audit.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(content=content[:30]):
                opener = FakeOpener(content)
                with patch.object(audit.urllib.request, "build_opener", return_value=opener):
                    with self.assertRaises((ValueError, json.JSONDecodeError)):
                        audit.fetch_head("openai/plugins")
                self.assertEqual(
                    [("https://api.github.com/repos/openai/plugins/commits/main", "GET", 10)],
                    opener.requests,
                )

    def test_config_tampering_and_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "watch.json"
            for edit in (
                lambda x: x["sources"][0].update(repository="untrusted/other"),
                lambda x: x["sources"].append(copy.deepcopy(x["sources"][0])),
                lambda x: x["sources"][0].update(reviewed_sha="0" * 39),
            ):
                raw = copy.deepcopy(self.config)
                edit(raw)
                path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    audit.load_config(path)
            path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON"):
                audit.load_config(path)

    def test_no_redirect_to_other_origins(self):
        handler = audit._NoRedirect()
        with self.assertRaisesRegex(ValueError, "redirected"):
            handler.redirect_request(None, None, 302, "Found", {}, "http://127.0.0.1/secret")


if __name__ == "__main__":
    unittest.main()
