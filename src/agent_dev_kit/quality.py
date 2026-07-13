"""Asset-platform security and deterministic performance checks."""

from __future__ import annotations

import json
import math
import os
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

from .compiler import export_assets
from .model import Manifest, ManifestError


SECRET_NAME_PATTERNS = (".env", ".pem", ".key", ".p12", ".pfx", "id_rsa")
SECRET_CONTENT = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")


def security_check(manifest: Manifest) -> Dict[str, Any]:
    failures: List[str] = []
    warnings: List[str] = []
    tracked = subprocess.run(
        ["git", "-C", str(manifest.root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if tracked.returncode != 0:
        raise ManifestError("cannot enumerate tracked files for security check")
    for raw in tracked.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", errors="replace")
        path = manifest.root / relative
        lowered = path.name.lower()
        if any(lowered == pattern or lowered.endswith(pattern) for pattern in SECRET_NAME_PATTERNS):
            failures.append("tracked sensitive filename: {}".format(relative))
        if path.is_symlink():
            resolved = path.resolve(strict=False)
            try:
                resolved.relative_to(manifest.root)
            except ValueError:
                failures.append("tracked symlink escapes repository: {}".format(relative))
        if path.is_file() and os.access(str(path), os.W_OK) and path.stat().st_mode & 0o002:
            failures.append("world-writable tracked file: {}".format(relative))
        if path.is_file() and path.stat().st_size <= 1024 * 1024:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line in content.splitlines():
                if SECRET_CONTENT.search(line) and not re.search(
                    r"(?i)(YOUR|EXAMPLE|REDACTED|CHANGEME)[_-][A-Z0-9_-]+", line
                ):
                    failures.append("credential-like content: {}".format(relative))
                    break

    workflows = list((manifest.root / ".github" / "workflows").glob("*.yml"))
    workflows.extend((manifest.root / ".github" / "workflows").glob("*.yaml"))
    for workflow in workflows:
        workflow_content = workflow.read_text(encoding="utf-8")
        if not re.search(r"(?m)^permissions:\n  contents: read$", workflow_content):
            failures.append("GitHub workflow does not set read-only contents permission: {}".format(workflow.name))
        for line_number, line in enumerate(workflow_content.splitlines(), start=1):
            match = re.match(r"\s*-?\s*uses:\s*([^\s#]+)", line)
            if match:
                action = match.group(1)
                if action.startswith("./"):
                    continue
                if action.startswith("docker://"):
                    if "@sha256:" not in action:
                        failures.append("container action is not pinned by digest: {}:{}".format(workflow.name, line_number))
                    continue
                ref = action.rsplit("@", 1)[1] if "@" in action else ""
                if not re.fullmatch(r"[0-9a-f]{40}", ref):
                    failures.append("GitHub action is not pinned by SHA: {}:{}".format(workflow.name, line_number))

    return {
        "schema_version": 1,
        "status": "fail" if failures else ("warn" if warnings else "pass"),
        "failures": failures,
        "warnings": warnings,
    }


def _measure(action: Callable[[], None], iterations: int) -> Dict[str, Any]:
    values: List[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        action()
        values.append((time.perf_counter() - started) * 1000.0)
    ordered = sorted(values)
    p95_index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
    return {
        "iterations": iterations,
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[p95_index], 3),
        "min_ms": round(min(ordered), 3),
        "max_ms": round(max(ordered), 3),
    }


def run_benchmark(manifest: Manifest, iterations: int = 5) -> Dict[str, Any]:
    if iterations < 1 or iterations > 100:
        raise ManifestError("benchmark iterations must be between 1 and 100")

    def load_validate() -> None:
        current = Manifest.load(manifest.root)
        failures = current.validate(strict=True)
        if failures:
            raise ManifestError("benchmark validation failed")

    def resolve_profile() -> None:
        manifest.resolve_profiles(["embedded-fullstack"])

    with tempfile.TemporaryDirectory(prefix="adk-benchmark-") as temp:
        output = Path(temp)

        def export_dry_run() -> None:
            export_assets(manifest, "claude-code", output, ["core"], dry_run=True)

        measurements = {
            "manifest_validate": _measure(load_validate, iterations),
            "profile_resolve": _measure(resolve_profile, iterations),
            "export_plan": _measure(export_dry_run, iterations),
        }
    budget_path = manifest.root / "manifests" / "adk_performance_budgets.json"
    try:
        budget_data = json.loads(budget_path.read_text(encoding="utf-8"))
        budgets = budget_data["platform_operations"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ManifestError("platform performance budgets are invalid: {}".format(exc)) from exc
    budget_gate: Dict[str, bool] = {}
    for name, metrics in measurements.items():
        raw_budget = budgets.get(name)
        if not isinstance(raw_budget, dict) or not isinstance(raw_budget.get("max_p95_ms"), (int, float)):
            raise ManifestError("platform performance budget missing for {}".format(name))
        budget_gate[name] = metrics["p95_ms"] <= float(raw_budget["max_p95_ms"])
    return {
        "schema_version": 1,
        "status": "pass" if all(budget_gate.values()) else "fail",
        "manifest_sha256": manifest.digest,
        "iterations": iterations,
        "budgets": budgets,
        "budget_gate": budget_gate,
        "measurements": measurements,
    }


def benchmark_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# ADK Benchmark",
        "",
        "- status: {}".format(report.get("status")),
        "",
        "| Operation | Iterations | Median ms | P95 ms | Budget ms | Gate |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, metrics in report.get("measurements", {}).items():
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                name,
                metrics["iterations"],
                metrics["median_ms"],
                metrics["p95_ms"],
                report.get("budgets", {}).get(name, {}).get("max_p95_ms", "n/a"),
                "pass" if report.get("budget_gate", {}).get(name) else "fail",
            )
        )
    return "\n".join(lines) + "\n"
