"""Read-only incremental packaging checks; no product tests or full rerun."""
from datetime import datetime, timezone
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

SCRATCH = Path("/workspace/scratch/2d4d08f07657")
ROOT = SCRATCH / "adk-other-skills"
CHANGE = ROOT / "docs/changes/20261116-skill-observation-precision"
EV = CHANGE / "evidence"
RTK = "/workspace/scratch/fe5385ca063a/verification-tools/rtk"
HEAD = "384bdcdfac75881891bce795991b68fa46d9b9d6"
TREE = "627aabff2317705de46b010126edf3b57a443d1f"
BASE = "fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9"
PATCH_SHA = "ae27a8e2e298f8f4e98290adba4f2e2d4609d5a3d29a1eea11edbac8172e4823"
commands = []


def sha(content):
    return hashlib.sha256(content).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def command(*args, binary=False):
    argv = [RTK, "bypass", "git", *args]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    output = result.stdout
    commands.append({"argv": argv, "cwd": str(ROOT), "exit_code": result.returncode,
                     "stdout": {"bytes": len(output), "sha256": sha(output)} if binary else output.decode(),
                     "stderr": result.stderr.decode()})
    return output if binary else output.decode()


identity = command("show", "-s", "--format=%H%n%T%n%P", "HEAD")
assert identity.splitlines() == [HEAD, TREE, BASE]
assert command("diff", "--name-status", "HEAD") == ""
assert command("diff", "--cached", "--name-status") == ""
untracked = command("ls-files", "--others", "--exclude-standard").splitlines()
expected_names = {"evidence/execution-bundle.json", "evidence/execution-summary.json",
                  "evidence/independent-source-review.json", "evidence/independent-source-review.md",
                  "evidence/original.patch", "evidence/review-validation.json",
                  "evidence/source-bindings.json", "review-evidence.json", "verification.md"}
assert set(untracked) == {str((CHANGE / p).relative_to(ROOT)) for p in expected_names}

bindings = load(EV / "source-bindings.json")
original_sources = load(SCRATCH / "other-skills-independent-probes/receipt.json")["source_hashes"]
assert len(bindings["files"]) == len(original_sources) == 45
assert {x["path"] for x in bindings["files"]} == {x["path"] for x in original_sources}
for item in bindings["files"]:
    data = (ROOT / item["path"]).read_bytes()
    assert len(data) == item["bytes"] and sha(data) == item["sha256"]
    assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == item["blob"]
for item in original_sources:
    data = (ROOT / item["path"]).read_bytes()
    assert len(data) == item["bytes"] and sha(data) == item["sha256"]

patch = command("diff", "--binary", "--full-index", "--no-ext-diff", BASE, HEAD, binary=True)
assert len(patch) == 451173 and sha(patch) == PATCH_SHA
assert patch == (EV / "original.patch").read_bytes()
assert patch == (SCRATCH / "other-skills-independent-probes/source.patch").read_bytes()

bundle = load(EV / "execution-bundle.json")
assert len(bundle["files"]) == 28
decoded = {}
payload_checks = []
for item in bundle["files"]:
    assert item["encoding"] == "gzip+base64"
    data = gzip.decompress(base64.b64decode(item["data"], validate=True))
    assert item["name"] not in decoded
    assert len(data) == item["bytes"] and sha(data) == item["sha256"]
    assert data == Path(item["original_path"]).read_bytes()
    decoded[item["name"]] = data
    payload_checks.append({"name": item["name"], "bytes": len(data), "sha256": sha(data),
                           "declared_identity_match": True, "original_bytes_equal": True})
probe_names = {"other-skills-independent-probes/" + p.name for p in
               (SCRATCH / "other-skills-independent-probes").iterdir() if p.is_file()}
assert len(probe_names) == 10 and probe_names <= set(decoded)
assert decoded["other-skills-independent-probes/source.patch"] == patch

