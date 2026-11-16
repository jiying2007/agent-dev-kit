"""Exact-From method controls using the real stdlib header parser.

The selector is test-owned, not an ADK mail client. Header octet/count budgets
refer only to these supplied fixtures; no live protocol or identity claim.
Only the source-contract test is expected to fail on the old Skill.
"""
from __future__ import annotations

from email import policy
from email.errors import HeaderParseError
from email.headerregistry import Address
from email.parser import BytesParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md"
TARGET = "build@example.test"


def header(sender: str) -> bytes:
    return f"From: {sender}\r\n\r\n".encode("ascii")


def select(candidates: list[tuple[int, bytes]], *, mode: str = "exact",
           semantics: str | None = "standard-mailbox", count_budget: int = 20,
           byte_budget: int = 4096) -> dict:
    """Fixture candidates are a known superset; any From mailbox may match.

    Exact mode explicitly preserves local-part and folds only the domain.
    Fuzzy mode preserves the supplied server search results without imposing
    exact-address semantics. Missing semantics never grants an exact result.
    """
    target = Address(addr_spec=TARGET)
    matched, excluded, undecided, parsed = [], [], [], []
    used = 0
    for uid, raw in candidates:
        reason = None
        if mode == "exact" and semantics != "standard-mailbox":
            reason = "unknown-address-semantics"
        elif len(parsed) >= count_budget:
            reason = "count-budget"
        elif len(raw) > byte_budget - used:
            reason = "byte-budget"
        if reason is not None:
            undecided.append({"uid": uid, "reason": reason})
            continue
        parsed.append(uid)
        used += len(raw)
        if mode == "fuzzy":
            matched.append(uid)
            continue
        try:
            message = BytesParser(policy=policy.default).parsebytes(raw)
            fields = message.get_all("From", [])
            if len(fields) != 1:
                undecided.append({"uid": uid, "reason": "missing-or-repeated-from"})
                continue
            field = fields[0]
            addresses = field.addresses
            invalid = (message.defects or field.defects or not addresses
                       or any(not a.username or not a.domain for a in addresses)
                       or any(group.display_name is not None for group in field.groups))
        except (HeaderParseError, ValueError, RecursionError):
            undecided.append({"uid": uid, "reason": "unparseable-from"})
            continue
        if invalid:
            undecided.append({"uid": uid, "reason": "invalid-from"})
            continue
        same = any(a.username == target.username
                   and a.domain.lower() == target.domain.lower() for a in addresses)
        (matched if same else excluded).append(uid)
    return {"matched": matched, "excluded": excluded, "undecided": undecided,
            "parsed": parsed, "header_bytes": used,
            "status": "partial" if undecided else "pass"}


class ImapSenderMethodTests(unittest.TestCase):
    def test_source_separates_exact_address_from_substring_and_identity(self):
        text = SKILL.read_text(encoding="utf-8")
        for term in ("完整发件地址", "FROM", "子串", "解析", "local-part",
                     "别名", "身份认证", "模糊", "未判定", "partial"):
            with self.subTest(term=term):
                self.assertTrue(term in text, f"missing source method: {term}")
        for retained in ("EXAMINE", "BODY.PEEK", "UIDVALIDITY", "最大封数与字节预算",
                         "INTERNALDATE", "另一时间字段", "not-verified"):
            self.assertIn(retained, text)

    def test_exact_addresses_accept_positive_controls_and_reject_substring_decoys(self):
        inputs = [(101, header(TARGET)), (102, header(f"Build <{TARGET}>")),
                  (103, header(f'"{TARGET}" <noise@example.test>')),
                  (104, header(f"{TARGET}.invalid"))]
        result = select(inputs)
        self.assertEqual([101, 102], result["matched"])
        self.assertEqual([103, 104], result["excluded"])
        self.assertEqual([], result["undecided"])
        self.assertEqual("pass", result["status"])
        # Wrong substring logic accepts both decoys on the same raw inputs.
        wrong = [uid for uid, raw in inputs if TARGET.lower().encode() in raw.lower()]
        self.assertEqual([101, 102, 103, 104], wrong)
        self.assertNotEqual(result["matched"], wrong)

    def test_domain_case_folds_but_local_part_and_aliases_are_preserved(self):
        inputs = [(201, header("build@EXAMPLE.TEST")),
                  (202, header("Build@example.test")),
                  (203, header("build+ci@example.test")),
                  (204, header("b.uild@example.test")),
                  (205, header('"build"@example.test'))]
        result = select(inputs)
        self.assertEqual([201, 205], result["matched"])
        self.assertEqual([202, 203, 204], result["excluded"])
        self.assertEqual("pass", result["status"])

    def test_missing_repeated_and_malformed_headers_preserve_partial_success(self):
        inputs = [(301, header(TARGET)), (302, b"Subject: fixture\r\n\r\n"),
                  (303, b"From: build@@example.test\r\n\r\n"),
                  (304, b"From: build@example.test\r\nFrom: noise@example.test\r\n\r\n")]
        result = select(inputs)
        self.assertEqual([301], result["matched"])
        self.assertEqual([], result["excluded"])
        self.assertEqual([{"uid": 302, "reason": "missing-or-repeated-from"},
                          {"uid": 303, "reason": "invalid-from"},
                          {"uid": 304, "reason": "missing-or-repeated-from"}], result["undecided"])
        self.assertEqual("partial", result["status"])

    def test_undefined_address_semantics_leave_candidates_undecided(self):
        result = select([(401, header(TARGET))], semantics=None)
        self.assertEqual([], result["matched"])
        self.assertEqual([], result["parsed"])
        self.assertEqual([{"uid": 401, "reason": "unknown-address-semantics"}], result["undecided"])
        self.assertEqual("partial", result["status"])

    def test_parser_failure_isolated_between_successes_with_deep_positive_controls(self):
        def commented(depth: int) -> bytes:
            return b"From: " + b"(" * depth + b"comment" + b")" * depth + b" build@example.test\r\n\r\n"

        inputs = [(411, header(TARGET)), (412, commented(100)),
                  (413, commented(300)), (414, commented(600)),
                  (415, header(TARGET))]
        self.assertLess(sum(len(raw) for _, raw in inputs), 4096)
        result = select(inputs)
        self.assertEqual([411, 412, 413, 415], result["matched"])
        self.assertEqual([], result["excluded"])
        self.assertEqual([{"uid": 414, "reason": "unparseable-from"}], result["undecided"])
        self.assertEqual("partial", result["status"])

    def test_count_and_header_byte_budgets_keep_success_and_unread_uids(self):
        inputs = [(501, header(TARGET)), (502, header(TARGET)), (503, header(TARGET))]
        for options, reason in (({"count_budget": 1}, "count-budget"),
                                ({"byte_budget": len(inputs[0][1])}, "byte-budget")):
            with self.subTest(reason=reason):
                result = select(inputs, **options)
                self.assertEqual([501], result["matched"])
                self.assertEqual([501], result["parsed"])
                self.assertEqual(len(inputs[0][1]), result["header_bytes"])
                self.assertEqual([{"uid": 502, "reason": reason},
                                  {"uid": 503, "reason": reason}], result["undecided"])
                self.assertEqual("partial", result["status"])

    def test_fuzzy_request_keeps_server_candidates_without_exact_refiltering(self):
        inputs = [(601, header(TARGET)),
                  (602, header(f'"{TARGET}" <noise@example.test>'))]
        result = select(inputs, mode="fuzzy")
        self.assertEqual([601, 602], result["matched"])
        self.assertEqual([], result["excluded"])
        self.assertEqual("pass", result["status"])


if __name__ == "__main__":
    unittest.main()
