import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/workspace/scratch/fe5385ca063a/round3-cmake-consumer')
if ROOT.exists():
    raise RuntimeError('consumer fixture already exists')
SOURCE = ROOT / 'project'
(SOURCE / 'toolchains').mkdir(parents=True)
(ROOT / 'evidence').mkdir()
(SOURCE / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.21)
project(variant_demo C)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_executable(variant_demo main.c)
enable_testing()
add_test(NAME variant_smoke COMMAND variant_demo)
set_tests_properties(variant_smoke PROPERTIES PASS_REGULAR_EXPRESSION "build_variant=[0-9]+")
''')
(SOURCE / 'main.c').write_text('''#include <stdio.h>
int main(void) { printf("build_variant=%d\\n", BUILD_VARIANT); return 0; }
''')
for name, number in (('release-a', 101), ('release-b', 202)):
    (SOURCE / 'toolchains' / f'{name}.cmake').write_text(
        'set(CMAKE_C_COMPILER "/usr/bin/cc")\n'
        f'set(CMAKE_C_FLAGS_INIT "-DBUILD_VARIANT={number}")\n')
environment = dict(os.environ)
for name in ('CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'CMAKE_TOOLCHAIN_FILE', 'CMAKE_GENERATOR'):
    environment.pop(name, None)
commands = [
    ['cmake', '-S', str(SOURCE), '-B', str(SOURCE / 'out/default'), '-G', 'Ninja',
     '-DCMAKE_TOOLCHAIN_FILE=' + str(SOURCE / 'toolchains/release-a.cmake'), '-DCMAKE_BUILD_TYPE=Debug'],
    ['cmake', '--build', str(SOURCE / 'out/default'), '--parallel', '1', '--verbose'],
    ['ctest', '--test-dir', str(SOURCE / 'out/default'), '--output-on-failure'],
    [str(SOURCE / 'out/default/variant_demo')],
]
records = []
for command in commands:
    start = datetime.now(UTC).isoformat()
    run = subprocess.run(command, cwd=SOURCE, env=environment, text=True, capture_output=True, timeout=60)
    records.append({'argv': command, 'started_at': start, 'finished_at': datetime.now(UTC).isoformat(),
                    'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
    if run.returncode:
        raise RuntimeError(records[-1])
def manifest(directory):
    return [{'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for path in sorted(directory.rglob('*')) if path.is_file() for raw in [path.read_bytes()]]
result = {'schema': 'adk-consumer-fixture/v1', 'prepared_at': datetime.now(UTC).isoformat(),
          'records': records, 'project_files': manifest(SOURCE),
          'boundary': 'Host CMake fixture only; no architecture change or native runtime qualification.'}
(ROOT / 'fixture-before.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'fixture': str(ROOT), 'commands': len(records), 'files': len(result['project_files']),
                  'existing_program_stdout': records[-1]['stdout'],
                  'receipt_sha256': hashlib.sha256((ROOT / 'fixture-before.json').read_bytes()).hexdigest()}))
