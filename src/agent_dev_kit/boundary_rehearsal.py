"""Deterministic tool-effect and MCP boundary rehearsals, without an executor.

Inputs are caller declarations. A passing rehearsal never attests permission,
DNS observations, token authenticity, server ownership or external effects.
"""
from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from .model import ManifestError, canonical_json_bytes, sha256_bytes


def _result(decision: str, reason: str) -> dict[str, Any]:
    return {"decision": decision, "reason": reason, "evidence_scope": "test-only",
            "external_effect_performed": False, "network_called": False,
            "release_authorized": False, "lifecycle_authority": "none-evidence-only",
            "input_authority": "caller-declared-not-attested"}


def proposal_digest(proposal: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(proposal))


def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ManifestError("rehearsal timestamp must be text")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("invalid rehearsal timestamp") from exc
    if parsed.tzinfo is None:
        raise ManifestError("rehearsal timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def effect_decision(proposal: Mapping[str, Any], approval: Mapping[str, Any], *,
                    now: datetime, target_state_sha256: str,
                    receipt: Mapping[str, Any] | None = None,
                    exclusive_claim: bool = True) -> dict[str, Any]:
    required = {"operation_id", "target_id", "parameters_sha256", "expected_state_sha256", "expires_at"}
    if set(proposal) != required or any(not isinstance(proposal[k], str) or not proposal[k] for k in required):
        return _result("deny", "invalid-proposal")
    if now.tzinfo is None:
        raise ManifestError("rehearsal now must include a timezone")
    for name in ("parameters_sha256", "expected_state_sha256"):
        if len(proposal[name]) != 64 or any(c not in "0123456789abcdef" for c in proposal[name]):
            return _result("deny", "invalid-proposal-digest")
    digest = proposal_digest(proposal)
    if receipt is not None:
        if receipt.get("operation_id") != proposal["operation_id"] or receipt.get("proposal_sha256") != digest:
            return _result("deny", "operation-identity-conflict")
        outcome = receipt.get("outcome")
        if outcome == "applied":
            return _result("already-applied", "deduplicated-no-replay")
        if outcome == "unknown":
            return _result("reconcile-required", "external-result-unknown-no-blind-retry")
        if outcome != "not-applied":
            return _result("deny", "invalid-receipt")
    if approval.get("allowed") is not True or approval.get("revoked") is not False:
        return _result("deny", "permission-denied-or-revoked")
    if not isinstance(approval.get("authority_id"), str) or not approval["authority_id"]:
        return _result("deny", "authority-identity-missing")
    if approval.get("proposal_sha256") != digest or approval.get("target_id") != proposal["target_id"]:
        return _result("deny", "approval-binding-changed")
    try:
        expired = now >= _time(proposal["expires_at"]) or now >= _time(approval.get("expires_at"))
    except ManifestError:
        return _result("deny", "invalid-expiry")
    if expired:
        return _result("deny", "proposal-or-approval-expired")
    if target_state_sha256 != proposal["expected_state_sha256"]:
        return _result("deny", "target-state-changed")
    if exclusive_claim is not True:
        return _result("deny", "concurrent-resume-not-exclusive")
    return _result("test-executor-ready", "bindings-current-at-attempt")


def mcp_observation(transport: str, urls: Sequence[str], addresses: Mapping[str, Sequence[str]], *,
                    server_audience: str, token_audience: str, principal_id: str,
                    handle_owner: str | None = None, allow_loopback: bool = False) -> dict[str, Any]:
    if transport not in {"stdio", "streamable-http"}:
        return _result("deny", "unsupported-transport")
    if not principal_id or (handle_owner is not None and handle_owner != principal_id):
        return _result("deny", "state-handle-caller-mismatch")
    if transport == "stdio":
        return _result("deny", "stdio-has-unexpected-remote-url") if urls else _result("test-observation-valid", "local-transport-only")
    if not server_audience or token_audience != server_audience:
        return _result("deny", "token-audience-mismatch")
    if not urls or len(urls) > 8:
        return _result("deny", "redirect-observation-missing-or-unbounded")
    for url in urls:
        try:
            parsed = urlsplit(url)
            host = parsed.hostname
            _ = parsed.port
            if not host or parsed.username is not None or parsed.password is not None or parsed.fragment:
                return _result("deny", "unsafe-url-shape")
            resolved = addresses.get(host, ())
            if not resolved or len(resolved) > 16:
                return _result("deny", "resolution-observation-missing-or-unbounded")
            ips = [ipaddress.ip_address(value) for value in resolved]
            ips = [getattr(value, "ipv4_mapped", None) or value for value in ips]
            loopback = allow_loopback is True and all(value.is_loopback for value in ips)
            if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
                return _result("deny", "https-required")
            if not loopback and any(not value.is_global for value in ips):
                return _result("deny", "private-or-reserved-destination")
        except (TypeError, ValueError):
            return _result("deny", "invalid-url-or-address-observation")
    return _result("test-observation-valid", "every-observed-hop-checked")


