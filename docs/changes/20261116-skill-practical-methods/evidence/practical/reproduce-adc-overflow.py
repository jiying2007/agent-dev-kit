"""Read-only ADK baseline review: execute its published C fixture safely on host."""
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/workspace/scratch/2d6ca6dc3d38/agent-dev-kit')
OUT = Path(__file__).resolve().parent
BASE = '63e8f61ad9a023b4349851ebb4c9a6eca042a119'
CC = shutil.which('cc')
assert CC is not None


def run(command):
    started = datetime.now(UTC).isoformat()
    result = subprocess.run(command, cwd=OUT, capture_output=True, text=True)
    return dict(command=command, started_at=started,
                finished_at=datetime.now(UTC).isoformat(),
                exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)


sources = {}
for relative in ('examples/embedded-test-matrix/src/adc_scale.h',
                 'examples/embedded-test-matrix/src/adc_scale.c',
                 'examples/embedded-test-matrix/tests/test_adc_scale.c'):
    raw = subprocess.check_output(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT)
    (OUT / Path(relative).name).write_bytes(raw)
    sources[relative] = hashlib.sha256(raw).hexdigest()

harness = OUT / 'adc-boundaries.c'
assert harness.is_file(), 'Create the independent acceptance harness before running.'
flags = [CC, '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-I', str(OUT)]
steps = []
steps.append(run(flags + [str(OUT / 'adc_scale.c'), str(OUT / 'test_adc_scale.c'),
                          '-o', str(OUT / 'original-tests')]))
steps.append(run([str(OUT / 'original-tests')]))
steps.append(run(flags + [str(OUT / 'adc_scale.c'), str(harness),
                          '-o', str(OUT / 'boundary-tests')]))
steps.append(run([str(OUT / 'boundary-tests')]))
steps.append(run(flags + ['-fsanitize=signed-integer-overflow', '-fno-sanitize-recover=all',
                          str(OUT / 'adc_scale.c'), str(harness),
                          '-o', str(OUT / 'sanitized-boundary-tests')]))
steps.append(run([str(OUT / 'sanitized-boundary-tests')]))
record = dict(schema='adk-practical-baseline-observation/v1', source_commit=BASE,
              scope='Native host C fixture only; no MCU, CMake, external service or device execution',
              observed_at=datetime.now(UTC).isoformat(), source_sha256=sources,
              compiler=run([CC, '--version']),
              expectation='Valid full-scale raw equals the positive reference voltage regardless of ADC count width; no signed overflow.',
              steps=steps,
              cmake_available=shutil.which('cmake') is not None,
              ninja_available=shutil.which('ninja') is not None,
              model_calls_executed_by_script=0)
(OUT / 'adc-overflow-red.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
