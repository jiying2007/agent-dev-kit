# 设计说明：adk-terminal-contract-hardening

## 架构决策

1. Truthful gate：执行性能工作负载的包装器必须调用同一份 `adk_performance_budgets.json` 严格校验，不能只检查 timing 文件存在。
2. Copy-only contract：当前 installer 只实现 copy 事务，因此 manifest、schema、CLI 和文档统一为 copy；不新增未设计的 symlink 生命周期。
3. Typed manifest：对发布、安装和路由决策有影响的 object 增加 `required`、`properties`、`enum` 与 `additionalProperties` 约束；大而异构的 provenance 数据保持现有专用 checker，不在一次变更中重写全部 schema。
4. Supported runtime：发布基线不继续承诺 EOL Python；CI 至少覆盖新的最低版本与 3.12，依赖下限与安全使用方式保持一致。
5. Controlled CI continuation：远端 CI 临时豁免只允许继续本地开发；用 pinned base digest、只读挂载和无凭证 Docker matrix 提供替代证据，但 release、Software M5、field 和远端状态声明保持 fail-closed。

## 性能门禁设计

- 根 `scripts/check-adk-performance-ops.sh` 运行 quick suite 后，调用 ADK `scripts/check-performance-budgets.sh --strict --timing-json`。
- 增加可注入 timing fixture 的回归路径，证明 `elapsed_ms > max_elapsed_ms` 返回非零，预算内返回零。
- 不把单次基准波动直接写成新预算；若 quick 仍超时，按 timing 子步骤减少重复门禁或拆分快慢路径。

## Manifest 与安装设计

- `install.default_mode` 固定为 `copy`，可选的 `supported_modes` 只允许且必须包含 `copy`。
- schema 明确拒绝未知 install 字段和非法 mode。
- installer 对 `symlink` 继续 fail-closed，并保留稳定错误码，避免行为突然放宽。
- 文档和命令示例不得再承诺 symlink。

## 安全维护基线

- Python 最低版本提升到仍受支持的版本，CI 同步更新最小版本 job。
- PyYAML 下限提升到已修复历史 FullLoader 问题的主版本；源码继续只用 `safe_load`。
- Ruff 与 pip-audit 继续在 CI 固定版本执行；本地若工具缺失，质量入口必须明确报告 unavailable，而不是把未执行记为通过。

## 测试策略

- Level 2：性能假绿、schema 漏检和 Harness 假通过均先有红灯再修复。
- Level 1：pyproject/CI/docs 同步和 copy-only 兼容回归。
- 回归范围：Harness、manifest schema、product maturity、install/export、docs CLI alignment、security、release、quick/full。

## 兼容与回滚

- breaking：最低 Python 版本提升；关键 nested manifest object 改为 typed、拒绝未知字段；在 README/usage/release notes 明示升级和 strict validate 步骤。
- non-breaking correction：symlink 之前已在运行时被拒绝，声明改为 copy 是纠错。
- 回滚锚点：当前 rc.2 manifest/pyproject/CI/docs；回滚后必须继续标记 needs-fix，不能作为 release-ready。

## 外部证据边界

GitHub CI、Scorecard、attestation、真实 runtime 和 30 天 field campaign 不由本地 fixture 替代。相关命令可通过本地静态/计划检查，但 certifier blocker 只在真实证据到位后清除。

本次 owner 授权的 CI waiver 记录在 `ci-waiver.json`，最长 7 天。waiver 到期、源码在取证后变化、替代验证失败或进入 release/certification 请求时立即失效。Docker runner 不接收宿主凭证，不挂载 Docker socket 或 HOME，不执行 push/tag/publish。
