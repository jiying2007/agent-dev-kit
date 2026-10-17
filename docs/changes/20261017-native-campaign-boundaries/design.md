# Native campaign boundary regression — Design

- Replace the escaped two-byte `\\n` separator with the actual single LF byte when producing combined assertion bytes. Keep version probes unchanged.
- Check the original leaf with `Path.is_symlink()` before `Path.resolve()` in the JSON writer.
- In the CLI output-path guard, preserve lexical and resolved root comparisons, but inspect each lexical component between the candidate output path and canonical root. Reject an in-root symlink even if it points to another managed directory.
- Add focused tests for LF vs literal backslash-n; leaf symlink no-clobber; same-root leaf and parent symlinks. Leave `_safe_output_path` return value resolved so callers retain existing behavior for valid paths.

## Evidence boundary
Deterministic tests and green CI can prove these source contracts. G21 authenticated native discovery/load/trigger, current candidate product M5 and human semantic reviews remain separate.
