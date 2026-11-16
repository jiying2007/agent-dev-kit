"""Bounded synthetic diagnostics; never writes to the ADK or Root checkout."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

STARTED = datetime.now(timezone.utc).isoformat()
OUT = Path('/workspace/scratch/fe5385ca063a/round2-core-probes.json')
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
           GIT_TERMINAL_PROMPT='0', LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
records = []


def call(argv, cwd, *, allowed=(0,)):
    p = subprocess.run(argv, cwd=cwd, env=ENV, text=True, capture_output=True, timeout=15)
    records.append({'argv': argv, 'cwd': str(cwd), 'exit': p.returncode,
                    'stdout': p.stdout, 'stderr': p.stderr})
    if p.returncode not in allowed:
        raise RuntimeError(records[-1])
    return p


with tempfile.TemporaryDirectory(prefix='adk-core-probes-') as temporary:
    scratch = Path(temporary)
    repo = scratch / 'repo'
    repo.mkdir()
    git = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null']
    call(git + ['init', '-b', 'main'], repo)
    call(git + ['config', 'user.name', 'Synthetic Diagnostic'], repo)
    call(git + ['config', 'user.email', 'diagnostic@example.invalid'], repo)
    # The property being bisected is semantic_regression, not buildability.
    states = [
        {'step': 0, 'runnable': True, 'semantic_regression': False},
        {'step': 1, 'runnable': True, 'semantic_regression': False},
        {'step': 2, 'runnable': False, 'semantic_regression': False},
        {'step': 3, 'runnable': True, 'semantic_regression': False},
        {'step': 4, 'runnable': True, 'semantic_regression': True},
        {'step': 5, 'runnable': True, 'semantic_regression': True},
    ]
    commits = []
    for state in states:
        (repo / 'state.json').write_text(json.dumps(state) + '\n')
        call(git + ['add', 'state.json'], repo)
        call(git + ['commit', '-m', 'synthetic step ' + str(state['step'])], repo)
        commits.append(call(git + ['rev-parse', 'HEAD'], repo).stdout.strip())
    probe = scratch / 'oracle.py'
    probe.write_text('import json,sys\nfrom pathlib import Path\n'
                     's=json.loads(Path("state.json").read_text())\n'
                     'print(json.dumps({"mode":sys.argv[1],"state":s}))\n'
                     'if not s["runnable"]: raise SystemExit(125 if sys.argv[1]=="guarded" else 1)\n'
                     'raise SystemExit(int(s["semantic_regression"]))\n')
    results = {}
    for mode in ('naive', 'guarded'):
        call(git + ['bisect', 'start', commits[-1], commits[0]], repo)
        result = call(git + ['bisect', 'run', 'python3', str(probe), mode], repo,
                      allowed=(0, 1, 2))
        bisect_log = call(git + ['bisect', 'log'], repo).stdout
        checked_out = call(git + ['rev-parse', 'HEAD'], repo).stdout.strip()
        match = re.search(r'^# first bad commit: \[([0-9a-f]{40})\]', bisect_log, re.MULTILINE)
        if not match:
            raise RuntimeError('bisect did not name a unique first bad commit: ' + bisect_log)
        located = match.group(1)
        results[mode] = {'exit': result.returncode, 'located_commit': located,
                         'located_step': commits.index(located), 'checked_out_head': checked_out,
                         'log': bisect_log,
                         'stdout': result.stdout, 'stderr': result.stderr}
        call(git + ['bisect', 'reset'], repo)
    assert results['naive']['located_step'] == 2, results
    assert results['guarded']['located_step'] == 4, results

    failure_dir = scratch / 'runner-output'
    failure_dir.mkdir()
    artifact = failure_dir / 'failure.json'
    original = b'{"synthetic":true,"request":17,"late_response_from":16}\n'
    artifact.write_bytes(original)
    preserved = scratch / 'preserved-failure.json'
    shutil.copyfile(artifact, preserved)
    original_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    # A synthetic runner clears its previous failure at the start of a new run.
    artifact.unlink()
    (failure_dir / 'result.json').write_text('{"synthetic":true,"status":"pass"}\n')
    preservation = {'synthetic_runner': True, 'raw_failure_after_rerun_exists': artifact.exists(),
                    'copied_before_rerun': preserved.exists(),
                    'original_sha256': original_digest,
                    'preserved_sha256': hashlib.sha256(preserved.read_bytes()).hexdigest()}
    assert not preservation['raw_failure_after_rerun_exists']
    assert preservation['original_sha256'] == preservation['preserved_sha256']
    outcome = {'schema': 'adk-core-diagnostic-probes/v1', 'status': 'pass',
               'started_at': STARTED, 'completed_at': datetime.now(timezone.utc).isoformat(),
               'scope': 'Synthetic isolated examples; not an observed agent/model failure or an ADK runner defect',
               'git_version': call(['git', '--version'], repo).stdout.strip(),
               'bisect': {'states': states, 'commits': commits, 'results': results},
               'preservation': preservation, 'commands': records}
    OUT.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': outcome['status'], 'output': str(OUT),
                      'naive_located_step': results['naive']['located_step'],
                      'guarded_located_step': results['guarded']['located_step'],
                      'actual_semantic_regression_step': 4,
                      'preservation': preservation,
                      'command_count': len(records)}, ensure_ascii=False))
