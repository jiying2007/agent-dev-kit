"""Independent checks for generic diagnosis versus established task owners."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path('/workspace/scratch/fe8de3b42084/adk-skill-usability')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest

cases = [
    ('立即进行 SSH调试：登录生产设备，抓取日志并执行诊断命令。', 'adk-embedded-debug-transport', None),
    ('只读 SSH调试：检查连接并诊断设备日志。', 'adk-embedded-remote-debug-log-triage', None),
    ('诊断这个 Python 脚本的异常', 'adk-systematic-debugging', None),
    ('先诊断 Web API 超时的根因', 'adk-systematic-debugging', None),
    ('请诊断这个普通命令的失败，先不修改代码', 'adk-systematic-debugging', None),
    ('不要诊断，只校验 commit message', 'adk-commit-pr-quality-gate', None),
    ('不要诊断这个脚本，只做中文代码评审', 'adk-code-review-loop', None),
    ('核对现场诊断和设备交付准备', 'adk-production-field-readiness', None),
    ('只读评估现场 OTA 回滚，不执行刷写', 'adk-production-field-readiness', None),
    ('已有明确根因且只需执行已确认修复；不要诊断', None, 'adk-systematic-debugging'),
    ('请做独立代码审查，关注诊断日志实现', 'adk-code-review-loop', None),
    ('请校验 commit message 中“诊断流程”的表述', 'adk-commit-pr-quality-gate', None),
    ('请写 ADR 记录诊断方案', 'adk-adr-writer', None),
]
manifest = Manifest.load(ROOT)
rows = []
for prompt, expected, excluded in cases:
    actual = match_text(manifest, prompt)
    passed = ((expected is None or actual.get('skill') == expected)
              and (excluded is None or actual.get('skill') != excluded)
              and actual.get('mutation_permission') == 'deny')
    rows.append({'prompt': prompt, 'expected_skill': expected, 'excluded_skill': excluded,
                 'passed': passed, 'actual': actual})
source_paths = ['manifest.json', 'skills/adk-systematic-debugging/SKILL.md',
                'tests/test_skill_trigger_matrix.py', 'src/agent_dev_kit/_matcher_kernel.py',
                'tests/fixtures/software_m5_eval_tasks.jsonl']
record = {'files_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_paths},
          'cases': rows, 'passed': all(row['passed'] for row in rows)}
(OUT / 'ssh-regression-after.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'files_sha256': record['files_sha256'], 'case_count': len(rows),
                  'passed': record['passed'], 'failures': [row for row in rows if not row['passed']]},
                 ensure_ascii=False, indent=2))
raise SystemExit(0 if record['passed'] else 1)
