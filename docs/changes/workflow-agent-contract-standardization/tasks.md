# Tasks: workflow-agent-contract-standardization

## Ownership 与并行冲突检查
| Task | Owner | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| workflow-contract | Codex | `manifest.yaml`, `workflows/`, `scripts/validate-assets.sh`, `scripts/check-workflow-closure.sh` | runtime live dirs | `rtk bash tests/test_workflow_contract.sh` |
| catalog-matrix | Codex | `scripts/catalog-assets.sh`, `docs/agent-skill-catalog.md`, `docs/workflow-contract-matrix.md` | skill bodies | `rtk bash tests/test_catalog.sh` |
| agent-contract | Codex | `manifest.yaml`, `scripts/validate-assets.sh`, `docs/skill-agent-runtime-model.md` | `agents/*/AGENTS.md` content semantics | `rtk bash scripts/devkit.sh validate --strict` |

## 轻量工件与收敛结论
- 新增 6 个 Workflow 契约文件。
- 新增 Agent Contract Matrix 与独立 Workflow Contract Matrix。
- 新增 workflow contract 测试并纳入全量回归。
- 收敛结论以 strict validate、全量回归和 source-to-live dry-run 为准。
