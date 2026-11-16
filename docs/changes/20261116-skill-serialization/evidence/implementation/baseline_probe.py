"""Synthetic serialization counterexample; never inspect real credentials."""
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

@dataclass
class Holder:
    endpoint: str
    credential: str = field(repr=False)

@dataclass
class Envelope:
    component: str
    client: Holder

holder = Holder("https://example.invalid", "SYNTHETIC_SERIALIZATION_PROBE")
envelope = Envelope("fixture", holder)
safe = {"component": envelope.component, "client": {"endpoint": holder.endpoint}}
reference = Path("optional-skills/adk-security-supply-chain/references/skill-scan-coverage.md").read_text()
print(json.dumps({
    "repr_hides_synthetic_value": holder.credential not in repr(holder),
    "asdict_json_contains_synthetic_value": holder.credential in json.dumps(asdict(holder)),
    "nested_asdict_contains_synthetic_value": holder.credential in json.dumps(asdict(envelope)),
    "allowlist_excludes_synthetic_value": holder.credential not in json.dumps(safe),
    "allowlist_preserves_public_fields": safe["component"] == envelope.component and safe["client"]["endpoint"] == holder.endpoint,
    "baseline_has_serialization_guidance": "asdict" in reference and "repr=False" in reference,
    "lessons_available": Path("knowledge/L2-domain/lessons.md").is_file(),
}, sort_keys=True))
