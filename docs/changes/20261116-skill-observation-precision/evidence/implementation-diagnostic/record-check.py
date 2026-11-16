"""Retain one bounded local implementation command and its source identities."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
RTK = '/workspace/scratch/fe5385ca063a/verification-tools/rtk'
PYTHON = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3'
label, *arguments = sys.argv[1:]
destination = EVIDENCE / (label + '.json')
if destination.exists():
    raise SystemExit('refusing to overwrite an existing command receipt')
environment = dict(os.environ, ADK_PYTHON_BIN=PYTHON, PYTHONPATH=str(ROOT / 'src'),
                   PYTHONDONTWRITEBYTECODE='1', LC_ALL='C',
                   PATH=str(Path(PYTHON).parent) + os.pathsep + os.environ['PATH'])
identities = {}
for name in ('skills/adk-fault-injection-recovery/SKILL.md',
             'optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md',
             'tests/test_skill_fault_activation.py', 'tests/fixtures/fault-activation.c',
             'tests/test_skill_imap_time_methods.py', 'tests/test_skill_content.sh', 'manifest.json',
             'manifests/profile_context_ratchets.json'):
    path = ROOT / name
    if path.is_file():
        data = path.read_bytes()
        identities[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
command = [RTK, 'bypass', *arguments]
started = time.monotonic()
completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                           text=True, timeout=180, check=False)
receipt = dict(argv=command, cwd=str(ROOT), elapsed_seconds=time.monotonic() - started,
               exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr,
               source_identities=identities, python=PYTHON)
destination.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(receipt=str(destination), exit_code=completed.returncode,
                      elapsed_seconds=receipt['elapsed_seconds'])))
raise SystemExit(completed.returncode)
