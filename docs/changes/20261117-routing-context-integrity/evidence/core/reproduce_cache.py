"""Read-only source audit: mutate isolated copies, never the ADK worktree."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path('/workspace/scratch/d417066aafa8/agent-dev-kit')
sys.path.insert(0, str(REPO / 'src'))
from agent_dev_kit import phase_context, matcher, skill_relationships, _matcher_kernel
from agent_dev_kit.model import Manifest, ManifestError


def alter(path: Path, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    assert len(old) == len(new) and old in raw
    stat = path.stat()
    path.write_bytes(raw.replace(old, new, 1))
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert (path.stat().st_mtime_ns, path.stat().st_size) == (stat.st_mtime_ns, stat.st_size)


def record_contract(module, filename: str, resolve):
    with tempfile.TemporaryDirectory(prefix='adk-core-cache-') as temporary:
        root = Path(temporary)
        for name in ('manifest.json', 'manifests', 'schemas', 'skills', 'optional-skills'):
            source = REPO / name
            if source.is_dir():
                shutil.copytree(source, root / name)
            else:
                shutil.copy2(source, root / name)
        manifest = Manifest.load(root)
        path = root / 'manifests' / filename
        module._load_contract.cache_clear()
        before = resolve(manifest)
        alter(path, b'/v2"', b'/v9"')
        warm = resolve(manifest)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        module._load_contract.cache_clear()
        try:
            resolve(manifest)
        except ManifestError as exc:
            cold = {'rejected': True, 'error': str(exc)[:300]}
        else:
            cold = {'rejected': False}
        return {
            'consumer': module.__name__, 'path': filename,
            'same_mtime_and_size': True, 'mutation': 'schema_version v2 -> v9',
            'warm_cache_accepted': isinstance(warm, dict),
            'warm_contract_digest_matches_changed_bytes': warm.get('contract_sha256') == digest,
            'cold_cache': cold,
            'warm_result': warm,
        }


results = [
    record_contract(phase_context, 'phase_context_contract_v2.json',
                    lambda manifest: phase_context.resolve_phase_context(manifest, 'general', 'route')),
    record_contract(skill_relationships, 'skill_relationship_contracts_v2.json',
                    skill_relationships.resolve_skill_relationships),
    record_contract(matcher, 'skill_content_contracts_v2.json',
                    lambda manifest: matcher.resolve_skill_content(manifest, 'adk-runtime-router')),
]
with tempfile.TemporaryDirectory(prefix='adk-frontmatter-cache-') as temporary:
    path = Path(temporary) / 'SKILL.md'
    shutil.copy2(REPO / 'skills/adk-runtime-router/SKILL.md', path)
    _matcher_kernel._frontmatter_cached.cache_clear()
    before = _matcher_kernel._frontmatter(path)
    alter(path, b'---', b'xxx')
    warm = _matcher_kernel._frontmatter(path)
    _matcher_kernel._frontmatter_cached.cache_clear()
    try:
        _matcher_kernel._frontmatter(path)
    except ManifestError as exc:
        cold = {'rejected': True, 'error': str(exc)}
    else:
        cold = {'rejected': False}
    results.append({'consumer': '_matcher_kernel._frontmatter', 'same_mtime_and_size': True,
                    'mutation': 'opening frontmatter delimiter invalidated',
                    'warm_cache_accepted': warm == before, 'cold_cache': cold})

print(json.dumps({'baseline_commit': '6d902f721f560f02883516e809fbd93a326405b6',
                  'cases': results}, ensure_ascii=False, indent=2))