review = load(CHANGE / "review-evidence.json")
validation = load(EV / "review-validation.json")
review_sha = sha((CHANGE / "review-evidence.json").read_bytes())
assert review_sha == validation["record_sha256"] == "f6fe33f7fe5235d5d6d1e04905c0b4497dbbc7c6e167f35ab746ec04f580fa2d"
assert validation["status"] == "pass"
assert all(validation[key] == value for key, value in review.items())
refs = review["sources"] + review["evidence"]
assert len(refs) == 51 and len({(x["base"], x["path"]) for x in refs}) == 51
for item in refs:
    base = ROOT if item["base"] == "repository" else CHANGE
    assert item["base"] in ("repository", "record")
    path = (base / item["path"]).resolve()
    assert path.is_relative_to(base)
    assert sha(path.read_bytes()) == item["sha256"]
source_report = load(SCRATCH / "other-skills-independent-review.json")
for suffix in ("json", "md"):
    assert (EV / f"independent-source-review.{suffix}").read_bytes() == (
        SCRATCH / f"other-skills-independent-review.{suffix}").read_bytes()
assert review["reviewer"]["id"] == source_report["reviewer"]["id"]
for key in ("reviewed_at", "evidence_completed_at"):
    assert datetime.fromisoformat(review[key]) == datetime.fromisoformat(source_report[key])
for key in ("verdicts", "findings", "limitations"):
    assert review[key] == source_report[key]

summary = load(EV / "execution-summary.json")
full = json.loads(decoded["other-skills-full-regression/receipt.json"])
timing = json.loads(decoded["other-skills-full-regression/timing.json"])
assert summary["source_commit"] == HEAD and summary["source_tree"] == TREE
assert all(summary["full"][key] == full[key] for key in summary["full"])
assert summary["full_total"] == timing["total"] == 102
assert summary["full_pass"] == timing["pass"] == 102
assert summary["independent_verdicts"] == source_report["verdicts"]
assert summary["consumer_observations"] == 1 and summary["consumer_pairing_or_effect_claim"] is False

wrapper_format = []
for relative in untracked:
    path = ROOT / relative
    data = path.read_bytes()
    if path.suffix == ".patch":
        wrapper_format.append({"path": relative, "check": "immutable Git patch byte identity; no whitespace rewriting"})
        continue
    assert b"\r" not in data and data.endswith(b"\n")
    assert all(line == line.rstrip() for line in data.decode().splitlines())
    if path.suffix == ".json":
        json.loads(data)
    wrapper_format.append({"path": relative, "check": "JSON parsing where applicable; LF/final newline/trailing-whitespace inspection", "pass": True})

