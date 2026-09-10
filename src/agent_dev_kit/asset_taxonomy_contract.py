from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_dev_kit.domain.asset_taxonomy import validate_asset_taxonomy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ADK asset taxonomy from canonical manifest.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_asset_taxonomy(Path(args.root))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"schema": "adk-asset-taxonomy-check/v2", "status": "fail", "error": str(exc)}
        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "[PASS] asset taxonomy checks passed "
            f"(source={result['source']}, skills={result['skills']}, optional={result['optional_skills']}, "
            f"profiles={result['profiles']}, workflows={result['workflows']}, routing={result['routing_scenarios']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
