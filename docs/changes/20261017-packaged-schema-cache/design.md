# Design

Profiled immutable v8.0.24 source: one test comparison spends most cumulative time in repeated jsonschema Draft202012Validator.check_schema invoked by Trace Summary and Run Evidence validators.

Use @lru_cache(maxsize=1) for _default_trace_validator and _default_composition_validator only. Public load_trace_summary_schema/load_run_evidence_schema retain fresh mutable returned documents; explicit schema objects or schema_path always compile freshly. No exported cache or new authority.

Do not cache by file path, change bootstrap_samples, or skip any privacy/authorization/evidence validation. Confirm exact-value and custom-policy isolation in the existing Effect Trials regression. Local Python 3.13 baseline: 34 cases, 22.14 s; optimized including added negative case: 35 cases, 5.94 s. Not a CI, model-runtime or field performance certification.
