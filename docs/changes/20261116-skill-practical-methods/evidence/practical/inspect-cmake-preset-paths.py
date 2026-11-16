#!/usr/bin/env python3
"""Freeze a source-command counterexample; this does not run or emulate CMake."""
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path('/workspace/scratch/2d6ca6dc3d38/agent-dev-kit')
OUT = Path(__file__).resolve().parent
BASE = '63e8f61ad9a023b4349851ebb4c9a6eca042a119'
SOURCE = 'skills/adk-cmake-cross-build/SKILL.md'
content = subprocess.check_output(['git', 'show', f'{BASE}:{SOURCE}'], cwd=ROOT)
text = content.decode()
section = text.split('## Commands\n', 1)[1].split('## Evidence Template', 1)[0]
project = OUT / 'cmake-preset-counterexample'
fixture = {
    'version': 3,
    'configurePresets': [{
        'name': 'demo-release', 'generator': 'Ninja',
        'binaryDir': '${sourceDir}/out/demo-release',
        'cacheVariables': {'CMAKE_BUILD_TYPE': 'Release'},
    }],
    'buildPresets': [{'name': 'demo-build', 'configurePreset': 'demo-release'}],
    'testPresets': [{'name': 'demo-test', 'configurePreset': 'demo-release'}],
}
expected = project / 'out' / 'demo-release'
commands = []
for line in section.splitlines():
    if line.startswith(('cmake ', 'ctest ', 'file ', 'arm-none-eabi-')):
        commands.append(line.split('  #', 1)[0].replace('<target>', 'demo')
                        .replace('<preset-name>', 'demo-release')
                        .replace('<resource-budget>', '1'))
build = shlex.split(next(c for c in commands if c.startswith('cmake --build ')))
test = shlex.split(next(c for c in commands if c.startswith('ctest ')))
build_path = project / build[build.index('--build') + 1]
test_path = project / test[test.index('--test-dir') + 1]
artifact = shlex.split(next(c for c in commands if c.startswith('file ')))[1]
result = {
    'schema': 'adk-practical-static-counterexample/v1',
    'source_commit': BASE, 'source_path': SOURCE,
    'source_sha256': hashlib.sha256(content).hexdigest(),
    'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'method': 'Resolve the documented command arguments against one official-schema preset; no CMake process, build, test, or tool shim is executed.',
    'fixture': fixture,
    'baseline_commands': commands,
    'expected_configured_binary_dir': str(expected),
    'actual_build_command_directory': str(build_path),
    'actual_test_command_directory': str(test_path),
    'actual_artifact_command_path': str(project / artifact),
    'build_uses_configured_directory': build_path == expected,
    'test_uses_configured_directory': test_path == expected,
    'cmake_available': shutil.which('cmake'),
    'ninja_available': shutil.which('ninja'),
    'execution_status': 'not-run: CMake and Ninja unavailable',
    'interpretation': 'Static path-contract counterexample only. Stale-directory build success or target execution is not claimed.',
    'official_source': 'https://cmake.org/cmake/help/v3.27/manual/cmake-presets.7.html',
    'model_calls_executed_by_script': 0,
}
(OUT / 'cmake-preset-static-red.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(0 if build_path == expected and test_path == expected else 1)
