# 从只读审查交接到实施

`review.json` 是已结束的只读审查及本轮授权，保持原样。所有 finding 共用这一个原验收项。输出 `handoff.json`，包含 `criterion_id`，以及按 finding 原顺序排列的 `batch`、`excluded`、`early_gate` 三组 ID。局部可逆项组成一批，误报排除，涉及共享契约的项进入提前门禁。该局部批次在批末集中验证一次，`batch_verification_runs` 用整数记录这一次批末验证，提前门禁另计。此题只交付计划，实际实现和验证交由后续执行者。
