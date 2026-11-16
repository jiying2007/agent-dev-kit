"""Record actual local command results for this implementation task."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

directory = Path(__file__).resolve().parent
label, *command = sys.argv[1:]
started = datetime.now(timezone.utc).isoformat()
clock = time.monotonic()
completed = subprocess.run(command, text=True, capture_output=True, check=False)
record = {
    "command": command,
    "cwd": str(Path.cwd()),
    "started_at": started,
    "elapsed_seconds": time.monotonic() - clock,
    "python": sys.version,
    "platform": platform.platform(),
    "returncode": completed.returncode,
    "stdout": completed.stdout,
    "stderr": completed.stderr,
}
path = directory / (label + ".json")
path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"receipt": str(path), "returncode": completed.returncode}))
raise SystemExit(completed.returncode)
