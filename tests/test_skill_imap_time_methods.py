"""IMAP method contract plus local protocol controls; no live/model qualification.

The test-owned peer/client demonstrates the method, not an ADK mail executor.
Only the source-contract test is expected to fail on the pre-enhancement Skill.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md"
FIXTURE = ROOT / "tests/fixtures/imap-time-fixture.py"


class ImapTimeMethodTests(unittest.TestCase):
    def test_source_distinguishes_conditional_exact_filtering_and_partial(self):
        text = SKILL.read_text(encoding="utf-8")
        for term in ("普通日级", "精确时间请求", "INTERNALDATE", "Date", "[start,end)",
                     "时区", "覆盖依据", "SINCE/BEFORE/ON", "SENT*", "未判定",
                     "另一时间字段", "主机时区", "partial"):
            with self.subTest(term=term):
                self.assertIn(term, text)
        for retained in ("EXAMINE", "BODY.PEEK", "UIDVALIDITY", "最大封数与字节预算",
                         "STORE/COPY/MOVE/EXPUNGE", "凭证必须从环境变量读取", "not-verified"):
            self.assertIn(retained, text)
        self.assertIn("不默认扫描所有邮箱", text)

    def observe(self, scenario: str, *options: str, host_zone: str = "UTC") -> dict:
        result = subprocess.run([sys.executable, "-B", str(FIXTURE), scenario, *options],
                                capture_output=True, text=True, timeout=10,
                                env={**os.environ, "LC_ALL": "C", "TZ": host_zone,
                                     "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)
        observation = json.loads(result.stdout)
        self.assertEqual({"build@example.test"}, {item["from"] for item in observation["inputs"]})
        commands = [line.split(" ", 1)[1] for line in observation["commands"]]
        self.assertIn("EXAMINE INBOX", commands)
        self.assertTrue(any(command.startswith("UID SEARCH ") for command in commands))
        self.assertTrue(all(command.startswith(("CAPABILITY", "EXAMINE ", "UID SEARCH ",
                                                "UID FETCH ", "LOGOUT")) for command in commands))
        self.assertFalse(any(" ALL" in command or "FROM" in command for command in commands))
        for command in commands:
            if "BODY" in command:
                self.assertIn("BODY.PEEK[HEADER.FIELDS", command)
        self.assertLessEqual(observation["content_bytes"], observation["byte_budget"])
        self.assertLessEqual(observation["fetched_count"], observation["count_budget"])
        return observation

    def test_ordinary_day_uses_server_calendar_day_without_exact_refiltering(self):
        result = self.observe("window", "--mode", "day")
        self.assertEqual([101, 103, 105, 106], result["matched"])
        self.assertEqual("day", result["mode"])
        self.assertEqual("pass", result["filter_status"])
        self.assertEqual([], result["undecided"])
        self.assertFalse(any("INTERNALDATE" in command for command in result["commands"]))
        self.assertTrue(any("SINCE 15-Nov-2026 BEFORE 16-Nov-2026" in command
                            for command in result["commands"]))

    def test_exact_window_covers_cross_timezone_and_half_open_boundaries(self):
        result = self.observe("window")
        self.assertEqual([101, 102, 104, 106], result["matched"])
        self.assertEqual([103, 105, 107], result["excluded"])
        self.assertEqual(list(range(101, 108)), result["candidates"])
        self.assertIn("fixed fixture offsets", result["coverage_basis"])
        self.assertEqual("pass", result["filter_status"])
        # Literal controls: 106 is the included start, 107 the excluded end.
        self.assertIn(106, result["matched"])
        self.assertNotIn(107, result["matched"])

    def test_received_and_sent_requests_use_the_selected_field(self):
        for basis, expected in (("received", [201]), ("sent", [202])):
            with self.subTest(basis=basis):
                result = self.observe("basis", "--basis", basis)
                self.assertEqual(expected, result["matched"])
                self.assertEqual([201, 202], result["candidates"])
                self.assertEqual("pass", result["filter_status"])
                self.assertTrue(any("UID SEARCH UID 201:202" in command for command in result["commands"]))

    def test_local_peer_logout_after_closed_read_pipe_is_quiet(self):
        # Deterministic regression for a real fresh-main failure: imaplib's
        # read end can close while the fixture peer is replying to LOGOUT.
        # A test-owned peer must not emit a BrokenPipe traceback on stderr.
        with tempfile.TemporaryDirectory(prefix="adk-imap-peer-close-") as directory:
            log = Path(directory) / "commands.txt"
            with subprocess.Popen(
                [sys.executable, "-B", str(FIXTURE), "basis", "--server-log", str(log)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={**os.environ, "LC_ALL": "C", "TZ": "UTC", "PYTHONDONTWRITEBYTECODE": "1"},
            ) as peer:
                assert peer.stdin is not None and peer.stdout is not None and peer.stderr is not None
                self.assertEqual(b"* PREAUTH local synthetic fixture\r\n", peer.stdout.readline())
                peer.stdout.close()
                peer.stdin.write(b"ZZ1 LOGOUT\r\n")
                peer.stdin.flush()
                peer.stdin.close()
                try:
                    status = peer.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    peer.kill()
                    peer.wait()
                    self.fail("IMAP peer did not finish its LOGOUT cleanup")
                error_text = peer.stderr.read().decode("utf-8", errors="replace")
                self.assertEqual(0, status, error_text)
                self.assertEqual("", error_text)
            self.assertIn("ZZ1 LOGOUT", log.read_text(encoding="ascii"))

    def test_missing_invalid_and_unknown_zone_stay_undecided_without_fallback(self):
        for scenario, basis, first in (("internal-errors", "received", 301),
                                       ("date-errors", "sent", 401)):
            for host_zone in ("UTC", "EST5EDT"):
                with self.subTest(scenario=scenario, host_zone=host_zone):
                    result = self.observe(scenario, "--basis", basis, host_zone=host_zone)
                    self.assertEqual([first], result["matched"])
                    self.assertEqual([], result["excluded"])
                    self.assertEqual([{"uid": first + 1, "reason": "missing-time"},
                                      {"uid": first + 2, "reason": "invalid-time"},
                                      {"uid": first + 3, "reason": "unknown-timezone"}], result["undecided"])
                    self.assertEqual("partial", result["filter_status"])

    def test_count_budget_keeps_success_and_unfetched_candidates(self):
        result = self.observe("budget", "--count-budget", "1")
        self.assertEqual([501], result["matched"])
        self.assertEqual([{"uid": 502, "reason": "count-budget"},
                          {"uid": 503, "reason": "count-budget"}], result["undecided"])
        self.assertEqual("partial", result["filter_status"])
        self.assertFalse(any("UID FETCH 502 " in command or "UID FETCH 503 " in command
                             for command in result["commands"]))

    def test_byte_budget_does_not_fetch_content_that_exceeds_remaining_budget(self):
        result = self.observe("budget", "--byte-budget", "100")
        self.assertEqual([501], result["matched"])
        self.assertEqual([{"uid": 502, "reason": "byte-budget"},
                          {"uid": 503, "reason": "byte-budget"}], result["undecided"])
        self.assertEqual("partial", result["filter_status"])
        for uid in (502, 503):
            self.assertTrue(any(f"UID FETCH {uid} (UID RFC822.SIZE)" in command
                                for command in result["commands"]))
            self.assertFalse(any(f"UID FETCH {uid} " in command and "BODY.PEEK" in command
                                 for command in result["commands"]))


if __name__ == "__main__":
    unittest.main()
