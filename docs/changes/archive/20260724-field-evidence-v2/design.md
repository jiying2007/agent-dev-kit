# 设计说明：field-evidence-v2

## 架构影响
- 根仓 `software_m5.py` 继续作为唯一 M5 ledger/event/certifier 实现，不新增第二套状态存储。
- `REQUIRED_FIELD_EVENT_TYPES` 和 `REQUIRED_METRIC_CONTRACTS` 提升为 v2 evidence baseline。
- `_field_progress` 仍只允许 completed independent pilot 进入认证，并增加 selection/baseline/time/reviewer assessment 检查。
- `adk-production-field-readiness` 只增加证据模板和反 KPI 边界，不承担 M5 状态机。

## 数据与配置影响
- 新增 `task_selection_recorded`：`preregistered_task_count`、`accepted_task_count`、`rejected_task_count`、`refusal_log_status`。
- 新增 `human_baseline_recorded`：`baseline_task_count`、`human_estimate_minutes`、`estimation_method`。
- 扩展 `workload_executed`：`preregistered_task_count`、`rejected_task_count`、`wall_clock_minutes`、`human_active_minutes`、`agent_active_minutes`、`concurrent_agent_peak`。
- 扩展 `pilot_reviewed`：`selection_bias_status`、`time_measurement_status`、`confidence_interval_status`。
- 不在 operator ledger 增加 PII；事件 metrics 只保存聚合标量。

## 兼容性与迁移方案
- 保持 event schema v1 和历史事件可读；v2 是 qualifying pilot 的 policy baseline，不改写已有 hash chain。
- 当前 self pilot 不满足新增字段但本来就不能 M5 certify，因此不产生错误的既得认证回退。
- 真实 pilot 若已开始，必须以新事件补充 v2 evidence，禁止修改旧事件。

## 验证策略
- 扩展 `tests/test_software_m5_certification.sh` 的完整 pass fixture。
- 负例：缺 selection event、缺 baseline event、计时字段缺失、review assessment 不完整、operator PII。
- `rtk tests/test_software_m5_certification.sh`
- `rtk scripts/software-m5.sh status --summary-json`
- `rtk scripts/check-software-m5-readiness.sh . --summary-json`
- `rtk scripts/check-all.sh --quick`
