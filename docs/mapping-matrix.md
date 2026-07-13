# Mapping Matrix

| Capability | Boundary | Entry |
|---|---|---|
| 资产安装 | 按声明式 tool target 执行 plan/apply/receipt/rollback | `agent_dev_kit.installer`、`scripts/devkit.sh install` |
| 可选技能注入 | 按需导出 optional skills，不影响默认 profile | `optional-skills/`、`scripts/devkit.sh export --with-optional-skill` |
| 资产编译 | 确定性导出多目标目录结构与元数据 | `agent_dev_kit.compiler`、`scripts/devkit.sh export` |
| 运行态边界 | 确保 ADK core 不暴露平台绑定交付路径 | `scripts/check-runtime-boundary.sh`、`scripts/devkit.sh runtime-boundary` |
| 官方参考治理 | 官方来源 freshness 与 promoted contract 门禁 | `scripts/check-official-docs-governance.sh` |
| 流程工件化 | 统一 propose/apply/verify/review/archive 交付链 | `scripts/workflow.sh`、`docs/changes/`、`manifest.json:change_sets` |
