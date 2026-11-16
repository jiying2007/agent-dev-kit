"""Read-only diagnostic of schema closure methods; no ADK/runtime mutation."""
from __future__ import annotations

import copy
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft7Validator, Draft202012Validator


def main() -> None:
    base = {
        "type": "object",
        "properties": {"id": {"type": "integer", "minimum": 0}},
        "required": ["id"],
    }
    extension = {
        "type": "object",
        "properties": {"mode": {"enum": ["safe", "fast"]}},
        "required": ["mode"],
    }
    flat = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {**base["properties"], **extension["properties"]},
        "required": ["id", "mode"],
        "additionalProperties": False,
    }
    broken = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "allOf": [{**base, "additionalProperties": False}, extension],
    }
    composed = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "allOf": [base, extension],
        "unevaluatedProperties": False,
    }
    legacy_unsupported = copy.deepcopy(composed)
    legacy_unsupported["$schema"] = "http://json-schema.org/draft-07/schema#"
    legacy_flat = copy.deepcopy(flat)
    legacy_flat["$schema"] = "http://json-schema.org/draft-07/schema#"

    cases = {
        "legitimate": {"id": 1, "mode": "safe"},
        "unknown_field": {"id": 1, "mode": "safe", "admin": True},
        "missing_id": {"mode": "safe"},
        "missing_mode": {"id": 1},
        "invalid_type": {"id": "1", "mode": "safe"},
        "invalid_enum": {"id": 1, "mode": "superuser"},
    }
    contract = {name: name == "legitimate" for name in cases}
    variants = [
        ("same_level_closed", Draft202012Validator, flat, contract),
        ("allof_closed_subschema", Draft202012Validator, broken,
         {name: False for name in cases}),
        ("allof_composed_closure", Draft202012Validator, composed, contract),
        ("draft7_unsupported_keyword", Draft7Validator, legacy_unsupported,
         {**contract, "unknown_field": True}),
        ("draft7_flattened_closure", Draft7Validator, legacy_flat, contract),
    ]
    results = []
    for name, validator_type, schema, expected_observation in variants:
        validator_type.check_schema(schema)
        validator = validator_type(schema)
        observed = {case: validator.is_valid(instance) for case, instance in cases.items()}
        assert observed == expected_observation, (name, observed, expected_observation)
        results.append({
            "variant": name,
            "validator": validator_type.__name__,
            "schema": schema,
            "observed_acceptance": observed,
            "meets_input_contract": observed == contract,
            "legitimate_errors": [error.message for error in validator.iter_errors(cases["legitimate"])],
        })
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "jsonschema": importlib.metadata.version("jsonschema"),
        "cases": cases,
        "required_acceptance": contract,
        "results": results,
        "boundary": "Deterministic JSON Schema semantics only; no LLM, native runtime, or ADK production validator result.",
    }
    target = Path(__file__).with_suffix(".json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
