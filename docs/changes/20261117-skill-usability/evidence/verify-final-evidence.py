"""Read-only final commit/evidence integrity checks; writes only reviewer evidence."""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
WORK = Path('/workspace/scratch/fe8de3b42084')
ROOT = WORK / 'adk-skill-usability'
OUT = WORK / 'skill-usability-review'
EVIDENCE = ROOT / 'docs/changes/20261117-skill-usability/evidence'
FINAL = EVIDENCE / 'final'
RTK = WORK / 'verification-tools/rtk'
BASE = '78c3be7f6f9b5ee2e557de54156532fb3169198d'
HEAD = 'a2b90b64d3ba83ac0c856ddb6a541450ead1bd36'
TREE = '53534d897a42e816525e310aa28134751ca5783f'
PATCH = '21dcecb8567e84e0bf3818185f3281827812d8d65dcf73a213e394578aeac414'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def git(*args, input_bytes=None):
    return subprocess.run(
        [str(RTK), 'bypass', 'git', '-c', 'core.fsmonitor=false',
         '-c', 'core.quotePath=false', '-C', str(ROOT), *args],
        input=input_bytes, capture_output=True, check=True,
    ).stdout


def commit_blobs(paths):
    paths = sorted(set(paths))
    data = git('cat-file', '--batch', input_bytes=''.join(
        HEAD + ':' + path + '\n' for path in paths).encode())
    position = 0
    result = {}
    for path in paths:
        end = data.index(b'\n', position)
        blob, kind, size_text = data[position:end].decode().split()
        assert kind == 'blob', (path, kind)
        size = int(size_text)
        content = data[end + 1:end + 1 + size]
        assert data[end + 1 + size:end + 2 + size] == b'\n'
        result[path] = {'git_blob': blob, 'sha256': digest(content), 'bytes': size}
        position = end + 2 + size
    assert position == len(data)
    return result


identity = git('show', '-s', '--format=%H%n%T%n%P', HEAD).decode().splitlines()
assert identity == [HEAD, TREE, BASE], identity
bindings = read_json(EVIDENCE / 'source-bindings.json')
snapshot = read_json(FINAL / 'tested-source-files.json')
changed = set(git('diff', '--name-only', BASE, HEAD).decode().splitlines())
assert changed == {item['path'] for item in bindings['files']}
assert len(changed) == 191 and len(snapshot) == 650
blobs = commit_blobs(changed | set(snapshot))
for item in bindings['files']:
    assert blobs[item['path']] == {key: item[key] for key in ('git_blob', 'sha256', 'bytes')}, item['path']
assert all(blobs[path]['sha256'] == sha for path, sha in snapshot.items())
current_changes = sorted(path for path, sha in snapshot.items()
                         if digest((ROOT / path).read_bytes()) != sha)
assert current_changes == ['.gitattributes'], current_changes
original_patch = (EVIDENCE / 'original.patch').read_bytes()
regenerated_patch = git('diff', '--no-ext-diff', '--no-textconv', BASE, HEAD)
assert regenerated_patch == original_patch and digest(original_patch) == PATCH

