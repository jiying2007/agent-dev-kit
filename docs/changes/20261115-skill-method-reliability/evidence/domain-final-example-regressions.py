#!/usr/bin/env python3
"""Execute the final Skill examples against isolated, host-only fixtures.

The workflow inputs deliberately start at a synthetic verified state. They test
the public consumer's parsing, never qualify this source tree for release.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time

REPO = Path('/workspace/scratch/771b38332ec2/agent-dev-kit-next')
ROOT = Path(__file__).resolve().parent
TOOLS = ROOT.parent / 'domain-audit-tools'
CMAKE_BIN = TOOLS / 'cmake-wheel/cmake/data/bin'
WIRESHARK = TOOLS / 'wireshark-root'
KERNEL = TOOLS / 'linux-v6.12'
SOURCE_PATHS = [
    'skills/adk-cmake-cross-build/SKILL.md',
    'skills/adk-integration-hil-sil/SKILL.md',
    'skills/adk-protocol-stack-integration/SKILL.md',
    'skills/adk-hardware-debugging/SKILL.md',
    'skills/adk-artifact-gating/SKILL.md',
    'skills/adk-artifact-gating/references/details.md',
    'skills/adk-interface-contract-design/SKILL.md',
    'docs/runbooks/artifact-gated-delivery.md',
    'scripts/workflow.sh',
]
ROWS = []
CHECKS = []
BASE_ENV = os.environ.copy()
BASE_ENV['PATH'] = str(CMAKE_BIN) + os.pathsep + BASE_ENV['PATH']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label, argv, *, cwd=None, env=None, source=None):
    started = time.monotonic()
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env or BASE_ENV,
                            capture_output=True, text=True, timeout=30)
    row = {'label': label, 'argv': [str(x) for x in argv],
           'exit': result.returncode, 'stdout': result.stdout,
           'stderr': result.stderr, 'elapsed_seconds': time.monotonic() - started}
    if source:
        row['source'] = source
    ROWS.append(row)
    return row


def shell(label, command, *, cwd=None, env=None, source=None):
    return run(label, ['bash', '-euo', 'pipefail', '-c', command],
               cwd=cwd, env=env, source=source)


def require(label, condition, evidence, interpretation):
    CHECKS.append({'label': label, 'passed': bool(condition),
                   'evidence_labels': evidence, 'interpretation': interpretation})
    if not condition:
        raise AssertionError(label)


def command_from(path, prefix):
    lines = (REPO / path).read_text().splitlines()
    matches = [(i + 1, line.strip()) for i, line in enumerate(lines)
               if line.strip().startswith(prefix)]
    if not matches:
        raise AssertionError(f'missing documented command {path}: {prefix}')
    line, command = matches[0]
    return command, {'path': path, 'line': line, 'command': command}


def md_block(path, marker):
    text = (REPO / path).read_text()
    return next(block for block in re.findall(r'```md\n(.*?)```', text, re.S)
                if marker in block)


sources = {path: {'sha256': digest(REPO / path),
                  'bytes': (REPO / path).stat().st_size} for path in SOURCE_PATHS}
work = Path(tempfile.mkdtemp(prefix='domain-final-', dir=ROOT))
run('ctest-version', [CMAKE_BIN / 'ctest', '--version'])
run('gcc-version', ['gcc', '--version'])
run('addr2line-version', ['addr2line', '--version'])

# Actual minimal CMake project, including discovery, disabled and runtime skip.
project = work / 'cmake-project'
project.mkdir()
(project / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.20)
project(domain_fixture NONE)
enable_testing()
if(NOT DOMAIN_CASE STREQUAL "empty")
  if(DOMAIN_CASE STREQUAL "fail" OR DOMAIN_CASE STREQUAL "runtime-skip")
    add_test(NAME example COMMAND "${CMAKE_COMMAND}" -E false)
  else()
    add_test(NAME example COMMAND "${CMAKE_COMMAND}" -E true)
  endif()
  if(DOMAIN_CASE STREQUAL "disabled")
    set_tests_properties(example PROPERTIES DISABLED TRUE)
  elseif(DOMAIN_CASE STREQUAL "runtime-skip")
    set_tests_properties(example PROPERTIES SKIP_RETURN_CODE 1)
  endif()
endif()
''')
require('make-available', bool(shutil.which('make')), [], 'existing host generator only')
ctest_cases = {'empty': 8, 'disabled': 8, 'filtered': 8,
               'pass': 0, 'fail': 8, 'runtime-skip': 0}
builds = {}
for name in ctest_cases:
    build = work / 'ctest' / name
    builds[name] = build
    configured = run(f'configure-{name}', [CMAKE_BIN / 'cmake', '-S', project,
                     '-B', build, '-G', 'Unix Makefiles', f'-DDOMAIN_CASE={name}'])
    require(f'configure-{name}', configured['exit'] == 0, [configured['label']],
            'host-only project configuration')

for skill, placeholder in [('adk-cmake-cross-build', 'build/<target>'),
                           ('adk-integration-hil-sil', 'build/sil')]:
    path = f'skills/{skill}/SKILL.md'
    command, ref = command_from(path, 'ctest --test-dir')
    if '--show-only' in command:
        lines = (REPO / path).read_text().splitlines()
        line, command = next((i + 1, line.strip()) for i, line in enumerate(lines)
                             if line.startswith('ctest ') and '--output-on-failure' in line)
        ref = {'path': path, 'line': line, 'command': command}
    for name, expected in ctest_cases.items():
        resolved = command.replace(placeholder, shlex.quote(str(builds[name])))
        if name == 'filtered':
            resolved += " -R '^not-a-test$'"
        row = shell(f'{skill}-{name}', resolved, cwd=work, source=ref)
        require(f'{skill}-{name}', row['exit'] == expected, [row['label']],
                'runtime skip remains not-run, not a test pass' if name == 'runtime-skip'
                else 'zero runnable tests fail; real pass/fail preserved')
        if name == 'runtime-skip':
            require(f'{skill}-skip-visible', 'Skipped' in row['stdout'], [row['label']],
                    'exit 0 does not turn skip into executed assertions')

discovery, discovery_ref = command_from('skills/adk-integration-hil-sil/SKILL.md',
                                       'ctest --test-dir build/sil --show-only')
discovered = shell('hil-sil-discovery', discovery.replace('build/sil', shlex.quote(str(builds['pass']))),
                   source=discovery_ref)
require('discovery-real-test', discovered['exit'] == 0 and
        len(json.loads(discovered['stdout'])['tests']) == 1,
        [discovered['label']], 'discovery sees one actual registered host test')

# Real TShark, reading self-authored captures only. No live capture invocation.
wireshark_env = BASE_ENV.copy()
wireshark_env['PATH'] = str(WIRESHARK / 'usr/bin') + os.pathsep + wireshark_env['PATH']
wireshark_env['LD_LIBRARY_PATH'] = str(WIRESHARK / 'usr/lib/x86_64-linux-gnu')
wireshark_env['WIRESHARK_DATA_DIR'] = str(WIRESHARK / 'usr/share/wireshark')
wireshark_env['WIRESHARK_CONFIG_DIR'] = str(work / 'wireshark-config')
run('tshark-version', [WIRESHARK / 'usr/bin/tshark', '--version'], env=wireshark_env)
valid_bytes = (ROOT / 'one-packet.pcap').read_bytes()
pcaps = {
    'valid-udp': (valid_bytes, 'udp', 0, 1),
    'malformed': (b'not a pcap\n', 'udp', 3, 0),
    'zero-byte': (b'', 'udp', 0, 0),
    'valid-zero-packet': (valid_bytes[:24], 'udp', 0, 0),
    'zero-filter-match': (valid_bytes, 'tcp', 0, 0),
}
pcap_command, pcap_ref = command_from('skills/adk-protocol-stack-integration/SKILL.md',
                                    'tshark -n -r')
for name, (content, display_filter, expected_exit, expected_frames) in pcaps.items():
    capture = work / f'{name} capture.pcap'
    capture.write_bytes(content)
    env = wireshark_env | {'PCAP': str(capture), 'DISPLAY_FILTER': display_filter}
    row = shell(f'pcap-{name}', pcap_command, cwd=work, env=env, source=pcap_ref)
    frames = len(re.findall(r'^\s*\d+\s+\d', row['stdout'], re.M))
    row['matched_frames'] = frames
    row['input_sha256'] = digest(capture)
    observation = ('read-error' if expected_exit else
                   'evidence-present' if expected_frames else 'partial-no-target-evidence')
    require(f'pcap-{name}', row['exit'] == expected_exit and frames == expected_frames,
            [row['label']], observation + '; not protocol integration qualification')

# Runtime PC, corrected link address, and function-offset helpers on host PIE.
source = ROOT / 'relocation.c'
binary = work / 'relocation'
compiled = run('pie-build', ['gcc', '-g', '-O0', '-fPIE', '-pie', source,
                           '-ldl', '-o', binary])
require('pie-build', compiled['exit'] == 0, [compiled['label']], 'host PIE only')
addresses = run('pie-runtime-addresses', [binary])
runtime_pc, base = [int(value, 16) for value in addresses['stdout'].split()]
addr_command, addr_ref = command_from('skills/adk-hardware-debugging/SKILL.md',
                                     '"$target_addr2line"')
symbol_env = BASE_ENV.copy()
symbol_env.pop('CROSS_COMPILE', None)
symbol_env.pop('LLVM', None)
symbol_env.update({'target_addr2line': shutil.which('addr2line'),
                   'matched_elf': str(binary), 'pc_link': hex(runtime_pc)})
wrong_address = shell('pie-raw-runtime-pc', addr_command, env=symbol_env, source=addr_ref)
require('raw-pc-not-resolved', wrong_address['exit'] == 0 and '??:0' in wrong_address['stdout'],
        [wrong_address['label']], 'raw runtime address is not a valid link address')
symbol_env['pc_link'] = hex(runtime_pc - base)
resolved = shell('pie-corrected-link-pc', addr_command, env=symbol_env, source=addr_ref)
require('corrected-pc-resolved', resolved['exit'] == 0 and 'relocation.c:7' in resolved['stdout'],
        [resolved['label']], 'actual dladdr base; not a KASLR kernel or MCU test')
helper, helper_ref = command_from('skills/adk-hardware-debugging/SKILL.md',
                                 '"$kernel_src/scripts/faddr2line"')
symbol_env.update({'kernel_src': str(KERNEL), 'function_offset': 'marked_function+0x0'})
decoded = shell('function-offset-helper', helper, env=symbol_env, source=helper_ref)
require('function-offset-resolved', decoded['exit'] == 0 and 'relocation.c:7' in decoded['stdout'],
        [decoded['label']], 'Linux v6.12 helper on host ELF, not a target kernel qualification')

# Final template consumption by the existing public workflow review command.
artifact_path = 'skills/adk-artifact-gating/references/details.md'
template = md_block(artifact_path, '[artifact:ImplementationPlan]')
for tag, fields in {'ImplementationPlan': {'status', 'owner', 'scope', 'handoff_to'},
                    'ReviewReport': {'status', 'owner', 'verdict', 'findings'},
                    'TestReport': {'status', 'owner', 'tests_run'}}.items():
    block = template.split(f'[artifact:{tag}]', 1)[1].split('[artifact:', 1)[0]
    actual = set(re.findall(r'^([a-z_]+):', block, re.M))
    require(f'template-fields-{tag}', fields <= actual, [], 'declared template fields exist; not runtime enforcement')
replacements = {'<agent>': 'fixture-planner', '<范围>': 'host-only synthetic consumer fixture',
                '<next-owner>': 'fixture-receiver', '<reviewer>': 'fixture-reviewer',
                '<finding or none>': 'none in this synthetic fixture', '<test-owner>': 'fixture-tester',
                '<command + result>': f'ctest --test-dir {builds["pass"]} --output-on-failure --no-tests=error; exit 0; host fixture only'}
for old, new in replacements.items():
    template = template.replace(old, new)
workflow_root = work / 'workflow-fixtures'
workflow_cases = {
    'pass': ('verified', template, 'pass', 0),
    'old-approved': ('verified', template.replace('status: PASS', 'status: approved'), 'pass', 1),
    'test-blocked': ('verified', template.replace('[artifact:TestReport]\nstatus: PASS',
                      '[artifact:TestReport]\nstatus: BLOCKED'), 'pass', 1),
    'conflicting-result': ('verified', template, 'needs-fix', 1),
    'not-verified': ('applied', template, 'pass', 1),
}
for name, (stage, content, result, expected) in workflow_cases.items():
    change = workflow_root / name
    change.mkdir(parents=True)
    (change / 'state.yaml').write_text(f'stage: {stage}\nowner: synthetic-fixture\n')
    (change / 'design.md').write_text(content)
    row = run(f'workflow-{name}', ['bash', REPO / 'scripts/workflow.sh', 'review',
              '--change', name, '--root', workflow_root, '--result', result,
              '--blockers', '0', '--majors', '0', '--minors', '0'], cwd=work,
              source={'path': artifact_path, 'template': 'minimal artifact tags'})
    require(f'workflow-{name}', row['exit'] == expected, [row['label']],
            'isolated verified-state consumer fixture; never source release qualification')

# Multi-file lexical candidates, using the exact final documented pipeline.
scan, scan_ref = command_from('skills/adk-interface-contract-design/SKILL.md',
                             'rg --no-filename -o')
scan_cases = {
    'cross-file-duplicate': ({'a.h': 'enum { ERR_A = -7 };\n', 'b.h': 'enum { ERR_B = -7 };\n'}, '= -7\n'),
    'unique': ({'a.h': 'enum { ERR_A = -7 };\n', 'b.h': 'enum { ERR_B = -8 };\n'}, ''),
    'symbolic-uncovered': ({'a.h': '#define ERR_BASE (-7)\nenum { ERR_A = ERR_BASE };\n',
                            'b.h': 'enum { ERR_B = -(1+6) };\n'}, ''),
}
for name, (files, expected) in scan_cases.items():
    case = work / 'interface' / name
    include = case / 'include'
    include.mkdir(parents=True)
    for filename, content in files.items():
        (include / filename).write_text(content)
    row = shell(f'interface-{name}', scan, cwd=case, source=scan_ref)
    require(f'interface-{name}', row['stdout'] == expected and row['exit'] in (0, 1),
            [row['label']], 'lexical candidate only; symbolic/namespace conflicts require separate analysis')

require('source-stable', all(digest(REPO / path) == value['sha256'] for path, value in sources.items()),
        [], 'source excerpts did not change during this run')
report = {'scope': 'real tools on isolated host fixtures; no live capture, kernel, MCU, HIL or model evaluation',
          'fixture_root': str(work), 'source_files': sources,
          'external_helper': {'url': 'https://raw.githubusercontent.com/torvalds/linux/v6.12/scripts/faddr2line',
                              'sha256': digest(KERNEL / 'scripts/faddr2line')},
          'independent_capture_flow_receipt': str(ROOT.parent / 'protocol-capture-flow-review.json'),
          'rows': ROWS, 'checks': CHECKS,
          'passed': sum(check['passed'] for check in CHECKS), 'total': len(CHECKS)}
output = ROOT / 'final-example-results.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'total': report['total'],
                  'report': str(output), 'fixtures': str(work)}, ensure_ascii=False))