assert command("diff", "--name-status", "HEAD") == ""
assert command("ls-files", "--others", "--exclude-standard").splitlines() == untracked
reviewed_at = datetime.now(timezone.utc).isoformat()
report = {
    "reviewer": {"id": "ai/root/embedded_methods", "role": "independent-incremental-packaging-review"},
    "reviewed_at": reviewed_at, "evidence_completed_at": reviewed_at,
    "verdicts": {"packaging": "pass"}, "findings": [],
    "source": {"base": BASE, "commit": HEAD, "tree": TREE, "patch_sha256": PATCH_SHA,
               "patch_bytes": len(patch), "unchanged_frozen_paths": 45},
    "scope": "Only the nine appended packaging files; source Spec/Quality verdict remains bound to the previously tested commit.",
    "checks": {"new_files": 9, "tracked_and_staged_diff_empty": True,
               "source_byte_sha_blob_checks": 45, "unique_reference_hash_checks": 51,
               "decoded_payloads_equal_originals": 28, "probe_directory_members_retained": 10,
               "original_reports_byte_equal": True, "timestamp_normalization_same_instant": True,
               "raw_patch_preserved_exactly": True, "validation_record_sha256": review_sha,
               "execution_summary_matches_archived_receipts": True},
    "packaging_snapshot": [{"path": p, "bytes": (ROOT / p).stat().st_size,
                            "sha256": sha((ROOT / p).read_bytes())} for p in untracked],
    "mechanical_commands": commands,
    "payload_checks": payload_checks,
    "wrapper_format_inspection": wrapper_format,
    "semantic_review": "verification.md and execution-summary.json preserve exact-source versus prefreeze hash-bound evidence, source-only consumer limits, fixture-derived SEARCH, and subsequent PR/main/release/Root steps. No completion, native or live qualification was added.",
    "auxiliary_review": {"reviewer": "ai/root/embedded_methods/evidence_binding_check",
                         "completed_at": "2026-11-16T14:58:31.192087+00:00",
                         "result": "No blocker in 51 refs, 45 source/tree blobs, report copies, timestamp equivalence, validator/policy hashes or wrapper claims."},
    "limitations": ["No product tests, full suite or validator rerun; existing validator PASS was inspected and hash-bound.",
                    "Only the nine-file snapshot is approved; the two packaging-review reports may be copied verbatim afterward as agreed.",
                    "Existing format gates and thresholds were not modified. The immutable raw patch is identity-checked, not normalized for Git context-marker whitespace.",
                    "Source runtime/HIL/mailbox/SLA/native/A-B limitations from the original independent report remain unchanged."],
    "negative_results": ["One exploratory python -c metadata query had a syntax error; corrected before checks. It performed no writes and is not product evidence."],
    "checker_source": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).read_bytes())},
    "repository_writes_by_reviewer": False,
}
json_path = SCRATCH / "other-skills-independent-packaging-review.json"
json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
md = f"""# 独立增量包装审查

**结论：PASS，无阻断。** Reviewer `ai/root/embedded_methods`；时间 `{reviewed_at}`。

审查限于新增9个包装文件。HEAD `{HEAD}` / tree `{TREE}` 不变；tracked/staged diff为空，45个冻结路径的bytes/SHA256/Git blob与原审查身份相符。

- 51个唯一引用全部解析并核SHA256；typed记录摘要 `{review_sha}` 与既有validator PASS一致。
- execution-bundle的28项均严格Base64解码、gzip解压、核bytes/SHA256，并与实际原文件逐字相同；包含独立probe目录全部10文件。
- original.patch、独立source.patch、归档patch与当前base→HEAD差异原字节相同：451173 bytes，SHA256 `{PATCH_SHA}`。未清理Git空白上下文标记。
- 原独立JSON/Markdown报告逐字复制；reviewer、verdicts/findings/limitations保持，`+00:00`→`Z`表示同一瞬间。
- execution-summary与归档full/timing相符；verification明确区分受测源码、冻结前按hash绑定的执行及后续交付，未冒称包装执行过full/native/真实邮箱/HIL。
- 非patch包装文本已检查JSON可解析、LF/终结换行和尾部空白；现有格式门禁、阈值和产品逻辑未改。

机械命令原输出、9文件冻结摘要、28项逐项解码结果保存在同名JSON报告中。辅助只读审查复核了51引用、45 tree blobs、时间及文字范围，结论一致。

未运行产品测试、full或validator，未写repo/index/ref。可按约定原样复制本次两份报告后提交；本次通过仅覆盖所记录9文件，原源码审查的runtime/SLA/native/A-B限制继续有效。一条探索性metadata命令曾有Python语法错误，已纠正且无写入，不作为产品失败或验证结果。
"""
md_path = SCRATCH / "other-skills-independent-packaging-review.md"
md_path.write_text(md, encoding="utf-8")
print(json.dumps({"status": "pass", "reviewed_at": reviewed_at,
                  "reports": [{"path": str(p), "bytes": p.stat().st_size,
                               "sha256": sha(p.read_bytes())} for p in (json_path, md_path)],
                  "checks": report["checks"]}, ensure_ascii=False, indent=2))
