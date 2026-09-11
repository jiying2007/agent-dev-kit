from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .schema_loader import sync_packaged_schemas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or regenerate packaged schema mirrors from canonical root schemas")
    parser.add_argument("--root", default=".")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify mirrors are byte-identical (default)")
    mode.add_argument("--write", action="store_true", help="regenerate existing packaged mirrors from canonical schemas")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)

    result = sync_packaged_schemas(Path(args.root), write=bool(args.write))
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["status"] == "pass":
        print(
            "[PASS] packaged schema mirrors {} count={} changed={}".format(
                result["mode"], result["count"], len(result["changed"])
            )
        )
    else:
        for failure in result["failures"]:
            print(f"[FAIL] {failure}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
