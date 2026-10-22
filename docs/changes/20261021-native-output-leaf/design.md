# Design

## Existing authority and failure

`native_campaign._safe_output_path` is the one CLI path selector for plan, candidate contract, run evidence, typed receipt and final contract. It currently returns a resolved external path. The downstream `_write_json` then sees the link target, so its symbolic-link leaf guard cannot inspect the user's supplied leaf.

## Change

Check the original absolute lexical output leaf before any `resolve()` call. Reuse the existing `ManifestError` failure path and keep the current repository confinement and repository ancestor checks. Do not introduce a second writer, change the wire schema or alter valid regular-file overwrite behavior. This is a path preflight under the existing assumption that parent directories are caller-controlled; it does not claim atomic protection against arbitrary concurrent parent renames.

Move `run`'s existing output-path selection before `run_campaign`. The invalid-output regression must prove that the execution function is not called; it does not substitute a fake success for a provider failure. `prepare` and `finalize` already select both output paths before writing either.

## Validation and review roles

The coordinator freezes this contract; an independent implementer owns source and regression changes; source reviewers remain read-only. Exercise the actual `prepare` command for both output options and both existing/dangling external leaves, preserving original target bytes and checking that neither result file was partially written. Existing normal external and repository confinement tests remain required. Review all five callers of the shared selector, then run supported regression once on the frozen source.

## Risk and rollback

Previously accepted external symlink leaves now fail explicitly; callers should pass a regular output path. No runtime installation or active target data changes. A rollback is a separately reviewed source revert; the original unsafe behavior is not retained as an option.
