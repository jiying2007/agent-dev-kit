import collections
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

WORK = Path('/workspace/scratch/fe5385ca063a')
ROOT = WORK / 'agent-dev-kit'
BASE = '80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b'
OUT = WORK / 'round3-portfolio-audit.json'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


reports = {}
inputs = []
for group in ('core', 'embedded', 'optional', 'platform'):
    path = WORK / f'round3-{group}-audit.json'
    raw = path.read_bytes()
    report = json.loads(raw)
    require(report.get('baseline_commit', report.get('baseline', {}).get('sha')) == BASE,
            f'wrong baseline: {group}')
    reports[group] = report
    inputs.append({'group': group, 'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)})

tracked = {}
for entry in git('ls-tree', '-rz', BASE, '--', 'skills', 'optional-skills').split(b'\0'):
    if not entry:
        continue
    identity, name = entry.split(b'\t', 1)
    mode, kind, blob = identity.decode().split()
    require(kind == 'blob', 'unexpected non-blob skill asset')
    tracked[name.decode()] = {'mode': mode, 'git_blob': blob}

files = []
decisions = []
groups = []
for group in ('core', 'embedded', 'optional'):
    report = reports[group]
    rows = report.get('files', report.get('local_files'))
    group_decisions = report.get('decisions', report.get('skills'))
    for row in rows:
        path = row['path']
        require(path in tracked, f'unknown audit file {path}')
        raw = git('show', f'{BASE}:{path}')
        require(row['git_blob'] == tracked[path]['git_blob'], f'blob mismatch {path}')
        require(row['sha256'] == sha(raw) and row['bytes'] == len(raw), f'byte mismatch {path}')
        if group == 'core':
            require(any('all bytes' in str(r.get('range', '')) for r in row['reading']), f'not full: {path}')
        elif group == 'embedded':
            require(row['read_status'] == 'full', f'not full: {path}')
        else:
            require(row['read_scope'] == 'full' and row['body_read_in_this_audit'], f'not full: {path}')
        files.append({'path': path, 'group': group, **tracked[path], 'sha256': sha(raw),
                      'bytes': len(raw), 'declared_read_scope': 'full', 'baseline_bytes_reverified': True})
    for row in group_decisions:
        decisions.append({'group': group, **row})
    groups.append({'group': group, 'skills': len(group_decisions), 'files': len(rows),
                   'bytes': sum(r['bytes'] for r in rows),
                   'decisions': dict(collections.Counter(r['decision'] for r in group_decisions))})

paths = [r['path'] for r in files]
require(len(paths) == len(set(paths)), 'duplicate local file coverage')
require(set(paths) == set(tracked), 'incomplete local file population')
skill_names = {Path(path).parent.name for path in tracked if path.endswith('/SKILL.md')}
decision_names = [r['skill'] for r in decisions]
require(len(decision_names) == len(set(decision_names)), 'duplicate skill decision')
require(set(decision_names) == skill_names, 'incomplete decision population')
require(len(skill_names) == 65 and len(files) == 153 and sum(r['bytes'] for r in files) == 422088,
        'baseline inventory changed unexpectedly')

external = {}
unavailable = []
retrieval_records = 0
for group, key in (('core', 'external_sources'), ('embedded', 'external_sources'),
                   ('optional', 'upstream_sources'), ('platform', 'records')):
    for row in reports[group][key]:
        if row.get('status') == 'unavailable':
            unavailable.append({'group': group, **row})
            continue
        retrieval_records += 1
        repo = row.get('repository', row.get('repo'))
        commit = row.get('commit')
        path = row.get('file') if group == 'optional' else row['path']
        url = row['url']
        if group == 'core':
            snapshot = Path(row['local_snapshot'])
            reading = row['reading']
            scope = 'full' if any('all bytes' in str(r.get('range', '')) for r in reading) else 'partial'
        elif group == 'embedded':
            snapshot = Path(row['snapshot'])
            reading = row['read_ranges']
            scope = row['read_status']
        elif group == 'optional':
            snapshot = Path(row['path'])
            reading = row.get('read_ranges_inclusive')
            scope = 'full' if row['read_scope'] in ('full', 'full-html-text') else 'partial'
        else:
            snapshot = WORK / 'round3-platform-upstream-raw' / row['raw_file']
            reading = row['scope']
            scope = 'full' if row['scope'] == 'full' else 'partial'
        raw = snapshot.read_bytes()
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'], f'upstream byte mismatch: {url}')
        local_git_blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        if row.get('git_blob'):
            require(local_git_blob == row['git_blob'], f'upstream blob mismatch: {url}')
        identity = (repo, commit, path) if repo else (None, None, url)
        item = external.setdefault(identity, {
            'repository': repo, 'commit': commit, 'path': path, 'url': url,
            'sha256': sha(raw), 'bytes': len(raw), 'local_git_blob': local_git_blob if repo else None,
            'read_scope': scope, 'observations': [],
        })
        require(item['sha256'] == sha(raw), f'divergent source snapshots: {identity}')
        if scope == 'full':
            item['read_scope'] = 'full'
        item['observations'].append({'group': group, 'read_scope': scope, 'read_ranges': reading,
                                     'snapshot': str(snapshot), 'snapshot_sha256_reverified': True,
                                     'provided_git_blob': row.get('git_blob')})

external_rows = sorted(external.values(), key=lambda r: (r['repository'] or '', r['path'] or '', r['url']))
counts = collections.Counter(r['decision'] for r in decisions)
result = {
    'schema': 'adk-skill-portfolio-audit/v3', 'baseline_commit': BASE,
    'verified_at': datetime.now(UTC).isoformat(), 'input_reports': inputs,
    'population': {'skills': len(skill_names), 'files': len(files), 'bytes': sum(r['bytes'] for r in files),
                   'exact_baseline_file_match': True, 'exact_skill_decision_match': True,
                   'duplicate_paths': [], 'missing_paths': [], 'all_baseline_bytes_reverified': True},
    'groups': groups, 'decision_counts': dict(counts),
    'files': sorted(files, key=lambda r: r['path']),
    'decisions': sorted(decisions, key=lambda r: r['skill']),
    'external_summary': {
        'successful_retrieval_records': retrieval_records, 'unique_source_files_or_pages': len(external_rows),
        'unique_pinned_repositories': len({r['repository'] for r in external_rows if r['repository']}),
        'unique_pinned_repository_files': sum(bool(r['repository']) for r in external_rows),
        'unique_official_web_pages': sum(not bool(r['repository']) for r in external_rows),
        'read_scope_counts': dict(collections.Counter(r['read_scope'] for r in external_rows)),
        'unique_snapshot_bytes': sum(r['bytes'] for r in external_rows),
        'deduplication': 'repository + commit + repository path, or official web URL; identical bytes required',
        'unavailable_attempts': len(unavailable),
    },
    'external_sources': external_rows, 'unavailable_sources': unavailable,
    'boundaries': [
        'All local file read scopes are auditor declarations; this consolidation independently verifies baseline identities, bytes and complete disjoint coverage, not a replay of human/model reading.',
        'Upstream full versus excerpt reading is preserved. A full-body hash does not imply full reading. Optional repository downloads were pinned URLs with local hashes, not independently re-attested remote Git tree identities by this consolidator.',
        'Web discovery is a broad selected survey, not an exhaustive enumeration or installation of all Skills on the internet. Existing keep decisions are retained methods, not measured improvements.',
        'No upstream source text is imported here; this is provenance and methodological review metadata. Source URLs and hashes support re-fetch; scratch paths describe the actual session.',
        'No native runtime loading, controlled model A/B, paid models, device/HIL/field qualification or token/cost improvement is established.',
    ],
}
require(not OUT.exists(), 'do not overwrite prior consolidation receipt')
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(OUT), 'sha256': sha(OUT.read_bytes()),
                  'population': result['population'], 'groups': groups,
                  'decision_counts': dict(counts), 'external_summary': result['external_summary']},
                 ensure_ascii=False, indent=2))
