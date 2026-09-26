"""Shared digest-pinned Sigstore blob verification primitive.

This module verifies caller-supplied bytes against an exact Sigstore bundle and
an exact cosign binary. It does not decide authority scope, enable a trust
policy, collect evidence, or grant runtime/lifecycle/release authority.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .model import ManifestError

MAX_BUNDLE_BYTES = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(prefix: str, reason: str) -> ManifestError:
    return ManifestError(f"{prefix}_{reason}")


def verify_sigstore_blob(
    payload: bytes,
    *,
    bundle: Path,
    expected_bundle_sha256: str,
    cosign_binary: str,
    expected_cosign_sha256: str,
    certificate_identity: str,
    certificate_oidc_issuer: str,
    error_prefix: str = "sigstore_blob",
    timeout_seconds: int = 30,
) -> bool:
    """Verify exact bytes through a digest-pinned cosign binary.

    Authority/scope validation belongs to the caller. This function only proves
    payload bytes + bundle bytes + certificate identity/issuer under the exact
    verifier binary supplied by the caller.
    """
    if not isinstance(payload, bytes) or not payload:
        raise _fail(error_prefix, "payload_missing")
    if (
        bundle.suffix != ".json"
        or bundle.is_symlink()
        or not bundle.is_file()
    ):
        raise _fail(error_prefix, "bundle_missing_or_unsafe")
    if bundle.stat().st_size > MAX_BUNDLE_BYTES:
        raise _fail(error_prefix, "bundle_exceeds_byte_budget")
    if sha256_file(bundle) != expected_bundle_sha256:
        raise _fail(error_prefix, "bundle_digest_mismatch")

    binary = Path(cosign_binary)
    if binary.is_absolute():
        resolved_binary = binary.resolve()
    else:
        located = shutil.which(cosign_binary)
        if located is None:
            raise _fail(error_prefix, "cosign_not_found")
        resolved_binary = Path(located).resolve()
    if not resolved_binary.is_file():
        raise _fail(error_prefix, "cosign_not_regular")
    if sha256_file(resolved_binary) != expected_cosign_sha256:
        raise _fail(error_prefix, "cosign_digest_mismatch")

    if not certificate_identity or not certificate_identity.startswith("https://"):
        raise _fail(error_prefix, "certificate_identity_not_configured")
    if not certificate_oidc_issuer or not certificate_oidc_issuer.startswith("https://"):
        raise _fail(error_prefix, "certificate_oidc_issuer_not_configured")

    stdin_path = Path("/dev/stdin")
    if not stdin_path.exists():
        raise _fail(error_prefix, "in_memory_verification_unsupported")

    verifier_env = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    for key in ("HOME", "XDG_CACHE_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR"):
        value = os.environ.get(key)
        if value:
            verifier_env[key] = value

    with tempfile.TemporaryDirectory(prefix=f"adk-{error_prefix}-") as temporary:
        try:
            completed = subprocess.run(
                [
                    str(resolved_binary),
                    "verify-blob",
                    "--bundle",
                    str(bundle),
                    "--certificate-identity",
                    certificate_identity,
                    "--certificate-oidc-issuer",
                    certificate_oidc_issuer,
                    str(stdin_path),
                ],
                cwd=temporary,
                env=verifier_env,
                input=payload,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise _fail(error_prefix, "cosign_timeout") from exc
    return completed.returncode == 0
