from __future__ import annotations

import hashlib
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import ManifestError
from agent_dev_kit.sigstore_blob import verify_sigstore_blob


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_cosign(root: Path, exit_code: int = 0) -> Path:
    path = root / "cosign"
    path.write_text(
        f"#!{sys.executable}\n"
        "import pathlib,sys\n"
        "args=sys.argv[1:]\n"
        "blob=sys.stdin.buffer.read()\n"
        "ok=(len(args)==8 and args[0]=='verify-blob' and args[1]=='--bundle' "
        "and args[3]=='--certificate-identity' and args[5]=='--certificate-oidc-issuer' "
        "and pathlib.Path(args[2]).is_file() and args[7]=='/dev/stdin' and len(blob)>0)\n"
        f"sys.exit({exit_code} if ok else 97)\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path.resolve()


class SigstoreBlobVerifierTest(unittest.TestCase):
    def test_exact_blob_bundle_binary_and_identity_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            bundle = root / "payload.sigstore.json"
            bundle.write_text('{"fixture":"sigstore"}\n', encoding="utf-8")
            binary = fake_cosign(root)
            self.assertTrue(
                verify_sigstore_blob(
                    b'{"plan":"exact"}',
                    bundle=bundle,
                    expected_bundle_sha256=sha256(bundle),
                    cosign_binary=str(binary),
                    expected_cosign_sha256=sha256(binary),
                    certificate_identity="https://github.com/example/repo/.github/workflows/preregister.yml@refs/heads/main",
                    certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                )
            )

    def test_digest_identity_and_signature_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            bundle = root / "payload.sigstore.json"
            bundle.write_text("{}\n", encoding="utf-8")
            binary = fake_cosign(root)

            with self.assertRaisesRegex(ManifestError, "bundle_digest_mismatch"):
                verify_sigstore_blob(
                    b"x",
                    bundle=bundle,
                    expected_bundle_sha256="0" * 64,
                    cosign_binary=str(binary),
                    expected_cosign_sha256=sha256(binary),
                    certificate_identity="https://github.com/example/repo/.github/workflows/preregister.yml@refs/heads/main",
                    certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                )
            with self.assertRaisesRegex(ManifestError, "cosign_digest_mismatch"):
                verify_sigstore_blob(
                    b"x",
                    bundle=bundle,
                    expected_bundle_sha256=sha256(bundle),
                    cosign_binary=str(binary),
                    expected_cosign_sha256="0" * 64,
                    certificate_identity="https://github.com/example/repo/.github/workflows/preregister.yml@refs/heads/main",
                    certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                )
            with self.assertRaisesRegex(ManifestError, "certificate_identity_not_configured"):
                verify_sigstore_blob(
                    b"x",
                    bundle=bundle,
                    expected_bundle_sha256=sha256(bundle),
                    cosign_binary=str(binary),
                    expected_cosign_sha256=sha256(binary),
                    certificate_identity="",
                    certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                )

            failed = fake_cosign(root, exit_code=1)
            self.assertFalse(
                verify_sigstore_blob(
                    b"x",
                    bundle=bundle,
                    expected_bundle_sha256=sha256(bundle),
                    cosign_binary=str(failed),
                    expected_cosign_sha256=sha256(failed),
                    certificate_identity="https://github.com/example/repo/.github/workflows/preregister.yml@refs/heads/main",
                    certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                )
            )


if __name__ == "__main__":
    unittest.main()
