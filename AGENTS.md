<!-- repo-intro:start -->
## 仓库介绍（持续维护）

- 仓库名称：`global-dev-kit`
- 仓库定位：全局 Agent/Skill 资产与工作流门禁工具仓库
- 维护状态：持续维护（人工 + Agent 协作）
- 维护目标：在不偏离上游核心定位的前提下，保持中文可读说明、可执行流程与可验证交付。
- 维护边界：默认优先更新文档、规则与配置；涉及大规模重构或行为变更需先评估影响并记录。
- 最小验证：`bash scripts/devkit.sh test`
- 维护记录：建议在每次关键调整后追加“变更摘要 + 验证结果 + 日期”。

<!-- repo-intro:end -->

# Repository Guidelines

## Project Structure & Module Organization
- `agents/`: role-specific agent instructions (`agents/<name>/AGENTS.md`).
- `skills/`: core reusable skills (`skills/<name>/SKILL.md`).
- `optional-skills/`: opt-in skills, only installed/exported when explicitly requested.
- `scripts/`: install/convert/validate/workflow/catalog/match entrypoints.
- `docs/`: usage, commands, workflow guide, runbooks, change artifacts.
- `tests/`: shell-based regression suite and fixtures.
- `manifest.yaml`: single source of truth for tools, profiles, agents, skills, optional skills.

## Build, Test, and Development Commands
- `bash scripts/devkit.sh validate --strict`: full structure/schema validation.
- `bash scripts/devkit.sh validate --quick`: fast pre-check for local iteration.
- `bash scripts/devkit.sh install --tool codex --profile core`: install assets.
- `bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean`: export assets.
- `bash scripts/devkit.sh catalog build`: regenerate catalog docs.
- `bash scripts/devkit.sh match --skill gdk-requirements-triage --text "..."`: trigger matching.
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

---

## 仓库深度分析报告 (2026-05-05)

### 功能定位
gdk 是面向 ~/.codex 等开发代理运行目录的 Agent/Skill/Profile 生产资产包。核心目标：把参考仓中的优秀方法论压实为可安装、可验证、可回滚、可迭代的工程资产。

### 资产统计
- Agents: 10 个角色（全部 p0 级）
- Core Skills: 22 个（p0:8, p1:14）
- Optional Skills: 7 个（p2 级）
- Profiles: 10 个（core + 7 extends + 2 独立）
- Scripts: 24 个
- Tests: 21 个测试文件，59 个用例
- Docs: 42 个文档 + 26 个 Runbook

### 质量评分: 8.0/10

### 优点
1. 方法论工程化：从"口头约定"压实为可安装、可验证、可回滚的工程资产
2. 嵌入式领域深度：22 个 Core Skill 覆盖嵌入式全栈（寄存器/BSP/RTOS/协议栈/HIL-SIL）
3. Evidence Index 机制：强制"结论必有证据"，解决 AI Agent 输出可信度问题
4. Profile 分层：10 个 Profile 覆盖个人/团队/嵌入式/发布/重构/事故场景
5. 工作流门禁：propose->apply->verify->review->archive 状态机 + 分级评审
6. 多工具支持：codex/claude-code/hermes-agent/opencode 四个工具目标

### 缺点
1. 版本撕裂：manifest(1.0.0) vs README(0.3.0) 不一致
2. 配置冲突：manifest default_mode(symlink) vs README 推荐(copy)
3. 动态路由缺失：runtime routing 是静态文档，缺少运行时路由引擎
4. Evidence Index 纯 Markdown 表格，缺少结构化查询能力
5. 生产运维脚本（monitoring/auto-ops/performance/security）实现深度待验证
6. 42 个文档缺少统一导航索引
7. Profile 冲突检测缺失（两个 optional profile 叠加时的兼容性）
8. 技能间依赖关系未在 manifest 中显式声明

### 可借鉴点（供其他仓库参考）
1. manifest.yaml 单一事实源设计
2. Profile extends 继承机制
3. Evidence Index 命令级证据追加
4. devkit.sh 统一命令入口
5. check_profile_coherence.sh 自动一致性检查

### 资产来源
- 方法论类资产：从外部参考仓吸收并本地化
- 技能格式规范：遵循通用 skill 格式标准
- 门禁协议：基于通用 artifact 门禁机制
- 变更管理：基于通用变更管理流程
