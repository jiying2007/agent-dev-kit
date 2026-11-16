import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path('/workspace/scratch/2d6ca6dc3d38/agent-dev-kit')
BASELINE = '907080d5a0f6e49daa93e217f60383b23ed89d37'
def read(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT, text=True)

with tempfile.TemporaryDirectory() as name:
    root = Path(name)
    source = root / 'source'
    source.mkdir()
    (source / 'Makefile').write_text('.PHONY: all defconfig\nall defconfig:\n\t@printf "target=%s arch=%s cross=%s flags=%s out=%s\\n" "$@" "$(ARCH)" "$(CROSS_COMPILE)" "$(MAKEFLAGS)" "$(O)"\n')
    text = read('skills/adk-bsp-porting-playbook/SKILL.md')
    example = re.search(r'```bash\n(.*?)```', text, re.S).group(1).split('\ndtc ')[0]
    result = subprocess.run(['bash', '-c', example], cwd=source, text=True, capture_output=True,
                            env=dict(os.environ, ARCH='arm', CROSS_COMPILE='arm-linux-gnueabihf-',
                                     BSP_ARCH='arm', BSP_CROSS_COMPILE='arm-linux-gnueabihf-',
                                     BSP_BUILD_JOBS='2', BSP_DEFCONFIG='board_defconfig'), timeout=15)
    bsp = {'command_exit_code': result.returncode, 'expected_arch': 'arm',
           'expected_toolchain': 'arm-linux-gnueabihf-', 'expected_jobs': 2,
           'expected_defconfig': 'board_defconfig', 'actual_stdout': result.stdout,
           'acceptance_passed': 'arch=arm ' in result.stdout and 'cross=arm-linux-gnueabihf-' in result.stdout}
    text = read('skills/adk-interface-contract-design/SKILL.md')
    example = re.search(r'```c\n(.*?)```', text, re.S).group(1)
    source_file = root / 'version.c'
    source_file.write_text('#include <stdbool.h>\n#include <stdint.h>\n#include <stdio.h>\n' + example +
        '\nint main(void) { bool actual = iface_version_compatible(IFACE_VERSION_MAKE(2, 0)); '
        'printf("consumer_requires=2.1 provider=2.0 accepted=%d expected=0\\n", actual); return actual ? 1 : 0; }\n')
    compiled = subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source_file), '-o', str(root / 'version')],
                              capture_output=True, text=True, timeout=15)
    assert compiled.returncode == 0, compiled.stderr
    executed = subprocess.run([str(root / 'version')], capture_output=True, text=True, timeout=15)
    interface = {'compile_exit_code': compiled.returncode, 'assertion_exit_code': executed.returncode,
                 'actual_stdout': executed.stdout, 'acceptance_passed': executed.returncode == 0,
                 'assumption': 'Consumer requires functionality first introduced in minor 2.1; the baseline never states this required capability policy.'}
    closeout = read('skills/adk-branch-closeout/references/closeout-options.md')
    approval = {'baseline_statement': next(line for line in closeout.splitlines() if 'previous conversation' in line),
                'case': 'Earlier trusted explicit approval names the same repository, action and branch scope, and has not been revoked.',
                'expected': 'Reuse that authorization; still verify current HEAD/checks and host permissions.',
                'method': 'Static contradiction review only; no model or permission-runtime experiment is claimed.',
                'acceptance_passed': False}
    record = {'baseline_sha': BASELINE, 'bsp': bsp, 'interface': interface, 'closeout': approval,
              'negative_history_lookup': 'knowledge/L2-domain/lessons.md does not exist; no prior lesson was inferred.'}
    assert not bsp['acceptance_passed'] and not interface['acceptance_passed']
    output = ROOT.parent / 'audit-repros/domain-baseline-red.json'
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
