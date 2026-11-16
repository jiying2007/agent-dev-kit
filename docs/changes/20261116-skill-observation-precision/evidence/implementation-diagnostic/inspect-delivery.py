"""Bind source-only checks to real exported bytes; do not generate consumer answers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from agent_dev_kit.model import Manifest
from agent_dev_kit.profile_context_footprint import enforce_profile_ratchet
from agent_dev_kit.versioning import version_identity_failures

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
BASE = 'fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9'
RTK = '/workspace/scratch/fe5385ca063a/verification-tools/rtk'
EXPORT = Path('/workspace/scratch/2d4d08f07657/other-skills-export-11.3.12/claude-code')
receipt = dict(baseline=BASE, commands=[], source_identities={}, profiles=[],
               runtime_initial_context_claim=False, hardware_qualification='not_evaluated')
destination = EVIDENCE / (sys.argv[1] + '.json')
if destination.exists():
    raise SystemExit('refusing to overwrite a prior delivery inspection')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*arguments):
    command = [RTK, 'bypass', 'git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *arguments]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=15)
    receipt['commands'].append(dict(argv=command, cwd=str(ROOT), exit_code=result.returncode,
                                     stdout=result.stdout.decode(), stderr=result.stderr.decode()))
    require(result.returncode == 0, 'source identity command failed')
    return result.stdout


try:
    require(git('rev-parse', 'HEAD').decode().strip() == BASE, 'unexpected source base')
    require(not version_identity_failures(ROOT), 'version projections disagree')
    manifest = Manifest.load(ROOT)
    require(manifest.data['version'] == '11.3.12', 'wrong candidate version')
    old_manifest = json.loads(git('show', BASE + ':manifest.json'))
    old_manifest['version'] = '11.3.12'
    require(old_manifest == manifest.data, 'manifest changed beyond version projection')
    receipt['registered_skill_identities'] = len(manifest.data['skills']) + len(manifest.data['optional_skills'])
    require(receipt['registered_skill_identities'] == 65, 'skill identity count changed')

    policy = 'manifests/profile_context_ratchets.json'
    require((ROOT / policy).read_bytes() == git('show', BASE + ':' + policy), 'profile thresholds changed')
    for profile in sorted(manifest.data['profiles']):
        result = enforce_profile_ratchet(manifest, profile)
        receipt['profiles'].append(result)
        require(result['status'] == 'pass', 'source budget failed: ' + profile)
    require(len(receipt['profiles']) == 8, 'profile count changed')

    prereg_path = 'tests/fixtures/skill_method_ab_prereg.json'
    prior = json.loads(git('show', BASE + ':' + prereg_path))
    candidate = json.loads((ROOT / prereg_path).read_text())
    require(candidate['candidate']['planned_release'] == 'v11.3.12', 'prereg identity is stale')
    history = candidate['unexecuted_candidate_history'].pop(0)
    require(history['planned_release'] == 'v11.3.11' and history['merged_main_sha'] == BASE
            and history['model_runs'] == 0, 'previous unexecuted identity was not retained')
    candidate['candidate']['planned_release'] = prior['candidate']['planned_release']
    require(candidate == prior, 'preregistered criteria changed')
    receipt['preregistered_criteria_unchanged'] = True

    imap_path = 'optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md'
    pre_bump = (ROOT / imap_path).read_bytes().replace(b'version: 1.0.4\n', b'version: 1.0.3\n', 1)
    pre_bump = pre_bump.replace(b'last_updated: 2026-11-16\n', b'last_updated: 2026-11-15\n', 1)
    require(sha(pre_bump) == '819382860f8d29999b71fe80721f9ffeaca26750621fa67d8358adc08ff188d5',
            'IMAP implementation changed after its author handed off')
    require((ROOT / 'skills/adk-fault-injection-recovery/SKILL.md').stat().st_size <= 3559,
            'fault skill exceeds its unchanged source limit')
    registration = (ROOT / 'tests/test_skill_content.sh').read_text()
    for module in ('tests.test_skill_fault_activation', 'tests.test_skill_imap_time_methods'):
        require(registration.count(module) == 1, 'module registration missing or duplicated')

    exported_manifest = json.loads((EXPORT / 'adk-export-manifest.json').read_text())
    require(exported_manifest['manifest_version'] == '11.3.12'
            and exported_manifest['target'] == 'claude-code', 'wrong export identity')
    require(exported_manifest['optional_skills'] == ['adk-email-imap-fetch'], 'optional selection changed')
    expected_files = {entry['path'] for entry in exported_manifest['files']}
    actual_files = {str(path.relative_to(EXPORT)) for path in EXPORT.rglob('*') if path.is_file()}
    require(actual_files == expected_files | {'adk-export-manifest.json'}, 'unexpected export files')
    for entry in exported_manifest['files']:
        require(sha((EXPORT / entry['path']).read_bytes()) == entry['sha256'], 'export digest mismatch')
    receipt['export_file_count'] = len(expected_files)
    receipt['exported_skills'] = []
    for name in ('adk-fault-injection-recovery', 'adk-email-imap-fetch'):
        entries = [entry for entry in exported_manifest['files']
                   if entry['name'] == name and entry['path'].endswith('/SKILL.md')]
        require(len(entries) == 1, 'missing or duplicate selected Skill in actual export')
        entry, = entries
        source = (ROOT / entry['source']).read_bytes()
        exported = (EXPORT / entry['path']).read_bytes()
        source_body = re.split(rb'(?m)^---\s*$', source, maxsplit=2)[2].strip()
        exported_body = re.split(rb'(?m)^---\s*$', exported, maxsplit=2)[2].strip()
        require(source_body == exported_body, 'export altered the Skill method body')
        retained = EVIDENCE / 'exported-consumer' / name / 'SKILL.md'
        retained.parent.mkdir(parents=True, exist_ok=True)
        require(not retained.exists(), 'consumer input already exists')
        shutil.copyfile(EXPORT / entry['path'], retained)
        receipt['exported_skills'].append(dict(name=name, source=entry['source'],
                                               source_sha256=sha(source), exported_sha256=sha(exported),
                                               retained=str(retained.relative_to(ROOT)), body_equal=True))
    shutil.copyfile(EXPORT / 'adk-export-manifest.json', EVIDENCE / 'adk-export-manifest.json')

    originals = {
        'fault-activation.c': '135434b9f3330715568aa61863bb50f89fe2eb1dee8a8613d156c12a182b3b94',
        'run-fault-activation.py': 'a7179a54ef8c5e4acb4d79274df5070a51923bd85ff1c9b09d52e8b340030baf',
        'fault-activation-results.json': '7c52d835e3effb0e3674ad6552b765a252f518dfdfa3781759324ca56d47a177',
    }
    audit_root = Path('/workspace/scratch/2d4d08f07657/other-skills-diagnostic-audit')
    for name, expected in originals.items():
        require(sha((audit_root / name).read_bytes()) == expected, 'original probe changed: ' + name)
    receipt['original_probe_preserved'] = originals
    changed = git('diff', '--no-ext-diff', '--name-only').decode().splitlines()
    changed += ['tests/test_skill_fault_activation.py', 'tests/fixtures/fault-activation.c',
                'tests/test_skill_imap_time_methods.py', 'tests/fixtures/imap-time-fixture.py']
    for name in sorted(set(changed)):
        data = (ROOT / name).read_bytes()
        receipt['source_identities'][name] = dict(bytes=len(data), sha256=sha(data))
    receipt['status'] = 'pass'
except BaseException as error:
    receipt['status'] = 'fail'
    receipt['error'] = repr(error)
    raise
finally:
    destination.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=receipt['status'], receipt=str(destination),
                      profiles=len(receipt['profiles']), exported=receipt.get('exported_skills', [])),
                 ensure_ascii=False))
