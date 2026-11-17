"""Hash tracked operational inputs; exclude accumulated historical evidence."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2])
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
excluded = ("docs/changes/", "reports/", "evals/results/")
rows = {}
for name in paths:
    path = root / name
    if name and not name.startswith(excluded) and path.is_file():
        raw = path.read_bytes()
        rows[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
record = {
    "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "all tracked regular files except accumulated change/report/result evidence",
    "excluded_prefixes": list(excluded),
    "file_count": len(rows),
    "files": rows,
}
output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"file_count": len(rows), "output": str(output)}))
