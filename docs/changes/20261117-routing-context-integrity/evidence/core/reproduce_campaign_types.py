"""Reuse repository synthetic campaign fixture; never launch a model/runtime."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path('/workspace/scratch/d417066aafa8/agent-dev-kit')
sys.path.insert(0, str(REPO / 'src'))
from agent_dev_kit.campaign_model import _digest, _result_path
from agent_dev_kit.effect_campaign_materializer import materialize_effect_campaign

spec = importlib.util.spec_from_file_location('campaign_fixture', REPO / 'tests/test_effect_campaign_materializer.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
results = []
for field, value in [('actual_safe', 1), ('elapsed_ms', True), ('cost_usd', False)]:
    case = fixture.EffectCampaignMaterializerTest()
    case.setUp()
    try:
        path = _result_path(case.state, 'claude', 'adk', 1, 'task-a')
        record = json.loads(path.read_text())
        for item in record['attempts']:
            item[field] = value
        record['final'][field] = value
        del record['record_sha256']
        record['record_sha256'] = _digest(record)
        fixture.write_json(path, record)
        report = materialize_effect_campaign(fixture.MANIFEST, case.contract_path, case.state,
                                             case.effect_plan_path, 'claude', campaign_root=case.root)
        observed = next(t for t in report['trials'] if t['trial_id'] == 'trial-1')['candidate'][0]['run']['trace_summary']
        results.append({'field': field, 'malformed_value': value, 'accepted': True,
                        'outcome': observed['outcome'], 'elapsed_ms': observed['elapsed_ms'],
                        'cost': observed.get('cost'), 'guardrails': observed['guardrails']})
    except Exception as exc:
        results.append({'field': field, 'malformed_value': value, 'accepted': False,
                        'exception': type(exc).__name__, 'message': str(exc)})
    finally:
        case.tearDown()
print(json.dumps({'baseline_commit': '6d902f721f560f02883516e809fbd93a326405b6',
                  'scope': 'synthetic fixture / no runtime execution', 'cases': results}, indent=2))
