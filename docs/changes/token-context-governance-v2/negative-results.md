# Negative Results

| Attempt | Result | Root Cause | Decision |
|---|---|---|---|
| Codex apply-ready help | fail then fixed | `scripts/apply-ready.sh` 把 `--help` 当 plan path，误执行 build/doctor 后失败 | 增加 side-effect-free help/unknown 参数门禁及非仓 cwd 测试 |
| Codex governance probe | fail, no product defect | 错把 `doctor` 子命令当作支持 `--summary-json` | 改用 `governance-report --summary-json`，保留 CLI 边界 |
| Codex keep receipt test | fail then fixed | fixture 同时包含 generated managed state keep path，错误断言 keep 总数为 1 | 改为断言目标 keep path 存在，不削弱生产门禁 |
| Hub review SLA fixture | fail then fixed | 极简 root 缺少完整 registry，index plan 正确返回 blocked/exit 1，且结果位于 `indexes.by_review_queue` | 测试允许治理诊断 exit 1，并读取 canonical JSON 路径 |
| root full gate first pass | 60/61 then fixed | `check-workspace-entrypoints` 的 health summary 仍走 release-clean subrepo gate，未继承 working-tree 模式 | health/workspace/check-all 增加显式 gate mode；最终 full 61/61 |
| Hub candidate first dry-run | blocked, no writes | 自由文本 scope 不符合 `project-specific` 枚举；error summary 同时遗漏 error 字段 | 使用合法 scope，并保留 error/dry_run 与 applied write_count 的 summary 回归 |
| smoke latency target | 27s, accepted with evidence | live footprint 7s、routing 6s、evidence bundle 10s；继续压缩会扩大运行逻辑改动 | 保留 13/13、reuse=7 与 slowest evidence，后续单独优化 runtime-live |
