# 评测输入与跨目录回归可靠性

用户授权 ADK 全面内部审查与本地迭代。目标是使重复 trial 评测文件拒绝歧义 JSON，并使全回归入口在父仓或其他 cwd 正确运行。

- 范围：effect_trials 文件解析、tests/run_all.sh；不改变 schema、评测统计、发布权限与运行部署。
- 验收：根级和嵌套重复 JSON 键拒绝；合法输入不变；父仓调用 full suite 正确选择 ADK tests 包和资源目录。
- 风险：之前依赖 JSON last-key-wins 的歧义输入将被拒绝，需修正输入后重跑。
- 回滚：仅回退本 change 的解析与 runner 修改；不触碰已有用户改动。
