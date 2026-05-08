# agent-dev-kit 文档-代码一致性审计报告

**审计日期**: 2026-05-08
**审计范围**: 所有 SKILL.md、AGENTS.md、manifest.yaml、docs/、README.md、templates/、references/

---

## 1. 断裂脚本引用（24 个脚本被文档引用但不存在）

以下脚本在 SKILL.md、docs/、README.md 或 AGENTS.md 中被引用，但实际不存在于 `scripts/` 目录：

| 缺失脚本 | 引用来源 |
|----------|---------|
| `scripts/analyze-repo.sh` | 父目录 AGENTS.md |
| `scripts/check-adk-harden-readiness.sh` | 父目录 AGENTS.md, README.md, 多个 SKILL.md, docs/commands.md |
| `scripts/check-adoption-matrix-status.sh` | docs/ |
| `scripts/check-agents-coverage.sh` | 父目录 AGENTS.md, SKILL.md |
| `scripts/check-all.sh` | 父目录 AGENTS.md |
| `scripts/check-codex-pilot.sh` | docs/ |
| `scripts/check-delivery-adopt-depth.sh` | docs/ |
| `scripts/check-doc-sync.sh` | docs/ |
| `scripts/check-global-codex-health.sh` | README.md, SKILL.md, docs/commands.md |
| `scripts/check-global-codex-target-policy.sh` | docs/ |
| `scripts/check-observe-intake-depth.sh` | docs/ |
| `scripts/check-runtime-routing.sh` | optional-skills/ |
| `scripts/check-skill-metadata.sh` | docs/ |
| `scripts/check-skill-routing-conflicts.sh` | docs/ |
| `scripts/check-upstream-intake-readiness.sh` | docs/ |
| `scripts/ci_test.sh` | SKILL.md (adk-integration-hil-sil) |
| `scripts/cleanup-reports.sh` | 父目录 AGENTS.md |
| `scripts/diff-scan.sh` | 父目录 AGENTS.md |
| `scripts/doctor.sh` | docs/ |
| `scripts/generate-adoption-matrix-summary.sh` | docs/ |
| `scripts/generate-weekly-report.sh` | 父目录 AGENTS.md, SKILL.md |
| `scripts/install-pre-commit-hook.sh` | 父目录 AGENTS.md |
| `scripts/new-repo-onboard.sh` | 父目录 AGENTS.md, SKILL.md |
| `scripts/pipeline-subrepo-update.sh` | 父目录 AGENTS.md |
| `scripts/sync-subrepos.sh` | 父目录 AGENTS.md, SKILL.md |

---

## 2. 断裂文档引用（3 个内部链接指向不存在的文件）

| 源文件 | 引用的目标 | 状态 |
|--------|-----------|------|
| `docs/reference/tool-cheatsheet.md:210` | `workflows/tool-selection.md` | **不存在** |
| `docs/reference/tool-cheatsheet.md:210` | `workflows/scenarios.md` | **不存在** |
| `docs/reference/tool-cheatsheet.md:217` | `common/prompting.md` | **不存在** |

---

## 3. NAVIGATION.md 断裂链接（3 个 Runbook 不存在）

`docs/NAVIGATION.md` 声称有 26 个 Runbooks，但以下 3 个实际不存在：

| Runbook 引用 | 状态 |
|-------------|------|
| `docs/runbooks/adk-planning-execution-loop.md` | **不存在** |
| `docs/runbooks/adk-security-supply-chain.md` | **不存在** |
| `docs/runbooks/adk-cross-team-handoff-delivery.md` | **不存在** |

---

## 4. manifest.yaml 问题

### 4.1 重复条目
- `adk-skill-deep-analyzer` 在 `skills:` 和 `routing:` 区域之后**重复声明**了两次（行 348-355 和 557-560）

### 4.2 3 个 Skill 目录存在但未在 manifest 中声明
| 目录 | 状态 |
|------|------|
| `skills/adk-artifact-gating/` | 有 SKILL.md 但未列入 manifest |
| `skills/adk-intake-workflow/` | 有 SKILL.md 但未列入 manifest |
| `skills/adk-pilot-framework/` | 有 SKILL.md 但未列入 manifest |

---

## 5. 版本不一致

| 来源 | 版本 |
|------|------|
| `manifest.yaml` | **2.7.0** |
| `.version-lock` | **2.7.0** |
| `README.md` 第 5 行 | **2.6.0** ❌ |
| `CHANGELOG.md` 最新条目 | v2.6.0 |

README.md 中的版本落后于 manifest.yaml。

---

## 6. 统计数据不一致

`AGENTS.md` 中"深度分析报告"声称的数据 vs 实际：

| 指标 | AGENTS.md 声称 | 实际值 | 差异 |
|------|---------------|--------|------|
| Core Skills | 22 | **33** | +11 |
| Optional Skills | 7 | **10** | +3 |
| Profiles | 10 | **23** (含 quality_tiers) | 概念不同 |
| Tests 文件数 | 21 | **29** | +8 |
| Docs 数 | 42 | **58** | +16 |
| Runbooks 数 | 26 | **31** | +5 |
| Scripts 数 | 24 | **24** | ✅ 一致 |
| Agents 数 | 10 | **10** | ✅ 一致 |

---

## 7. 孤立文件（存在但未被任何文档引用）

