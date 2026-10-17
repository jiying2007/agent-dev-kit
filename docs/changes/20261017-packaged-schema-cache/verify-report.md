# Verification record (pre-CI)

- Source baseline: exact immutable ADK 8.0.24 artifact, Python 3.13, Effect Trials 34/34 PASS in 22.14s wall (memory 122,776 KiB).
- Source candidate: same isolated machine with targeted cache and added policy-isolation test, 35/35 PASS in 5.94s wall (memory 121,876 KiB).
- Command: PYTHONPATH=src python3 -m unittest discover -s tests -p test_effect_trials.py -q.
- This comparison includes one additional regression test, but uses the same hardware/Python build; the result is a local source-level optimization, not production-runtime behavior.
- Still required: hosted Python 3.8/3.11/3.12 CI, exact-main promotion, immutable Release and Root integration.
- First PR head CI: all three version regressions failed only `test_harness_readiness` because Owner readiness metadata aged out of its authentic 90-day window. This was independently reproduced locally with real `harness readiness --gate` exit 2 and `stale_last_verified_at` on 2026-10-17. A follow-up regression change preserves, rather than bypasses, the live Gate. Fresh PR checks are required before release.

No fake model/provider/effect/Owner verdict was created.
