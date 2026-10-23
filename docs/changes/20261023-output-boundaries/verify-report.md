# 输出写入边界实施验证

## 实施结果

实现者：`ai/root/implement_paths`。固定父提交：`bf9ec8164e2c80394ce997f8a8b51515cad4746e`。本阶段完成 ADK-06、ADK-04、ADK-05 的代码修复与定向验证；独立审核、全回归、版本整合及远端发布由主 Agent 继续执行，未在此声明闭环完成。

- compiler 复用 installation_contract 的原始路径检查；保留请求的 root/target，在获取锁后和发布前复核原始路径与 inode 身份。目录链接不再经 resolve 获得清理权限。
- Native prepare/run/finalize 入口预检所有输出、输入路径，拒绝目录/FIFO、路径/硬链接别名、输入输出冲突、祖先链接和输出父子重叠；运行前及实际发布前均检查。
- Native 原先重复的临时文件写入实现已移除，统一由 atomic_io 发布。批量先完成全部编码和 staging；后项失败按原始文件恢复先前项及 mode；恢复自身失败保留原始备份并报告具体路径。
- 多文件发布使用补偿恢复，不是崩溃原子事务；沿用 caller-owned parent / writer 前提，不声明能防御所有同用户恶意并发改目录行为。

## 新鲜验证

| 范围 | 结果 |
|---|---:|
| Native campaign 全部单测 | 34/34 通过 |
| 安装升级 + export 边界 | 12/12 通过 |
| 安装 receipt 权威 | 8/8 通过 |
| Native 模块边界 | 3/3 通过 |
| Ruff：4 个生产文件、2 个测试文件 | 通过 |
| Mypy：4 个生产文件 | 通过 |
| owned files `git diff --check` | 通过 |

共 57 项定向测试。本轮新增 16 个行为测试方法，覆盖同根/根外链接、锁后和 staging 后路径变化、真实无害 stage 在非法输出下不执行、批量编码/staging 失败、late I/O 补偿和无法恢复时的材料保留。逐文件 SHA-256、原始命令输出与时间见 `evidence/regression-green.json`；先失败的原始证据见 `evidence/regression-red.json`。

## 调用点与迁移

修改前检索了 compiler.export_assets 的 CLI、release、quality、target-source-probe 与测试调用点；Native 三个动作及 `_write_json` 直接测试；atomic_io 已有安装/锁调用保持原接口。没有增加兼容 shim 或平行路径模块。

合法 CLI 参数保持。输出路径含 `..`、原始路径中的祖先链接、FIFO 和冲突别名改为拒绝；调用方应传明确的普通路径。既有正常 export 清理、替换失败恢复及 Native prepare → run → finalize 控制继续通过。

## 尚未关闭的独立事项

Native 既有 exited-launcher pipe-drain 测试仍产生 asyncio ResourceWarning / Event loop is closed，命令 exit 0；这是未改动 executor 的资源清理问题，原始日志保留且已报告主 Agent。本阶段不伪称已修复该告警。

环境没有 `~/codex` Knowledge Provider / Execution Policy；没有把本地 conformance 记作项目验收。没有运行真实付费模型、现场操作、签名认证或 live apply。
