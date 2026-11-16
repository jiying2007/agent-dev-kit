"""Read-only, bounded evidence packaging review. No product tests or writes."""
from __future__ import annotations

import base64
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/workspace/scratch/fe8de3b42084/adk')
SCRATCH = ROOT.parent
CHANGE = Path('docs/changes/20261116-cmake-timeout-observation')
BASE = '643bb1e93d118bb36c322094b4d1b70078ce78c5'
HEAD = 'fe5f908d821b8cf56db140d053134ae835127c57'
EXPECTED_NEW = {
    str(CHANGE / p) for p in (
        'completion-verification.md', 'review-evidence.json',
        'evidence/final-source-review.json', 'evidence/integration-bundle.json',
        'evidence/original.patch', 'evidence/prior-tool-transcripts.txt',
        'evidence/probe-review.py', 'evidence/source-bindings.json',
        'evidence/source-review-observations.json',
    )
}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), bytes=len(data), sha256=digest(data))


started = dt.datetime.now(dt.timezone.utc).isoformat()
status_before = git('status', '--porcelain').decode()
assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('diff') == b'' and git('diff', '--cached') == b''
new_paths = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
assert new_paths == EXPECTED_NEW
source_report = json.loads((SCRATCH / 'review/final-source-review.json').read_text())
assert len(source_report['sources']) == 14
bound_sources = []
for reference in source_report['sources']:
    path = ROOT / reference['path']
    data = path.read_bytes()
    assert digest(data) == reference['sha256']
    assert data == git('show', HEAD + ':' + reference['path'])
    bound_sources.append(fingerprint(path))

copied_reports = []
for name in ('final-source-review.json', 'source-review-observations.json',
             'prior-tool-transcripts.txt', 'probe-review.py'):
    current = ROOT / CHANGE / 'evidence' / name
    assert current.read_bytes() == (SCRATCH / 'review' / name).read_bytes()
    copied_reports.append(fingerprint(current))

envelope_path = ROOT / CHANGE / 'evidence/integration-bundle.json'
envelope = json.loads(envelope_path.read_text())
assert envelope['encoding'] == 'gzip+base64' and envelope['files'] == 13
assert 0 < envelope['gzip_bytes'] < 128_000
assert 0 < envelope['uncompressed_bytes'] < 1_000_000
compressed = base64.b64decode(envelope['data'], validate=True)
assert len(compressed) == envelope['gzip_bytes']
assert digest(compressed) == envelope['gzip_sha256']
with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
    raw = stream.read(envelope['uncompressed_bytes'] + 1)
assert len(raw) == envelope['uncompressed_bytes']
assert digest(raw) == envelope['uncompressed_sha256']
payload = json.loads(raw)
assert len(payload['files']) == 13
names = set()
bundle_items = []
for item in payload['files']:
    assert item['name'] not in names
    names.add(item['name'])
    name = Path(item['name'])
    assert not name.is_absolute() and '..' not in name.parts
    assert item['encoding'] == 'utf-8'
    data = item['text'].encode('utf-8')
    assert len(data) == item['bytes'] and digest(data) == item['sha256']
    original = SCRATCH / name
    matches_original = None
    if original.is_file():
        matches_original = data == original.read_bytes()
        assert matches_original
    bundle_items.append(dict(name=item['name'], bytes=len(data), sha256=digest(data),
                             original_scratch_file_compared=original.is_file(),
                             original_scratch_bytes_equal=matches_original))

original_patch = (ROOT / CHANGE / 'evidence/original.patch').read_bytes()
computed_patch = git('diff', '--binary', '--full-index', BASE, HEAD)
assert original_patch == computed_patch
bindings = json.loads((ROOT / CHANGE / 'evidence/source-bindings.json').read_text())
assert bindings['baseline'] == BASE and bindings['canonical_source'] == HEAD
assert bindings['tree'] == git('rev-parse', HEAD + '^{tree}').decode().strip()
assert bindings['patch_sha256'] == digest(computed_patch)
assert sorted(bindings['files'], key=lambda x: x['path']) == sorted(bound_sources, key=lambda x: x['path'])

sys.path.insert(0, str(ROOT / 'src'))
from agent_dev_kit.review_evidence import validate_review

validated = validate_review(ROOT, CHANGE / 'review-evidence.json',
                            expected_subject='20261116-cmake-timeout-observation',
                            expected_scope='source-change')
assert validated['status'] == 'pass'
assert validated['record_sha256'] == '24ebf332c21ca6bf18bfa7213120d05f8866b721c6d098aa9a08e2fe7e94f43f'
status_after = git('status', '--porcelain').decode()
assert status_before == status_after

report = dict(
    schema='adk-independent-packaging-review/v1',
    reviewer='ai/root/root_prepare',
    started_at=started,
    completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    status='pass', findings=[],
    source_commit=HEAD,
    source_tree=bindings['tree'],
    checks=dict(new_paths_exact_whitelist=True, added_files=9,
                original_14_source_files_unchanged=True, tracked_diff_empty=True,
                copied_reports_byte_identical=True, copied_reports=4,
                bundle_encoding_lengths_hashes=True, bundle_items_verified=13,
                original_patch_equals_full_index_binary_git_diff=True,
                source_bindings_match_all_14_files=True,
                formal_review_validator='pass', formal_review_reference_count=21,
                repository_status_unchanged=True),
    added_file_bindings=[fingerprint(ROOT / p) for p in sorted(new_paths)],
    source_bindings=bound_sources,
    copied_report_bindings=copied_reports,
    bundle_item_bindings=bundle_items,
    original_patch_sha256=digest(computed_patch),
    review_record_sha256=validated['record_sha256'],
    narrative_review={
        'completion_verification_fully_read': True,
        'future_ci_main_release_root_success_prefilled': False,
        'historical_timeouts_remain_unknown': True,
        'initial_cmake_skip_preserved': True,
        'test_owned_parser_defect_scope_preserved': True,
        'source_review_target_and_historical_binding_boundary_preserved': True,
        'source_stage_14_files_and_packaging_stage_9_files_separate': True,
    },
    limitations=[
        'No product tests were re-run. This operation checked evidence packaging only.',
        'The two CI log items were verified against envelope hashes and sizes; their decoded text is not claimed to be byte-identical to original GitHub binary log archives.',
        'Formal review reviewed_at retains the earlier source review timestamp. This separate packaging review records the later packaging observation time.',
        'Protected exact-head CI, main CI, immutable Release and Root delivery remain subsequent steps.',
        'No runtime, hardware/HIL, mailbox authentication/side-effect, M5 or Token/cost qualification is established.',
    ],
)
output = SCRATCH / 'review/packaging-review.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=report['status'], output=str(output), sha256=digest(output.read_bytes()),
                     completed_at=report['completed_at'], checks=report['checks']), ensure_ascii=False))