### 7.1 孤立文档（12 个）

| 文件 | 说明 |
|------|------|
| `docs/best-practices-cookbook.md` | 最佳实践菜谱 |
| `docs/hook-degradation-pattern.md` | Hook 降级模式 |
| `docs/reference-adoption-matrix.md` | 参考采纳矩阵 |
| `docs/skill-audit-2026-05-05.md` | 技能审计报告 |
| `docs/workspace-governance.md` | 工作区治理 |
| `docs/reference/superpowers-agents.md` | Superpowers 参考 |
| `docs/reference/tool-cheatsheet.md` | 工具速查表 |
| `docs/runbooks/artifact-gated-protocol-full.md` | 完整门禁协议 |
| `docs/runbooks/codex-pilot-evidence.md` | Codex Pilot 证据 |
| `docs/runbooks/gitlab-runner-setup.md` | GitLab Runner 设置 |
| `docs/runbooks/workspace-maintenance-guide.md` | 工作区维护指南 |
| `docs/runbooks/workspace-scripts-guide.md` | 工作区脚本指南 |

### 7.2 孤立模板（16 个）

所有 `templates/artifacts/` 和 `templates/workflows/` 下的模板均未被任何文档引用：

- `templates/agent-template.md`
- `templates/skill-template.md`
- `templates/artifacts/approval-template.md`
- `templates/artifacts/blocked-template.md`
- `templates/artifacts/code-delivery-template.md`
- `templates/artifacts/design-spec-template.md`
- `templates/artifacts/implementation-plan-template.md`
- `templates/artifacts/review-report-template.md`
- `templates/artifacts/review-verdict-template.md`
- `templates/artifacts/system-arch-template.md`
- `templates/artifacts/task-breakdown-template.md`
- `templates/artifacts/tech-debt-ticket.md`
- `templates/artifacts/test-report-template.md`
- `templates/artifacts/user-story-template.md`
- `templates/workflows/emergency-workflow-template.md`
- `templates/workflows/standard-workflow-template.md`

### 7.3 孤立 references/（4 个）

`references/` 目录下所有文件均未被引用：

- `references/acceptance-criteria-format.md`
- `references/context-collection-guide.md`
- `references/design-principles.md`
- `references/orchestration-patterns.md`

### 7.4 孤立脚本（1 个）

- `scripts/check-terminology-consistency.sh` — 存在但未被任何文档引用

### 7.5 孤立根目录文件（6 个）

| 文件 | 状态 |
|------|------|
| `FULL-AUDIT-2026-05-05.md` | 历史审计报告，未归档 |
| `PHASE3-COMPLETE.md` | 阶段完成报告，未归档 |
| `PHASE4-COMPLETE.md` | 阶段完成报告，未归档 |
| `PRODUCTION-READINESS-AUDIT.md` | 生产就绪审计，未归档 |
| `OPTIMIZATION-PLAN-2.0.0.md` | 优化计划，未归档 |
| `CHANGELOG-1.0.0.md` | 旧版变更日志 |

### 7.6 .out-of-scope/ 目录（2 个文件）

- `.out-of-scope/gdk-prefix-not-global.md`
- `.out-of-scope/README.md`

---

## 8. AGENTS.md 引用缺失文件

- `negative-results.md` — AGENTS.md 第 54 行引用作为示例文件，但根目录不存在（这是模板文件，非实际文件，但引用方式容易误导）

---

## 9. 问题汇总统计

| 类别 | 数量 |
|------|------|
| 断裂脚本引用 | **24** |
| 断裂文档链接 | **3** |
| NAVIGATION.md 断裂 Runbook 链接 | **3** |
| manifest.yaml 重复条目 | **1** |
| 未注册到 manifest 的 Skill | **3** |
| 版本不一致 | **1** |
| 统计数据过期 | **6 项** |
| 孤立文档 | **12** |
| 孤立模板 | **16** |
| 孤立 references | **4** |
| 孤立脚本 | **1** |
| 孤立根目录文件 | **6** |
| **总计问题** | **80** |

---

## 10. 建议修复优先级

### P0（立即修复）
1. **修复 README.md 版本号**: 2.6.0 → 2.7.0
2. **移除 manifest.yaml 中 adk-skill-deep-analyzer 重复条目**
3. **将 3 个未注册 Skill 加入 manifest**: adk-artifact-gating, adk-intake-workflow, adk-pilot-framework
4. **修复 NAVIGATION.md 断裂 Runbook 链接**: 删除不存在的条目或创建对应文件

### P1（近期修复）
5. **更新 AGENTS.md 统计数据**使其与实际一致
6. **修复 docs/reference/tool-cheatsheet.md 中 3 个断裂链接**
7. **审查 24 个断裂脚本引用**: 要么创建缺失脚本，要么清除无效引用
8. **归档或删除根目录历史文件** (FULL-AUDIT, PHASE3/4-COMPLETE 等)

### P2（后续优化）
9. **为孤立文档添加 NAVIGATION.md 条目或标记归档**
10. **为孤立模板添加引用或移至 archive/**
11. **清理 references/ 目录** — 要么集成到文档，要么归档
12. **更新 AGENTS.md 中"深度分析报告"的统计数据**

---

*审计完成。共发现 80 个文档-代码一致性问题。*
