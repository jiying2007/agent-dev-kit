# 负结果：trace-summary-contract-v2

| 阶段 | 观察 | 根因 | 修复 | 复验 |
|---|---|---|---|---|
| 首轮兼容回归 | runtime boundary 拒绝测试中的 `codex-app-server` | 通用 ADK 测试引入平台专属 runtime 名称 | 改为 `local-agent-runtime` | runtime boundary 通过 |
| 首轮兼容回归 | official docs governance 报 v2 缺基础 trace 字段和合同键 | 新 v2 首稿只覆盖新增 R7 指标，未延续既有 trace evidence 基线 | 补齐严格 typed goal/prompt/tool/handoff/guardrail/verification/blocker/failure/next-goal 及 contract metadata | official governance 通过 |
| 质量工具 | `rtk ruff ...` 无法启动 | 当前环境未安装 ruff | 使用仓库 `test_format.sh`、120 列扫描、`git diff --check` 和 quick suite 作为替代证据；不冒充 ruff 已通过 | 替代检查通过；ruff 保持 not-available |
| 并行 quick | 27 个子测试通过后聚合脚本收尾出现 unmatched quote | suite 运行期间共享 `run_all.sh` 被并行任务改写，运行快照不一致 | 等待并行写入稳定，先执行 `bash -n`，再从头复跑 quick | 当前 quick 28/28 通过 |
| emitter 宿主测试 | import 阶段报 `dataclass() got an unexpected keyword argument 'kw_only'` | 宿主 development lane 为 Python 3.8，`kw_only` 是 Python 3.10+ API | 改用普通 frozen dataclass，调用方继续显式 keyword 构造 | 宿主 `test_trace_summary.sh` 12/12 通过 |

上述失败均未通过弱化门禁处理；没有修改 runtime boundary 或 official governance checker。
