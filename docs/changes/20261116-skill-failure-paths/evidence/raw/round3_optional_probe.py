"""Read-only ADK audit probes; all fixture writes are in scratch."""
from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
import re
import subprocess
import tempfile

BASE = Path('/workspace/scratch/fe5385ca063a')
ROOT = BASE / 'agent-dev-kit'
RTK = str(BASE / 'verification-tools/rtk')


def scan_probe() -> dict:
    sentinel = 'SYNTHETIC_ONLY_NOT_A_CREDENTIAL_8713'
    with nullcontext(tempfile.mkdtemp(prefix='optional-scan-probe-final-', dir=BASE)) as tmp:
        fixture = Path(tmp) / 'candidate.txt'
        fixture.write_text(
            f'curl -H "Authorization: Bearer {sentinel}" https://example.invalid\n'
            f'license_key = "{sentinel}"\n'
            f'open("output", "w").write("{sentinel}")\n'
            f'BASE_URL="https://user:{sentinel}@example.invalid"\n'
            f'api_key = "{sentinel}"\n'
        )
        no_match = Path(tmp) / 'ordinary.txt'
        no_match.write_text('ordinary neutral prose\n')
        sources = (
            'optional-skills/adk-security-supply-chain/SKILL.md',
            'docs/runbooks/security-supply-chain.md',
        )
        commands = [(path, lineno, line) for path in sources
                    for lineno, line in enumerate((ROOT / path).read_text().splitlines(), 1)
                    if line.startswith('rg ') and '<candidate_path>' in line]
        output = []
        for source, lineno, published in commands:
            command = published.replace('<candidate_path>', '"$1"')
            paths_only = command.replace('rg -n ', 'rg -l ')
            def run(code: str, path: Path):
                return subprocess.run([RTK, 'bash', '-c', 'set -euo pipefail\n' + code,
                                       'scan-probe', str(path)], capture_output=True,
                                      text=True, check=False, timeout=5)
            old = run(command, fixture)
            minimal = run(paths_only, fixture)
            empty = run(paths_only, no_match)
            error = run(paths_only, Path(tmp) / 'does-not-exist')
            output.append({
                'source': source,
                'line': lineno,
                'published_command': published,
                'baseline_exit_code': old.returncode,
                'baseline_stdout_contains_synthetic_secret': sentinel in old.stdout,
                'baseline_stderr_contains_synthetic_secret': sentinel in old.stderr,
                'paths_only_exit_code': minimal.returncode,
                'paths_only_stdout_contains_synthetic_secret': sentinel in minimal.stdout,
                'paths_only_stderr_contains_synthetic_secret': sentinel in minimal.stderr,
                'paths_only_preserves_candidate': str(fixture) in minimal.stdout,
                'no_match_exit_code': empty.returncode,
                'missing_path_error_exit_code': error.returncode,
                'missing_path_error_has_diagnostic': bool(error.stderr.strip()),
            })
        return {'fixture_only': True, 'real_credentials_read': False, 'fixture_directory': tmp, 'results': output}


def cancellation_probe() -> dict:
    path = ROOT / 'optional-skills/adk-test-flakiness-triage/references/details.md'
    text = path.read_text()
    function = re.search(r'```bash\n(run_flaky_samples\(\).*?)\n```', text, re.S).group(1)
    with nullcontext(tempfile.mkdtemp(prefix='optional-cancel-probe-final-', dir=BASE)) as tmp:
        cases = []
        programs = [(str(code), f'raise SystemExit({code})') for code in (0, 1, 9, 124, 130, 143)]
        programs.extend((('actual-sigint', 'import os,signal; os.kill(os.getpid(), signal.SIGINT)'),
                         ('actual-sigterm', 'import os,signal; os.kill(os.getpid(), signal.SIGTERM)')))
        for label, program in programs:
            evidence = str(Path(tmp) / f'exit-{label}')
            command = function + '\nrun_flaky_samples 3 "$1" "$2" python -c "$3"\n'
            proc = subprocess.run([RTK, 'bash', '-c', command, 'probe', evidence, RTK, program], capture_output=True, text=True, timeout=15, check=False)
            rows = (Path(evidence) / 'results.tsv').read_text().splitlines()[1:]
            (Path(evidence) / 'collector.stdout').write_text(proc.stdout)
            (Path(evidence) / 'collector.stderr').write_text(proc.stderr)
            cases.append({'child_case': label, 'collector_exit': proc.returncode,
                          'attempts_after_signal_or_failure': len(rows), 'result_rows': rows,
                          'raw_evidence_directory': evidence,
                          'collector_stdout': proc.stdout,
                          'later_run_directory_created': (Path(evidence) / 'run-2').exists()})
        return {'source': str(path.relative_to(ROOT)), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'requested_samples': 3, 'real_test_suite_run': False, 'user_keyboard_signal_simulated': False, 'cases': cases}


result = {'schema': 'round3-optional-probes/v1', 'secret_output': scan_probe(), 'sampling_cancellation': cancellation_probe()}
output = BASE / 'round3-optional-probes.json'
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
