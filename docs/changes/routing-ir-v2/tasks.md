# 任务：routing-ir-v2

- [x] 固定三条组合否定复现输入与原始输出。
- [x] 冻结目标、范围、兼容性和回滚边界。
- [x] 扩展 manifest schema 与 JSON/YAML routing 合同。
- [x] 实现 task mode、局部否定、组合 negated intent 和 abstain。
- [x] 增加三条反例、对应正例、近义否定 metamorphic、多轮 latest-turn 和 schema/投影合同测试。
- [x] 执行定向、quick 与适用完整回归。
- [x] 复审风险并记录最终验证证据。

## Ownership

- scope_write：`manifest.json`、`manifest.yaml`、`manifests/manifest.schema.json`、`src/agent_dev_kit/matcher.py`、路由 tests 与本目录。
- scope_read：Skill frontmatter、现有 matcher 调用方和综合设计评估报告。
- 冲突边界：不修改 Profile、Workflow、Agent、Skill 正文或其他并行任务文件。

## 验证证据

| 命令 | 结果 |
|---|---|
| `rtk tests/test_match_effectiveness.sh` | 39/39 pass，含三组 contrastive、6 类近义否定 metamorphic、两组 multi-turn、intent 权限上限、否定 non-trigger 和 review→readonly 映射 |
| `rtk bash -lc 'PYTHONPATH="$PWD/src" python3 -m unittest tests.test_routing_ir_contract'` | 3/3 pass，含 phrase class fail-closed 与 routing matrix 强投影 |
| `rtk tests/test_boundary_conditions_match.sh` | 39/39 pass，现有正向关键词与边界兼容 |
| `rtk tests/test_product_maturity_v4.sh` | pass，含 routing IR/version/permission/negated intent schema 负例 |
| `rtk tests/test_effect_eval.sh` | pass |
| `rtk tests/test_format.sh` | pass |
| `rtk tests/test_skill_trigger_matrix.sh` | pass |
| `rtk tests/test_runtime_control.sh` | 14/14 pass；routing artifact mode 映射闭合到 Runtime Control v2 canonical modes |
| `rtk scripts/devkit.sh validate --strict --summary-json` | pass；当前 Python 3.8.10，仅属 development evidence |

共享 quick suite 曾在并行官方来源任务的 `test_official_docs_timezone` 中间态提前停止；主线恢复后 strict validation 已重跑通过。Python 3.11/3.12 release evidence 由主线统一环境门禁负责。

CR2 首轮发现四个 major：不安全 mode/permission 配对、全局 implementation signal 放宽 intent 权限、
否定 non-trigger 误 veto、routing mode 与 Runtime Control mode 未闭合。四项均已实现修复并加入回归，
原 reviewer 复审确认 blocker=0、major=0；其新增的“task mode signal 可重复/遗漏”minor 也已通过
五种 signal mode 各恰好一次的 schema 和删除/重复负例关闭。
