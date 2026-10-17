# Verification record (pre-CI)

- Source baseline: exact immutable ADK 8.0.24 artifact, Python 3.13, Effect Trials 34/34 PASS in 22.14s wall (memory 122,776 KiB).
- Source candidate: same isolated machine with targeted cache and added policy-isolation test, 35/35 PASS in 5.94s wall (memory 121,876 KiB).
- Command: PYTHONPATH=src python3 -m unittest discover -s tests -p test_effect_trials.py -q.
- This comparison includes one additional regression test, but uses the same hardware/Python build; the result is a local source-level optimization, not production-runtime behavior.
- Still required: hosted Python 3.8/3.11/3.12 CI, exact-main promotion, immutable Release and Root integration.

No fake model/provider/effect/Owner verdict was created.
