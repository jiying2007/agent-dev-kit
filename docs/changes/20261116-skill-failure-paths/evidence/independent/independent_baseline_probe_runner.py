"""Independent read-only baseline review; writes only round3-independent-stage1/."""
from __future__ import annotations

import collections
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path('/workspace/scratch/fe5385ca063a')
REPO = ROOT / 'agent-dev-kit'
RTK = ROOT / 'verification-tools/rtk'
BASELINE = '80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b'
OUT = ROOT / 'round3-independent-stage1'
OUT.mkdir(exist_ok=False)
START = datetime.now(timezone.utc).isoformat()
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
       'PATH': str(ROOT / 'verification-tools') + os.pathsep + os.environ['PATH']}


def git(*args):
    return subprocess.check_output([str(RTK), 'bypass', 'git', '--no-optional-locks',
                                    '-C', str(REPO), *args], env=ENV)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def run(args, *, cwd=None, timeout=30):
    proc = subprocess.run([str(RTK), 'bypass', *map(str, args)], cwd=cwd, env=ENV,
                          text=True, capture_output=True, timeout=timeout)
    return {'argv': list(map(str, args)), 'exit_code': proc.returncode,
            'stdout': proc.stdout, 'stderr': proc.stderr}


def save(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return identity(path)


reports = {g: json.loads((ROOT / f'round3-{g}-audit.json').read_text())
           for g in ['core', 'embedded', 'optional', 'platform', 'portfolio']}
errors = []
population = {}
for row in git('ls-tree', '-rz', BASELINE, '--', 'skills', 'optional-skills').split(b'\0'):
    if not row:
        continue
    info, name = row.split(b'\t')
    mode, kind, blob = info.decode().split()
    population[name.decode()] = (mode, blob)

local = []
for group, key in [('core', 'files'), ('embedded', 'local_files'), ('optional', 'files')]:
    for record in reports[group][key]:
        path = record['path']
        raw = git('show', BASELINE + ':' + path)
        lines = raw.splitlines(keepends=True)
        actual = {'path': path, 'group': group, 'mode': population[path][0],
                  'git_blob': population[path][1], 'sha256': sha(raw),
                  'bytes': len(raw), 'lines': len(lines)}
        for field in ['git_blob', 'sha256', 'bytes', 'lines']:
            if record.get(field) != actual[field]:
                errors.append(['local_identity', group, path, field])
        if group == 'core':
            valid = any(r['range'] == f'all bytes; lines 1-{len(lines)}'
                        for r in record['reading'])
            declaration = record['reading']
        elif group == 'embedded':
            valid = record['read_status'] == 'full' and record['read_ranges'] == [{
                'line_start': 1, 'line_end_inclusive': len(lines),
                'byte_start': 0, 'byte_end_exclusive': len(raw)}]
            declaration = record['read_ranges']
        else:
            valid = (record['read_scope'] == 'full' and record['body_read_in_this_audit']
                     and record['read_ranges_inclusive'] == [[1, len(lines)]])
            declaration = record['read_ranges_inclusive']
        if not valid:
            errors.append(['inconsistent_read_declaration', group, path])
        actual['auditor_declared_read_ranges'] = declaration
        actual['independent_review_scope'] = 'full-byte identity verification; no independent full-content review claimed'
        local.append(actual)
local_names = [r['path'] for r in local]
if set(local_names) != set(population) or len(local_names) != len(set(local_names)):
    errors.append(['population_mismatch'])
portfolio = reports['portfolio']
portfolio_by_name = {r['path']: r for r in portfolio['files']}
for record in local:
    for field in ['group', 'mode', 'git_blob', 'sha256', 'bytes']:
        if portfolio_by_name.get(record['path'], {}).get(field) != record[field]:
            errors.append(['portfolio_identity', record['path'], field])
for record in portfolio['input_reports']:
    actual = identity(Path(record['path']))
    if any(record[k] != actual[k] for k in ['bytes', 'sha256']):
        errors.append(['input_identity', record['path']])
expected_skills = sorted(Path(p).parent.name for p in population if p.endswith('/SKILL.md'))
if sorted(r['skill'] for r in portfolio['decisions']) != expected_skills:
    errors.append(['decision_population'])

external = []
for record in portfolio['external_sources']:
    normalized = copy.deepcopy(record)
    for observed in normalized['observations']:
        raw = Path(observed['snapshot']).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if record['sha256'] != sha(raw) or record['bytes'] != len(raw):
            errors.append(['external_identity', observed['snapshot']])
        if record.get('local_git_blob') and record['local_git_blob'] != blob:
            errors.append(['external_blob', observed['snapshot']])
        if observed.get('provided_git_blob') and observed['provided_git_blob'] != blob:
            errors.append(['external_provided_blob', observed['snapshot']])
        lines = raw.splitlines(keepends=True)
        ranges = observed['read_ranges']
        if isinstance(ranges, list):
            for r in ranges:
                if isinstance(r, dict) and 'line_start' in r:
                    first, last = r['line_start'], r['line_end_inclusive']
                    if not (1 <= first <= last <= len(lines)):
                        errors.append(['external_line_range', observed['snapshot'], r])
                    if r.get('byte_start') != sum(map(len, lines[:first-1])) or r.get('byte_end_exclusive') != sum(map(len, lines[:last])):
                        errors.append(['external_byte_range', observed['snapshot'], r])
                elif isinstance(r, list):
                    first, last = r
                    if not (1 <= first <= last <= len(lines)):
                        errors.append(['external_line_range', observed['snapshot'], r])
        observed['independent_local_hash_verified'] = True
    normalized['independent_remote_tree_attestation'] = 'not-performed; local blob hashes alone do not attest remote membership'
    external.append(normalized)
source_inventory = save('audit-identity-verification.json', {
    'reviewer': '/root/round3_independent_review', 'baseline_commit': BASELINE,
    'baseline_tree': git('rev-parse', BASELINE + '^{tree}').decode().strip(),
    'inputs': [identity(ROOT / f'round3-{g}-audit.json') for g in reports],
    'counts': {'skills': len(expected_skills), 'files': len(local),
               'bytes': sum(r['bytes'] for r in local),
               'decisions': dict(collections.Counter(r['decision'] for r in portfolio['decisions']))},
    'errors': errors, 'local_files': local, 'external_sources': external,
    'reading_boundary': 'Declarations are internally coherent metadata, not replayed mental reading. Independent semantic review is separately listed.'})

# Isolated exact-baseline source allows real export without importing changing worktree code.
snapshot = OUT / 'baseline'
snapshot.mkdir()
with tarfile.open(fileobj=io.BytesIO(git('archive', BASELINE)), mode='r:') as tar:
    tar.extractall(snapshot, filter='data')

# F1: execute the exact published baseline rg commands, never any real credential.
scan_dir = OUT / 'scan'
scan_dir.mkdir()
sentinel = 'INDEPENDENT_SYNTHETIC_VALUE_54219'
candidate = scan_dir / 'candidate.txt'
candidate.write_text(f'curl https://example.invalid Authorization: {sentinel}\n'
                     f'license_key = {sentinel}\nopen("out").write("{sentinel}")\n'
                     f'BASE_URL={sentinel}\napi_key={sentinel}\n')
neutral = scan_dir / 'neutral.txt'
neutral.write_text('ordinary neutral prose\n')
scan_rows = []
for path in ['optional-skills/adk-security-supply-chain/SKILL.md', 'docs/runbooks/security-supply-chain.md']:
    for lineno, published in enumerate((snapshot / path).read_text().splitlines(), 1):
        if published.startswith('rg ') and '<candidate_path>' in published:
            command = 'set -euo pipefail\n' + published.replace('<candidate_path>', '"$1"')
            observation = run(['bash', '-c', command, 'independent-scan', candidate])
            scan_rows.append({'source': path, 'line': lineno, 'published_command': published,
                              'observation': observation,
                              'synthetic_value_leaked': sentinel in observation['stdout'] + observation['stderr']})
assert len(scan_rows) == 7 and sum(r['synthetic_value_leaked'] for r in scan_rows) == 6, scan_rows
scan_result = save('scan-original-failure.json', scan_rows)

# F2: exact baseline function, raw Bash and ordinary/self-signalled children.
function_source = 'optional-skills/adk-test-flakiness-triage/references/details.md'
function = re.search(r'```bash\n(run_flaky_samples\(\).*?)\n```',
                     (snapshot / function_source).read_text(), re.S).group(1)
cancel_rows = []
for label, code in [(str(n), f'raise SystemExit({n})') for n in [0, 1, 9, 124, 130, 143]] + [
    ('sigint', 'import os,signal;os.kill(os.getpid(),signal.SIGINT)'),
    ('sigterm', 'import os,signal;os.kill(os.getpid(),signal.SIGTERM)')]:
    directory = OUT / ('sampling-' + label)
    observation = run(['bash', '-c', function + '\nrun_flaky_samples 3 "$1" "$2" -c "$3"\n',
                       'independent-sampling', directory, sys.executable, code])
    rows = (directory / 'results.tsv').read_text().splitlines()[1:]
    cancel_rows.append({'case': label, 'observation': observation, 'rows': rows,
                        'run_2_exists': (directory / 'run-2').exists()})
    assert len(rows) == 3 and (directory / 'run-2').exists()
    assert observation['exit_code'] == (0 if label == '0' else 1)
cancel_result = save('sampling-original-failure.json', cancel_rows)

# F3: independent values and project; actual compiled output is the oracle.
cmake_dir = OUT / 'cmake'
(cmake_dir / 'src').mkdir(parents=True)
cmake = Path('/workspace/scratch/771b38332ec2/domain-audit-tools/cmake-wheel/cmake/data/bin/cmake')
ninja = ROOT / 'verification-tools/ninja'
(cmake_dir / 'src/CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(identity C)\nadd_executable(probe main.c)\n')
(cmake_dir / 'src/main.c').write_text('#include <stdio.h>\nint main(void){printf("%d\\n",REVIEW_BUILD_ID);return 0;}\n')
for name, compiler, value in [('a', '/usr/bin/gcc', 701), ('b', '/usr/bin/cc', 902)]:
    (cmake_dir / f'{name}.cmake').write_text(f'set(CMAKE_C_COMPILER {compiler})\nset(CMAKE_C_FLAGS_INIT "-DREVIEW_BUILD_ID={value}")\n')
cmake_rows = []
for label, build, toolchain, expected, clean in [
    ('fresh-a', 'reused', 'a', '701', False), ('same-a', 'reused', 'a', '701', False),
    ('changed-to-b', 'reused', 'b', '701', False), ('forced-rebuild-b', 'reused', 'b', '701', True),
    ('fresh-b', 'fresh-b', 'b', '902', False)]:
    directory = cmake_dir / build
    configured = run([cmake, '-S', cmake_dir / 'src', '-B', directory, '-G', 'Ninja',
                      f'-DCMAKE_MAKE_PROGRAM={ninja}', f'-DCMAKE_TOOLCHAIN_FILE={cmake_dir / (toolchain + ".cmake")}',
                      '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
    built = run([cmake, '--build', directory, '--parallel', '1', '--verbose', *(['--clean-first'] if clean else [])])
    executed = run([directory / 'probe'])
    assert configured['exit_code'] == built['exit_code'] == executed['exit_code'] == 0
    assert executed['stdout'].strip() == expected
    cache = (directory / 'CMakeCache.txt').read_text()
    system = next((directory / 'CMakeFiles').glob('*/CMakeSystem.cmake')).read_text()
    cmake_rows.append({'case': label, 'configure': configured, 'build': built, 'execute': executed,
                       'cache_toolchain': [l for l in cache.splitlines() if l.startswith('CMAKE_TOOLCHAIN_FILE:')],
                       'system_toolchain': [l for l in system.splitlines() if '.cmake' in l],
                       'compile_commands': json.loads((directory / 'compile_commands.json').read_text())})
cmake_result = save('cmake-original-failure.json', {'version': run([cmake, '--version']), 'cases': cmake_rows})

# F4: independent payload names, true validator; no ADK runtime behavior claim.
from jsonschema import Draft7Validator, Draft202012Validator
base = {'type': 'object', 'properties': {'revision': {'type': 'integer'}}, 'required': ['revision']}
extension = {'type': 'object', 'properties': {'mode': {'enum': ['safe', 'fast']}}, 'required': ['mode']}
modern = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
          'type': 'object', 'allOf': [base, extension], 'unevaluatedProperties': False}
broken = {'type': 'object', 'allOf': [{**base, 'additionalProperties': False}, extension]}
flat = {'type': 'object', 'properties': {**base['properties'], **extension['properties']},
        'required': ['revision', 'mode'], 'additionalProperties': False}
legacy = {**modern, '$schema': 'http://json-schema.org/draft-07/schema#'}
cases = [{'revision': 3, 'mode': 'safe'}, {'revision': 3, 'mode': 'safe', 'extra': True},
         {'mode': 'safe'}, {'revision': 3}, {'revision': '3', 'mode': 'safe'},
         {'revision': 3, 'mode': 'admin'}]
schema_rows = []
for name, validator, schema, expected in [
    ('closed-subschema', Draft202012Validator, broken, [False]*6),
    ('modern-composition', Draft202012Validator, modern, [True]+[False]*5),
    ('legacy-unsupported', Draft7Validator, legacy, [True, True]+[False]*4),
    ('same-level-modern', Draft202012Validator, flat, [True]+[False]*5),
    ('same-level-legacy', Draft7Validator, flat, [True]+[False]*5)]:
    validator.check_schema(schema)
    observed = [validator(schema).is_valid(c) for c in cases]
    assert observed == expected
    schema_rows.append({'case': name, 'validator': validator.__name__, 'schema': schema, 'accepted': observed})
schema_result = save('schema-original-failure.json', {'jsonschema_version': importlib.metadata.version('jsonschema'),
                      'payloads': cases, 'cases': schema_rows})

# F5: real export from the immutable baseline snapshot into reviewer-owned scratch.
sys.path.insert(0, str(snapshot / 'src'))
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest
checklist_rows = []
for target in ['claude-code', 'opencode']:
    exported = export_assets(Manifest.load(snapshot), target, OUT / 'exports', ['core'])
    consumer = Path(exported['output'])
    entry = next(p for p in consumer.rglob('SKILL.md') if p.parent.name == 'adk-parallel-agent-governance')
    package = entry.parent / 'references/parallel-worktree-task-package.md'
    checklist = entry.parent / 'references/subagent-review-checklist.md'
    assert 'subagent-review-checklist.md' in package.read_text()
    section = checklist.read_text().split('## Completion Review', 1)[1].split('## Rework Decision', 1)[0]
    rows = [[c.strip() for c in line.strip('|').split('|')] for line in section.splitlines()
            if line.startswith('|') and not line.startswith('| Check') and not line.startswith('|---')]
    assert len(rows) == 5 and all(row[1] == 'pass' and not row[2] for row in rows)
    checklist_rows.append({'target': target, 'rows': rows, 'checklist': identity(checklist),
                           'default_task_package_links_checklist': True})
checklist_result = save('checklist-original-failure.json', checklist_rows)

finished = datetime.now(timezone.utc).isoformat()
summary = {'schema': 'round3-independent-stage1-probes/v1', 'reviewer': '/root/round3_independent_review',
           'baseline_commit': BASELINE, 'started_at': START, 'completed_at': finished,
           'identity_errors': errors, 'five_original_failures_independently_reproduced': True,
           'evidence': [source_inventory, scan_result, cancel_result, cmake_result, schema_result, checklist_result],
           'boundaries': ['No repository/index/ref mutation or fixes.', 'Only reviewer-owned scratch files created.',
                          'Baseline identity coverage is not full semantic re-review of all 153 files.',
                          'No native runtime/model A/B, paid models, device or process-group cancellation evidence.',
                          'Current worktree implementation remains unfrozen and is not adjudicated by this report.']}
report = save('summary.json', summary)
print(json.dumps({'summary': report, 'counts': {'skills': len(expected_skills), 'files': len(local)},
                  'identity_errors': errors, 'five_original_failures_independently_reproduced': True,
                  'started_at': START, 'completed_at': finished}, ensure_ascii=False, indent=2))
