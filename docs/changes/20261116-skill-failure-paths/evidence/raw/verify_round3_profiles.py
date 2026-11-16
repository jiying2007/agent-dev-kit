import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

WORK = Path('/workspace/scratch/fe5385ca063a')
ROOT = WORK / 'agent-dev-kit'
BASE = '80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b'
parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--tree', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
HEAD = args.source
TREE = args.tree
OUT = Path(args.out)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def identity():
    return {'head': git('rev-parse', 'HEAD').decode().strip(),
            'tree': git('rev-parse', 'HEAD^{tree}').decode().strip(),
            'status': git('status', '--porcelain').decode()}


before = identity()
if before != {'head': HEAD, 'tree': TREE, 'status': ''}:
    raise RuntimeError(before)
policy_path = 'manifests/profile_context_ratchets.json'
policy = (ROOT / policy_path).read_bytes()
if policy != git('show', f'{BASE}:{policy_path}'):
    raise RuntimeError('budget policy changed')
profiles = sorted(json.loads(policy)['profiles'])
records = []
for profile in profiles:
    command = ['bash', 'scripts/devkit.sh', 'profile-footprint', '--profile', profile, '--ratchet', '--summary-json']
    started = datetime.now(UTC).isoformat()
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    parsed = json.loads(run.stdout)
    records.append({'profile': profile, 'argv': command, 'started_at': started,
                    'finished_at': datetime.now(UTC).isoformat(), 'exit_code': run.returncode,
                    'stdout': run.stdout, 'stderr': run.stderr, 'result': parsed})
after = identity()
if after != before:
    raise RuntimeError('source changed during profile checks')
result = {'schema': 'adk-profile-check-observation/v1', 'before': before, 'after': after,
          'baseline_commit': BASE, 'policy_path': policy_path,
          'policy_sha256': hashlib.sha256(policy).hexdigest(), 'thresholds_unchanged': True,
          'results': records,
          'status': 'pass' if len(records) == 8 and all(r['exit_code'] == 0 and r['result']['status'] == 'pass' for r in records) else 'fail',
          'boundary': 'UTF-8 source budget only, not provider tokens, native initial context, latency or cost.'}
if OUT.exists():
    raise RuntimeError('do not overwrite original receipt')
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(OUT), 'status': result['status'], 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
                  'profiles': [{'name': r['profile'], 'status': r['result']['status'],
                                'actual': r['result']['actual'], 'limit': r['result']['ratchet']} for r in records]},
                 ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'pass' else 1)
