"""Test-owned IMAP time-method fixture; never a general or published mail client.

Real imaplib parses a fixed stdio protocol peer. No sockets, credentials, or
mailbox writes. The peer implements only the commands exercised by this test.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import imaplib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile


START = datetime(2026, 11, 15, tzinfo=timezone.utc)
END = datetime(2026, 11, 16, tzinfo=timezone.utc)


def message(uid: int, internal: str, **overrides: object) -> dict:
    item = {"uid": uid, "from": "build@example.test", "internaldate": internal,
            "returned_internaldate": internal,
            "date": datetime.strptime(internal, "%d-%b-%Y %H:%M:%S %z").strftime(
                "%a, %d %b %Y %H:%M:%S %z")}
    item.update(overrides)
    return item


MESSAGES = {
    "window": [
        message(101, "15-Nov-2026 12:00:00 +0000"),
        message(102, "14-Nov-2026 23:30:00 -0200"),
        message(103, "15-Nov-2026 23:30:00 -0200"),
        message(104, "16-Nov-2026 00:30:00 +0200"),
        message(105, "15-Nov-2026 00:15:00 +0200"),
        message(106, "15-Nov-2026 00:00:00 +0000"),
        message(107, "16-Nov-2026 00:00:00 +0000"),
    ],
    "basis": [
        message(201, "15-Nov-2026 10:00:00 +0000", date="Sat, 14 Nov 2026 10:00:00 +0000"),
        message(202, "14-Nov-2026 10:00:00 +0000", date="Sun, 15 Nov 2026 10:00:00 +0000"),
    ],
    "internal-errors": [
        message(301, "15-Nov-2026 10:00:00 +0000"),
        message(302, "15-Nov-2026 11:00:00 +0000", returned_internaldate=None),
        message(303, "15-Nov-2026 12:00:00 +0000", returned_internaldate="not-a-time"),
        message(304, "15-Nov-2026 13:00:00 +0000", returned_internaldate="15-Nov-2026 13:00:00"),
    ],
    "date-errors": [
        message(401, "15-Nov-2026 10:00:00 +0000"),
        message(402, "15-Nov-2026 11:00:00 +0000", date=None),
        message(403, "15-Nov-2026 12:00:00 +0000", date="not-a-time"),
        message(404, "15-Nov-2026 13:00:00 +0000", date="Sun, 15 Nov 2026 13:00:00"),
    ],
    "budget": [message(uid, f"15-Nov-2026 {hour}:00:00 +0000")
               for uid, hour in ((501, 10), (502, 11), (503, 12))],
}


def headers(item: dict, *, subset: bool = False) -> bytes:
    # All senders are identical: this regression evaluates time alone.
    date_field = f"Date: {item['date']}\r\n" if item["date"] is not None else ""
    sender = "" if subset else f"From: {item['from']}\r\n"
    return (sender + date_field
            + f"Subject: synthetic {item['uid']}\r\n\r\n").encode("ascii")


def serve(scenario: str, log: Path) -> None:
    def emit(raw: bytes) -> None:
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()

    records = MESSAGES[scenario]
    emit(b"* PREAUTH local synthetic fixture\r\n")
    with log.open("wb") as transcript:
        for raw in sys.stdin.buffer:
            transcript.write(raw)
            transcript.flush()
            tag, command, *args = shlex.split(raw.decode("ascii"))
            if command == "CAPABILITY":
                emit(b"* CAPABILITY IMAP4rev1\r\n")
            elif command == "EXAMINE":
                emit(f"* {len(records)} EXISTS\r\n* OK [UIDVALIDITY 777] fixture\r\n".encode())
                emit(f"{tag} OK [READ-ONLY] EXAMINE complete\r\n".encode())
                continue
            elif command == "UID" and args[0] == "SEARCH":
                if args[1] == "UID":
                    low, high = map(int, args[2].split(":"))
                    candidates = [x["uid"] for x in records if low <= x["uid"] <= high]
                else:
                    pairs = dict(zip(args[1::2], args[2::2]))
                    low = datetime.strptime(pairs["SINCE"], "%d-%b-%Y").date()
                    high = datetime.strptime(pairs["BEFORE"], "%d-%b-%Y").date()
                    candidates = [x["uid"] for x in records if low <= datetime.strptime(
                        x["internaldate"], "%d-%b-%Y %H:%M:%S %z").date() < high]
                emit(("* SEARCH " + " ".join(map(str, candidates)) + "\r\n").encode())
            elif command == "UID" and args[0] == "FETCH":
                uid = int(args[1])
                index, item = next((i, x) for i, x in enumerate(records, 1) if x["uid"] == uid)
                body = headers(item)
                if raw.rstrip().endswith(b"(UID RFC822.SIZE)"):
                    # These fixed messages have no body; full size bounds the
                    # requested Date/Subject subset without downloading it.
                    emit(f"* {index} FETCH (UID {uid} RFC822.SIZE {len(body)})\r\n".encode())
                elif b"BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)]" in raw:
                    body = headers(item, subset=True)
                    timestamp = item["returned_internaldate"]
                    internal = (f'INTERNALDATE "{timestamp}" '
                                if b"INTERNALDATE" in raw and timestamp is not None else "")
                    emit((f"* {index} FETCH (UID {uid} " + internal
                          + f"BODY[HEADER.FIELDS (DATE SUBJECT)] {{{len(body)}}}\r\n").encode())
                    emit(body + b")\r\n")
                else:
                    raise AssertionError("fixture refuses unsupported or non-PEEK fetch")
            elif command == "LOGOUT":
                try:
                    emit(b"* BYE fixture ended\r\n")
                    emit(f"{tag} OK LOGOUT complete\r\n".encode())
                except BrokenPipeError:
                    # The test client may close its stdout pipe immediately
                    # after consuming LOGOUT. This is not a protocol failure.
                    # Redirect the inherited fd so interpreter shutdown does
                    # not print another BrokenPipeError to stderr.
                    with open(os.devnull, "wb") as sink:
                        os.dup2(sink.fileno(), sys.stdout.fileno())
                break
            else:
                raise AssertionError(f"fixture refuses command: {command}")
            emit(f"{tag} OK {command} complete\r\n".encode())


def timestamp_value(value: str | None, basis: str) -> tuple[datetime | None, str | None]:
    if value is None:
        return None, "missing-time"
    try:
        if basis == "sent":
            parsed = parsedate_to_datetime(value)
        else:
            try:
                parsed = datetime.strptime(value, "%d-%b-%Y %H:%M:%S %z")
            except ValueError:
                # Recognize a missing zone, but never substitute the host zone.
                parsed = datetime.strptime(value, "%d-%b-%Y %H:%M:%S")
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None, "unknown-timezone"
        return parsed.astimezone(timezone.utc), None
    except (TypeError, ValueError, OverflowError):
        return None, "invalid-time"


def observe(scenario: str, mode: str, basis: str, count_budget: int, byte_budget: int) -> dict:
    records = MESSAGES[scenario]
    if scenario == "window":
        criteria = ("SINCE", "15-Nov-2026", "BEFORE", "16-Nov-2026") if mode == "day" else (
            "SINCE", "14-Nov-2026", "BEFORE", "17-Nov-2026")
        coverage = ("ordinary server calendar-day semantics" if mode == "day" else
                    "fixed fixture offsets lie in [-02:00,+02:00]; local dates 14..16 cover this UTC window")
    else:
        criteria = ("UID", f"{records[0]['uid']}:{records[-1]['uid']}")
        coverage = "request explicitly scopes these fixture UIDs; no timestamp is used to omit candidates"
    matched, excluded, undecided = [], [], []
    fetched, content_bytes = 0, 0
    with tempfile.TemporaryDirectory(prefix="adk-imap-time-") as directory:
        log = Path(directory) / "commands.txt"
        command = shlex.join([sys.executable, "-B", str(Path(__file__).resolve()),
                              scenario, "--server-log", str(log)])
        with imaplib.IMAP4_stream(command) as client:
            assert client.select("INBOX", readonly=True)[0] == "OK"
            assert client.response("UIDVALIDITY")[1] == [b"777"]
            status, response = client.uid("SEARCH", None, *criteria)
            assert status == "OK"
            candidates = [int(x) for x in response[0].split()]
            assert len(candidates) <= 7  # Fixed fixture, not a general search-size policy.
            for uid in candidates:
                if fetched >= count_budget:
                    undecided.append({"uid": uid, "reason": "count-budget"})
                    continue
                status, size_response = client.uid("FETCH", str(uid), "(UID RFC822.SIZE)")
                assert status == "OK"
                size_match = re.search(rb"UID (\d+) RFC822.SIZE (\d+)", size_response[0])
                assert size_match and int(size_match[1]) == uid
                if content_bytes + int(size_match[2]) > byte_budget:
                    undecided.append({"uid": uid, "reason": "byte-budget"})
                    continue
                fields = "UID INTERNALDATE" if mode == "exact" and basis == "received" else "UID"
                status, data = client.uid("FETCH", str(uid),
                                          f"({fields} BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)])")
                assert status == "OK"
                literals = [part for part in data if isinstance(part, tuple)]
                assert len(literals) == 1
                metadata, raw_header = literals[0]
                identity = re.search(rb"UID (\d+)", metadata)
                assert identity and int(identity[1]) == uid
                fetched += 1
                content_bytes += len(raw_header)
                assert content_bytes <= byte_budget
                if mode == "day":
                    matched.append(uid)
                    continue
                if basis == "received":
                    found = re.search(rb'INTERNALDATE "([^"]+)"', metadata)
                    raw_time = found[1].decode("ascii") if found else None
                else:
                    raw_time = BytesParser(policy=policy.compat32).parsebytes(raw_header).get("Date")
                value, error = timestamp_value(raw_time, basis)
                if error:
                    undecided.append({"uid": uid, "reason": error})
                elif START <= value < END:
                    matched.append(uid)
                else:
                    excluded.append(uid)
        commands = log.read_text(encoding="ascii").splitlines()
    return {"scope": "test-only filtering observation, not live mailbox qualification",
            "scenario": scenario, "mode": mode, "basis": basis, "coverage_basis": coverage,
            "window": [START.isoformat(), END.isoformat()], "inputs": records,
            "candidates": candidates, "matched": matched, "excluded": excluded,
            "undecided": undecided, "filter_status": "partial" if undecided else "pass",
            "count_budget": count_budget, "byte_budget": byte_budget,
            "fetched_count": fetched, "content_bytes": content_bytes, "commands": commands}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=tuple(MESSAGES))
    parser.add_argument("--server-log", type=Path)
    parser.add_argument("--mode", choices=("day", "exact"), default="exact")
    parser.add_argument("--basis", choices=("received", "sent"), default="received")
    parser.add_argument("--count-budget", type=int, default=7)
    parser.add_argument("--byte-budget", type=int, default=16384)
    args = parser.parse_args()
    if args.server_log:
        serve(args.scenario, args.server_log)
    else:
        print(json.dumps(observe(args.scenario, args.mode, args.basis,
                                 args.count_budget, args.byte_budget), ensure_ascii=False))
