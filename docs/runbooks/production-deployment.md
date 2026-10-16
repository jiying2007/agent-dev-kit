# Production Deployment

Production deployment is target-explicit. ADK produces validated assets; the selected runtime adapter owns final installation, backup and rollback.

## Minimum Gate

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh release check --summary-json
bash tests/run_all.sh --fail-fast
```

## Requirements

- deployment target is declared in `manifest.json:tool_targets`, or is an explicit external handoff
- install uses plan/apply/receipt and has a verified rollback path
- release artifact includes checksum and SBOM
- generated assets have a review owner
- runtime smoke evidence is recorded before production claims
- hardware/field claims remain `field_not_verified` until real evidence exists

## Incomplete installation or rollback

An installation or rollback with a failed compensation is **not** a completed
rollback. Stop further plan/apply/rollback attempts against the affected target
and preserve `.adk-backups/<receipt-id>`, `.adk-staging/<receipt-id>`,
`.adk-rollback-staging/<receipt-id>`, and the active receipt. Never delete
these directories to make a retry pass. Make a byte-for-byte, permission-
preserving copy of the target before a supervised recovery; compare file
hashes to the preserved receipt/backup and restore missing assets explicitly.
A successful command exit or verified manual repair is required before
claiming the target is healthy. Atomic rename protection in one operation
does not imply power-loss-safe multi-file transactions.

The runtime now refuses another install **and** rollback while an unfinished
`.adk-staging/<run-id>` or `.adk-rollback-staging/<receipt-id>` exists. This
fail-closed guard intentionally requires supervised recovery, even if the
leftover directory is empty. Do not delete a marker until its backing data and
receipt have been independently verified. `.adk-backups` remains valid for
completed installs and is not itself an incomplete-operation marker.

Managed install paths must not contain symlink aliases, even if the link resolves
inside the same target. A plan created before a file/directory is replaced by
a symlink is rejected at apply and rollback. Resolve that drift under operator
review; never chmod or overwrite a different file through an aliased path.

Before applying a reviewed installation plan, the executor re-binds every
`replace-managed` operation to the active receipt's exact installed digest.
Editing a plan's `destination_sha256` does not waive managed-file drift.
Existing unmanaged files cannot be promoted to `replace-managed`, and missing
managed files cannot be reclassified as `create`. Investigate the discrepancy,
then use a fresh plan or a supervised rollback; do not edit the plan to bypass
the active receipt.

## Rollback receipt path authority (8.0.14)

The stored SHA-256 on a local receipt is a content-integrity checksum, **not** a
signature or an independent capability to delete files. Before any rollback
mutation, the executor verifies the canonical run identifier and binds
`backup_root` to exactly `.adk-backups/<receipt-id>`; each per-asset backup
must be the corresponding path beneath that root. The previous-receipt
reference must also be the canonical receipt inside the same run-specific
backup directory. Reject edited or misplaced paths even when their bytes and
receipt SHA-256 match. Reconcile under supervised recovery; never edit a
receipt's backup paths to force a rollback or delete preserved evidence.

## Trusted rollback inventory (8.0.15)

The local receipt's SHA-256 alone is not an authorization for file deletion.
Rollback now requires the **trusted ADK Manifest used to install** and
reconstructs the exact target/profile/optional-skill/asset-kind rendered file
set. The receipt must match that Manifest's version/digest and its installed
asset set, metadata, original source hashes, rendered hashes, file modes, and
on-disk content before any file is moved. Rehashed receipt entries that name
non-managed files do **not** gain deletion rights.

Run `install rollback` from the exact ADK source/version that produced the
active receipt; newer installations must be rolled back one version at a time.
For a source-identity mismatch, stop and use reviewed, byte-preserving manual
recovery with the original pinned ADK source. Library callers must pass
`manifest=trusted_manifest`; there is no receipt-only rollback fallback.

## Shared receipt and backup authority (8.0.16)

Install planning, install apply, and rollback must validate the entire active
receipt against a trusted same-version Manifest and rendered asset selection.
A recomputed local SHA-256 cannot grant unmanaged-file replacement rights. An
installed older version must be rolled back using its original trusted source
before switching versions; editing a receipt to force migration is forbidden.

Before any rollback file mutation, a bounded traversal verifies that the
transaction backup tree contains exactly the referenced regular asset backups,
optional previous receipt, and necessary parent directories. Omitted backup
references and unexpected files/directories, symlinks or special entries block
destructive cleanup. Preserve unknown recovery data for supervised review.
This validation does not protect against same-UID concurrent filesystem races
or power loss; use isolated targets and byte-preserving recovery procedures.


## Installed file mode authority (8.0.17)

A managed file's content SHA-256 does not include POSIX permission bits.
Planning a replacement now reports a conflict if the actual regular file's
mode differs from the trusted renderer-bound install receipt. Apply
revalidates the mode under the target lock, and rollback refuses both an
installed asset or its previous managed backup if either has permission
drift. No destructive file move is performed before all modes are checked.
After inspecting unexpected permission changes, restore the trusted mode or
use a supervised recovery process; never edit the receipt's hashes or mode
to force an operation. This deliberately does not claim protection from
same-user concurrent mutation after validation or filesystem-level faults.
