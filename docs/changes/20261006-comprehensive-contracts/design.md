# 设计、迁移与回滚

安装复用 strict_json 的单一解码器。regular_only 使用 O_NOFOLLOW/O_NONBLOCK 打开叶节点并 fstat 校验常规文件，避免检查后叶节点变为链接或 FIFO；不具备安全打开能力的平台拒绝该操作。此规则不宣称父目录身份/并发内容快照锁定；plan/receipt 原 digest 和事务校验继续负责语义完整性。

此能力检查同时影响计划安装与读取 receipt 的校验/回滚入口。未提供这些 descriptor 能力的平台（例如部分 Windows Python 环境）不再维持旧的不安全文件读取能力；应在采纳前核实能力，保留原发行版作为明确回滚选择，不能自动降级到 Path.open。平台中立资产模型与导出不等于所有平台可执行安全安装。

producer/readback 使用同一严格 JSON 字节和深度预算。write_plan 先序列化校验，再创建输出目录；安装在事务目录/资产写入前按所有条目都需要 backup 的保守上界预检 receipt，发布实际 receipt 前再次校验，异常仍走原 rollback。保守预检可能拒绝靠近 4 MiB 边界的大 bundle；超限应拆分显式安装边界，不能产生成功但无法读取/回滚的 receipt。获取现有 TargetLock 的元数据写入不属于资产部署，预检不宣称该锁也无写入。

运行扫描保留原 rg 参数，显式区分 rc=0 命中、rc=1 无命中、rc>1 扫描失败。工具缺失及错误进入原失败集合。

maintenance_plan 只清点显式 root 下 `.cache` 与 `dist` 的元数据，不读文件内容或生成文件摘要。目录通过打开的父目录 descriptor 做相对 stat/open，拒绝链接跟随并核对 inode/device；2000 条、64 层限制及保护目录使报告有界。不输出执行许可，不删除、不 chmod。平台能力不足或竞争变化导致 blocked；此计划不是原子快照，也不授权后续执行。

## 8.0.0 公开 CLI 迁移

- `performance.sh optimize` 与 `auto-ops.sh cleanup/optimize` 由旧的 pass 摘要变为 `schema=adk-maintenance-plan/v1`、`status=planned`、`applied=false`、`execution_supported=false` 的只读候选。调用方应按这些字段显示报告，不将 exit 0 当执行成功。
- 维护 `--apply` 返回 blocked、exit 2；`--force` 不能绕过。移除自动化中的维护 `--apply`/`--force`，保留 report-only。daily/weekly/monthly/security 的默认只读命令保留；它们使用 --apply 同样拒绝，不能依赖旧的写入行为。
- `performance.sh report --summary-json --out PATH` 只有实际写出指定报告后才返回 written=1；报告输出不属于维护清理许可。
- 现有运行资产构建/安装/发布的 apply 契约没有被此维护 CLI 退役替代。未来若增加执行器，必须独立审查 action/path/identity/budget/receipt，不复用本报告的候选作为许可。

调用点检索覆盖 scripts、tests、docs 和 README；源仓唯一旧 --apply 示例已改为 summary-json。外部消费者必须在采纳 8.0.0 前核实自己的自动化；现有运行 profile 不由此变更自动重选。

回滚锚为 7.14.2 exact main e9fab289；保留工作树和已签名发布身份。回滚源码会恢复旧维护 --apply 风险，使用旧版本时仍应禁用这些维护写命令。未进行真实模型、签名重建或 runtime 部署，不能将候选声明为 production-ready。
