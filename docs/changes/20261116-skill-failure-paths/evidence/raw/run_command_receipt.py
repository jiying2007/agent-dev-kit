import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--cwd', required=True)
p.add_argument('--out', required=True)
p.add_argument('--timeout', type=int, default=1800)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ['--'] else a.command
root, out = Path(a.cwd), Path(a.out)
out.mkdir(parents=True, exist_ok=False)

def now():
    return datetime.now(UTC).isoformat()

def git(*args):
    r = subprocess.run(['git', '-c', 'core.fsmonitor=false', *args], cwd=root,
                       text=True, capture_output=True, check=False)
    return {'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}

def identity():
    return {k: git(*v) for k, v in {
        'head': ['rev-parse', 'HEAD'], 'indexed_tree': ['write-tree'],
        'status': ['status', '--porcelain=v1'],
        'staged_diff': ['diff', '--cached', '--no-ext-diff', '--no-textconv', '--binary'],
    }.items()}

receipt = {'schema': 'local-command-observation/v1', 'cwd': str(root),
           'command': command, 'started_at': now(), 'before': identity()}
(out / 'started.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'started_at': receipt['started_at'], 'command': command, 'out': str(out)}), flush=True)
started = time.monotonic()
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    child = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                             env=os.environ.copy(), start_new_session=True)
    try:
        code = child.wait(timeout=a.timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        code = child.wait()
        timed_out = True
receipt.update(finished_at=now(), elapsed_seconds=time.monotonic() - started,
               exit_code=code, timed_out=timed_out, after=identity())
receipt['logs'] = {name: {'bytes': (out / name).stat().st_size,
                         'sha256': hashlib.sha256((out / name).read_bytes()).hexdigest()}
                   for name in ('stdout.log', 'stderr.log')}
(out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('finished_at', 'elapsed_seconds', 'exit_code', 'timed_out', 'logs')}), flush=True)
for name in ('stdout.log', 'stderr.log'):
    lines = (out / name).read_text(errors='replace').splitlines()
    print(json.dumps({name: lines[-25:]}), flush=True)
raise SystemExit(code or timed_out)
