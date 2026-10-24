# ADK F2 独立源码与执行审查

## 结论与范围

审查人 `ai/root/root_code_audit` 对 F2 范围给出 **Spec PASS / Quality PASS**，没有未解决的 blocker 或 major。本记录是实际独立审查工作底稿，供主 Agent 按既有规范归档；它不是自动生成的 `adk-review-evidence/v1` 收据，也不代替最后实现 commit、完整回归、保护 CI 或发布事实。

审查人没有实现或修改 F2 源码。仅写入本审查目录，分别保留修改前后快照、原始 stdout/stderr、失败记录及环境对照。F1 对 `targets.py` 的渲染预算改动由另一位独立 reviewer 审查；本次审查聚焦其 smoke 调用路径。

已阅读仓库规则、F2 requirements/design/tasks、共享进程 owner、Native 调用迁移、target smoke、原始测试与业务文档。独立执行既有原测试和额外的真实子进程反例。最后执行的七个源码/测试文件在复制前、原仓验证后、快照验证后的 SHA256 完全一致。

## 最后源码绑定

| 文件 | SHA256 |
|---|---|
| `src/agent_dev_kit/process_execution.py` | `01e3da0bc9cee08055dafafb178c270f8e6ece2a18de2ad542027a1b252d5b9d` |
| `src/agent_dev_kit/native_campaign_execution.py` | `4855a70b34ec92839c0b7f52e750f534b031c7f23e9bdc6311bfd9c26d2fc397` |
| `src/agent_dev_kit/targets.py` | `a188891cb0569a1b4cea7721aea51d8770b218fe7f62cbfa2e2ed18b57456d6a` |
| `tests/test_target_smoke.py` | `fb941ffdbd753eefa16d7b8178144543c77895665a0dd8935359bb891e5fa7b9` |
| `tests/test_target_contracts.sh` | `74b8741210c9c1f173a9068744a66e1ccf39a94ca900341dfa3e141e7299d669` |
| `tests/test_native_campaign.py` | `fc188ae2fc5d69c37c1288c2f9a922ea4b00761afddaff0d10a61a4978812076` |
| `tests/test_native_campaign_boundaries.py` | `2db0cadb3965b9e9ac3062c31bd567499d45203c321df4c59f2f451853b7724d` |

`run_target_smoke` 的 AST 原文 SHA256 为 `ecf2f92f2d7ab55e3c473b5e607d61ee4fde0dabc933bac9617a502545a514e8`。最后快照为 `source-snapshot-final/`，详见 `executions-final.json`。源码 baseline HEAD 为 `415590db44e88979185efb850e2339a3f95411ef`，最终实现 commit 由主 Agent 随后绑定；不得把这个 baseline 当作本次已实现树的身份。

## 独立验证结果

最后一轮通过标准执行环境运行，原测试未改变断言或预算。

| 验证 | Python | 结果 |
|---|---|---|
| `bash tests/test_target_contracts.sh`，包含原始 smoke 9 例 | 3.8.20 | exit 0；9/9，9.585 秒；shell 总 17.635 秒 |
| `bash tests/test_native_campaign.sh` | 3.8.20 | exit 0；34/34，10.625 秒 |
| `test_native_campaign_boundaries.py` | 3.8.20 | exit 0；3/3 |
| 审查人新增的 7 组真实进程反例 | 3.8.20 | exit 0；7/7；6.287 秒 |
| 同一 7 组反例，最后源码 | 3.12.14 | exit 0；7/7；5.923 秒 |
| 新共享模块 focused ruff：E4/E7/E9/F/B/UP/SIM/I | 3.12.14 | exit 0 |
| 新共享模块 mypy | 3.12.14 | exit 0 |

3.12 最初快照还独立通过 target shell / smoke 9、Native 34、boundary 3；这些历史执行保存在 `executions.json`，不能代替最后源码绑定。共享 owner 的后续差异仅是两处等价 `contextlib.suppress` 清理，最后一轮又真实覆盖了超时和取消路径。

