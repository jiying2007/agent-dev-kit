"""Offline command examples only; no models, devices, mailboxes or network."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml

REPO = Path('/workspace/scratch/771b38332ec2/agent-dev-kit')
OUT = Path(__file__).resolve().parent
WORK = Path(tempfile.mkdtemp(prefix='examples-', dir=OUT))
records = []


def run(name, argv, *, cwd=WORK, input=None, env=None, expected=0):
    result = subprocess.run(argv, cwd=cwd, input=input, capture_output=True,
                            text=True, env=env, timeout=30)
    records.append({'name': name, 'argv': argv, 'cwd': str(cwd),
                    'exit_code': result.returncode, 'stdout': result.stdout,
                    'stderr': result.stderr})
    if expected is not None:
        assert result.returncode == expected, records[-1]
    return result


def source(name):
    return (REPO / 'skills' / name / 'SKILL.md').read_text()


try:
    for name in ('old', 'new', 'include', 'tests', 'build', 'src'):
        (WORK / name).mkdir()
    old_header = 'struct payload { int value; int reserved; };\nint component_get(struct payload *p);\n'
    new_header = 'struct payload { int reserved; int value; };\nint component_get(struct payload *p);\n'
    for version, header in (('old', old_header), ('new', new_header)):
        (WORK / version / 'component.h').write_text(header)
    (WORK / 'provider.c').write_text('#include <component.h>\nint component_get(struct payload *p) { return p->value; }\n')
    consumer = '#include <component.h>\nint main(void) { struct payload p = {.value=7, .reserved=19}; return component_get(&p) == 7 ? 0 : 7; }\n'
    (WORK / 'tests/compat_v1.c').write_text(consumer)
    for version in ('old', 'new'):
        run('build-' + version, ['gcc', '-g', '-shared', '-fPIC', '-I', version,
                                'provider.c', '-o', version + '/libcomponent.so'])
    run('build-old-consumer', ['gcc', '-I', 'old', 'tests/compat_v1.c', '-L', 'old',
                              '-lcomponent', '-Wl,-rpath,$ORIGIN', '-o', 'old/consumer'])
    run('old-consumer-old-library', ['./old/consumer'])
    candidate_env = {**os.environ, 'LD_LIBRARY_PATH': str(WORK / 'new')}
    run('old-consumer-new-library', ['./old/consumer'], env=candidate_env, expected=7)
    symbols = []
    for version in ('old', 'new'):
        result = run('symbols-' + version, ['nm', '-D', '--defined-only', version + '/libcomponent.so'])
        symbols.append([line.split()[-1] for line in result.stdout.splitlines()])
    assert symbols[0] == symbols[1] == ['component_get'], symbols

    text = source('adk-component-api-stability')
    native = next(block for block in re.findall(r'```bash\n(.*?)\n```', text, re.S)
                  if 'gcc -I include/' in block)
    (WORK / 'include/component.h').write_text(new_header)
    shutil.copy2(WORK / 'new/libcomponent.so', WORK / 'libcomponent.so')
    env = {**os.environ, 'LD_LIBRARY_PATH': str(WORK)}
    run('native-source-example', ['bash'], input=native, env=env)
    shutil.copy2(WORK / 'old/consumer', WORK / 'compat_test_v1')
    wrapper = native[native.index('if ./compat_test_v1;'):]
    run('new-wrapper-propagates-seven', ['bash'], input=wrapper, env=env, expected=7)
    run('old-wrapper-hides-seven', ['bash', '-c', './compat_test_v1 && echo "ABI compatible" || echo "ABI broken"'], env=env)
    stale = native.replace('tests/compat_v1.c', 'tests/missing.c')
    result = run('compile-failure-stops-before-stale-executable', ['bash'], input=stale, env=env, expected=None)
    assert result.returncode != 0 and 'source compatibility case passed' not in result.stdout

    translation_unit = WORK / 'src/header consumer.c'
    header = WORK / 'src/sample.h'
    header.write_text('static inline int sample(void) { return 1; }\n')
    translation_unit.write_text('#include "sample.h"\nint main(void) { return sample(); }\n')
    run('header-baseline-compiles', ['gcc', '-fsyntax-only', str(translation_unit)])
    source_hash = hashlib.sha256(translation_unit.read_bytes()).hexdigest()
    header.write_text('#error deterministic-header-only-change\n')
    result = run('header-only-change-reaches-consumer', ['gcc', '-fsyntax-only', str(translation_unit)], expected=None)
    assert result.returncode != 0
    assert hashlib.sha256(translation_unit.read_bytes()).hexdigest() == source_hash
    row = {'directory': str(WORK), 'file': 'src/header consumer.c',
           'arguments': ['gcc', '-c', 'src/header consumer.c']}
    (WORK / 'build/compile_commands.json').write_text(json.dumps([row, row]))
    static = source('adk-static-analysis-c-cpp')
    yml = re.search(r'```yaml\n(.*?)\n```', static, re.S).group(1)
    pipeline = yaml.safe_load(yml)['static-analysis']['steps'][-1]['run']
    run('static-example-bash-syntax', ['bash', '-n'], input=pipeline)
    lines = pipeline.splitlines()
    begin = next(i for i, line in enumerate(lines) if line.startswith("python3 - <<'PY'"))
    end = lines.index('PY', begin + 1)
    enumerator = '\n'.join(lines[begin + 1:end])
    result = run('actual-tu-enumerator-header-only', ['python3', '-c', enumerator])
    assert result.stdout.split('\0') == [str(translation_unit), ''], repr(result.stdout)
    (WORK / 'build/compile_commands.json').write_text('[]')
    result = run('empty-tu-database-not-scanned', ['python3', '-c', enumerator], expected=None)
    assert result.returncode != 0 and 'not-scanned' in result.stderr

    for include_irq, expected in ((False, [3, 4, 4]), (True, [3, 4.5, 6.0])):
        values = [3]
        for _ in range(10):
            value = 3 + math.ceil(values[-1] / 4)
            if include_irq:
                value += math.ceil(values[-1] / 3) * 0.5
            values.append(value)
            if value == values[-2] or value > 5:
                break
        assert values == expected, values
        records.append({'name': 'rtos-response-time', 'include_irq': include_irq,
                        'iterations': values, 'deadline': 5, 'within_deadline': values[-1] <= 5})

    offline = source('adk-offline-core-dump-triage')
    batch = re.search(r'```bash\n(.*?)\n```', offline, re.S).group(1)
    run('core-batch-shell-syntax', ['bash', '-n'], input=batch)
    records.append({'name': 'scope', 'real_scanner_gdb_abidiff': 'not-run: tools unavailable',
                    'url_imap': 'not-run: no external account or fetch requested',
                    'performance_or_model_improvement': 'not-measured',
                    'note': 'TU enumeration and shell syntax are not scanner/GDB execution evidence'})
    print(json.dumps({'result': 'pass', 'checks': len(records), 'work': str(WORK),
                      'log': str(OUT / 'domain-example-results.json')}, ensure_ascii=False))
finally:
    (OUT / 'domain-example-results.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
