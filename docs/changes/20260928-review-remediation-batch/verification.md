# 本地验证与剩余门禁

## 已验证

- Python 3.8：`rtk bash tests/test_runtime_comparison_contract.sh`，14 项通过；覆盖缺字段/错误类型、敏感错误文本、provider 参数、逐例模型错配与费用确认。
- Python 3.8：`rtk bash tests/test_effect_eval.sh`、`rtk bash tests/test_software_m5_ready.sh` 通过；混合高风险意图与重复 JSON/非有限阈值反例已加入。
- `rtk scripts/devkit.sh validate --strict`、`rtk bash scripts/check-runtime-boundary.sh`、`rtk bash tests/test_module_size_budget.sh`、`rtk bash scripts/devkit.sh release check`、`rtk git diff --check` 通过。
- 最新全套回归为 96 项中 95 通过、1 失败；唯一失败是 `test_runtime_bundle` 要求 clean Git source。直接运行 identity verifier 明确返回 `release build requires a clean source distribution worktree`，门禁未放宽。

## 未闭环

- `test_runtime_bundle` 的三个功能单测通过，但后续 clean Git commit 身份步骤因当前脏源码树退出；此门禁必须在冻结提交后重跑，不降低身份要求。
- 未执行真实 Codex/Claude 调用，模型行为、实际费用与 provider CLI stdin 行为未获得服务端证据；目前仅以本机 CLI 帮助和 mock 验证。
- 根仓隔离工作树持续修复验证计划、外部实践与 ADK JSON Manifest 入口、采纳证据路径和运行源边界；`check-all --quick --working-tree` 从 38/52 改善为 49/52。剩余 cosign、参考仓 baseline 到期和 Software M5 证据身份三项保持阻断。根仓全套回归因 Python 3.11 环境缺少 `jsonschema` 未完成；固定 ADK 子仓在临时解释器映射下 quick 49/49。

## 收口判断

本批源码与确定性测试可审查；不能据此声明运行时生产可用、全仓通过、可发布或 source-to-live 完成。下一轮优先解决根仓旧 manifest 检查入口、M5 证据漂移与 Python 3.11 测试依赖，再做一次完整复核。
