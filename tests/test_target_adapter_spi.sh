#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_dev_kit.targets import (
    CONFORMANCE_CAPABILITIES,
    AdapterContext,
    AdapterOperation,
    AdapterPlan,
    AdapterResult,
    RuntimeAdapter,
)

root = Path(sys.argv[1])
schema = json.loads((root / "manifests/target-contract.schema.json").read_text(encoding="utf-8"))
contract_caps = set(
    schema["properties"]["adapter"]["properties"]["capabilities"]["propertyNames"]["enum"]
)
assert contract_caps == set(CONFORMANCE_CAPABILITIES), (contract_caps, CONFORMANCE_CAPABILITIES)


class DummyAdapter:
    adapter_id = "dummy-adapter"
    target = "dummy"

    @staticmethod
    def _pass(name: str) -> AdapterResult:
        return AdapterResult(status="pass", summary=name)

    def detect(self, context: AdapterContext) -> AdapterResult:
        return self._pass("detect")

    def version(self, context: AdapterContext) -> AdapterResult:
        return self._pass("version")

    def plan(self, context: AdapterContext) -> AdapterPlan:
        return AdapterPlan(
            target=self.target,
            operations=(AdapterOperation(kind="read", description="inspect runtime"),),
            required_capabilities=frozenset({"discovery"}),
        )

    def export(self, context: AdapterContext, plan: AdapterPlan) -> AdapterResult:
        return self._pass("export")

    def install(self, context: AdapterContext, plan: AdapterPlan) -> AdapterResult:
        return AdapterResult(status="blocked", summary="mutation intentionally blocked")

    def discover(self, context: AdapterContext) -> AdapterResult:
        return self._pass("discover")

    def load(self, context: AdapterContext) -> AdapterResult:
        return self._pass("load")

    def trigger(self, context: AdapterContext) -> AdapterResult:
        return self._pass("trigger")

    def resume(self, context: AdapterContext) -> AdapterResult:
        return self._pass("resume")

    def cancel(self, context: AdapterContext) -> AdapterResult:
        return self._pass("cancel")

    def rollback(self, context: AdapterContext) -> AdapterResult:
        return self._pass("rollback")

    def health(self, context: AdapterContext) -> AdapterResult:
        return self._pass("health")

    def collect_evidence(self, context: AdapterContext, *, capabilities: list[str]) -> AdapterResult:
        return AdapterResult(
            status="pass",
            summary="collected",
            evidence_refs=tuple(f"runtime:{name}" for name in capabilities),
        )


adapter = DummyAdapter()
assert isinstance(adapter, RuntimeAdapter)
context = AdapterContext(target="dummy", workspace=root, dry_run=True)
plan = adapter.plan(context)
assert plan.required_capabilities == frozenset({"discovery"})
assert plan.operations[0].kind == "read"
assert adapter.detect(context).ok is True
assert adapter.install(context, plan).ok is False
assert adapter.install(context, plan).status == "blocked"

# The SPI itself carries no conformance/certification flag: native status remains
# solely governed by adk-target-contract/v2 and runtime evidence receipts.
for forbidden in ("certified", "conformance_certified", "native_verified"):
    assert not hasattr(adapter, forbidden)

print("[PASS] target adapter SPI matches target-contract/v2 capability vocabulary")
PY
