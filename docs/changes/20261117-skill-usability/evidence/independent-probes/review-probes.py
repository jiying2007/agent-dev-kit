"""Independent source review probes; outputs only into this review directory."""
from __future__ import annotations

import importlib.util
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path('/workspace/scratch/fe8de3b42084/adk-skill-usability')
OUT = Path(__file__).resolve().parent
BASE = '78c3be7f6f9b5ee2e557de54156532fb3169198d'
RTK = '/workspace/scratch/fe8de3b42084/verification-tools/rtk'
sys.path.insert(0, str(ROOT / 'src'))

from agent_dev_kit.intent_boundary import validate_task_package, validate_prototype_evidence
from agent_dev_kit.matcher import match_text, resolve_skill_content
from agent_dev_kit.model import Manifest
from agent_dev_kit.profile_context_footprint import enforce_profile_ratchet


def git(*args: str) -> bytes:
    return subprocess.run([RTK, 'bypass', 'git', *args], cwd=ROOT,
                          check=True, capture_output=True).stdout


def task(kind='research'):
    permission, gate = {
        'decision': ('forbidden', 'owner-decision'),
        'research': ('forbidden', 'evidence-reviewed'),
        'prototype': ('forbidden', 'prototype-reviewed'),
        'implementation': ('approved', 'implementation-verified'),
    }[kind]
    return {
        'structured_output_schema': 'adk-task-package-schema-v2',
        'strict_schema_decision': True,
        'refusal_handling': 'Stop and report blocked',
        'goal': 'Inspect the approved boundary',
        'context': 'Frozen source and original owner',
        'constraints': ['scope_write: []'],
        'done_when': ['Boundary is evidenced'],
        'primary_action': 'inspect',
        'action_mode': 'read-only',
        'verification': ['Inspect source and verify the original criterion'],
        'artifacts': ['prototype_evidence:evidence/observations.json'] if kind == 'prototype' else ['review.md'],
        'blockers': [],
        'work_item_kind': kind,
        'question_to_resolve': 'Does the declared boundary hold?',
        'evidence_required': ['Pinned source and original output'],
        'implementation_permission': permission,
        'exit_gate': gate,
        'handoff_target': 'parent-owner',
        'retention_decision': 'keep-final',
    }


def prototype():
    return {
        'structured_output_schema': 'adk-prototype-evidence-schema-v1',
        'question': 'Does the bounded hypothesis hold?',
        'base_commit': BASE,
        'scope': 'isolated host-only evidence',
        'artifact_path': 'evidence/check.json',
        'artifact_sha256': 'a' * 64,
        'runtime_assumptions': 'No live runtime or device',
        'observed_result': 'Bounded observation',
        'decision_supported': False,
        'verification_command': 'host check',
        'verification_exit_code': 1,
        'retention_decision': 'keep-final',
        'expires_at': '2026-12-01',
        'cleanup_owner': 'source-owner',
        'rollback_anchor': BASE,
        'active_references_absent': True,
    }


