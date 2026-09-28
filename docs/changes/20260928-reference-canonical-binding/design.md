# 设计与观察证据

2026-09-28 使用根仓隔离 worktree 的显式 `--allow-network` 只读远端审计，复核当前 pin manifest 与 registry 摘要后观察四个仓的 exact HEAD。OpenSpec 与 planning-with-files 为 `different`，VibeFlow 与 Scale Engine 为 `same`；工具没有执行 ancestry 检查或 checkout 写入。仓库规范地址也与 [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)、[ttttstc/vibeflow](https://github.com/ttttstc/vibeflow) 和根仓受管 pin 清单交叉核对。

既有 method-only manifest 保持单一 SSOT：改 `url` 为当前规范地址，旧别名移到 `historical_url`；加入 `reference_pin`、`remote_head_observed`、`remote_relation`、`canonical_checked_at`、`ancestry_checked=false`。没有声称历史方法在这些 exact pin 上被重新评审。checker 对本地参考项执行 HTTPS 主机、40 位 SHA、关系、日期及同仓重复记录一致性核验；默认仅离线读取 manifest，`--manifest` 只供受控测试替换输入。
checker 的默认和测试输入共享 2 MiB 有界读取、非 symlink、UTF-8/唯一 JSON 字段检查；不因测试覆盖入口而给未审文件放宽门禁。

可选 `--reference-lock` 在 1 MiB、非 symlink、唯一 JSON 字段预算内读取根仓 `reference_pins/v2`，核其 `pin_is_evidence_not_source=true`、`runtime_enablement=false`，并按 local_path 比较规范 URL 与 exact pin；`.git` 后缀只作传输形式归一。`--max-observation-age-days` 是显式 opt-in 的新鲜度门禁，默认不对历史观察自动宣称 current。该对照借鉴 [SLSA Source 验证](https://slsa.dev/spec/v1.2/verifying-source)区分仓库 URI 与 revision 的方法，但没有证明 SLSA provenance、远端 HEAD 真实性或提交祖先关系。

回滚可恢复 manifest 字段和 checker/test 变更；没有运行态迁移、自动 fetch、安装或外部写入。