index = read_json(EVIDENCE / 'final-evidence-index.json')
assert index['source_commit'] == HEAD
for item in index['files']:
    assert digest((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
result = read_json(FINAL / 'full-regression-result.json')
timing = read_json(FINAL / 'full-regression-timing.json')
log = (FINAL / 'full-regression.log').read_bytes()
assert result['exit_code'] == 0
assert result['log_sha256'] == digest(log)
assert result['source_files_sha256'] == digest((FINAL / 'tested-source-files.json').read_bytes())
passes = re.findall(rb'^\[PASS\] ([^\r\n]+)$', log, re.MULTILINE)
assert len(passes) == len(set(passes)) == 102
assert not re.findall(rb'^\[FAIL\]', log, re.MULTILINE)
assert b'[SUMMARY] tests=102 pass=102 fail=0' in log
assert timing['status'] == 'pass' and timing['total'] == timing['pass'] == 102 and timing['fail'] == 0
assert len(timing['tests']) == 102 and all(item['status'] == 'pass' for item in timing['tests'])
assert {x.decode() for x in passes} == {x['name'] for x in timing['tests']}

quality = read_json(FINAL / 'quality-results.json')
reuse = read_json(FINAL / 'quality-reuse.json')
previous_dir = WORK / 'skill-usability-validation-final'
previous_bytes = (previous_dir / 'tested-source-files.json').read_bytes()
previous = json.loads(previous_bytes)
assert digest(previous_bytes) == reuse['previous_snapshot_sha256']
assert digest((FINAL / 'tested-source-files.json').read_bytes()) == reuse['current_snapshot_sha256']
changed_inputs = sorted(path for path in set(previous) | set(snapshot)
                        if previous.get(path) != snapshot.get(path))
assert changed_inputs == reuse['changed_since_previous']
assert changed_inputs == ['manifest.json', 'skills/adk-systematic-debugging/SKILL.md',
                          'tests/test_skill_trigger_matrix.py']
assert len(quality) == 9
for item in quality:
    assert item['exit_code'] == 0
    assert digest((FINAL / (item['name'] + '.log')).read_bytes()) == item['log_sha256']
    if item['evidence_origin'] == 'reused-unchanged-inputs':
        assert (FINAL / (item['name'] + '.log')).read_bytes() == (previous_dir / (item['name'] + '.log')).read_bytes()
fresh = [x['name'] for x in quality if x['evidence_origin'] == 'fresh-final-source']
reused = [x['name'] for x in quality if x['evidence_origin'] == 'reused-unchanged-inputs']
assert len(fresh) == 4 and len(reused) == 5
assert all(not path.startswith(('src/', 'tools/')) for path in changed_inputs)
assert previous['pyproject.toml'] == snapshot['pyproject.toml']

exports = []
all_skills = read_json(FINAL / 'all-skill-verification.json')
for target in ('claude-code', 'opencode'):
    inventory_path = FINAL / (target + '-export-inventory.json')
    inventory = read_json(inventory_path)
    export_dir = WORK / 'skill-usability-validation-release/all-skill-exports' / target
    entries = 0
    supports = 0
    for item in inventory['files']:
        data = (export_dir / item['path']).read_bytes()
        assert digest(data) == item['sha256'], (target, item['path'])
        if item['source'].endswith('/SKILL.md'):
            entries += 1
        else:
            supports += 1
            assert data == (ROOT / item['source']).read_bytes(), item['source']
    assert entries == 65 and supports == 54 and len(inventory['files']) == 119
    declaration = next(item for item in all_skills['exports'] if item['target'] == target)
    assert digest(inventory_path.read_bytes()) == declaration['export_inventory_sha256']
    exports.append({'target': target, 'entries': entries, 'support_files': supports,
                    'files': len(inventory['files']), 'inventory_sha256': digest(inventory_path.read_bytes()),
                    'actual_export_and_support_bytes_match': True})
assert len(all_skills['ratchets']) == 8 and all(x['status'] == 'pass' for x in all_skills['ratchets'])
assert all_skills['core'] == 56 and all_skills['optional'] == 9
tightest = min(all_skills['ratchets'], key=lambda x: x['ratchet']['potential_full_source_bytes'] - x['actual']['potential_full_source_bytes'])

after = read_json(OUT / 'ssh-regression-after.json')
assert after['passed'] and len(after['cases']) == 13
assert all(blobs[path]['sha256'] == sha for path, sha in after['files_sha256'].items())
linear = read_json(OUT / 'linear-helper-probes.json')
assert linear['passed'] and len(linear['regression_cases']) == 17
assert linear['kernel_sha256'] == blobs['src/agent_dev_kit/_matcher_kernel.py']['sha256']
postfix = read_json(OUT / 'postfix-probes.json')
for path in ('src/agent_dev_kit/intent_boundary.py', 'pyproject.toml'):
    assert postfix['candidate_files_sha256'][path] == digest((ROOT / path).read_bytes())

sys.path.insert(0, str(ROOT / 'src'))
from agent_dev_kit.intent_boundary import validate_task_package
observation_dir = EVIDENCE / 'consumer-observation'
observation = read_json(observation_dir / 'observation.json')
consumer_results = []
for item in observation['records']:
    for file in item['files']:
        assert digest((observation_dir / file['path']).read_bytes()) == file['sha256']
    errors = validate_task_package(read_json(observation_dir / str(item['consumer']) / 'task-package.json'))
    assert list(errors) == item['validator_errors']
    consumer_results.append({'consumer': item['consumer'], 'errors': list(errors), 'valid_v2_payload': not errors})
assert not observation['registered_ab_trial'] and not observation['native_runtime_qualification']

output = {
    'verified_at': datetime.now(timezone.utc).isoformat(),
    'source': {'base_commit': BASE, 'head_commit': HEAD, 'tree': TREE,
               'changed_files_verified': len(changed), 'tested_source_files_verified': len(snapshot),
               'original_patch_sha256': PATCH, 'original_patch_bytes': len(original_patch),
               'regenerated_patch_identical': True, 'post_source_snapshot_changes': current_changes},
    'final_evidence_index_files_verified': len(index['files']),
    'full_regression': {**result, 'suites': 102, 'passed': 102, 'failed': 0,
                        'independently_counted_log_records': len(passes)},
    'quality': {'fresh': fresh, 'reused': reused, 'all_log_hashes_verified': True,
                'changed_snapshot_inputs_since_previous': changed_inputs,
                'dependency_declaration_unchanged': True, 'reused_logs_identical': True},
    'exports': exports,
    'ratchets': {'passed': 8, 'tightest_profile': tightest['profile'],
                 'potential_full_source_bytes': tightest['actual']['potential_full_source_bytes'],
                 'potential_full_source_ceiling': tightest['ratchet']['potential_full_source_bytes']},
    'independent_final_routing': {'implicit_context_cases': 17, 'specific_vs_generic_owner_cases': 13,
                                 'final_file_hashes_match': True},
    'consumer_payload_revalidation': consumer_results,
    'mismatches': [],
}
(OUT / 'final-verification.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(output, ensure_ascii=False, indent=2))
