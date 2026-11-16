"""Independent read-only review probes; writes results outside the reviewed tree."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/workspace/scratch/fe8de3b42084/adk')
OUT = Path('/workspace/scratch/fe8de3b42084/review')
SOURCE_PATHS = [
    'tests/test_skill_command_examples.py',
    'optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md',
    'tests/test_skill_imap_sender_methods.py',
    'tests/test_skill_content.sh',
]
CHANGE_DIRS = [
    'docs/changes/20261116-cmake-timeout-observation',
    'docs/changes/20261116-imap-exact-sender',
]


def bindings():
    paths = [ROOT / p for p in SOURCE_PATHS]
    paths.extend(p for name in CHANGE_DIRS for p in sorted((ROOT / name).rglob('*'))
                 if p.is_file())
    return [dict(path=p.relative_to(ROOT).as_posix(), bytes=len(data),
                 sha256=hashlib.sha256(data).hexdigest())
            for p in paths for data in [p.read_bytes()]]


def run(command):
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    return dict(command=command, exit_code=result.returncode,
                elapsed_seconds=time.monotonic() - started,
                stdout=result.stdout, stderr=result.stderr)


observations = dict(
    schema='adk-independent-source-review-observations/v1',
    reviewer='ai/root/root_prepare',
    started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    python=sys.version,
    recursion_limit=sys.getrecursionlimit(),
    source_before=bindings(),
)
observations['final_imap_tests'] = run([
    sys.executable, '-B', '-m', 'unittest', 'tests.test_skill_imap_sender_methods', '-v'])

sys.path.insert(0, str(ROOT))
from tests.test_skill_imap_sender_methods import select, header, TARGET

results = []
for depth in (100, 300, 600):
    raw = b'From: ' + b'(' * depth + b'comment' + b')' * depth + b' build@example.test\r\n\r\n'
    result = select([(1, header(TARGET)), (2, raw), (3, header(TARGET))])
    expected = [1, 2, 3] if depth < 600 else [1, 3]
    assert result['matched'] == expected
    assert result['status'] == ('pass' if depth < 600 else 'partial')
    if depth == 600:
        assert result['undecided'] == [{'uid': 2, 'reason': 'unparseable-from'}]
    results.append(dict(depth=depth, header_bytes=len(raw), result=result))
observations['independent_parser_closure_probe'] = results

record_path = ROOT / 'docs/changes/20261116-skill-observation-precision/review-evidence.json'
record = json.loads(record_path.read_text())
mismatches = []
for group in ('sources', 'evidence'):
    for reference in record[group]:
        base = ROOT if reference['base'] == 'repository' else record_path.parent
        actual = hashlib.sha256((base / reference['path']).read_bytes()).hexdigest()
        if actual != reference['sha256']:
            mismatches.append(dict(path=reference['path'], historical_sha256=reference['sha256'],
                                   current_sha256=actual))
observations['historical_review_relation'] = dict(
    original_target=record['target'],
    mismatches_against_current_source=mismatches,
    historical_directory_diff=run(['git', 'diff', '643bb1e93d118bb36c322094b4d1b70078ce78c5',
                                  '--', 'docs/changes/20261116-skill-observation-precision']),
)
observations['source_after'] = bindings()
observations['source_unchanged_during_probes'] = observations['source_before'] == observations['source_after']
observations['completed_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
assert observations['final_imap_tests']['exit_code'] == 0
assert observations['source_unchanged_during_probes']
output = OUT / 'source-review-observations.json'
output.write_text(json.dumps(observations, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(output=str(output), completed_at=observations['completed_at'],
                     imap_tests_exit=observations['final_imap_tests']['exit_code'],
                     parser_closure='pass', source_unchanged=observations['source_unchanged_during_probes']),
                 ensure_ascii=False))
