# 真实负向结果

实现者：`ai/root/adk_code_audit`。本阶段是 F1 实现，不是独立审核。固定父提交 `415590db44e88979185efb850e2339a3f95411ef`；审查反例和用户新授权经主 Agent 的 requirements/design 冻结后进入实现。

## 原实现失败

2026-10-24，先增加公开行为验收，再在未改生产实现上运行：

```text
python3 -m unittest test_release_integrity.ReleaseGitInputTest.test_real_bundle_bytes_modes_inventory_and_target_counts_are_required test_release_integrity.ReleaseGitInputTest.test_recomputed_export_manifest_cannot_authorize_a_changed_bundle test_release_integrity.ReleaseGitInputTest.test_public_publish_rejects_missing_bundles_before_github_discovery test_release_integrity.ReleaseGitInputTest.test_real_clean_bundle_validation_remains_positive
```

实际退出码 `1`；原始结果尾部：

```text
Ran 4 tests in 12.006s

FAILED (failures=9)
```

其中七个归档变体（全部 bundle 缺失、单 target 缺失、单文件缺失、Skill 内容修改、额外文件、模式变化、虚假 target count）以及自重算 export manifest 均出现 `AssertionError: ValueError not raised`；公开 publish 的缺 bundle 变体仍到达 GitHub CLI discovery，触发预设的 `AssertionError: premature gh discovery`。真实干净包正向控制通过。fixture 发布始终 dry-run，没有网络写入。

旧 archive-resource / strict-json / release-manifest 正例只声明 target，但不含可渲染 source 或 bundle；这些正例随合同迁移为真实最小 source/export，不新增 `release_eligible=false` 豁免。

## 新增历史验收测试的断言修正

`python3 -m unittest test_release_integrity.ReleaseInventoryTest` 首轮为 `Ran 9 tests in 0.557s / FAILED (failures=1)`，退出码 `1`。历史包验证已经通过，当前准入确实拒绝过期 contract，但测试误匹配了 `expired`，实际稳定错误码为 `target_contract_stale`。按已有 owner 的错误码修正断言，不改生产准入或历史逻辑。

## 新读取 source schema 的失败边界

在源码重渲染路径加入后，仓外只读网络阻断探针 `/tmp/adk_f1_schema_probe.py` 观察到自引用 schema 抛 `RecursionError`，缺失 local reference 抛 jsonschema 的 `_WrappedReferencingError`；未出现 PASS。它们原先不在 CLI 已有的 `ValueError` 失败边界内，会产生未结构化 traceback。新增公开 `_main` 回归首先实际失败：`Ran 1 test in 0.147s / FAILED (errors=2)`，退出码 `1`。将归档控制的 renderer/schema 非标准异常在 release verifier 入口包装成 `ValueError`，保留原始 cause；没有改 schema、准入或 renderer 语义。嵌套旧式 `id` 作用域和 `$recursiveRef` 外部引用也在离线 guard 中拒绝。

## 环境与范围

当前运行解释器 Python 3.12，依赖为本轮独立环境中的 PyYAML 6.0.3 / jsonschema 4.26.0。历史知识文件不存在；没有执行真实 Native、G22、LTA 或产品资格。

## 输出放大预算先红

主 Agent 批准补齐 renderer 预算后，先在未加预算的实现运行四个公开 release validator 用例：单文件深层 YAML 编码放大、跨资产/跨 target 累计输出、80 个资产别名复用同一源文件、20 个资产重复导出同一 48 KiB support 文件。测试仅将现有归档常量缩小到 128–512 KiB / 64 members，真实输入仍低于这些上限，不进行 OOM 实验。

实际命令：

```text
python3 -m unittest test_release_integrity.ReleaseInventoryTest.test_frontmatter_output_is_bounded_during_encoding test_release_integrity.ReleaseInventoryTest.test_cumulative_render_budget_is_shared_by_assets_and_targets test_release_integrity.ReleaseInventoryTest.test_aliased_source_assets_cannot_exceed_rendered_file_budget test_release_integrity.ReleaseInventoryTest.test_repeated_support_output_uses_the_same_byte_budget
```

