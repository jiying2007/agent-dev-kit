# Mapping Matrix

| Capability | Boundary | Entry |
|---|---|---|
| 资产安装 | 按声明式 tool target 安装 Agents/Skills | `scripts/install-assets.sh`、`scripts/devkit.sh install` |
| 可选技能注入 | 按需导出 optional skills，不影响默认 profile | `optional-skills/`、`scripts/devkit.sh convert --with-optional-skill` |
| 资产转换 | 导出多目标目录结构与元数据 | `scripts/convert-assets.sh`、`scripts/devkit.sh convert` |
| 运行态边界 | 确保 ADK core 不暴露平台绑定交付路径 | `scripts/check-runtime-boundary.sh`、`scripts/devkit.sh runtime-boundary` |
| 官方参考治理 | 官方来源 freshness 与 promoted contract 门禁 | `scripts/check-official-docs-governance.sh` |
| 流程工件化 | 统一 propose/apply/verify/review/archive 交付链 | `scripts/workflow.sh`、`docs/changes/`、`manifest.yaml:change_sets` |