def rehearse() -> dict[str, Any]:
    """Exercise fixed fault cases. No tool, DNS, token or target is contacted."""
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    proposal = {"operation_id": "fixture-operation", "target_id": "fixture-target",
                "parameters_sha256": "a" * 64, "expected_state_sha256": "b" * 64,
                "expires_at": "2026-01-02T00:00:00Z"}
    approval = {"authority_id": "fixture-authority", "allowed": True, "revoked": False,
                "target_id": "fixture-target", "proposal_sha256": proposal_digest(proposal),
                "expires_at": "2026-01-02T00:00:00Z"}
    receipt = {"operation_id": proposal["operation_id"], "proposal_sha256": proposal_digest(proposal)}
    effect_cases = [
        ("authorized-fixture", {}, {}, {}, "test-executor-ready"),
        ("permission-denied", {}, {"allowed": False}, {}, "deny"),
        ("permission-revoked", {}, {"revoked": True}, {}, "deny"),
        ("parameter-substitution", {"parameters_sha256": "c" * 64}, {}, {}, "deny"),
        ("target-substitution", {"target_id": "other"}, {}, {}, "deny"),
        ("expired-proposal", {"expires_at": "2025-12-31T00:00:00Z"}, {}, {}, "deny"),
        ("stale-target", {}, {}, {"target_state_sha256": "c" * 64}, "deny"),
        ("concurrent-resume", {}, {}, {"exclusive_claim": False}, "deny"),
        ("duplicate-applied", {}, {}, {"receipt": {**receipt, "outcome": "applied"}}, "already-applied"),
        ("unknown-result", {}, {}, {"receipt": {**receipt, "outcome": "unknown"}}, "reconcile-required"),
        ("operation-conflict", {}, {}, {"receipt": {**receipt, "operation_id": "other", "outcome": "applied"}}, "deny"),
        ("reconciled-not-applied", {}, {}, {"receipt": {**receipt, "outcome": "not-applied"}}, "test-executor-ready"),
    ]
    results = []
    for name, changed_proposal, changed_approval, options, expected in effect_cases:
        actual = effect_decision({**proposal, **changed_proposal}, {**approval, **changed_approval},
                                 **{"now": now, "target_state_sha256": "b" * 64, **options})
        results.append({"case": name, "expected": expected, "actual": actual["decision"],
                        "reason": actual["reason"], "passed": actual["decision"] == expected})
    base = {"server_audience": "fixture-server", "token_audience": "fixture-server", "principal_id": "fixture-caller"}
    mcp_cases = [
        ("public-https", ["https://public.test"], {"public.test": ["8.8.8.8"]}, {}, "test-observation-valid"),
        ("http-default-deny", ["http://public.test"], {"public.test": ["8.8.8.8"]}, {}, "deny"),
        ("redirect-private", ["https://public.test", "https://private.test"],
         {"public.test": ["8.8.8.8"], "private.test": ["127.0.0.1"]}, {}, "deny"),
        ("mixed-resolution", ["https://public.test"], {"public.test": ["8.8.8.8", "10.0.0.1"]}, {}, "deny"),
        ("mapped-private-ipv6", ["https://private.test"], {"private.test": ["::ffff:10.0.0.1"]}, {}, "deny"),
        ("missing-resolution", ["https://public.test"], {}, {}, "deny"),
        ("token-passthrough", ["https://public.test"], {"public.test": ["8.8.8.8"]}, {"token_audience": "other"}, "deny"),
        ("handle-hijack", ["https://public.test"], {"public.test": ["8.8.8.8"]}, {"handle_owner": "other"}, "deny"),
        ("explicit-loopback-development", ["http://localhost"], {"localhost": ["127.0.0.1"]}, {"allow_loopback": True}, "test-observation-valid"),
    ]
    for name, urls, addresses, options, expected in mcp_cases:
        actual = mcp_observation("streamable-http", urls, addresses, **{**base, **options})
        results.append({"case": name, "expected": expected, "actual": actual["decision"],
                        "reason": actual["reason"], "passed": actual["decision"] == expected})
    return {"schema": "adk-boundary-rehearsal/v1", "status": "pass" if all(c["passed"] for c in results) else "fail",
            "cases": results, "total": len(results), "passed": sum(c["passed"] for c in results),
            "evidence_scope": "test-only", "external_effect_performed": False, "network_called": False,
            "runtime_enabled": False, "release_authorized": False,
            "limitations": ["caller declarations are not managed authorization or DNS evidence",
                            "real transport, executor, concurrency lock and target reconciliation need integration verification"]}