退出码 `1`，`Ran 4 tests in 0.613s / FAILED (failures=5)`。原实现把所有放大输出构造完，最终才报 `release bundle files, bytes or modes differ from source renderer`，没有在单文件、累计或文件数上限处停止；因此未满足用例要求的 `render_output_budget_exceeded`。跨 target 子例单独失败，避免只给每个 target 重置预算的伪修复。

## Lint 范围与实际失败

主 Agent 的真实 CI focused lint 报告 `release_contract.py` 的 `I001`：compiler import 需排在 contracts import 前。已用 apply_patch 仅修正导入顺序，随后 `ruff check --select E4,E7,E9,F,B,UP,SIM,I src/agent_dev_kit/distribution` 实际 exit 0。

实现者额外把同一严格 profile 试用于 CI 此选择范围外的 legacy `targets.py` / `compiler.py`，实际 exit 1 / 56 项，主要为既有 `typing.Optional/Dict/Tuple` 与 `.format` 风格（新增参数沿用该文件风格），另有现有 alias import block 排序。没有批量改写这些非本次预算缺陷；它们的项目默认 lint、mypy 和实际 CI distribution 选择均通过。该额外检查不记为 PASS，也不改 lint 配置来隐藏结果。

## 独立复核的三个 P2 与实现前 RED

独立 reviewer `ai/root/release_governance_audit` 使用真实公开 `validate_release_artifact` 找到三项遗漏。原始脚本与输出保存在 `/workspace/scratch/712af632e2a5/apply20261024/review-f1/`；没有覆盖其 RED，也没有改变探针断言：

- `probe_native_schema_offline.py` / `native-schema-offline-v2-red.*`：runtime conformance 的第三份 Native receipt schema 可以请求外部 `$ref`；`urllib.request.urlopen` 在测试边界被拦截，实际网络 I/O 为 0。
- `probe_support_containment.py` / `support-containment-red.*`：归档可放宽自身 schema 并把 support root 指向临时目录，原 renderer 先 `rglob`，逐文件 containment 才拒绝；独立探针实际委托遍历一个自建无害文件，未读该文件正文。
- `probe_native_execution_boundary.py` / `native-execution-red.*`：使用未修改的完整 Native receipt schema、合法 receipt 结构和包内 enabled authority，能够到达归档指定的 `/usr/bin/true verify-blob …` 调用；在 `subprocess.run` 前拦截，实际执行为 0。这证明自报二进制摘要和 source inventory 不能充当宿主执行授权。

实现者按冻结验收新增真实归档回归，在生产修复之前执行以下方法：

```text
python3 -m unittest test_release_integrity.ReleaseInventoryTest.test_native_receipt_schema_is_checked_before_reference_resolution test_release_integrity.ReleaseInventoryTest.test_local_native_schema_preserves_receipt_validation test_release_integrity.ReleaseInventoryTest.test_external_support_root_is_rejected_before_filesystem_inspection test_release_integrity.ReleaseInventoryTest.test_archive_registry_cannot_authorize_host_native_verifier_execution
```

实际退出码 `1`，`Ran 4 tests in 0.356s / FAILED (failures=4)`。`$ref` 与 `$dynamicRef` 各触发一次被拦截的 urlopen；support 记录为 `['exists', 'rglob']`；执行反例使用当前 Python 解释器路径及真实 SHA256，观察到一次 `verify-blob` subprocess 调用并在执行前阻断。原始完整记录为 `/workspace/scratch/712af632e2a5/apply20261024/adk-f1-review-regressions-red.{json,stdout,stderr}`，stderr SHA256 为 `9a4bc00133718d4b0d29ebe8fe2f2699aab1809f26f9a8377413db42c811320e`。

修复后的同一安全验收全部通过，stdout/stderr 和实际命令见 `adk-f1-review-regressions-green.*`。默认本地 receipt 的正向控制迁至显式 `load_target_contract` 与 `_load_historical_target_contract`，因为冻结设计要求公开 release 在 receipt 验证之前拒绝归档 runtime conformance；公开入口另以完整 receipt 反例断言 managed verifier 构造与 subprocess 均为 0，没有以不完整 receipt 提前失败来替代执行边界验证。后续原本地 managed Native 成功用例、安装恢复、整包与历史时钟正控制均保持通过。
