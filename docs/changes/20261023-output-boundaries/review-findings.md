# 独立 Spec / Quality 审查

审查者：`ai/root/architecture_audit`；实现者：`ai/root/implement_paths`。两者为不同 Agent 身份；本审查者未实现这批修复。负责 Owner 为 `leiwenjun`，执行依据是仓库已记录的明确自动审核委派。

## 审查对象和方法

本次完整读取 requirements、design、tasks、verify-report、negative-results，并逐段审查 `atomic_io.py`、`compiler.py`、`native_campaign.py`、`native_campaign_contract.py` 的当前实现和 Git diff，以及 `test_install_upgrade.py`、`test_native_campaign.py` 中对应回归。另检查被复用的 installation path policy、writer lock 与 review validator，核对调用顺序、失败边界和真实证据适用范围。

独立命令于 `2026-10-23T12:05:20.352386Z` 完成：18 项聚焦行为测试全部通过，耗时 11.148 秒；被审查的六个文件执行前后 SHA-256 一致。真实 argv、完整输出、时间和摘要记录在 `evidence/independent-review-execution.json`。另外重新调用本审查者在修复前写下的同根符号链接反例，当前实现返回 `export target must not use symlink aliases`，没有再返回成功。

## Spec 结论：PASS

1. 原始导出根/target 路径保留到入口、锁后和发布前检查；对根内或根外链接、root 祖先链接的拒绝不依赖 resolve 后的 containment。已有普通目录替换及失败恢复仍可工作。
2. Native prepare/run/finalize 在进入各动作前统一预检完整输出集合，普通叶类型、父目录、重复路径、父子输出、硬链接和输入输出别名均受约束。已知非法目录/FIFO 在 discovery/load/trigger 前拒绝，真实无害 stage marker 保持不存在。
3. `_write_jsons` 在任何 staging 前完成所有 JSON 编码和字节预算检查，`write_texts_atomic` 在全部 staging 完成后才发布。已知非法第二输出与编码/staging 失败不改变已存在的第一输出。
4. 后项发布失败会按逆序恢复原有输出与 mode；恢复失败时原始备份保留，错误给出可恢复位置。正常单文件、双输出及现有 CLI 参数保持。
5. 原有 runtime 认证、签名及产品授权边界未被提升；测试只使用本地无害 fixture。

## Quality 结论：PASS

- 路径策略复用 `installation_contract._regular_install_path`；批量文档发布归属 `atomic_io`，Native 不再维护另一份临时文件写入逻辑。
- 对拒绝路径的检查发生在写入或真实 stage 之前；发布前还会重新读取原始 CLI 路径，未因首次 resolve 丢失路径身份。
- 多输出事务显式区分 staging、原始文件备份、已发布项与补偿失败；不把多次 rename 宣称为天然原子集合。
- 回归来自原始缺陷与验收边界，包含非法输入、晚发 I/O 失败及正常控制；独立审查没有修改源码、测试或测试期望。
- scoped review 未发现尚未解决的 blocker 或 major；完整回归、最终 Git 提交绑定、受保护 CI 与发布由协调者继续核验。

## 独立执行覆盖

18 项用例覆盖：export 链接拒绝和锁后/staging 后变更、普通替换和恢复；JSON 全集合编码与单叶链接拒绝；prepare 同路径/硬链接/输入别名/父子重叠/非法第二输出/外部祖先链接；后项发布失败恢复新旧两类输出；staging 失败保留原始材料；恢复失败留存；run 目录/FIFO 在真实 fixture stage 前拒绝；finalize 的输出别名、输入冲突和目录预检。

## 限制和未声明事项

- 本结论覆盖上述六个文件及其既有调用边界。执行时验证的是工作区内容，最终 canonical `review-evidence.json` 必须另外绑定实际存在的 base/head 与完整原始 Git patch；不会为尚未存在的提交填写身份。
- 父目录与并发写入者仍由调用者管理。实现提供入口/锁后/发布前复核与补偿恢复，不宣称抵抗所有同用户恶意目录重命名，也不提供跨文件系统或崩溃原子事务。
- 实现者日志中已有 Native executor 的 asyncio transport 清理告警属于未改动执行器；本次选取的 18 项输出边界用例没有重跑该单独的 pipe-drain 告警场景，不能宣称该告警已修复。
- 无真人审核、真实 Native provider 执行、可信签名、G22 effect 测量、LTA 现场观测或 Product M5 放行。摘要只能绑定内容，不能认证声明的 Agent 身份。
- `~/codex` Knowledge Provider / Execution Policy 在本环境不可用；未声称其 gate 通过。首次探索 Harness CLI 使用了不存在的 `--mode report-only` 参数并被 argparse 拒绝；读取入口后改用默认 report-only，不把该用法错误列为仓库缺陷。

## 最终 Git 绑定

本审查者已通过真实 Git 对象确认 implementation head `c06fd629fa9a08f3079e7a606f45e65fcccbfc28`、tree `87293e6c835585d7084077dc57184842548c6180`，其父提交为原基线 `bf9ec8164e2c80394ce997f8a8b51515cad4746e`。后续 canonical 记录保存该实际 base → head 的完整原始 Git patch，并逐文件核对独立测试时的六个文件及最终 head 的 blob 字节。

完整 patch 也包含并行实施的 release-contract 和共享版本整合；本结论仅授予上述 output-boundaries 范围的 Spec / Quality 判断。发布实现由另一个独立 reviewer 审查，完整 Git diff 的保留不表示本 reviewer 声称审过所有并行代码。
