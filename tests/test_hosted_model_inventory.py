"""Synthetic source-derived layouts; never a replay of the lost hosted model tree."""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from agent_dev_kit import hosted_model_inventory as models
from agent_dev_kit import hosted_task_native as native


class Store:
    def __init__(self, parent: Path) -> None:
        self.root = parent / "models"
        (self.root / "blobs").mkdir(parents=True)
        config = self.layer(b'{"model_format":"gguf"}')
        weight = self.layer(b"synthetic public weights, not a real model")
        self.leaf: dict[str, Any] = {
            "schemaVersion": 2,
            "mediaType": models.MANIFEST_TYPE,
            "config": config,
            "layers": [weight],
            "runner": "ggml",
        }
        self.digest = self.blob(self.json_bytes(self.leaf))
        self.named = self.root / "manifests-v2/ollama.com/library/qwen3/1.7b"
        self.alias(self.named, self.digest)
        self.api: dict[str, Any] = {
            "name": "qwen3:1.7b",
            "model": "qwen3:1.7b",
            "digest": self.digest,
            "details": {"runner": "ggml", "format": "gguf"},
        }

    @staticmethod
    def json_bytes(value: object) -> bytes:
        return (json.dumps(value, separators=(",", ":")) + "\n").encode()

    def blob(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        (self.root / "blobs" / ("sha256-" + digest)).write_bytes(data)
        return digest

    def layer(self, data: bytes) -> dict[str, Any]:
        return {"mediaType": "application/octet-stream", "digest": "sha256:" + self.blob(data), "size": len(data)}

    def alias(self, path: Path, digest: str, *, regular: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink() or path.exists():
            path.unlink()
        blob = self.root / "blobs" / ("sha256-" + digest)
        if regular:
            path.write_bytes(blob.read_bytes())
        else:
            path.symlink_to(os.path.relpath(blob, path.parent))

    def descriptor(self, *, runner: str = "ggml") -> dict[str, Any]:
        return {
            "mediaType": models.MANIFEST_TYPE,
            "digest": "sha256:" + self.digest,
            "runner": runner,
            "format": "gguf",
        }

    def parent(self, children: list[dict[str, Any]]) -> str:
        digest = self.blob(self.json_bytes({"schemaVersion": 2, "mediaType": models.LIST_TYPE, "manifests": children}))
        self.alias(self.named, digest)
        return digest

    def freeze(self) -> dict[str, Any]:
        return models.inventory_model_store(self.root, self.api, "qwen3:1.7b")


class ModelInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = Store(Path(self.temporary.name))

    def test_official_relative_v2_link_is_recorded_without_relaxing_generic_inventory(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Unexpected symlink"):
            native.inventory(self.store.root)
        frozen = self.store.freeze()
        link = frozen["files"][self.store.named.relative_to(self.store.root).as_posix()]
        self.assertEqual(link["kind"], "symlink")
        self.assertEqual(link["target"], os.readlink(self.store.named))
        self.assertEqual(link["link_sha256"], hashlib.sha256(link["target"].encode()).hexdigest())
        self.assertEqual(link["normalized_target"], "blobs/sha256-" + self.store.digest)
        self.assertEqual(link["target_sha256"], self.store.digest)
        identity = frozen["identity"]
        self.assertEqual(identity["binding"], "direct-manifest")
        self.assertEqual(identity["api_digest"], self.store.digest)
        self.assertEqual(hashlib.sha256(identity["named_manifest"]["raw_utf8"].encode()).hexdigest(), self.store.digest)

    def test_regular_legacy_and_v2_copy_fallback_are_supported(self) -> None:
        for path in (self.store.named, self.store.root / "manifests/registry.ollama.ai/library/qwen3/1.7b"):
            with self.subTest(path=str(path)):
                if self.store.named.exists():
                    self.store.named.unlink()
                self.store.alias(path, self.store.digest, regular=True)
                self.assertEqual(
                    self.store.freeze()["identity"]["named_entry"], path.relative_to(self.store.root).as_posix()
                )

    def test_manifest_list_binds_distinct_parent_to_selected_child_and_api_runner(self) -> None:
        parent = self.store.parent([self.store.descriptor()])
        self.assertNotEqual(parent, self.store.digest)
        identity = self.store.freeze()["identity"]
        self.assertEqual(identity["binding"], "manifest-list-child")
        self.assertEqual(identity["named_manifest"]["sha256"], parent)
        self.assertEqual(identity["selected_manifest"]["sha256"], self.store.digest)
        self.assertEqual(identity["api_runner"], "ggml")

    def test_v2_priority_cannot_be_bypassed_by_matching_legacy_entry(self) -> None:
        legacy = self.store.root / "manifests/registry.ollama.ai/library/qwen3/1.7b"
        self.store.alias(legacy, self.store.digest, regular=True)
        wrong = self.store.blob(self.store.json_bytes({**self.store.leaf, "marker": "different manifest"}))
        self.store.alias(self.store.named, wrong)
        with self.assertRaisesRegex(models.ModelInventoryError, "complete API digest"):
            self.store.freeze()
        self.store.alias(self.store.named, self.store.digest)
        self.store.alias(legacy, wrong, regular=True)
        self.assertEqual(
            self.store.freeze()["identity"]["named_entry"], self.store.named.relative_to(self.store.root).as_posix()
        )

    def test_matching_arbitrary_blob_or_wrong_named_entry_is_insufficient(self) -> None:
        self.store.named.rename(self.store.named.with_name("other-tag"))
        with self.assertRaisesRegex(models.ModelInventoryError, "canonical named manifest"):
            self.store.freeze()

    def test_api_name_digest_and_runner_are_independently_bound(self) -> None:
        original = copy.deepcopy(self.store.api)
        for change in (
            {"name": "other:tag"},
            {"model": "other:tag"},
            {"digest": "f" * 64},
            {"digest": "short"},
            {"details": {"runner": "llamacpp"}},
        ):
            with self.subTest(change=change):
                self.store.api = {**original, **change}
                with self.assertRaises(models.ModelInventoryError):
                    self.store.freeze()

    def test_absolute_escape_self_cycle_and_link_chain_targets_are_rejected(self) -> None:
        sibling = self.store.named.with_name("other-tag")
        self.store.alias(sibling, self.store.digest)
        for target in ("/models/blobs/sha256-" + self.store.digest, "../../../../../outside", "1.7b", "other-tag"):
            with self.subTest(target=target):
                self.store.named.unlink()
                self.store.named.symlink_to(target)
                with self.assertRaises(models.ModelInventoryError):
                    self.store.freeze()

    def test_raw_link_ancestors_cannot_be_lexically_cancelled(self) -> None:
        (self.store.named.parent / "ordinary").write_bytes(b"ordinary file")
        (self.store.named.parent / "detour").mkdir()
        for prefix, native_errno in (("1.7b", errno.ELOOP), ("ordinary", errno.ENOTDIR), ("detour", None)):
            with self.subTest(prefix=prefix):
                self.store.named.unlink()
                self.store.named.symlink_to(prefix + "/../../../../../blobs/sha256-" + self.store.digest)
                if native_errno is not None:
                    with self.assertRaises(OSError) as raised:
                        self.store.named.stat()
                    self.assertEqual(raised.exception.errno, native_errno)
                with self.assertRaises(models.ModelInventoryError):
                    self.store.freeze()

    def test_dangling_and_directory_targets_are_rejected(self) -> None:
        blob = self.store.root / "blobs" / ("sha256-" + self.store.digest)
        blob.unlink()
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()
        blob.mkdir()
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()

    def test_symlinked_blob_and_ancestors_are_rejected(self) -> None:
        blob = self.store.root / "blobs" / ("sha256-" + self.store.digest)
        outside = Path(self.temporary.name) / "outside-blob"
        blob.rename(outside)
        blob.symlink_to(outside)
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()
        blob.unlink()
        outside.rename(blob)
        alias = Path(self.temporary.name) / "linked-parent"
        alias.symlink_to(self.store.root.parent, target_is_directory=True)
        with self.assertRaises(models.ModelInventoryError):
            models.inventory_model_store(alias / "models", self.store.api, "qwen3:1.7b")
        directory = self.store.root / "manifests-v2/ollama.com/library"
        saved = self.store.root / "saved-library"
        directory.rename(saved)
        directory.symlink_to(saved, target_is_directory=True)
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()

    def test_unsupported_link_location_and_special_file_are_rejected(self) -> None:
        link = self.store.root / "unexpected-link"
        link.symlink_to("blobs/sha256-" + self.store.digest)
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()
        link.unlink()
        os.mkfifo(self.store.root / "unexpected-fifo")
        with self.assertRaisesRegex(models.ModelInventoryError, "Special"):
            self.store.freeze()

    def test_blob_filename_and_complete_content_must_agree(self) -> None:
        blob = self.store.root / "blobs" / ("sha256-" + self.store.digest)
        blob.write_bytes(b"corrupt manifest")
        with self.assertRaisesRegex(models.ModelInventoryError, "complete content digest"):
            self.store.freeze()

    def test_ambiguous_runner_inline_and_nested_lists_are_rejected(self) -> None:
        descriptor = self.store.descriptor()
        children_cases = [
            [descriptor, descriptor],
            [descriptor, self.store.descriptor(runner="llamacpp")],
            [self.store.descriptor(runner="llamacpp")],
            [{**descriptor, "config": {}}],
            [{**descriptor, "mediaType": models.LIST_TYPE}],
            [{**descriptor, "digest": "sha256:" + "e" * 64}],
        ]
        for children in children_cases:
            with self.subTest(children=children):
                self.store.parent(children)
                with self.assertRaises(models.ModelInventoryError):
                    self.store.freeze()

    def test_missing_leaf_blob_layer_or_wrong_size_is_rejected(self) -> None:
        self.store.parent([self.store.descriptor()])
        (self.store.root / "blobs" / ("sha256-" + self.store.digest)).unlink()
        with self.assertRaises(models.ModelInventoryError):
            self.store.freeze()
        self.store.blob(self.store.json_bytes(self.store.leaf))
        wrong = copy.deepcopy(self.store.leaf)
        wrong["config"]["size"] += 1
        self.store.api["digest"] = self.store.blob(self.store.json_bytes(wrong))
        self.store.alias(self.store.named, self.store.api["digest"])
        with self.assertRaisesRegex(models.ModelInventoryError, "layer size"):
            self.store.freeze()

    def test_json_api_record_and_manifest_limits_are_enforced(self) -> None:
        record = Path(self.temporary.name) / "model.json"
        record.write_bytes(self.store.json_bytes(self.store.api))
        self.assertEqual(models.read_model_record(record), self.store.api)
        record.write_bytes(b" " * (models.MAX_JSON_BYTES + 1))
        with self.assertRaisesRegex(models.ModelInventoryError, "byte limit"):
            models.read_model_record(record)
        oversized = self.store.blob(b" " * (models.MAX_JSON_BYTES + 1))
        self.store.alias(self.store.named, oversized)
        self.store.api["digest"] = oversized
        with self.assertRaisesRegex(models.ModelInventoryError, "byte limit"):
            self.store.freeze()

    def test_entry_depth_and_child_count_are_bounded(self) -> None:
        self.store.parent([self.store.descriptor()] * (models.MAX_CHILDREN + 1))
        with self.assertRaisesRegex(models.ModelInventoryError, "bounds"):
            self.store.freeze()
        self.store.alias(self.store.named, self.store.digest)
        deep = self.store.root.joinpath(*(["deep"] * (models.MAX_DEPTH + 1)))
        deep.mkdir(parents=True)
        with self.assertRaisesRegex(models.ModelInventoryError, "depth or entry limit"):
            self.store.freeze()
        with tempfile.TemporaryDirectory() as temporary:
            other = Store(Path(temporary))
            metadata = other.root / "metadata"
            metadata.mkdir()
            for index in range(models.MAX_ENTRIES + 1):
                (metadata / str(index)).write_bytes(b"public")
            with self.assertRaisesRegex(models.ModelInventoryError, "depth or entry limit"):
                other.freeze()

    def test_duplicate_json_fields_are_not_silently_interpreted(self) -> None:
        data = self.store.json_bytes(self.store.leaf).replace(
            b'{"schemaVersion":2,', b'{"schemaVersion":2,"schemaVersion":2,', 1
        )
        digest = self.store.blob(data)
        self.store.alias(self.store.named, digest)
        self.store.api["digest"] = digest
        with self.assertRaisesRegex(models.ModelInventoryError, "duplicate"):
            self.store.freeze()

    def test_shared_strict_json_rejects_depth_nonfinite_and_invalid_unicode(self) -> None:
        record = Path(self.temporary.name) / "model.json"
        nested = b'{"nested":' + b"[" * models.MAX_JSON_DEPTH + b"0" + b"]" * models.MAX_JSON_DEPTH + b"}"
        for data, reason in (
            (nested, "nesting"),
            (b'{"bad":NaN}', "non-finite"),
            (b'{"bad":1e9999}', "non-finite"),
            (b"\xff", "invalid JSON"),
            (b'{"bad":"\\ud800"}', "Unicode"),
        ):
            with self.subTest(reason=reason):
                record.write_bytes(data)
                with self.assertRaisesRegex(models.ModelInventoryError, reason):
                    models.read_model_record(record)

    def test_content_changed_between_inventory_and_identity_read_fails_closed(self) -> None:
        original = models._small_bytes
        blob = self.store.root / "blobs" / ("sha256-" + self.store.digest)

        def mutate(parent: int, name: str, expected: models.Signature) -> bytes:
            info = blob.stat()
            os.utime(blob, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000_000))
            return original(parent, name, expected)

        with patch.object(models, "_small_bytes", side_effect=mutate):
            with self.assertRaisesRegex(models.ModelInventoryError, "identity changed"):
                self.store.freeze()


if __name__ == "__main__":
    unittest.main()
