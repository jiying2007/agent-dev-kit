"""Capture the limited independent review suite without touching source files."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

ROOT = Path('/workspace/scratch/fe8de3b42084/adk-skill-usability')
OUT = Path(__file__).resolve().parent
RTK = '/workspace/scratch/fe8de3b42084/verification-tools/rtk'
argv = [RTK, 'bypass', sys.executable, '-m', 'unittest',
        'tests.test_task_package_delivery', 'tests.test_skill_consumer_usability',
        'tests.test_skill_rtos_methods', 'tests.test_skill_trigger_matrix', '-v']
started = time.monotonic()
run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=180,
                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                          'PYTHONPATH': str(ROOT / 'src'), 'TMPDIR': str(OUT)})
log = OUT / 'postfix-targeted.log'
log.write_text(run.stdout + run.stderr)
record = {'argv': argv, 'returncode': run.returncode,
          'duration_seconds': time.monotonic() - started, 'log': str(log)}
(OUT / 'postfix-targeted.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
print('\n'.join((run.stdout + run.stderr).splitlines()[-8:]))
raise SystemExit(run.returncode)
