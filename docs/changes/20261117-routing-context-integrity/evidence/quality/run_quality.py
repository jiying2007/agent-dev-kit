"""Capture the existing quality gates, without altering product sources."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/workspace/scratch/d417066aafa8/agent-dev-kit')
OUT = Path('/workspace/scratch/d417066aafa8/verification/quality')
RTK = '/workspace/scratch/fe8de3b42084/verification-tools/rtk'
ENV = {**os.environ, 'PATH': str(ROOT / '.venv/bin') + os.pathsep + os.environ['PATH']}
ENV['PYTHONPATH'] = 'src'


def utc():
    return datetime.now(UTC).isoformat()


def run(name, command):
    started = utc()
    clock = time.monotonic()
    log = OUT / (name + '.log')
    invoked = [RTK, 'proxy', *command]
    with log.open('wb') as stream:
        completed = subprocess.run(invoked, cwd=ROOT, env=ENV, stdout=stream, stderr=subprocess.STDOUT)
    result = {'name': name, 'command': invoked, 'cwd': str(ROOT), 'started_at': started,
              'finished_at': utc(), 'elapsed_seconds': time.monotonic() - clock,
              'exit_code': completed.returncode, 'log': str(log),
              'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
    (OUT / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    return result


def main():
    versions = run('versions', ['bash', '-c',
        'python --version; ruff --version; mypy --version; shellcheck --version; '
        'pip-audit --version; git --version; bash --version; ' + RTK + ' --version'])
    commands = {
        'ruff': ['ruff', 'check', 'src', 'tools', 'tests/fixtures/fake_target_runtime.py'],
        'mypy': ['mypy', 'src/agent_dev_kit/contracts', 'src/agent_dev_kit/evidence',
                 'src/agent_dev_kit/target_adapters', 'src/agent_dev_kit/distribution',
                 'src/agent_dev_kit/execution_policy', 'src/agent_dev_kit/versioning.py'],
        'shellcheck': ['bash', '-c', 'shellcheck -S error -x -P scripts scripts/*.sh tests/*.sh'],
        'pip-audit': ['pip-audit', '--strict', '--progress-spinner', 'off', '.'],
        'format': ['bash', 'scripts/check-format.sh'],
    }
    results = []
    with ThreadPoolExecutor(max_workers=len(commands)) as pool:
        jobs = [pool.submit(run, name, command) for name, command in commands.items()]
        for job in as_completed(jobs):
            results.append(job.result())
    summary = {'completed_at': utc(), 'versions': versions, 'gates': sorted(results, key=lambda x: x['name']),
               'all_passed': all(result['exit_code'] == 0 for result in results),
               'scope': 'read-only quality gates; no runtime, model, device or product qualification'}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
