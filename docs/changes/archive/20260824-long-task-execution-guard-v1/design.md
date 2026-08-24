# 设计说明：long-task-execution-guard-v1

## 架构影响
- D1：`execution_guard.py` 是 pure evaluator；CLI 只加载 JSON、传 as-of、输出 summary/exit code。
- D2：复用 token monitor summary schema，不导入 provider adapter 或事件 history。
- D3：决策优先级：invalid completion > stale/retry exhausted > token action > continue；合法 completed pass。

## 数据与配置影响
- D4：新增 `long_task_state/v1` 与 `execution_guard.decision/v1`，无 manifest schema 变化。
- D5：证据使用 bounded stable IDs/relative refs；输出仅 counts/missing IDs，不输出 open item 正文。

## 兼容性与迁移方案
- D6：additive CLI；现有 Skill/runbook/fixture contract 保持，后续 runner 可选择消费。

## 验证策略
- unittest + CLI：fresh continue、stale/retry replan、Token 4 级、complete pass/fail、future/sensitive。
- docs/format/strict、host quick、Python 3.11 full。
