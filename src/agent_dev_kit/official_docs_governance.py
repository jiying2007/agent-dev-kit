"""Stable read-only entrypoint for owned official documentation audit stages."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .official_docs_context import AuditContext
from .official_docs_sources import check as check_sources
from .official_docs_evidence import check as check_evidence
from .official_docs_runtime import check as check_runtime
from .official_docs_delivery import check as check_delivery
from .official_docs_adoption import check as check_adoption
from .official_docs_summary import check as check_summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check official reference and execution contracts without network or writes")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    context = AuditContext(Path(args.root).resolve(), args.summary_json)
    check_sources(context)
    check_evidence(context)
    check_runtime(context)
    check_delivery(context)
    check_adoption(context)
    check_summary(context)
    return 0 if not context.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