def compact_route(value):
    keys = ('match', 'skill', 'source', 'reason', 'mutation_permission',
            'effect_ceiling', 'execution_effort')
    return {key: value.get(key) for key in keys}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-name', default='review-probes.json')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    if Path(args.output_name).name != args.output_name:
        parser.error('output-name must be a single filename inside the review directory')
    changed = git('diff', '--name-only', BASE).decode().splitlines()
    changed.extend(git('ls-files', '--others', '--exclude-standard', 'tests').decode().splitlines())
    fingerprints = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in sorted(set(changed)) if (ROOT / name).is_file()}
    result = {'base': BASE, 'python': sys.version,
              'head_at_probe': git('rev-parse', 'HEAD').decode().strip(),
              'head_tree_at_probe': git('rev-parse', 'HEAD^{tree}').decode().strip(),
              'candidate_files_sha256': fingerprints}
    current = Manifest.load(ROOT)
    raw = git('archive', BASE, 'src', 'manifest.json', 'manifests', 'skills', 'optional-skills', 'agents')
    with tempfile.TemporaryDirectory(prefix='base-', dir=OUT) as folder:
        baseline_root = Path(folder)
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(baseline_root, filter='data')
        baseline = Manifest.load(baseline_root)
        result['unchanged_matcher_implementation'] = all(
            (ROOT / p).read_bytes() == (baseline_root / p).read_bytes()
            for p in ('src/agent_dev_kit/matcher.py', 'src/agent_dev_kit/_matcher_kernel.py')
        )
        identity = lambda m: sorted((section, item['name'], item['path'])
                                   for section in ('skills', 'optional_skills') for item in m.data[section])
        result['identities'] = {'same': identity(baseline) == identity(current),
                                'core': len(current.data['skills']),
                                'optional': len(current.data['optional_skills'])}
        result['unchanged_authority'] = all(
            resolve_skill_content(baseline, item['name']) == resolve_skill_content(current, item['name'])
            for section in ('skills', 'optional_skills') for item in current.data[section]
        )
        result['unchanged_ratchet_bytes'] = (ROOT / 'manifests/profile_context_ratchets.json').read_bytes() == (baseline_root / 'manifests/profile_context_ratchets.json').read_bytes()
        result['unchanged_canonical_schema_bytes'] = (ROOT / 'manifests/structured_output_contracts.json').read_bytes() == (baseline_root / 'manifests/structured_output_contracts.json').read_bytes()
        result['profiles'] = [enforce_profile_ratchet(current, name)
                              for name in json.loads((ROOT / 'manifests/profile_context_ratchets.json').read_text())['profiles']]
        prompts = [
            '评估嵌入式设备 OTA 的断电恢复、回滚和上线 readiness',
            '请只读检查 OTA 签名和回滚验证证据',
            'Review OTA firmware rollback readiness',
            '检查固件 OTA 升级准备',
            '文档示例：`OTA`；请检查数据库回滚方案',
            '请检查数据库回滚方案',
            '请设计 FreeRTOS 任务优先级',
            '请为 Zephyr 做任务设计',
            '请为 VxWorks 做任务设计',
            '裸机系统没有 RTOS；请评估实时任务设计',
            '不要做代码评审，只发起PR',
            '只读核验本地修改的代码评审结果',
            '梳理现有 BSP；这次只做源码分析',
            '不涉及 BSP；请梳理脚本入口',
            '请检查 DMA 缓存一致性，这是受 CPU budget 的场景限制的系统。',
            '只检查无中断且无 DMA 的纯轮询任务',
        ]
        baseline_route_code = (
            'import json,sys; from pathlib import Path; '
            'from agent_dev_kit.matcher import match_text; '
            'from agent_dev_kit.model import Manifest; '
            'm=Manifest.load(Path.cwd()); '
            'print(json.dumps([match_text(m,p) for p in json.load(sys.stdin)],ensure_ascii=False))'
        )
        baseline_run = subprocess.run(
            [RTK, 'bypass', sys.executable, '-c', baseline_route_code],
            cwd=baseline_root, input=json.dumps(prompts), text=True, capture_output=True,
            check=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                             'PYTHONPATH': str(baseline_root / 'src')},
        )
        baseline_routes = json.loads(baseline_run.stdout)
        result['baseline_route_execution'] = 'isolated exact-base Python package and assets'
        result['routing'] = [{'prompt': prompt,
                              'base': compact_route(old_result),
                              'candidate': compact_route(match_text(current, prompt))}
                             for prompt, old_result in zip(prompts, baseline_routes, strict=True)]
        spec = importlib.util.spec_from_file_location('baseline_intent', baseline_root / 'src/agent_dev_kit/intent_boundary.py')
        old_validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old_validator)
        result['baseline_malformed_controls'] = []
        for field, value in [('artifacts', None), ('artifacts', [1]), ('work_item_kind', []), ('retention_decision', [])]:
            sample = task()
            sample[field] = value
            entry = {'field': field, 'value': value}
            try:
                entry['baseline_errors'] = old_validator.validate_task_package(sample)
            except Exception as exc:
                entry['baseline_exception'] = type(exc).__name__
            entry['candidate_errors'] = validate_task_package(sample)
            result['baseline_malformed_controls'].append(entry)
    alternatives = [None, True, False, 0, 1, -1, 1.5, '', 'invalid', {}, [], [1], [None], [''], {'x': []}]
    cases, exceptions, non_tuple_results = 0, [], []
    for name, validator, samples in [
        ('task', validate_task_package, [task(k) for k in ('decision', 'research', 'prototype', 'implementation')]),
        ('prototype', validate_prototype_evidence, [prototype()]),
    ]:
        for sample in samples:
            assert validator(sample) == (), (name, validator(sample))
            for field in sample:
                for value in alternatives:
                    changed = {**sample, field: value}
                    cases += 1
                    try:
                        errors = validator(changed)
                        if not isinstance(errors, tuple):
                            non_tuple_results.append([name, field, value])
                    except Exception as exc:
                        exceptions.append([name, field, value, type(exc).__name__, str(exc)])
        for value in alternatives:
            cases += 1
            try:
                assert validator(value), (name, value)
            except Exception as exc:
                exceptions.append([name, 'root', value, type(exc).__name__, str(exc)])
    result['malformed_json_matrix'] = {'cases': cases, 'exceptions': exceptions,
                                       'non_tuple_results': non_tuple_results,
                                       'note': 'Valid typed replacements may pass; this matrix tests exception-free behavior, not semantic permission enforcement.'}
    field_skill = 'adk-production-field-readiness'
    rtos_skill = 'adk-rtos-task-design'
    independent_cases = [
        ('不涉及量产或 OTA；请检查数据库回滚方案', None, field_skill),
        ('不涉及量产、OTA 或 RMA；请检查数据库回滚方案', None, field_skill),
        ('不涉及量产和 OTA，只检查数据库回滚方案', None, field_skill),
        ('不涉及量产或 OTA，但请检查 OTA 签名和回滚证据', field_skill, None),
        ('不涉及量产，检查 OTA 签名和回滚证据', field_skill, None),
        ('不涉及量产；检查 OTA 签名和回滚证据', field_skill, None),
        ('不涉及量产而是 OTA，检查签名和回滚证据', field_skill, None),
        ('不做量产或 OTA 发布，只检查数据库回滚方案', None, field_skill),
        ('不涉及量产或 OTA；核对 RMA 现场恢复证据', field_skill, None),
        ('not production-field or OTA; check database rollback', None, field_skill),
        ('without production-field or OTA; check database 回滚', None, field_skill),
        ('文档示例：`OTA`；请检查数据库回滚方案', None, field_skill),
        ('请只读检查 `OTA` 的签名和回滚证据', field_skill, None),
        ('评估嵌入式设备 OTA 的断电恢复、回滚和上线 readiness', field_skill, None),
        ('请为 VxWorks 做任务设计', rtos_skill, None),
        ('不涉及 RTOS 或 VxWorks；请做销售团队任务设计', None, rtos_skill),
        ('请为 Zephyr 做任务设计', rtos_skill, None),
    ]
    result['independent_regression_cases'] = []
    for prompt, expected, excluded in independent_cases:
        actual = match_text(current, prompt)
        passed = ((expected is None or actual.get('skill') == expected)
                  and (excluded is None or actual.get('skill') != excluded)
                  and actual.get('mutation_permission') == 'deny')
        result['independent_regression_cases'].append(
            {'prompt': prompt, 'expected_skill': expected, 'excluded_skill': excluded,
             'passed': passed, 'actual': compact_route(actual)}
        )
    path = OUT / args.output_name
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if args.summary:
        print(json.dumps({
            'output': str(path), 'head': result['head_at_probe'],
            'identities': result['identities'], 'unchanged_authority': result['unchanged_authority'],
            'profiles': {row['profile']: row['status'] for row in result['profiles']},
            'malformed_json_matrix': result['malformed_json_matrix'],
            'routing_fixes': [result['routing'][n] for n in (0, 1, 2, 8)],
            'regression_case_count': len(result['independent_regression_cases']),
            'regression_failures': [row for row in result['independent_regression_cases'] if not row['passed']],
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
