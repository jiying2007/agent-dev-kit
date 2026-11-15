"""Independent read-only pre-freeze checks; all written evidence is scratch-only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone


ROOT = Path('/workspace/scratch/771b38332ec2/agent-dev-kit-next')
OUT = Path('/workspace/scratch/771b38332ec2/method-review-pre-freeze-checks.json')
CTEST = Path('/workspace/scratch/771b38332ec2/domain-audit-tools/cmake-wheel/cmake/data/bin/ctest')
SOURCE_PATHS = ('src/agent_dev_kit/planning_state.py', 'src/agent_dev_kit/goal_plan.py')


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


started = now()
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))
from agent_dev_kit import planning_state as new_state, goal_plan as new_goal

source_before = {name: digest((ROOT / name).read_bytes()) for name in SOURCE_PATHS}
baseline_commit = git('rev-parse', 'HEAD').decode().strip()
old_state = types.ModuleType('agent_dev_kit.planning_state_old')
old_state.__package__ = 'agent_dev_kit'
old_goal = types.ModuleType('agent_dev_kit.goal_plan_old')
old_goal.__package__ = 'agent_dev_kit'
baseline_hashes = {}
for module, name in ((old_state, SOURCE_PATHS[0]), (old_goal, SOURCE_PATHS[1])):
    raw = git('show', baseline_commit + ':' + name)
    baseline_hashes[name] = digest(raw)
    exec(compile(raw, name, 'exec'), module.__dict__)

base = {'schema_version': 'adk.current-state/v1', 'goal_ref': 'g', 'milestone': 'm',
        'evidence_refs': [], 'blockers': [], 'next_actions': ['next'], 'history_refs': []}
plan_path = ROOT / 'skills/adk-goal-authoring/references/goal-plan.json'
plan_raw = plan_path.read_bytes()
plan = json.loads(plan_raw)
values = [None, False, 0, '', 'x', {}, [], [None], [{}], [[]], [' '], ['a'],
          ['a', 'a'], ['x' + str(i) for i in range(4)], ['x' + str(i) for i in range(9)]]
cases = []
with tempfile.TemporaryDirectory(prefix='independent-frontier-') as temp:
    path = Path(temp) / 'state.json'
    for field in base:
        for value in values:
            state = dict(base)
            state[field] = value
            raw = json.dumps(state).encode()
            path.write_bytes(raw)
            old = old_state.check_current_state(path)
            new = new_state.check_current_state(path)
            old_plan = old_goal.check(plan, state)
            new_plan = new_goal.check(plan, state)
            assert path.read_bytes() == raw
            cases.append({'field': field, 'value': value, 'input_utf8': raw.decode(),
                          'input_sha256': digest(raw), 'old_state_check': old,
                          'new_state_check': new, 'old_goal_check': old_plan,
                          'new_goal_check': new_plan})

version = subprocess.run([str(CTEST), '--version'], capture_output=True, text=True, timeout=15)
ctest_document = ROOT / 'skills/adk-cmake-cross-build/SKILL.md'
command = next(line for line in ctest_document.read_text().splitlines()
               if line.startswith('ctest --test-dir build/<target> --output-on-failure'))
fixture = 'add_test(disabled_case "/bin/true")\nset_tests_properties(disabled_case PROPERTIES DISABLED TRUE)\n'
with tempfile.TemporaryDirectory(prefix='independent-ctest-') as temp:
    (Path(temp) / 'CTestTestfile.cmake').write_text(fixture)
    argv = [str(CTEST), *command.split()[1:]]
    argv[argv.index('build/<target>')] = temp
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15)

source_after = {name: digest((ROOT / name).read_bytes()) for name in SOURCE_PATHS}
assert source_before == source_after
differences = [c for c in cases if c['old_state_check'] != c['new_state_check']]
goal_differences = [c for c in cases if c['old_goal_check'] != c['new_goal_check']]
assert len(cases) == 105 and len(differences) == 8 and not goal_differences
assert all(c['old_state_check']['status'] == 'pass' and
           c['new_state_check']['status'] == 'fail' for c in differences)
assert version.returncode == 0 and result.returncode == 8

record = {
    'reviewer_id': 'ai/root/remote_source_review',
    'scope': 'pre-freeze targeted source and method checks; not final review or full-suite run',
    'started_at': started, 'completed_at': now(), 'baseline_commit': baseline_commit,
    'source_hashes_before': source_before, 'source_hashes_after': source_after,
    'source_unchanged_during_checks': True, 'baseline_source_hashes': baseline_hashes,
    'script_sha256': digest(Path(__file__).read_bytes()),
    'plan_input_sha256': digest(plan_raw), 'cases': cases,
    'summary': {'cases': 105, 'goal_behavior_differences': 0,
                'state_check_new_rejections': 8,
                'new_rejection_types': 'duplicate list entries and excess history/evidence/blocker entries'},
    'ctest': {'source_document': str(ctest_document.relative_to(ROOT)),
              'source_document_sha256': digest(ctest_document.read_bytes()),
              'extracted_source_command': command,
              'fixture_utf8': fixture, 'fixture_sha256': digest(fixture.encode()),
              'tool_path': str(CTEST), 'tool_sha256': digest(CTEST.read_bytes()),
              'version_exit_code': version.returncode, 'version_stdout': version.stdout,
              'version_stderr': version.stderr, 'actual_argv': argv,
              'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
    'limitations': [
        'Checks ran before source freeze. Preserve their actual timestamps and file hashes.',
        '105 cases exercise Python public functions with real bounded temporary-file reads; they are not 105 separate CLI tests.',
        'Goal baseline imports the unchanged valid_work_in_progress dependency from the current module.',
        'The isolated CTest case validates all-disabled rejection only; no device, board or runtime was used.',
        'No full regression suite or real model task was run by this reviewer.',
    ], 'status': 'pass',
}
OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(OUT), 'sha256': digest(OUT.read_bytes()),
                  'started_at': started, 'completed_at': record['completed_at'],
                  'source_hashes': source_before, 'summary': record['summary'],
                  'ctest_exit_code': result.returncode}, ensure_ascii=False, indent=2))
