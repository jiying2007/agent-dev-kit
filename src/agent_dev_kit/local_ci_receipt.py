"""Write and verify bounded, snapshot-bound local CI parity receipts."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .model import ManifestError


SCHEMA = "adk-local-ci-parity-receipt/v1"


def _parse_record(value: str) -> Dict[str, Any]:
    parts = value.split("|")
    if len(parts) != 10:
        raise ManifestError("local CI receipt record must contain ten pipe-delimited fields")
    version, runtime, image_id, gate_sha, audit_sha, wheel_sha, total, passed, routing_total, routing_passed = parts
    for digest in (gate_sha, audit_sha, wheel_sha):
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ManifestError("local CI receipt contains an invalid SHA-256")
    for field in (total, passed, routing_total, routing_passed):
        if not field.isdigit():
            raise ManifestError("local CI receipt count must be numeric")
    return {
        "python": version,
        "runtime_version": runtime,
        "tool_image_id": image_id,
        "gates_log_sha256": gate_sha,
        "audit_log_sha256": audit_sha,
        "wheel_sha256": wheel_sha,
        "tests": {"total": int(total), "passed": int(passed)},
        "routing": {"total": int(routing_total), "passed": int(routing_passed)},
        "audit": "pass",
    }


def _safe_output(root: Path, raw: str) -> Path:
    output = Path(raw).resolve()
    allowed = ((root / ".cache" / "local-ci").resolve(), Path(tempfile.gettempdir()).resolve())
    if not any(output == parent or parent in output.parents for parent in allowed):
        raise ManifestError("local CI receipt must stay under .cache/local-ci or system tmp")
    current = output.parent
    while current != current.parent:
        if current.exists() and current.is_symlink():
            raise ManifestError("local CI receipt path must not traverse a symlink")
        current = current.parent
    return output


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix="." + path.name + ".", suffix=".tmp",
        dir=str(path.parent), delete=False,
    ) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    try:
        temporary.chmod(0o600)
        os.replace(str(temporary), str(path))
    finally:
        temporary.unlink(missing_ok=True)


def _load(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("local CI parity receipt is missing or invalid") from exc
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ManifestError("local CI parity receipt schema is invalid")
    return value


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    check = sub.add_parser("check")
    for command in (write, check):
        command.add_argument("--receipt", required=True)
        command.add_argument("--mode", required=True, choices=("quick", "full"))
        command.add_argument("--source-snapshot-sha256", required=True)
        command.add_argument("--file-mode-inventory-sha256", required=True)
        command.add_argument("--definition-sha256", required=True)
    write.add_argument("--record", action="append", required=True)
    write.add_argument("--summary-json", action="store_true")
    check.add_argument("--python-image", action="append", required=True)
    check.add_argument("--max-age-hours", type=int, default=72)
    check.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    root = Path(args.root).resolve()
    try:
        receipt_path = _safe_output(root, args.receipt)
        if args.command == "write":
            records = [_parse_record(item) for item in args.record]
            if len({item["python"] for item in records}) != len(records):
                raise ManifestError("local CI receipt Python matrix contains duplicates")
            value = {
                "schema": SCHEMA,
                "status": "pass",
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "mode": args.mode,
                "source_snapshot_sha256": args.source_snapshot_sha256,
                "file_mode_inventory_sha256": args.file_mode_inventory_sha256,
                "local_ci_definition_sha256": args.definition_sha256,
                "matrix": records,
                "release_authority": "none-local-parity-only",
                "raw_logs_stored": False,
            }
            _write(receipt_path, value)
            result = {"status": "pass", "receipt": str(receipt_path), "matrix": len(records)}
        else:
            value = _load(receipt_path)
            expected_images = dict(item.split("=", 1) for item in args.python_image)
            actual_images = {str(item.get("python")): item.get("tool_image_id") for item in value.get("matrix", [])}
            expected = {
                "mode": args.mode,
                "source_snapshot_sha256": args.source_snapshot_sha256,
                "file_mode_inventory_sha256": args.file_mode_inventory_sha256,
                "local_ci_definition_sha256": args.definition_sha256,
            }
            if value.get("status") != "pass" or any(value.get(key) != item for key, item in expected.items()):
                raise ManifestError("local CI parity receipt does not match the current snapshot")
            if actual_images != expected_images:
                raise ManifestError("local CI parity receipt tool image matrix has drifted")
            generated = datetime.fromisoformat(str(value.get("generated_at", "")).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600
            if age_hours < 0 or age_hours > args.max_age_hours:
                raise ManifestError("local CI parity receipt is stale")
            for item in value.get("matrix", []):
                if item.get("tests", {}).get("total") != item.get("tests", {}).get("passed"):
                    raise ManifestError("local CI parity receipt contains a failing test matrix")
                if item.get("routing", {}).get("total") != item.get("routing", {}).get("passed"):
                    raise ManifestError("local CI parity receipt contains a failing routing matrix")
                if item.get("audit") != "pass":
                    raise ManifestError("local CI parity receipt contains a failing audit")
            result = {"status": "pass", "receipt": str(receipt_path), "matrix": len(actual_images)}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":") if args.summary_json else None))
        return 0
    except (ManifestError, OSError, ValueError) as exc:
        print("[FAIL] {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
