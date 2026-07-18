<!-- repo-intro:start -->
## 仓库介绍（持续维护）

- 仓库名称：`agent-dev-kit`
- 仓库定位：通用 ADK Agent/Skill 资产与工作流门禁工具包，当前深度覆盖嵌入式全栈开发
- 领域范围：core 保持平台中立；`embedded-fullstack` profile 覆盖芯片/板级约束、启动链、BSP、OS/runtime、驱动、中间件、协议栈、设备应用、上位机/产测/诊断工具、构建调试、验证、发布、量产和现场维护
- 维护状态：持续维护（人工 + Agent 协作）
- 维护目标：在不偏离上游核心定位的前提下，保持中文可读说明、可执行流程与可验证交付。
- 维护边界：默认优先更新文档、规则与配置；涉及大规模重构或行为变更需先评估影响并记录。
- 最小验证：`bash scripts/devkit.sh test`
- 维护记录：建议在每次关键调整后追加"变更摘要 + 验证结果 + 日期"。

<!-- repo-intro:end -->

# Repository Guidelines

## Project Structure & Module Organization
- `agents/`: role-specific agent instructions (`agents/<name>/AGENTS.md`).
- `skills/`: core reusable skills (`skills/<name>/SKILL.md`).
- `optional-skills/`: opt-in skills, only installed/exported when explicitly requested.
- `src/agent_dev_kit/`: typed manifest、compiler、installer、quality、evaluation 和 release core。
- `scripts/`: `devkit.sh` 稳定包装层及 legacy governance check entrypoints。
- `docs/`: usage, commands, workflow guide, runbooks, change artifacts.
- `tests/`: shell-based regression suite and fixtures.
- `manifest.json`: 3.x single source of truth for product boundary, targets, profiles and assets.
- `manifest.yaml`: compatibility mirror guarded by `tools/check_manifest_sync.py`.

## Build, Test, and Development Commands
- `bash scripts/devkit.sh validate --strict`: full structure/schema validation.
- `bash scripts/devkit.sh validate --quick`: fast pre-check for local iteration.
- `bash scripts/devkit.sh export --target claude-code --profile core --out dist --clean`: export deterministic assets for a direct target.
- `bash scripts/devkit.sh install plan ...` / `install apply` / `install rollback`: transactional installation lifecycle.
- `bash scripts/devkit.sh release check`: validate version, target and release contracts.
- `bash scripts/devkit.sh catalog build`: regenerate catalog docs.
- `bash scripts/devkit.sh match --skill adk-requirements-triage --text "..."`: trigger matching.
- `bash tests/run_all.sh`: complete regression (required before merge).

## Coding Style & Naming Conventions
- Shell scripts use `bash`, `set -euo pipefail`, LF endings, and kebab-case file names.
- Agent/Skill IDs must be kebab-case and match manifest names.
- `SKILL.md` requires frontmatter keys: `name/description/triggers/non_triggers/inputs/outputs/constraints`.
- Prefer small, focused changes; avoid unrelated refactors.

## Testing Guidelines
- Add or update tests for every behavior change in `scripts/`, `manifest.yaml`, or templates.
- Keep tests deterministic and non-interactive.
- For workflow changes, validate `propose -> apply -> verify -> review -> archive` end-to-end.
- Ensure state transition gates are preserved (`proposed -> applied -> verified -> review-passed`).

## Commit & Pull Request Guidelines
- Commit format: `<type>(scope): <summary>` (e.g., `feat(workflow): 增加 review 门禁`).
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
- PRs must include: change summary, validation evidence, risk/rollback note, and affected files.

## Safety & Quality Gates
- Do not claim completion without verification evidence.
- Debugging follows read-only-first and single-variable experiments.
- Keep negative findings (`negative-results.md`) to avoid repeated failed paths.
- Breaking changes must be explicitly declared with migration and rollback plans.
- One change should focus on one real problem; avoid bundling unrelated fixes.
- Explicitly decide whether a capability belongs to `core` or `optional-skills`.

## 详细执行规则与生命周期

- 非平凡实现、长任务、失败恢复或 Gate 变更必须读取 `docs/agent-operating-rules.md`。
- 该文档保留 R1-R8、清窗/恢复协议、八阶段生命周期、快速模式和 Gate 选择原则。
- 当前轮仍必须立即遵守：无需求/设计/tasks 不写代码；行为变更必须有测试；不弱化失败用例；扩大范围先更新计划；删除或公共 API 变更前先检索调用点；没有验证证据不得声明完成。

---

## 当前资产边界

### 功能定位
adk 是面向通用 Agent/Skill/Workflow/Profile 的生产资产包。核心目标：把本仓认可的方法论压实为可交接到显式 tool target、可验证、可回滚、可迭代的工程资产，不绑定单一运行时。

### 资产统计

- Agent、Core Skill、Optional Skill、Profile、Workflow、Target 和 MCP server 的数量以 `manifest.json` 为单一事实源，不在本文件硬编码；`manifest.yaml` 只用于兼容读取。
- 结构与数量复核使用 `bash scripts/devkit.sh validate --strict`、`bash scripts/devkit.sh catalog build`、`bash scripts/devkit.sh security check` 和 `bash scripts/devkit.sh release check`。
- MCP server 保持显式清单；空清单表示默认不隐式安装 MCP。

### 硬边界
1. 不直接把 adk 资产安装到未声明或未审查的运行时目录。
2. 不保留重复 skill/profile；调试统一走 `adk-systematic-debugging`，artifact 门禁统一走 `adk-artifact-gating`。
3. 参考仓只作为治理输入，不作为生产资产来源；生产资产必须由 manifest 和 handoff fragment 声明。
4. `SKILL.md` 只保留触发、流程和输出契约；长示例与背景进入 `references/`。
