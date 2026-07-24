# 设计说明：terminal-maturity-optimization-v2

## 架构影响
- 根测试新增 `tests/run_all.sh`，负责枚举并执行全部 `tests/test_*.sh`，输出
  有界失败日志、计数和可选 timing JSON。
- `scripts/check-root-regression.sh` 作为 `check-all.sh` 自动发现入口；只
  调用根测试 runner，不复制测试清单。
- `scripts/check-all.sh` 保留直接 gate 语义，同时在失败时输出有界日志，
  支持 `--result-json` 机器证据，避免删除唯一根因。
- `test_architecture_reports.sh` fixture 与 checker 当前 SSOT 合同对齐。
- ADK `scripts/devkit.sh` 增加显式 `ADK_PYTHON_BIN` 选择、解释器存在性和版本
  提示；`doctor` 始终可用于诊断，release/test 类命令可选择严格支持门禁。
- product maturity scorecard 新增 `effective_level` 与状态语义，effective
  level 固定为 implementation/evidence 较低者。

## 数据与配置影响
- 根 full JSON 增加 schema、mode、total/pass/fail、elapsed、checks。
- scorecard 保留原 `level/implementation_level/evidence_level/status`，
  新增 `effective_level` 和顶层语义，避免破坏旧 reader。
- 不改变 Software M5 blocker、ledger hash chain 或现场证据阈值。

## 兼容性与迁移方案
- 既有 `check-all.sh --smoke|--quick|--full|--verbose` 保持兼容。
- 新增参数均为 opt-in；默认人类摘要保持。
- `ADK_PYTHON_BIN` 未设置时继续使用 `python3`，但输出的 unsupported 状态必须
  可操作；严格验证使用 Docker parity 或受支持解释器。
- scorecard consumer 可忽略新增字段；新 tests 要求字段与旧字段一致。

## 验证策略
- 红灯：保存根 52/58、根测试 13/15、architecture fixture 和 doctor failure。
- 定向：architecture/current-status/product maturity/root runner/check-all
  fixture。
- ADK：strict、security、release、target static、57 项 full。
- 支持矩阵：Python 3.11/3.12 local-CI quick；候选收口前 full。
- 根：全部 root tests、`check-all.sh --quick`、`check-all.sh --full`。
- 交付：`git diff --check`、session coach、`final-ready.sh`。

## 执行与恢复
- retry budget：同一根因 2 次；第三次前 replan。
- workflow `verify-failed` 必须是可恢复重试状态；修复工件后由同一 change
  重新 verify，禁止手改 state 或重建工件掩盖首轮失败。
- staleness threshold：45 分钟或每完成一个 T 项更新状态。
- stop condition：`pass | replan | split | blocked | abort`。
- 外部 blocker 只允许 `blocked_external`，不得改成 pass。
