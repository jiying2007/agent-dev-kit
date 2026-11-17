"""Read-only audit of frozen source, execution records, and reversible wrappers."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import json
import subprocess

REPO = Path('/workspace/scratch/d417066aafa8/agent-dev-kit')
CHANGE = Path(__file__).resolve().parent.parent
EVIDENCE = CHANGE / 'evidence'
RTK = '/workspace/scratch/fe8de3b42084/verification-tools/rtk'
started = datetime.now(timezone.utc).isoformat()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    return subprocess.check_output([RTK, 'proxy', 'git', '-C', str(REPO), *args])

def unwrap(path):
    wrapper = json.loads(path.read_text())
    assert wrapper['encoding'] in {'utf-8', 'base64'}
    raw = (wrapper['content'].encode('utf-8') if wrapper['encoding'] == 'utf-8'
           else base64.b64decode(wrapper['content'], validate=True))
    assert len(raw) == wrapper['bytes'] and digest(raw) == wrapper['sha256'], str(path)
    return wrapper, raw

def original_json(path):
    return json.loads(unwrap(EVIDENCE / path)[1])

state_path = EVIDENCE / 'review-input-state.json'
state = json.loads(state_path.read_text())
head = '64d120ebcbc5d77fd90af99bac2bb9f4f3a13682'
tree = '35a666c2b4349b1890f5788241ac32bcf8080e38'
assert state['head_commit'] == head and state['tree'] == tree
assert git('rev-parse', 'HEAD').decode().strip() == head
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == tree
assert not git('status', '--porcelain', '--untracked-files=no').strip()
assert state['tracked_overlay'] == []
patch = git('diff', '--binary', state['base_commit'], head)
assert patch == (EVIDENCE / 'original.patch').read_bytes()
assert len(patch) == state['original_patch_bytes'] and digest(patch) == state['original_patch_sha256']
changed = git('diff', '--name-only', state['base_commit'], head).decode().splitlines()
assert set(changed) == set(state['product_sources']) and len(changed) == 10
for name, identity in state['product_sources'].items():
    raw = (REPO / name).read_bytes()
    assert raw == git('show', head + ':' + name)
    assert len(raw) == identity['bytes'] and digest(raw) == identity['sha256']
for entry in state['change_inputs']:
    raw = (CHANGE / entry['path']).read_bytes()
    assert len(raw) == entry['bytes'] and digest(raw) == entry['sha256'], entry['path']

indexes = []
wrapper_count = raw_bytes = 0
historical_origin_differences = []
for index_path in sorted(EVIDENCE.rglob('index.json')):
    index = json.loads(index_path.read_text())
    directory = Path(index['source_directory'])
    for entry in index['records']:
        path = index_path.parent / entry['path']
        assert digest(path.read_bytes()) == entry['wrapper_sha256']
        wrapper, raw = unwrap(path)
        assert digest(raw) == entry['raw_sha256'] and len(raw) == entry['raw_bytes']
        origin = directory / wrapper['origin']
        if origin.read_bytes() != raw:
            # These two snapshots intentionally precede normal verify formatting repairs.
            assert index_path.parent.name == 'verify-format-failure', str(origin)
            historical_origin_differences.append({'wrapper': str(path.relative_to(CHANGE)),
                'original_location': str(origin), 'retained_raw_sha256': digest(raw),
                'current_location_sha256': digest(origin.read_bytes()),
                'meaning': 'Historical failed-verify snapshot; origin is not a current-content identity claim'})
        wrapper_count += 1
        raw_bytes += len(raw)
    indexes.append({'path': str(index_path.relative_to(CHANGE)), 'sha256': digest(index_path.read_bytes()),
                    'wrappers': len(index['records'])})

before = original_json('full/source-before.json.json')
after = original_json('full/source-after.json.json')
assert before == after
assert before['head'] == head and before['tree'] == tree and before['tracked_status'] == ''
assert len(before['files']) == 1082
for name, identity in before['files'].items():
    raw = (REPO / name).read_bytes()
    assert digest(raw) == identity['sha256'] and len(raw) == identity['bytes'], name
stages = original_json('full/results.json.json')
assert len(stages) == 8 and all(s['exit_code'] == 0 for s in stages)
for stage in stages:
    assert digest(unwrap(EVIDENCE / 'full' / (stage['log'] + '.json'))[1]) == stage['log_sha256']
timing = original_json('full/full-timing.json.json')
assert timing['status'] == 'pass' and timing['total'] == timing['pass'] == len(timing['tests']) == 102
assert timing['fail'] == 0 and all(t['status'] == 'pass' for t in timing['tests'])
assert timing['elapsed_ms'] == 410588
summary = original_json('full/summary.json.json')
assert summary['head'] == head and summary['tree'] == tree and summary['changed_sources'] == []
assert summary['source_file_count'] == 1082 and summary['stages'] == stages
independent_index = original_json('independent/source-probe-index.json.json')
assert independent_index['count'] == 21 and independent_index['total_bytes'] == 88597
for entry in independent_index['files']:
    raw = unwrap(EVIDENCE / 'independent' / (entry['path'] + '.json'))[1]
    assert digest(raw) == entry['sha256'] and len(raw) == entry['bytes']

record = {'reviewer': 'ai/independent-review', 'started_at': started,
    'completed_at': datetime.now(timezone.utc).isoformat(), 'exit_code': 0, 'status': 'pass',
    'script_sha256': digest(Path(__file__).read_bytes()), 'head_commit': head, 'tree': tree,
    'original_patch_sha256': digest(patch), 'frozen_input_state_sha256': digest(state_path.read_bytes()),
    'product_files_bound_to_git_and_current_tree': len(changed),
    'frozen_change_inputs_verified': len(state['change_inputs']), 'tracked_overlay': [],
    'wrapper_indexes': indexes, 'wrapper_count': wrapper_count, 'decoded_raw_bytes': raw_bytes,
    'historical_origin_differences': historical_origin_differences,
    'full': {'stages_exit_zero': 8, 'tests_passed': 102, 'tests_failed': 0,
             'timing_elapsed_ms': timing['elapsed_ms'], 'process_elapsed_seconds': stages[-1]['elapsed_seconds'],
             'started_at': stages[-1]['started_at'], 'completed_at': stages[-1]['completed_at'],
             'source_before_after_equal': True, 'current_operational_files_equal': 1082},
    'independent_originals_verified': 21,
    'boundary': 'Artifact integrity and actual recorded execution reviewed; this audit does not rerun product tests or certify remote/release/runtime outcomes'}
target = EVIDENCE / 'independent-packaging-audit.json'
assert not target.exists()
target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