额外反例验证：二进制输出摘要与计数、正常退出 0 与非零 17 的业务结果、stdout 300000 字节加 stderr 748576 字节恰好 1 MiB 成功、再加 1 字节失败、存活 launcher 与忽略 SIGTERM 的后代、launcher 已退出但后代仍持管道、两管道先关闭而进程继续存活、原 Native 业务错误码、异步取消后清理。不存在通过 mock 跳过子进程的情况。两个最终反例记录的 `resource_warnings` 均为空，命令 stderr 为空。

## 生命周期、预算与证据判断

- 单一 event loop 更新 stdout/stderr 合计字节计数；等于限额接受，大于限额拒绝，溢出的 chunk 不进入保留缓存。两流同时输出不能获取两份预算。
- 完成条件以整个 subprocess transport 的 `connection_lost` 为准。直接子进程退出不能绕过后代持有管道时的 deadline；先关闭管道也不能绕过仍存活进程的 deadline。
- 失败先终止原进程组，再关闭 transport，并给关闭回调固定的额外清理等待。清理路径涵盖超时、输出预算错误与取消；没有将取消转换成成功。
- smoke 成功或普通非零退出只返回摘要、计数、退出码和命令哈希；超时与溢出返回固定错误码。保密 canary 和原始 stdout/stderr 均未进入公开结果。
- Native 的原错误映射、业务验证和认证 owner 保持原边界；共享底层 owner 没有新增认证承诺。smoke 仍为 `caller-supplied-smoke`。
- `asyncio.SubprocessProtocol` 与 public subprocess transport 在实际 3.8 上通过，未依赖较新 Python 的 `Process._transport` 私有接口。future annotations 与 typed core 的 3.8 导入、执行均已真实验证。

## 两次环境/审查仪器负例及更正

**审查仪器 PID 误判。** 最初两个额外反例用 `/proc/<namespace pid>/stat` 查询进程状态。该执行器的 PID namespace 与挂载的 `/proc` 身份不同：自身 `os.getpid()=6`，`/proc/self` 中为 `257629`；已死亡 runtime 的 namespace PID 9 被错误对应到宿主 PID 9。实际 `os.kill(9, 0)` 已抛出 `ProcessLookupError`。审查脚本改用同一 namespace 的信号 API，并用后代 delayed marker 独立验证；原始失败保留，生产源码未改。更正后的同一 3.12 快照 7/7 通过。

**Python 3.8 隔离执行假负。** 隔离执行的原始 smoke 9 例有 2 例失败：`test_exact_combined_output_budget_passes` 和 `test_timeout_stops_descendant_before_returning`。后者观察约 6.14 秒，原断言 `<2.75` 未放宽。开始时曾怀疑最低版本回归；回调对照已推翻此归因，不能列作产品缺陷。

同一解释器、源码与诊断脚本的单变量环境对照显示：隔离环境 exact-1MiB 子进程在 0.020028 秒已被 `waitpid` 收割，两个管道也已关闭，但 `process_exited` 回调直到 5.007304 秒的定时器唤醒才执行；标准环境的对应时间为 0.016570 → 0.016704 秒。隔离环境 timeout 的 `waitpid` 在 kill 后立即返回 -9，thread → loop 回调却再迟约 5 秒；标准环境总耗时 1.003224 秒。定位为隔离环境事件循环跨线程唤醒延迟，不能归因于未终止或未收割子进程。

对照文件为 `lifecycle-python38-sandbox.json`、`lifecycle-python38-host.json`。诊断仅在单独 Python 进程中包装回调和 `os.waitpid` 后委托真实函数，源码未改；它用于归因，最终通过结论来自上表未改的原始测试与独立反例。原先隔离长测没有完成的后续命令未被记作通过。

## 保留限制

真实验证平台是 Linux/POSIX，覆盖原启动 session 的进程组；没有认证主动创建新 session 逃离该组的后代，也没有运行 Windows/macOS。仅证明本地软件行为与调用契约，不能升级为 live provider、Native runtime、effect、field、G22、LTA 或 Product M5 资格。固定清理等待仍是 bounded best effort；不承诺 OS 无响应时绝对消灭所有进程。
